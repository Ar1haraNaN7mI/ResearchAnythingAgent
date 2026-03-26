from __future__ import annotations

import re
from typing import Optional, Tuple

from research_agent.executor import ProcessRunner
from research_agent.os_info import current_os_family
from research_agent.os_translate import infer_linux_windows_from_line, translate_for_current_os

LogRc = Tuple[str, int]


def _hint_to_source_os(hint: str) -> str:
    if hint == "darwin":
        return "darwin"
    if hint == "linux":
        return "linux"
    return "windows"


def try_handle_os_command(raw: str, runner: ProcessRunner) -> Optional[LogRc]:
    """
    OS / shell lines bypass the LLM (no `claude` call).
    Returns None if this line should be handled by the rest of the dispatcher.
    """
    text = raw.strip()
    if not text:
        return None

    low = text.lower()

    if low.startswith("shell "):
        cmd = text[6:].strip()
        if not cmd:
            return ("Usage: shell <command>", 1)
        rc = runner.run_shell(cmd)
        return (f"[shell] exit {rc}", 0 if rc == 0 else 1)

    m = re.match(r"^os\s+(win|windows|linux|ubuntu)\s+(.+)$", text, re.I | re.S)
    if m:
        tag = m.group(1).lower()
        inner = m.group(2).strip()
        if not inner:
            return ("Usage: os linux|ubuntu|win|windows <command>", 1)
        src_os = "linux" if tag in ("linux", "ubuntu") else "windows"
        note, cmd = translate_for_current_os(inner, src_os)
        rc = runner.run_shell(cmd)
        return (f"{note}\n[os] exit {rc}", 0 if rc == 0 else 1)

    hint = infer_linux_windows_from_line(text)
    if hint is None:
        return None

    fam = current_os_family()

    if (hint == "windows" and fam == "windows") or (hint == "linux" and fam == "linux") or (
        hint == "darwin" and fam == "darwin"
    ):
        rc = runner.run_shell(text)
        return (f"[os native] exit {rc}", 0 if rc == 0 else 1)

    src = _hint_to_source_os(hint)
    note, cmd = translate_for_current_os(text, src)
    rc = runner.run_shell(cmd)
    return (f"{note}\n[os] exit {rc}", 0 if rc == 0 else 1)
