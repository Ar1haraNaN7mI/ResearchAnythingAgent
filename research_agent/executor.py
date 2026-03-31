from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable, Optional

from research_agent.paths import AUTORESEARCH_DIR, CIL_SCRIPT, ROOT

SCRAPLING_ENTRY = Path(__file__).resolve().parent / "scrapling_entry.py"


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

    def run_shell(self, command: str, cwd: Optional[Path] = None) -> int:
        """Run a shell string on the current OS (cmd.exe / PowerShell on Windows, /bin/sh on Unix)."""
        self._log(f"[shell] {command}" + (f"  (cwd={cwd})" if cwd else ""))
        rc, _ = self._run_shell_impl(command, cwd=cwd, capture=False)
        return rc

    def run_shell_capture(self, command: str, cwd: Optional[Path] = None) -> tuple[int, str]:
        """Like run_shell but returns (exit_code, full combined output) for repair loops."""
        self._log(f"[shell] {command}" + (f"  (cwd={cwd})" if cwd else ""))
        return self._run_shell_impl(command, cwd=cwd, capture=True)

    def _run_shell_impl(
        self, command: str, cwd: Optional[Path], capture: bool
    ) -> tuple[int, str]:
        cwd_s = str(cwd) if cwd is not None else None
        with self._lock:
            if sys.platform == "win32":
                self._proc = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=cwd_s,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            else:
                self._proc = subprocess.Popen(
                    ["/bin/sh", "-c", command],
                    cwd=cwd_s,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            proc = self._proc
        assert proc is not None
        assert proc.stdout is not None
        chunks: list[str] = []
        try:
            for line in proc.stdout:
                if capture:
                    chunks.append(line)
                self._log(line.rstrip())
            rc = proc.wait()
            out = "".join(chunks) if capture else ""
            return int(rc), out
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

    def run_scrapling_cli(self, *cli_args: str) -> int:
        """Upstream Scrapling CLI: mcp, shell, extract, install (vendored under Scrapling/)."""
        self._log(f"[scrapling-cli] {' '.join(cli_args)}")
        return self._run_list([sys.executable, str(SCRAPLING_ENTRY), *cli_args], cwd=ROOT)
