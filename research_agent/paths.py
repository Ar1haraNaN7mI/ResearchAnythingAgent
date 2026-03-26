from __future__ import annotations

from pathlib import Path

# Workspace root: parent of research_agent/
ROOT = Path(__file__).resolve().parent.parent
AUTORESEARCH_DIR = ROOT / "autoresearch"
CIL_SCRIPT = ROOT / "cil_anything.py"

__all__ = ["ROOT", "AUTORESEARCH_DIR", "CIL_SCRIPT"]
