from __future__ import annotations

from pathlib import Path

from research_agent.knowledge.db import (
    clear_all,
    delete_source,
    list_sources,
    total_chunk_count,
)
from research_agent.knowledge.ingest import ingest_path
from research_agent.knowledge.retrieve import build_fts_query, retrieve_for_prompt
from research_agent.llm_settings import kb_retrieve_max_chars
from research_agent.paths import knowledge_base_dir

_SKILL_MD = Path(__file__).resolve().parent / "knowledge" / "SKILL.md"
_MANUAL_MD = Path(__file__).resolve().parent / "knowledge" / "MANUAL.md"


def _usage() -> str:
    return """kb — local knowledge base (Markdown, text, HTML, PDF)
  kb manual             — detailed handbook (web ?commands, REST, Git sync)
  kb guide              — concise skill doc (OpenDataLoader PDF, env, retrieval)
  kb status             — chunk count, index path, retrieve budget
  kb list               — numbered sources (use with kb remove <n>)
  kb add <file>         — ingest .pdf .md .txt .html (PDF needs Java 11+)
  kb remove <n>         — remove source #n from kb list
  kb search <query>     — debug FTS excerpts (same style as LLM injection)
  kb clear              — delete all indexed chunks (files on disk stay)
  kb sync               — git add/commit/push knowledge_base/github_sync/ (needs env allow)
Chat shortcuts: ?upload  ?delete <n>  ?sync
Prefix: `skill kb …`"""


def handle_kb(args: list[str]) -> tuple[str, int]:
    if not args or args[0].lower() in ("help", "-h", "--help"):
        return (_usage(), 0)

    sub = args[0].lower()
    rest = args[1:]

    if sub == "manual":
        if not _MANUAL_MD.is_file():
            return (f"Missing {_MANUAL_MD}", 1)
        return (_MANUAL_MD.read_text(encoding="utf-8", errors="replace"), 0)

    if sub == "guide":
        if not _SKILL_MD.is_file():
            return (f"Missing {_SKILL_MD}", 1)
        return (_SKILL_MD.read_text(encoding="utf-8", errors="replace"), 0)

    if sub == "sync":
        from research_agent.knowledge.git_sync import run_knowledge_github_sync

        return run_knowledge_github_sync()

    if sub == "status":
        n = total_chunk_count()
        root = knowledge_base_dir()
        budget = kb_retrieve_max_chars()
        return (
            f"knowledge_base_dir={root}\n"
            f"indexed_chunks={n}\n"
            f"KB_RETRIEVE_MAX_CHARS={budget}\n"
            f"Set KB_RETRIEVE_DISABLE=1 to turn off LLM retrieval.",
            0,
        )

    if sub == "list":
        rows = list_sources()
        if not rows:
            return ("(no sources)", 0)
        lines = []
        for i, (key, cnt) in enumerate(rows, start=1):
            lines.append(f"{i}. {key}  ({cnt} chunks)")
        return ("\n".join(lines), 0)

    if sub == "add":
        if not rest:
            return ("Usage: kb add <path-to-file>", 1)
        raw_path = " ".join(rest).strip().strip('"')
        p = Path(raw_path)
        try:
            key, chunks = ingest_path(p)
            return (f"Added {key!r} ({chunks} chunks).", 0)
        except Exception as exc:
            return (f"kb add failed: {exc}", 1)

    if sub == "remove":
        if not rest:
            return ("Usage: kb remove <n>  (see kb list)", 1)
        idx_s = rest[0].strip()
        try:
            idx = int(idx_s)
        except ValueError:
            return (f"Invalid index: {idx_s!r}", 1)
        rows = list_sources()
        if idx < 1 or idx > len(rows):
            return (f"Index out of range (1–{len(rows)}).", 1)
        key = rows[idx - 1][0]
        deleted = delete_source(key)
        return (f"Removed {key!r} ({deleted} rows).", 0)

    if sub == "search":
        q = " ".join(rest).strip()
        if not q:
            return ("Usage: kb search <query>", 1)
        text = retrieve_for_prompt(q, max_chars=kb_retrieve_max_chars())
        if not text:
            fts_q = build_fts_query(q)
            return (
                f"(no hits) fts_query={fts_q!r}" if fts_q else "(no hits; query too short)",
                0,
            )
        return (text, 0)

    if sub == "clear":
        clear_all()
        return ("Cleared all chunks from the index (files under knowledge_base/files/ unchanged).", 0)

    return (_usage(), 0)
