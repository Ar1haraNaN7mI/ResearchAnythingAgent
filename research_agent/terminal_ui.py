from __future__ import annotations

import sys
import threading
import time
from research_agent import runtime

_print_lock = threading.Lock()

# ANSI: terminal "loading skin" analogous to the HTML/CSS splash (no real CSS in consoles).
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_C = "\033[96m"  # bright cyan
_M = "\033[95m"  # bright magenta
_G = "\033[92m"  # green
_Y = "\033[93m"


def enable_terminal_colors() -> None:
    """Enable ANSI colors in Windows console (safe no-op elsewhere)."""
    _enable_windows_ansi()


def _enable_windows_ansi() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return
        mode.value |= 0x0004
        kernel32.SetConsoleMode(handle, mode)
    except Exception:
        pass


def _print_splash_frame(progress: float, phase: int) -> None:
    """Redraw splash (same aesthetic role as the web boot layer)."""
    bar_w = 36
    filled = int(bar_w * progress)
    bar = _G + "█" * filled + _DIM + "░" * (bar_w - filled) + _RESET
    hues = (_C, _M, _Y, _C)
    h = hues[phase % len(hues)]
    lines = [
        "",
        h + _BOLD + "   ╔══════════════════════════════════════════╗" + _RESET,
        h + _BOLD + "   ║  RESEARCH ANYTHING                       ║" + _RESET,
        _DIM + "   ║  autoresearch · CIL · Claude             " + _RESET + _DIM + "║" + _RESET,
        h + _BOLD + "   ╚══════════════════════════════════════════╝" + _RESET,
        "",
        "   " + bar + "  " + _C + f"{int(progress * 100):3d}%" + _RESET,
        "",
    ]
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.write("\n".join(lines))
    sys.stdout.flush()


def run_boot_animation(duration_sec: float = 2.8) -> None:
    """
    Full-screen terminal loading sequence (styled like the HTML boot screen).
    Uses ANSI motion and a progress bar, not browser CSS.
    """
    _enable_windows_ansi()
    t0 = time.monotonic()
    phase = 0
    while True:
        elapsed = time.monotonic() - t0
        p = min(1.0, elapsed / duration_sec)
        _print_splash_frame(p, phase)
        if p >= 1.0:
            break
        time.sleep(0.05)
        phase += 1
    time.sleep(0.15)
    sys.stdout.write(_RESET + "\n")
    sys.stdout.flush()


def _terminal_broadcast(msg: str) -> None:
    with _print_lock:
        print(msg, flush=True)


def run_terminal_session(prompt: str = "RA> ") -> None:
    """TTY command loop: same agent queue as the web UI."""
    run_boot_animation()
    runtime.start_worker(_terminal_broadcast)
    with _print_lock:
        print(
            _C
            + _BOLD
            + "RESEARCH ANYTHING"
            + _RESET
            + _DIM
            + " — terminal mode · type `help` · Ctrl+C to exit"
            + _RESET,
            flush=True,
        )
    try:
        while True:
            try:
                line = input(prompt)
            except EOFError:
                break
            text = line.strip()
            if not text:
                continue
            try:
                runtime.get_bus().prepend_user(text)
            except ValueError:
                continue
            w = runtime.get_worker()
            if w:
                w.on_user_command_submitted()
    except KeyboardInterrupt:
        with _print_lock:
            print("\n" + _DIM + "exit" + _RESET, flush=True)
