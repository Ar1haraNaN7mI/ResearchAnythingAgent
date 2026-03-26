from __future__ import annotations

import re
import shlex
from typing import Tuple

from research_agent.executor import ProcessRunner


def parse_and_dispatch(text: str, runner: ProcessRunner) -> Tuple[str, int]:
    """
    Returns (human-readable summary, exit code 0=ok).
    """
    raw = text.strip()
    low = raw.lower()

    if not raw:
        return ("empty command", 1)

    if low in ("stop", "cancel", "abort"):
        runner.cancel()
        return ("cancel requested for running job", 0)

    if low in ("help", "?", "commands"):
        return (
            _help_text(),
            0,
        )

    parts = raw.split(None, 1)
    if parts and parts[0].lower() == "claude":
        prompt = parts[1].strip() if len(parts) > 1 else ""
        if not prompt:
            return ("Usage: claude <prompt>  (uses ANTHROPIC_API_KEY / CLAUDE_API_KEY)", 1)
        try:
            from research_agent.claude_client import claude_code_assist

            reply = claude_code_assist(prompt)
            return (reply or "(empty reply)", 0)
        except Exception as exc:
            return (f"Claude API error: {exc}", 1)

    if low.startswith("cil ") or low.startswith("cil\t"):
        rest = raw[4:].strip()
        try:
            args = shlex.split(rest, posix=False)
        except ValueError as exc:
            return (f"CIL parse error: {exc}", 1)
        if not args:
            return ("CIL: no arguments", 1)
        rc = runner.run_cil(*args)
        return (f"CIL finished with exit code {rc}", 0 if rc == 0 else 1)

    if low.startswith("uv ") or low.startswith("uv\t"):
        rest = raw[3:].strip()
        try:
            args = shlex.split(rest, posix=False)
        except ValueError as exc:
            return (f"uv parse error: {exc}", 1)
        rc = runner.run_uv(*args)
        return (f"uv finished with exit code {rc}", 0 if rc == 0 else 1)

    # Keyword routing for autoresearch
    if any(k in low for k in ("prepare", "download data", "tokenizer", "data prep")):
        rc = runner.run_uv_fallback_python("prepare.py")
        return (f"prepare.py finished with exit code {rc}", 0 if rc == 0 else 1)

    if any(
        k in low
        for k in (
            "train",
            "training",
            "experiment",
            "run model",
            "val_bpb",
            "autoresearch",
        )
    ):
        rc = runner.run_uv_fallback_python("train.py")
        return (f"train.py finished with exit code {rc}", 0 if rc == 0 else 1)

    # Default: treat whole line as extra args to CIL if it looks like flags
    if raw.startswith("--"):
        rc = runner.run_cil(*shlex.split(raw, posix=False))
        return (f"CIL finished with exit code {rc}", 0 if rc == 0 else 1)

    return (
        "Unknown command. Type `help`. You can say: train, prepare, cil discover --window-title ... --json",
        1,
    )


def _help_text() -> str:
    return """Commands (newest chat message is always handled before background research):
  claude <prompt>        — call Anthropic Claude (preconfigured API; set ANTHROPIC_API_KEY)
  train / experiment     — run autoresearch train.py (uv run, fallback python)
  prepare / data prep    — run autoresearch prepare.py
  cil ...                — pass-through to cil_anything.py (quote paths)
  uv ...                 — uv run in autoresearch (e.g. uv run train.py)
  stop / cancel          — stop current subprocess
  auto on / auto off     — (handled by worker) toggle continuous research
  help                   — this text
"""


def parse_auto_toggle(text: str) -> str | None:
    low = text.strip().lower()
    if re.search(r"\b(auto\s+research\s+on|auto\s+on|start\s+auto|continuous\s+on)\b", low):
        return "on"
    if re.search(r"\b(auto\s+research\s+off|auto\s+off|stop\s+auto|continuous\s+off)\b", low):
        return "off"
    return None
