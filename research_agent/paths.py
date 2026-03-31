from __future__ import annotations

import os
from pathlib import Path

# Workspace root: parent of research_agent/
ROOT = Path(__file__).resolve().parent.parent
AUTORESEARCH_DIR = ROOT / "autoresearch"
CIL_SCRIPT = ROOT / "cil_anything.py"
# Vendored Scrapling library (see research_agent/skills/scrapling/SKILL.md)
SCRAPLING_DIR = ROOT / "Scrapling"


def drawio_export_dir() -> Path:
    """Directory for exported diagrams (PNG/SVG/drawio); MCP uses DRAWIO_EXPORT_DIR the same way."""
    raw = os.environ.get("DRAWIO_EXPORT_DIR", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (ROOT / "drawio_exports").resolve()


__all__ = [
    "ROOT",
    "AUTORESEARCH_DIR",
    "CIL_SCRIPT",
    "SCRAPLING_DIR",
    "drawio_export_dir",
]
