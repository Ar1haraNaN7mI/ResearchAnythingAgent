from __future__ import annotations

import threading
from typing import Callable, Optional

from research_agent.priority_queue import PriorityCommandBus
from research_agent.worker import ResearchWorker

LogFn = Callable[[str], None]

_bus = PriorityCommandBus()
_worker: Optional[ResearchWorker] = None
_worker_lock = threading.Lock()


def get_bus() -> PriorityCommandBus:
    return _bus


def get_worker() -> Optional[ResearchWorker]:
    return _worker


def start_worker(broadcast: LogFn) -> ResearchWorker:
    """Start the research worker thread once (idempotent)."""
    global _worker
    with _worker_lock:
        if _worker is not None and _worker.is_alive():
            return _worker
        _worker = ResearchWorker(_bus, broadcast)
        _worker.start()
        return _worker
