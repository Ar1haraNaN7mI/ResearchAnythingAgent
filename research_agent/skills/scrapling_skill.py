from __future__ import annotations

import sys
from pathlib import Path

from research_agent.paths import ROOT, SCRAPLING_DIR

_MAX_OUT = 48_000
_SKILL_MD = Path(__file__).resolve().parent / "scrapling" / "SKILL.md"
_REFS_ROOT = SCRAPLING_DIR / "agent-skill" / "Scrapling-Skill" / "references"


def ensure_scrapling_on_path() -> None:
    s = str(SCRAPLING_DIR.resolve())
    if s not in sys.path:
        sys.path.insert(0, s)


def handle_scrapling(args: list[str]) -> tuple[str, int]:
    if not args or args[0].lower() in ("help", "-h", "--help"):
        return _usage(), 0

    sub = args[0].lower()
    rest = args[1:]

    if sub == "guide":
        return _read_skill_md()

    if sub == "refs":
        return _list_refs()

    if sub == "fetch":
        return _cmd_fetch(rest)

    if sub == "parse":
        return _cmd_parse(rest)

    return (f"Unknown scrapling subcommand {sub!r}. {_usage()}", 1)


def _usage() -> str:
    return """scrapling — bundled under Scrapling/
  Skill shortcuts:
  scrapling guide          — skill doc (API + MCP + CLI)
  scrapling refs           — list reference .md under agent-skill
  scrapling fetch <url> [css_selector]  — Fetcher.get + optional css
  scrapling parse <file> <css_selector> — Selector from local HTML
  Upstream CLI (full MCP / extract / install):
  scrapling mcp --http --host 127.0.0.1 --port 8766
  scrapling extract …  |  scrapling install  |  scrapling shell -c "…"
Prefix with `skill` is optional: `skill scrapling guide`."""


def _read_skill_md() -> tuple[str, int]:
    if not _SKILL_MD.is_file():
        return (f"Missing skill file: {_SKILL_MD}", 1)
    text = _SKILL_MD.read_text(encoding="utf-8", errors="replace")
    if len(text) > _MAX_OUT:
        text = text[:_MAX_OUT] + "\n\n[truncated]"
    return (text, 0)


def _list_refs() -> tuple[str, int]:
    if not _REFS_ROOT.is_dir():
        return (
            f"No references dir (expected {_REFS_ROOT}). "
            "Keep the Scrapling/ folder intact.",
            1,
        )
    paths = sorted(_REFS_ROOT.rglob("*.md"))
    if not paths:
        return ("No .md files under references/.", 0)
    lines = ["Scrapling reference docs (open in editor):\n"]
    for p in paths:
        try:
            rel = p.relative_to(SCRAPLING_DIR)
        except ValueError:
            rel = p
        lines.append(f"  {rel.as_posix()}")
    return ("\n".join(lines), 0)


def _cmd_fetch(parts: list[str]) -> tuple[str, int]:
    if not parts:
        return ("Usage: scrapling fetch <url> [css_selector]", 1)
    url = parts[0]
    selector = parts[1] if len(parts) > 1 else None

    ensure_scrapling_on_path()
    try:
        from scrapling.fetchers import Fetcher
    except ImportError as exc:
        return (
            f"Scrapling fetchers unavailable: {exc}\n"
            "Install fetcher deps, e.g. pip install curl_cffi "
            'and pip install -e "Scrapling/[fetchers]" in a venv.',
            1,
        )

    try:
        resp = Fetcher.get(url)
    except Exception as exc:
        return (f"Fetch failed: {exc}", 1)

    try:
        status_code = int(getattr(resp, "status", 0))
    except (TypeError, ValueError):
        status_code = 0
    out_lines = [f"status={status_code} url={url}\n"]
    if selector:
        try:
            nodes = resp.css(selector)
            got = nodes.getall()
            if not got:
                out_lines.append(f"(no matches for css: {selector!r})\n")
            else:
                for i, el in enumerate(got[:200], 1):
                    out_lines.append(f"[{i}] {el!s}\n")
                if len(got) > 200:
                    out_lines.append(f"\n... and {len(got) - 200} more matches\n")
        except Exception as exc:
            return (f"CSS error: {exc}", 1)
    else:
        try:
            raw = resp.body.decode("utf-8", errors="replace")
        except Exception as exc:
            raw = f"(could not decode body: {exc})"
        out_lines.append(raw)

    body = "".join(out_lines)
    if len(body) > _MAX_OUT:
        body = body[:_MAX_OUT] + "\n\n[truncated]"
    return (body, 0 if status_code < 400 else 1)


def _resolve_path(s: str) -> Path:
    p = Path(s)
    if not p.is_absolute():
        p = (ROOT / p).resolve()
    return p


def _cmd_parse(parts: list[str]) -> tuple[str, int]:
    if len(parts) < 2:
        return ("Usage: scrapling parse <path_to.html> <css_selector>", 1)
    file_path = _resolve_path(parts[0])
    selector = parts[1]

    if not file_path.is_file():
        return (f"Not a file: {file_path}", 1)

    ensure_scrapling_on_path()
    try:
        from scrapling.parser import Selector
    except ImportError as exc:
        return (f"Scrapling parser unavailable: {exc}", 1)

    try:
        html = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return (f"Read error: {exc}", 1)

    try:
        sel = Selector(html, url=f"file://{file_path}")
        nodes = sel.css(selector)
        got = nodes.getall()
    except Exception as exc:
        return (f"Parse/css error: {exc}", 1)

    lines = [f"file={file_path} selector={selector!r} matches={len(got)}\n"]
    for i, el in enumerate(got[:200], 1):
        lines.append(f"[{i}] {el!s}\n")
    if len(got) > 200:
        lines.append(f"\n... and {len(got) - 200} more\n")
    body = "".join(lines)
    if len(body) > _MAX_OUT:
        body = body[:_MAX_OUT] + "\n\n[truncated]"
    return (body, 0)
