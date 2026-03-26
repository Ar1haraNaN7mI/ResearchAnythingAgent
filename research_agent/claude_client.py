from __future__ import annotations

from typing import List, Optional

from research_agent.claude_settings import (
    anthropic_api_key,
    anthropic_base_url,
    claude_max_tokens,
    claude_model,
)


def get_anthropic_client():
    """Lazy import so the rest of the agent works without anthropic installed."""
    from anthropic import Anthropic

    key = anthropic_api_key()
    if not key:
        raise RuntimeError(
            "Missing ANTHROPIC_API_KEY (or CLAUDE_API_KEY). Set it in .env or environment."
        )
    base = anthropic_base_url()
    if base:
        return Anthropic(api_key=key, base_url=base)
    return Anthropic(api_key=key)


def claude_complete(
    user_message: str,
    *,
    system: Optional[str] = None,
) -> str:
    """
    Single-turn Messages API call. Returns assistant text (concatenated blocks).
    """
    client = get_anthropic_client()
    model = claude_model()
    max_tokens = claude_max_tokens()
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": user_message}],
    }
    if system:
        kwargs["system"] = system
    msg = client.messages.create(**kwargs)
    return _blocks_to_text(msg.content)


def _blocks_to_text(blocks: List[object]) -> str:
    parts: List[str] = []
    for block in blocks:
        if isinstance(block, dict):
            if block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            continue
        btype = getattr(block, "type", None)
        if btype == "text":
            parts.append(getattr(block, "text", "") or "")
    return "".join(parts).strip()


def claude_code_assist(instruction: str, *, context: str = "") -> str:
    """
    Predefined 'coding agent' style system prompt for research tooling.
    """
    system = (
        "You are the embedded coding agent for the Research Agent workspace. "
        "You help with autoresearch (train.py, prepare.py) and CIL Anything (Windows UI automation). "
        "Be concise, actionable, and prefer concrete shell commands or Python snippets when relevant."
    )
    user = instruction.strip()
    if context:
        user = f"Context:\n{context}\n\nRequest:\n{user}"
    return claude_complete(user, system=system)
