from __future__ import annotations

from typing import Any


def search_web(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Lightweight web search via DDGS metasearch (no API key).
    Returns list of dicts with keys: title, href, body.
    """
    try:
        from ddgs import DDGS
    except ImportError as exc:
        raise RuntimeError(
            "ddgs is required for web search. Install: pip install ddgs"
        ) from exc

    q = query.strip()
    if not q:
        return []

    n = max(1, min(15, int(max_results)))
    out: list[dict[str, Any]] = []
    with DDGS() as ddgs:
        for r in ddgs.text(q, max_results=n):
            if isinstance(r, dict):
                out.append(
                    {
                        "title": str(r.get("title", "")),
                        "href": str(r.get("href", "")),
                        "body": str(r.get("body", "")),
                    }
                )
            else:
                out.append({"title": str(r), "href": "", "body": ""})
    return out


def format_search_for_llm(query: str, max_results: int = 5) -> str:
    """Human-readable block for LLM context."""
    rows = search_web(query, max_results=max_results)
    lines = [f"### Web search: {query}\n"]
    for i, r in enumerate(rows, 1):
        title = r.get("title", "")
        href = r.get("href", "")
        body = (r.get("body") or "")[:800]
        lines.append(f"{i}. **{title}**\n   {href}\n   {body}\n")
    return "\n".join(lines)
