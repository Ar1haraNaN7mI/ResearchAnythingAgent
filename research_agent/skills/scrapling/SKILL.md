# Scrapling (Research Agent skill)

Bundled source: repository folder `Scrapling/` (do not remove).

## Two ways to use it here

1. **Agent skills (lightweight)** — `scrapling guide|refs|fetch|parse` (no MCP, no browser install required for parse-only).
2. **Upstream CLI + MCP (full)** — same entry as PyPI `scrapling`, launched via `research_agent/scrapling_entry.py`. The upstream **MCP** (`scrapling.core.ai.ScraplingMCPServer`, FastMCP) exposes `get`, `fetch`, `stealthy_fetch`, sessions, etc.

## Official MCP (recommended for agents)

In **this chat**, always use **HTTP** transport (stdio would block the worker):

```text
scrapling mcp --http --host 127.0.0.1 --port 8766
```

Point your MCP client at that streamable-http URL. Stop the server from chat with `stop` / `cancel`.

Dependencies: install `scrapling[ai]` equivalents (see `research_agent/requirements.txt`: `mcp`, `markdownify`, fetchers). Run `scrapling install` once for Playwright browsers if you use browser tools.

## Other upstream CLI commands (chat)

- `scrapling extract ...` — `get` / `fetch` / `stealthy-fetch` file output (see upstream docs).
- `scrapling install` — browser deps installer.
- `scrapling shell -c "code"` — one-off eval; full interactive REPL → run in a real terminal:
  `python research_agent/scrapling_entry.py shell`

## Windows desktop automation (this repo)

Use **`cil ...`** (`cil_anything.py`). That is **not** part of Scrapling; Scrapling covers web fetching/scraping and MCP.

## Skill subcommands (same as `skill scrapling ...`)

- `scrapling guide` — this file.
- `scrapling refs` — list `Scrapling/agent-skill/.../references/*.md`.
- `scrapling fetch <url> [css]` — `Fetcher.get` + optional CSS.
- `scrapling parse <file> <css>` — local HTML + `Selector`.

## Python API (in-code)

```python
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "Scrapling"))

from scrapling.parser import Selector
from scrapling.fetchers import Fetcher

page = Fetcher.get("https://example.com")
```

## Deeper docs (offline, in repo)

- `Scrapling/README.md`
- `Scrapling/agent-skill/Scrapling-Skill/SKILL.md`
