from __future__ import annotations

from pathlib import Path

# Workspace root: parent of research_agent/
ROOT = Path(__file__).resolve().parent.parent
AUTORESEARCH_DIR = ROOT / "autoresearch"
CIL_SCRIPT = ROOT / "cil_anything.py"
# Vendored Scrapling library (see research_agent/skills/scrapling/SKILL.md)
SCRAPLING_DIR = ROOT / "Scrapling"

__all__ = ["ROOT", "AUTORESEARCH_DIR", "CIL_SCRIPT", "SCRAPLING_DIR"]
