from __future__ import annotations

import re
import sys
from urllib.parse import urlparse

from research_agent.llm_settings import (
    env_setup_scrapling_max_total_chars,
    env_setup_scrapling_max_urls,
    env_setup_scrapling_per_url_chars,
    env_setup_scrapling_urls_per_query,
    env_setup_scrapling_enabled,
)
from research_agent.paths import SCRAPLING_DIR
from research_agent.web_search import search_web


def _ensure_scrapling_on_path() -> None:
    s = str(SCRAPLING_DIR.resolve())
    if s not in sys.path:
        sys.path.insert(0, s)


def _is_fetchable_doc_url(href: str) -> bool:
    h = href.strip()
    if not h.lower().startswith(("http://", "https://")):
        return False
    low = h.lower()
    if low.endswith(".pdf") or ".pdf?" in low:
        return False
    if low.startswith(("mailto:", "tel:", "javascript:")):
        return False
    try:
        host = urlparse(h).netloc.lower()
    except ValueError:
        return False
    if not host:
        return False
    skip_hosts = (
        "youtube.com",
        "youtu.be",
        "facebook.com",
        "twitter.com",
        "x.com",
        "instagram.com",
        "tiktok.com",
    )
    if any(s in host for s in skip_hosts):
        return False
    return True


def _collect_urls_from_queries(queries: list[str], *, per_query: int, max_urls: int) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for q in queries:
        if len(urls) >= max_urls:
            break
        try:
            rows = search_web(q, max_results=8)
        except Exception:
            continue
        n = 0
        for r in rows:
            if len(urls) >= max_urls or n >= per_query:
                break
            href = (r.get("href") or "").strip()
            if not href or href in seen or not _is_fetchable_doc_url(href):
                continue
            seen.add(href)
            urls.append(href)
            n += 1
    return urls


def _response_body_to_text(resp: object) -> tuple[str, bool]:
    """Returns (text, looks_like_html)."""
    raw = getattr(resp, "body", b"") or b""
    if not isinstance(raw, (bytes, bytearray)):
        raw = bytes(raw)
    try:
        html = raw.decode("utf-8", errors="replace")
    except Exception:
        html = raw.decode("latin-1", errors="replace")
    sample = html[:2000].lstrip().lower()
    if sample.startswith("<!") or "<html" in sample[:500] or "<body" in sample[:800]:
        return html, True
    return html, False


def _html_to_markdown(html: str) -> str:
    from markdownify import markdownify as md

    return md(html, heading_style="ATX", strip=["script", "style", "nav", "footer"])


def fetch_doc_pages_markdown(
    urls: list[str],
    *,
    total_budget: int,
    per_url_cap: int,
) -> str:
    """
    GET each URL via Scrapling Fetcher; convert HTML to Markdown for LLM context.
    """
    if not urls:
        return ""

    _ensure_scrapling_on_path()
    try:
        from scrapling.fetchers import Fetcher
    except ImportError as exc:
        return f"(Scrapling fetchers unavailable: {exc})\n"

    parts: list[str] = []
    used = 0
    for url in urls:
        if used >= total_budget:
            break
        try:
            resp = Fetcher.get(url)
        except Exception as exc:
            parts.append(f"### Fetch failed: {url}\n{exc}\n\n")
            continue
        try:
            status = int(getattr(resp, "status", 0))
        except (TypeError, ValueError):
            status = 0
        if status >= 400:
            parts.append(f"### HTTP {status}: {url}\n\n")
            continue
        html, is_html = _response_body_to_text(resp)
        if is_html:
            try:
                text = _html_to_markdown(html)
            except Exception as exc:
                text = f"(markdownify failed: {exc})\n{html[:per_url_cap]}"
        else:
            text = html
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if len(text) > per_url_cap:
            text = text[:per_url_cap] + "\n\n[truncated per URL cap]\n"
        block = f"### Scrapling page ({status}) {url}\n\n{text}\n\n"
        if used + len(block) > total_budget:
            remain = total_budget - used
            if remain < 400:
                break
            block = block[:remain] + "\n[truncated total budget]\n"
        parts.append(block)
        used += len(block)
    if not parts:
        return ""
    return (
        "## Official / doc pages (fetched with Scrapling for deeper context)\n\n"
        + "".join(parts)
    )


def scrapling_context_for_queries(
    queries: list[str],
    *,
    max_urls_override: int | None = None,
) -> str:
    """Search → pick URLs → Scrapling fetch → markdown blob."""
    if not env_setup_scrapling_enabled():
        return ""
    per_q = env_setup_scrapling_urls_per_query()
    max_u = env_setup_scrapling_max_urls()
    if max_urls_override is not None:
        max_u = min(max_u, max(0, max_urls_override))
    if per_q <= 0 or max_u <= 0:
        return ""
    urls = _collect_urls_from_queries(queries, per_query=per_q, max_urls=max_u)
    if not urls:
        return ""
    return fetch_doc_pages_markdown(
        urls,
        total_budget=env_setup_scrapling_max_total_chars(),
        per_url_cap=env_setup_scrapling_per_url_chars(),
    )
