from __future__ import annotations

from pathlib import Path

_MAX_CHARS = 5000

_DRAWIO_EN = (
    "drawio",
    "draw.io",
    "flowchart",
    "next-ai-draw-io",
    "mxgraph",
    "drawio_exports",
)
_DRAWIO_ZH = (
    "流程图",
    "架构图",
    "示意图",
    "时序图",
    "拓扑图",
    "绘图",
    "画图",
    "draw.io",
)

_SCRAPE_EN = (
    "scrapling",
    "scrape",
    "scraping",
    "web scrape",
    "web-scrap",
    "crawler",
    "crawl ",
    "crawling",
    "parse html",
    "html parse",
    "css selector",
    "xpath",
    "fetch url",
    "fetch the page",
    "get the page",
    "page source",
    "anti-bot",
    "cloudflare",
    "curl_cffi",
    "stealthy fetch",
)
_SCRAPE_ZH = (
    "爬虫",
    "抓取网页",
    "爬取",
    "网页抓取",
    "获取网页",
    "解析html",
    "解析 html",
    "查看网页",
    "打开网页",
    "页面抓取",
    "页面内容",
    "网站内容",
)


def prompt_requests_drawio(text: str) -> bool:
    """True if the user message likely needs diagram / draw.io help."""
    if not text or not text.strip():
        return False
    low = text.lower()
    if any(n in low for n in _DRAWIO_EN):
        return True
    return any(n in text for n in _DRAWIO_ZH)


def prompt_requests_scrapling(text: str) -> bool:
    """True if the user message likely needs scraping or live page/HTML inspection."""
    if not text or not text.strip():
        return False
    low = text.lower()
    if any(n in low for n in _SCRAPE_EN):
        return True
    return any(n in text for n in _SCRAPE_ZH)


def _snippet(md_path: Path) -> str:
    if not md_path.is_file():
        return f"(missing {md_path.name})"
    body = md_path.read_text(encoding="utf-8", errors="replace").strip()
    if len(body) > _MAX_CHARS:
        body = body[:_MAX_CHARS] + "\n\n[truncated]"
    return body


def build_conditional_skill_context(instruction: str, context: str = "") -> str:
    """
    Extra system context for llm_code_assist only when the combined prompt
    indicates draw.io or scraping intent. Empty string = inject nothing.
    """
    combined = f"{instruction}\n{context}".strip()
    parts: list[str] = []

    if prompt_requests_drawio(combined):
        p = Path(__file__).resolve().parent / "drawio" / "SKILL.md"
        parts.append(
            "### Draw.io skill reference (injected because the user message suggests diagrams)\n"
            "Chat commands: `drawio guide`, `drawio path`, `drawio bg transparent|white`, `drawio url`.\n\n"
            + _snippet(p)
        )

    if prompt_requests_scrapling(combined):
        p = Path(__file__).resolve().parent / "scrapling" / "SKILL.md"
        parts.append(
            "### Scrapling skill reference (injected because the user message suggests scraping / pages)\n"
            "Chat commands: `scrapling guide`, `scrapling fetch <url> [css]`, `scrapling parse <file> <css>`, "
            "`scrapling mcp --http ...`.\n\n"
            + _snippet(p)
        )

    if not parts:
        return ""

    return "\n\n---\n\n".join(parts)
