from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable, Optional

from research_agent.paths import AUTORESEARCH_DIR, CIL_SCRIPT, ROOT


LogFn = Callable[[str], None]


class ProcessRunner:
    """Runs subprocesses; supports cancel via terminate (Windows-friendly)."""

    def __init__(self, log: LogFn) -> None:
        self._log = log
        self._proc: Optional[subprocess.Popen[str]] = None
        self._lock = threading.Lock()

    def cancel(self) -> None:
        with self._lock:
            p = self._proc
        if p is None:
            return
        try:
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        except Exception as exc:
            self._log(f"[cancel] {exc}")
        finally:
            with self._lock:
                self._proc = None

    def run_uv(self, *args: str, cwd: Optional[Path] = None) -> int:
        cwd = cwd or AUTORESEARCH_DIR
        cmd = ["uv", "run", *args]
        return self._run_list(cmd, cwd=cwd)

    def run_python(self, script: Path, *args: str, cwd: Optional[Path] = None) -> int:
        cmd = [sys.executable, str(script), *args]
        return self._run_list(cmd, cwd=cwd or script.parent)

    def run_shell(self, command: str) -> int:
        """Run a shell string on the current OS (cmd.exe / PowerShell on Windows, /bin/sh on Unix)."""
        self._log(f"[shell] {command}")
        with self._lock:
            if sys.platform == "win32":
                self._proc = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            else:
                self._proc = subprocess.Popen(
                    ["/bin/sh", "-c", command],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            proc = self._proc
        assert proc is not None
        assert proc.stdout is not None
        try:
            for line in proc.stdout:
                self._log(line.rstrip())
            rc = proc.wait()
            return int(rc)
        finally:
            with self._lock:
                if self._proc is proc:
                    self._proc = None

    def _run_list(self, cmd: list[str], cwd: Path) -> int:
        self._log(f"[exec] {' '.join(cmd)}")
        with self._lock:
            self._proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
            )
            proc = self._proc
        assert proc is not None
        assert proc.stdout is not None
        try:
            for line in proc.stdout:
                self._log(line.rstrip())
            rc = proc.wait()
            return int(rc)
        finally:
            with self._lock:
                if self._proc is proc:
                    self._proc = None

    def run_uv_fallback_python(self, script_name: str) -> int:
        """Prefer `uv run script` in autoresearch; fallback to `python script`."""
        if AUTORESEARCH_DIR.joinpath(script_name).exists():
            try:
                return self.run_uv(script_name)
            except FileNotFoundError:
                pass
            except OSError:
                pass
        path = AUTORESEARCH_DIR / script_name
        return self.run_python(path, cwd=AUTORESEARCH_DIR)

    def run_cil(self, *cil_args: str) -> int:
        return self._run_list([sys.executable, str(CIL_SCRIPT), *cil_args], cwd=ROOT)
