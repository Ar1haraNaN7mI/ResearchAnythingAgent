from __future__ import annotations

import os
from pathlib import Path

from research_agent.paths import ROOT

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def llm_provider() -> str:
    """
    Backend: claude | ollama | qwen
    Override with LLM_PROVIDER in .env
    """
    p = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if p in ("claude", "ollama", "qwen"):
        return p
    # Soft defaults when LLM_PROVIDER is unset
    if anthropic_api_key():
        return "claude"
    if os.environ.get("OLLAMA_MODEL", "").strip():
        return "ollama"
    if qwen_api_key():
        return "qwen"
    return "claude"


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


def ollama_base_url() -> str:
    return os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/")


def ollama_model() -> str:
    return os.environ.get("OLLAMA_MODEL", "llama3.2").strip()


def qwen_api_key() -> str:
    return (
        os.environ.get("QWEN_API_KEY", "").strip()
        or os.environ.get("DASHSCOPE_API_KEY", "").strip()
    )


def qwen_base_url() -> str:
    u = os.environ.get("QWEN_BASE_URL", "").strip()
    if u:
        return u.rstrip("/")
    return "https://dashscope.aliyuncs.com/compatible-mode/v1"


def qwen_model() -> str:
    return os.environ.get("QWEN_MODEL", "qwen-turbo").strip()


def max_output_tokens() -> int:
    raw = os.environ.get("LLM_MAX_TOKENS", os.environ.get("CLAUDE_MAX_TOKENS", "4096")).strip()
    try:
        return max(256, int(raw))
    except ValueError:
        return 4096


def claude_max_tokens() -> int:
    """Alias for legacy code; same as LLM_MAX_TOKENS."""
    return max_output_tokens()


def env_setup_step_attempts() -> int:
    """Max shell attempts per env-setup step (initial run + repairs). Default 5."""
    raw = os.environ.get("ENV_SETUP_STEP_ATTEMPTS", "5").strip()
    try:
        return max(1, min(20, int(raw)))
    except ValueError:
        return 5


def llm_config_summary() -> str:
    """One-line description for logs / UI."""
    p = llm_provider()
    if p == "claude":
        return f"claude model={claude_model()}"
    if p == "ollama":
        return f"ollama base={ollama_base_url()} model={ollama_model()}"
    if p == "qwen":
        return f"qwen model={qwen_model()} base={qwen_base_url()}"
    return p


def next_drawio_url() -> str:
    """
    Base URL for the bundled Next AI Draw.io app (npm run dev defaults to port 6002).
    Override with NEXT_DRAWIO_URL or DRAWIO_APP_URL in workspace root .env.
    """
    u = (
        os.environ.get("NEXT_DRAWIO_URL", "").strip()
        or os.environ.get("DRAWIO_APP_URL", "").strip()
    )
    if u:
        return u.rstrip("/")
    return "http://127.0.0.1:6002"
