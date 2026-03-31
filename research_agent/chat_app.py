from __future__ import annotations

import asyncio
import logging
import threading
from pathlib import Path
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from research_agent import runtime
from research_agent.llm_settings import llm_config_summary, next_drawio_url
from research_agent.os_info import format_startup_paragraph

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Research Agent Chatboard")
_log = logging.getLogger(__name__)

_clients: List[WebSocket] = []
_clients_lock = threading.Lock()
_main_loop: asyncio.AbstractEventLoop | None = None
_worker_lock = threading.Lock()


def _broadcast_threadsafe(message: str) -> None:
    loop = _main_loop
    if loop is None:
        return

    def _log_future_exc(fut) -> None:
        try:
            exc = fut.exception()
            if exc is not None:
                _log.error(
                    "WebSocket broadcast failed: %s",
                    exc,
                    exc_info=(type(exc), exc, exc.__traceback__),
                )
        except Exception as cb_exc:
            _log.error(
                "Broadcast future callback error: %s",
                cb_exc,
                exc_info=(type(cb_exc), cb_exc, cb_exc.__traceback__),
            )

    fut = asyncio.run_coroutine_threadsafe(_broadcast_all(message), loop)
    fut.add_done_callback(_log_future_exc)


async def _broadcast_all(message: str) -> None:
    with _clients_lock:
        snapshot = list(_clients)
    dead: List[WebSocket] = []
    for ws in snapshot:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    if dead:
        with _clients_lock:
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
    return {
        "text": format_startup_paragraph(),
        "llm": llm_config_summary(),
        "drawio_url": next_drawio_url(),
    }


@app.websocket("/ws")
async def websocket_chat(websocket: WebSocket) -> None:
    await websocket.accept()
    with _clients_lock:
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
        with _clients_lock:
            if websocket in _clients:
                _clients.remove(websocket)
