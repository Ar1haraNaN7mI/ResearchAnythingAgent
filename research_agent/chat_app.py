from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from research_agent import runtime
from research_agent.llm_settings import llm_config_summary
from research_agent.os_info import format_startup_paragraph

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Research Agent Chatboard")

_clients: List[WebSocket] = []
_main_loop: asyncio.AbstractEventLoop | None = None
_worker_lock = threading.Lock()


def _broadcast_threadsafe(message: str) -> None:
    loop = _main_loop
    if loop is None:
        return
    asyncio.run_coroutine_threadsafe(_broadcast_all(message), loop)


async def _broadcast_all(message: str) -> None:
    dead: List[WebSocket] = []
    for ws in list(_clients):
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in _clients:
            _clients.remove(ws)


@app.on_event("startup")
async def _startup() -> None:
    global _main_loop
    _main_loop = asyncio.get_event_loop()
    with _worker_lock:
        runtime.start_worker(_broadcast_threadsafe)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/system")
async def system_info() -> dict:
    """JSON for optional frontend banner; same text as startup paragraph."""
    return {"text": format_startup_paragraph(), "llm": llm_config_summary()}


@app.websocket("/ws")
async def websocket_chat(websocket: WebSocket) -> None:
    await websocket.accept()
    _clients.append(websocket)
    await websocket.send_text(
        format_startup_paragraph() + "\n\n[agent] connected. Type `help` for commands."
    )
    try:
        while True:
            raw = await websocket.receive_text()
            text = raw.strip()
            if not text:
                continue
            await websocket.send_text(f"[you] {text}")
            try:
                runtime.get_bus().prepend_user(text)
            except ValueError:
                await websocket.send_text("[agent] ignored empty message")
                continue
            w = runtime.get_worker()
            if w:
                w.on_user_command_submitted()
    except WebSocketDisconnect:
        if websocket in _clients:
            _clients.remove(websocket)
