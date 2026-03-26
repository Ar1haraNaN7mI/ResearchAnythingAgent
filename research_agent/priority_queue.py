from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class CommandKind(Enum):
    USER = auto()
    AUTO_RESEARCH = auto()


@dataclass
class QueuedCommand:
    kind: CommandKind
    text: str
    id: int = 0


class PriorityCommandBus:
    """
    User commands are prepended (newest user command runs first).
    Auto research tasks are appended; user work always jumps ahead.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._dq: deque[QueuedCommand] = deque()
        self._seq = 0

    def prepend_user(self, text: str) -> QueuedCommand:
        text = text.strip()
        if not text:
            raise ValueError("empty command")
        with self._cond:
            self._seq += 1
            cmd = QueuedCommand(kind=CommandKind.USER, text=text, id=self._seq)
            self._dq.appendleft(cmd)
            self._cond.notify_all()
        return cmd

    def append_auto_research(self) -> Optional[QueuedCommand]:
        with self._cond:
            self._seq += 1
            cmd = QueuedCommand(kind=CommandKind.AUTO_RESEARCH, text="train", id=self._seq)
            self._dq.append(cmd)
            self._cond.notify_all()
        return cmd

    def pop_next(self, timeout: Optional[float] = None) -> Optional[QueuedCommand]:
        with self._cond:
            if timeout is None:
                while not self._dq:
                    self._cond.wait()
                return self._dq.popleft()
            end = time.monotonic() + timeout
            while not self._dq:
                remaining = end - time.monotonic()
                if remaining <= 0:
                    return None
                self._cond.wait(timeout=remaining)
            return self._dq.popleft()

    def __len__(self) -> int:
        with self._lock:
            return len(self._dq)

    def clear_auto_pending(self) -> None:
        with self._cond:
            new_dq: deque[QueuedCommand] = deque()
            for c in self._dq:
                if c.kind != CommandKind.AUTO_RESEARCH:
                    new_dq.append(c)
            self._dq = new_dq
            self._cond.notify_all()
