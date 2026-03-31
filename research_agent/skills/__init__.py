from __future__ import annotations

import shlex
import sys
from typing import Callable

from research_agent.skills import scrapling_skill

SkillHandler = Callable[[list[str]], tuple[str, int]]

_HANDLERS: dict[str, SkillHandler] = {
    "scrapling": scrapling_skill.handle_scrapling,
}


def format_skills_list() -> str:
    lines = [
        "Built-in Research Agent skills (bundled Scrapling/):",
        "",
        "  scrapling — fetch/parse/guide/refs; full MCP via `scrapling mcp --http ...` (see skill scrapling guide)",
        "",
        "Usage:",
        "  skills",
        "  skill <name> [subcommand ...]",
        "  scrapling ...   (alias for skill scrapling ...)",
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
