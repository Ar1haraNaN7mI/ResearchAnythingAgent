from __future__ import annotations

"""
Backward-compatible names; implementation is provider-agnostic (see llm_client.py).
"""

from typing import Optional

from research_agent.llm_client import llm_code_assist, llm_complete


def claude_complete(
    user_message: str,
    *,
    system: Optional[str] = None,
) -> str:
    return llm_complete(user_message, system=system)


__all__ = ["claude_complete", "claude_code_assist", "llm_complete", "llm_code_assist"]
