from __future__ import annotations

from pathlib import Path

import os

from research_agent.llm_settings import next_drawio_url
from research_agent.paths import drawio_export_dir

_PREF_FILE = ".png_background"
_SKILL_MD = Path(__file__).resolve().parent / "drawio" / "SKILL.md"


def _effective_png_background() -> str:
    """Match MCP order: env beats on-disk .png_background; default transparent."""
    env = os.environ.get("DRAWIO_EXPORT_PNG_BACKGROUND", "").strip().lower()
    if env in ("white", "opaque"):
        return "white"
    if env in ("transparent", "clear"):
        return "transparent"
    d = drawio_export_dir()
    pref = d / _PREF_FILE
    if pref.is_file():
        t = pref.read_text(encoding="utf-8", errors="replace").strip().lower()
        if t in ("white", "opaque"):
            return "white"
        if t in ("transparent", "clear"):
            return "transparent"
    return "transparent"


def _usage() -> str:
    return """drawio — Next AI Draw.io (folder: next-ai-draw-io/)
  drawio guide   — export path, PNG background, MCP notes
  drawio url     — open app URL (NEXT_DRAWIO_URL)
  drawio path    — diagram export directory (DRAWIO_EXPORT_DIR or drawio_exports/)
  drawio status  — path + effective PNG background (transparent default)
  drawio bg transparent | drawio bg white  — default PNG backdrop for MCP / embed
Prefix: `skill drawio …`"""


def handle_drawio(args: list[str]) -> tuple[str, int]:
    if not args or args[0].lower() in ("help", "-h", "--help"):
        return (_usage(), 0)

    sub = args[0].lower()
    rest = args[1:]

    if sub == "guide":
        if not _SKILL_MD.is_file():
            return (f"Missing {_SKILL_MD}", 1)
        text = _SKILL_MD.read_text(encoding="utf-8", errors="replace")
        return (text, 0)

    if sub == "url":
        return (next_drawio_url(), 0)

    if sub == "path":
        d = drawio_export_dir()
        d.mkdir(parents=True, exist_ok=True)
        return (str(d), 0)

    if sub == "status":
        d = drawio_export_dir()
        d.mkdir(parents=True, exist_ok=True)
        bg = _effective_png_background()
        pref = d / _PREF_FILE
        hint = f"pref_file={pref}" if pref.is_file() else f"pref_file=(none, using env/default)"
        return (
            f"export_dir={d}\n"
            f"png_background={bg}\n"
            f"{hint}\n"
            f"app={next_drawio_url()}",
            0,
        )

    if sub == "bg":
        if not rest:
            return ("Usage: drawio bg transparent | drawio bg white", 1)
        mode = rest[0].lower()
        if mode not in ("transparent", "white"):
            return ("Use: transparent or white", 1)
        d = drawio_export_dir()
        d.mkdir(parents=True, exist_ok=True)
        p = d / _PREF_FILE
        p.write_text(mode, encoding="utf-8")
        return (
            f"PNG export background default set to {mode!r}.\n"
            f"Wrote {p}\n"
            "MCP reads this when DRAWIO_EXPORT_DIR points at this folder (match root .env).",
            0,
        )

    return (f"Unknown drawio subcommand {sub!r}. {_usage()}", 1)
