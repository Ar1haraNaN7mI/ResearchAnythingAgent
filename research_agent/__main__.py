from __future__ import annotations

import argparse
import sys

import uvicorn


def _run_web() -> None:
    uvicorn.run("research_agent.chat_app:app", host="127.0.0.1", port=8765, reload=False)


def _run_terminal() -> None:
    from research_agent.terminal_ui import run_terminal_session

    run_terminal_session()


def _interactive_menu() -> None:
    from research_agent.terminal_ui import enable_terminal_colors

    enable_terminal_colors()
    print()
    print("\033[96m\033[1m  RESEARCH ANYTHING\033[0m — choose interface")
    print()
    print("  \033[1m[1]\033[0m  Web UI   → http://127.0.0.1:8765  (HTML + CSS boot screen)")
    print("  \033[1m[2]\033[0m  Terminal → ANSI boot + command line (same agent)")
    print()
    choice = input("  Enter 1 or 2 (default 1): ").strip() or "1"
    if choice == "2":
        _run_terminal()
    else:
        _run_web()


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Anything Agent")
    parser.add_argument(
        "--web",
        action="store_true",
        help="Start browser UI only (skip menu)",
    )
    parser.add_argument(
        "--terminal",
        "-t",
        action="store_true",
        help="Start terminal UI only with ANSI loading (skip menu)",
    )
    args = parser.parse_args()

    if args.terminal:
        _run_terminal()
    elif args.web:
        _run_web()
    else:
        _interactive_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
