from __future__ import annotations

import os
from pathlib import Path

from research_agent.paths import ROOT

# Load workspace .env once (optional file).
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def anthropic_api_key() -> str:
    return (
        os.environ.get("ANTHROPIC_API_KEY", "").strip()
        or os.environ.get("CLAUDE_API_KEY", "").strip()
    )


def anthropic_base_url() -> str | None:
    u = os.environ.get("ANTHROPIC_BASE_URL", "").strip()
    return u or None


def claude_model() -> str:
    return os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514").strip()


def claude_max_tokens() -> int:
    raw = os.environ.get("CLAUDE_MAX_TOKENS", "4096").strip()
    try:
        return max(256, int(raw))
    except ValueError:
        return 4096
