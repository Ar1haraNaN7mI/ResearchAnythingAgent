from __future__ import annotations

import os
import re

from research_agent.knowledge.db import has_any_chunks, search_fts


def build_fts_query(user_text: str) -> str:
    """Token OR-query for FTS5; empty if nothing usable."""
    raw = (user_text or "").strip()
    if not raw:
        return ""
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", raw, flags=re.UNICODE)
    tokens = [t for t in tokens if len(t) >= 2][:18]
    if not tokens:
        return ""
    parts: list[str] = []
    for t in tokens:
        esc = t.replace('"', '""')
        parts.append(f'"{esc}"')
    return " OR ".join(parts)


def retrieve_for_prompt(user_text: str, *, max_chars: int = 6000) -> str:
    if os.environ.get("KB_RETRIEVE_DISABLE", "").strip().lower() in ("1", "true", "yes"):
        return ""
    if not has_any_chunks():
        return ""
    q = build_fts_query(user_text)
    if not q:
        return ""
    rows = search_fts(q, limit=30)
    if not rows:
        return ""
    lines: list[str] = []
    used = 0
    seen: set[tuple[str, str]] = set()
    for source_key, chunk_text, _rank in rows:
        key = (source_key, chunk_text[:200])
        if key in seen:
            continue
        seen.add(key)
        block = f"[{source_key}]\n{chunk_text.strip()}\n"
        if used + len(block) > max_chars:
            remain = max_chars - used
            if remain < 200:
                break
            block = f"[{source_key}]\n{chunk_text.strip()[:remain]}\n…\n"
        lines.append(block)
        used += len(block)
        if used >= max_chars:
            break
    return "\n".join(lines).strip()
