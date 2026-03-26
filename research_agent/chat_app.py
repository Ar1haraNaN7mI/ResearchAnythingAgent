from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from research_agent.priority_queue import PriorityCommandBus
from research_agent.worker import ResearchWorker

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Research Agent Chatboard")

_bus = PriorityCommandBus()
_clients: List[WebSocket] = []
_main_loop: asyncio.AbstractEventLoop | None = None
_worker: ResearchWorker | None = None
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
    global _main_loop, _worker
    _main_loop = asyncio.get_event_loop()
    with _worker_lock:
        if _worker is not None and _worker.is_alive():
            return
        _worker = ResearchWorker(_bus, _broadcast_threadsafe)
        _worker.start()


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.websocket("/ws")
async def websocket_chat(websocket: WebSocket) -> None:
    await websocket.accept()
    _clients.append(websocket)
    await websocket.send_text("[agent] connected. Type `help` for commands.")
    try:
        while True:
            raw = await websocket.receive_text()
            text = raw.strip()
            if not text:
                continue
            await websocket.send_text(f"[you] {text}")
            try:
                _bus.prepend_user(text)
            except ValueError:
                await websocket.send_text("[agent] ignored empty message")
                continue
            if _worker:
                _worker.on_user_command_submitted()
    except WebSocketDisconnect:
        if websocket in _clients:
            _clients.remove(websocket)
