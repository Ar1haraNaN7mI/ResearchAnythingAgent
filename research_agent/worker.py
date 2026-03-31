from __future__ import annotations

import threading
import time
from typing import Callable

from research_agent.dispatcher import parse_and_dispatch, parse_auto_toggle
from research_agent.executor import ProcessRunner
from research_agent.priority_queue import CommandKind, PriorityCommandBus, QueuedCommand

LogFn = Callable[[str], None]


class ResearchWorker(threading.Thread):
    """
    Processes the command bus: USER commands first (prepended), then AUTO_RESEARCH.
    When a new USER command is submitted, call on_user_command_submitted() to cancel running work.
    """

    def __init__(self, bus: PriorityCommandBus, broadcast: LogFn) -> None:
        super().__init__(daemon=True)
        self._bus = bus
        self._broadcast = broadcast
        self._runner = ProcessRunner(log=self._broadcast_line)
        self._auto_research = False
        self._stop_worker = threading.Event()

    @property
    def runner(self) -> ProcessRunner:
        return self._runner

    @property
    def auto_research_enabled(self) -> bool:
        return self._auto_research

    def stop_worker(self) -> None:
        self._stop_worker.set()

    def _broadcast_line(self, line: str) -> None:
        self._broadcast(line)

    def run(self) -> None:
        self._broadcast("[agent] worker started")
        while not self._stop_worker.is_set():
            cmd = self._bus.pop_next(timeout=0.5)
            if cmd is None:
                continue
            self._handle(cmd)

    def _handle(self, cmd: QueuedCommand) -> None:
        self._broadcast(f"[queue] run id={cmd.id} kind={cmd.kind.name} text={cmd.text!r}")
        toggle = parse_auto_toggle(cmd.text)
        if toggle == "on":
            self._auto_research = True
            self._broadcast("[agent] auto research ON")
            if len(self._bus) == 0:
                self._bus.append_auto_research()
            return
        if toggle == "off":
            self._auto_research = False
            self._bus.clear_auto_pending()
            self._broadcast("[agent] auto research OFF")
            return

        try:
            msg, exit_code = parse_and_dispatch(cmd.text, self._runner)
            self._broadcast(f"[result] exit={exit_code} {msg}")
        except Exception as exc:
            self._broadcast(f"[error] command crashed: {exc}")

        if cmd.kind == CommandKind.AUTO_RESEARCH and self._auto_research:
            time.sleep(0.3)
            if len(self._bus) == 0:
                self._bus.append_auto_research()

    def on_user_command_submitted(self) -> None:
        self._runner.cancel()
