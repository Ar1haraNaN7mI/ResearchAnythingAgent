from __future__ import annotations

import platform
import sys
from typing import Tuple


def _read_linux_os_release() -> Tuple[str, str]:
    """Return (ID, PRETTY_NAME) from /etc/os-release if present."""
    try:
        data: dict[str, str] = {}
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                data[k.strip()] = v.strip().strip('"')
        return data.get("ID", ""), data.get("PRETTY_NAME", "")
    except OSError:
        return "", ""


def current_os_family() -> str:
    if sys.platform == "win32":
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "darwin"
    return "other"


def format_startup_paragraph() -> str:
    """
    Human-readable OS report (shown at agent startup in terminal and Web UI).
    """
    lines: list[str] = []
    lines.append("[system] Runtime environment")
    lines.append(f"  · Python {platform.python_version()} ({platform.machine()})")
    lines.append(f"  · sys.platform = {sys.platform!r}")
    plat = platform.system()
    ver = platform.version()
    lines.append(f"  · {plat} — {ver}")

    if sys.platform == "win32":
        try:
            lines.append(f"  · Windows release: {platform.release()} (build {platform.version()})")
        except Exception:
            pass
    elif sys.platform.startswith("linux"):
        oid, pretty = _read_linux_os_release()
        if pretty:
            lines.append(f"  · Linux distribution: {pretty}")
        elif oid:
            lines.append(f"  · Linux distribution ID: {oid}")
        else:
            lines.append("  · Linux (could not read /etc/os-release)")
    elif sys.platform == "darwin":
        lines.append(f"  · macOS: {platform.mac_ver()[0] or 'unknown'}")

    fam = current_os_family()
    lines.append(f"  · Agent OS family for shell routing: {fam}")
    lines.append(
        "  · OS-style commands are executed locally (no LLM). "
        "Use prefix `shell ` for raw shell, or `os linux|ubuntu|win <cmd>` for cross-OS mapping."
    )
    return "\n".join(lines)
