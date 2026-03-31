from __future__ import annotations

import shlex
import sys
from typing import Callable

from research_agent.skills import drawio_skill, kb_skill, scrapling_skill

SkillHandler = Callable[[list[str]], tuple[str, int]]

_HANDLERS: dict[str, SkillHandler] = {
    "scrapling": scrapling_skill.handle_scrapling,
    "drawio": drawio_skill.handle_drawio,
    "kb": kb_skill.handle_kb,
}


def format_skills_list() -> str:
    lines = [
        "Built-in Research Agent skills:",
        "",
        "  scrapling — fetch/parse/guide/refs; MCP: `scrapling mcp --http ...`",
        "  drawio    — next-ai-draw-io: export path, PNG bg (transparent default), URL (see skill drawio guide)",
        "  kb        — local knowledge base: PDF/md/txt/html, FTS; see `kb guide`",
        "",
        "Usage:",
        "  skills",
        "  skill <name> [subcommand ...]",
        "  scrapling …  |  drawio …  |  kb …   (same as skill <name> …)",
        "",
        "LLM (`llm` / `claude`): draw.io + Scrapling SKILL excerpts are injected only when your text",
        "looks like diagramming or scraping / viewing pages — not on every message.",
        "Indexed knowledge base excerpts are prepended on every LLM call when the index is non-empty",
        "(unless KB_RETRIEVE_DISABLE=1).",
    ]
    return "\n".join(lines)


def dispatch_skill_line(line: str) -> tuple[str, int]:
    line = line.strip()
    if not line:
        return format_skills_list(), 0
    try:
        parts = shlex.split(line, posix=(sys.platform != "win32"))
    except ValueError as exc:
        return (f"skill parse error: {exc}", 1)
    if not parts:
        return format_skills_list(), 0

    name = parts[0].lower()
    handler = _HANDLERS.get(name)
    if handler is None:
        known = ", ".join(sorted(_HANDLERS))
        return (f"Unknown skill {name!r}. Known: {known}", 1)
    return handler(parts[1:])
