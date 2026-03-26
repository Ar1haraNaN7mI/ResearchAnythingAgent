from __future__ import annotations

from typing import List, Optional

from research_agent.llm_settings import (
    anthropic_api_key,
    anthropic_base_url,
    claude_model,
    llm_provider,
    max_output_tokens,
    ollama_base_url,
    ollama_model,
    qwen_api_key,
    qwen_base_url,
    qwen_model,
)


def llm_complete(
    user_message: str,
    *,
    system: Optional[str] = None,
) -> str:
    """Route to configured backend (Claude / Ollama / Qwen)."""
    provider = llm_provider()
    if provider == "claude":
        return _complete_claude(user_message, system=system)
    if provider == "ollama":
        return _complete_ollama(user_message, system=system)
    if provider == "qwen":
        return _complete_qwen(user_message, system=system)
    raise RuntimeError(f"Unknown LLM_PROVIDER: {provider}")


def _complete_claude(user_message: str, *, system: Optional[str]) -> str:
    from anthropic import Anthropic

    key = anthropic_api_key()
    if not key:
        raise RuntimeError(
            "LLM_PROVIDER=claude but ANTHROPIC_API_KEY (or CLAUDE_API_KEY) is missing."
        )
    base = anthropic_base_url()
    client = Anthropic(api_key=key, base_url=base) if base else Anthropic(api_key=key)
    model = claude_model()
    max_tokens = max_output_tokens()
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": user_message}],
    }
    if system:
        kwargs["system"] = system
    msg = client.messages.create(**kwargs)
    return _anthropic_blocks_to_text(msg.content)


def _anthropic_blocks_to_text(blocks: List[object]) -> str:
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


def _complete_ollama(user_message: str, *, system: Optional[str]) -> str:
    import httpx

    base = ollama_base_url()
    name = ollama_model()
    if not name:
        raise RuntimeError("OLLAMA_MODEL is empty (LLM_PROVIDER=ollama).")

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user_message})

    url = f"{base}/api/chat"
    payload = {
        "model": name,
        "messages": messages,
        "stream": False,
    }
    with httpx.Client(timeout=300.0) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    msg = data.get("message") or {}
    content = msg.get("content")
    if content is None:
        return str(data)
    return str(content).strip()


def _complete_qwen(user_message: str, *, system: Optional[str]) -> str:
    from openai import OpenAI

    key = qwen_api_key()
    if not key:
        raise RuntimeError(
            "LLM_PROVIDER=qwen but QWEN_API_KEY or DASHSCOPE_API_KEY is missing."
        )
    client = OpenAI(api_key=key, base_url=qwen_base_url())
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user_message})

    comp = client.chat.completions.create(
        model=qwen_model(),
        messages=messages,
        max_tokens=max_output_tokens(),
    )
    choice = comp.choices[0]
    text = choice.message.content
    return (text or "").strip()


def llm_code_assist(instruction: str, *, context: str = "") -> str:
    system = (
        "You are the embedded coding agent for the Research Agent workspace. "
        "You help with autoresearch (train.py, prepare.py) and CIL Anything (Windows UI automation). "
        "Be concise, actionable, and prefer concrete shell commands or Python snippets when relevant."
    )
    user = instruction.strip()
    if context:
        user = f"Context:\n{context}\n\nRequest:\n{user}"
    return llm_complete(user, system=system)
