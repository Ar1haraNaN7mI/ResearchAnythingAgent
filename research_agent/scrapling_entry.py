"""
Launch the vendored Scrapling package CLI (mcp, shell, extract, install).

Windows PowerShell (from repo root, folder that contains research_agent/):
  python research_agent\\scrapling_entry.py install
  python research_agent\\scrapling_entry.py mcp --http --host 127.0.0.1 --port 8766

Or: research_agent\\run_scrapling.bat install
(same as above; do not type `scrapling_entry.py` alone — PowerShell is not bash.)
"""
from __future__ import annotations

import sys
from pathlib import Path

_SCRAP_ROOT = Path(__file__).resolve().parent.parent / "Scrapling"
if str(_SCRAP_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRAP_ROOT))


def main() -> None:
    argv_rest = sys.argv[1:]
    sys.argv = ["scrapling", *argv_rest]
    from scrapling.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
