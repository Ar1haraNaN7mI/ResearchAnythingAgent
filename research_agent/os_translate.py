from __future__ import annotations

import re
import sys
from typing import Tuple

from research_agent.os_info import current_os_family


def _norm_pkg_apt_to_winget(fragment: str) -> str:
    """Best-effort package token (may differ between stores)."""
    return fragment.strip().split()[0] if fragment.strip() else ""


def translate_for_current_os(
    command: str,
    source_os: str,
) -> Tuple[str, str]:
    """
    Map a command written for `source_os` to something sensible on the current machine.

    Returns (annotation_line, command_to_execute).

    source_os: windows | linux | ubuntu (ubuntu treated as linux)
    """
    src = source_os.lower()
    if src == "ubuntu":
        src = "linux"
    tgt = current_os_family()
    cmd = command.strip()

    if src == tgt:
        return ("(native OS — no translation)", cmd)

    # linux-style apt on macOS -> brew
    if src == "linux" and tgt == "darwin":
        m = re.match(r"^(sudo\s+)?apt(-get)?\s+install\s+(.+)$", cmd, re.I)
        if m:
            rest = m.group(3).strip()
            pkg = _norm_pkg_apt_to_winget(rest)
            return (f"[translate linux→darwin] apt install → brew: {pkg}", f"brew install {pkg}")
        return ("[translate linux→darwin] passthrough", cmd)

    # linux / ubuntu -> windows
    if src == "linux" and tgt == "windows":
        m = re.match(r"^(sudo\s+)?apt(-get)?\s+install\s+(.+)$", cmd, re.I)
        if m:
            rest = m.group(3).strip()
            pkg = _norm_pkg_apt_to_winget(rest)
            out = f'winget install --accept-package-agreements --accept-source-agreements "{pkg}"'
            return (f"[translate linux→windows] apt install → winget: {pkg}", out)
        if re.match(r"^(sudo\s+)?apt\s+update\b", cmd, re.I):
            return ("[translate linux→windows] apt update → winget source update", "winget source update")
        if re.match(r"^ls(\s|$)", cmd):
            return ("[translate linux→windows] ls → dir", "dir")
        if re.match(r"^pwd(\s|$)", cmd):
            return ("[translate linux→windows] pwd → cd", "cd")

    # windows -> linux / ubuntu
    if src == "windows" and tgt == "linux":
        m = re.match(r"^winget\s+install\s+(.+)$", cmd, re.I)
        if m:
            rest = m.group(1).strip().strip('"')
            pkg = rest.split()[0] if rest else ""
            out = f"sudo apt-get update && sudo apt-get install -y {pkg}"
            return (f"[translate windows→linux] winget install → apt: {pkg}", out)
        m = re.match(r"^dir(\s|$)", cmd, re.I)
        if m:
            return ("[translate windows→unix] dir → ls", "ls -la")
        m = re.match(r"^cd(\s|$)", cmd, re.I)
        if m:
            return ("[translate windows→unix] cd is compatible", cmd)

    if src == "windows" and tgt == "darwin":
        m = re.match(r"^winget\s+install\s+(.+)$", cmd, re.I)
        if m:
            rest = m.group(1).strip().strip('"')
            pkg = rest.split()[0] if rest else ""
            return (f"[translate windows→darwin] winget → brew: {pkg}", f"brew install {pkg}")
        m = re.match(r"^dir(\s|$)", cmd, re.I)
        if m:
            return ("[translate windows→darwin] dir → ls", "ls -la")

    if src == "darwin" and tgt == "linux":
        m = re.match(r"^brew\s+install\s+(.+)$", cmd, re.I)
        if m:
            pkg = m.group(1).strip().split()[0]
            return (f"[translate darwin→linux] brew → apt: {pkg}", f"sudo apt-get install -y {pkg}")

    return (
        "[translate] no specific rule — executing as-is on target (may fail)",
        cmd,
    )


def infer_linux_windows_from_line(line: str) -> str | None:
    """
    Guess whether a one-liner is clearly Linux-, Windows-, or Homebrew-oriented.
    Returns 'linux', 'windows', 'darwin', or None.
    """
    s = line.strip()
    low = s.lower()
    if low.startswith(
        (
            "sudo ",
            "apt ",
            "apt-get ",
            "dnf ",
            "yum ",
            "pacman ",
            "snap ",
            "systemctl ",
            "journalctl ",
        )
    ):
        return "linux"
    if low.startswith(("winget ", "choco ", "scoop ", "powershell ", "cmd /c", "cmd.exe")):
        return "windows"
    if low.startswith("brew "):
        return "darwin"
    if re.match(r"^(ls|pwd)\b", low):
        return "linux"
    if sys.platform == "win32" and re.match(r"^[a-z]:\\", s, re.I):
        return "windows"
    return None

