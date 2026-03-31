from __future__ import annotations

import re
import shlex
import sys
from typing import Tuple

from research_agent.executor import ProcessRunner
from research_agent.os_shell import try_handle_os_command

_SCRAPLING_CLI_SUBCOMMANDS = frozenset({"mcp", "shell", "install", "extract"})


def _dispatch_scrapling_cli(raw: str, runner: ProcessRunner) -> Tuple[str, int] | None:
    """
    Route `scrapling mcp|shell|install|extract ...` to vendored Scrapling CLI.
    Other `scrapling ...` lines fall through to agent skills (fetch/parse/guide).
    """
    try:
        parts = shlex.split(raw.strip(), posix=(sys.platform != "win32"))
    except ValueError as exc:
        return (f"scrapling parse error: {exc}", 1)

    if not parts or parts[0].lower() != "scrapling" or len(parts) < 2:
        return None

    sub = parts[1].lower()
    if sub not in _SCRAPLING_CLI_SUBCOMMANDS:
        return None

    if sub == "mcp":
        if "--http" not in parts:
            return (
                "Scrapling MCP 默认走 stdio，适合作为 Cursor / IDE 的子进程；在聊天 Worker 里会阻塞等待标准输入。\n"
                "请使用官方实现的 streamable-http（与上游 FastMCP 一致），例如：\n"
                "  scrapling mcp --http --host 127.0.0.1 --port 8766\n"
                "然后用支持 HTTP 的 MCP 客户端指向该地址。停止：发送 stop / cancel。\n"
                "Windows 桌面 UI 自动化请用本仓库命令：cil ...（与 Scrapling 无关）。",
                1,
            )

    if sub == "shell":
        if not any(x in ("-c", "--code") for x in parts):
            return (
                "scrapling shell 是交互式 REPL，请在系统终端运行，例如：\n"
                f"  {sys.executable} research_agent\\\\scrapling_entry.py shell\n"
                "在聊天里仅支持一次性求值：scrapling shell -c \"1+1\"",
                1,
            )

    rc = runner.run_scrapling_cli(*parts[1:])
    return (f"scrapling CLI exited with code {rc}", 0 if rc == 0 else 1)


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

    if low == "skills":
        from research_agent.skills import format_skills_list

        return (format_skills_list(), 0)

    if low.startswith("skill "):
        from research_agent.skills import dispatch_skill_line

        return dispatch_skill_line(raw[6:].strip())

    if low.startswith("scrapling"):
        cli_hit = _dispatch_scrapling_cli(raw, runner)
        if cli_hit is not None:
            return cli_hit
        from research_agent.skills import dispatch_skill_line

        tail = raw[9:].strip() if len(raw) > 9 else ""
        return dispatch_skill_line(("scrapling " + tail).strip())

    if low == "drawio" or low.startswith("drawio ") or low.startswith("drawio\t"):
        from research_agent.skills import dispatch_skill_line

        return dispatch_skill_line(raw.strip())

    if low == "kb" or low.startswith("kb ") or low.startswith("kb\t"):
        from research_agent.skills import dispatch_skill_line

        return dispatch_skill_line(raw.strip())

    if low in ("flowchart", "draw.io"):
        from research_agent.llm_settings import next_drawio_url

        u = next_drawio_url()
        return (
            "Next AI Draw.io: "
            f"{u}\n"
            "Skill: `drawio guide` | `drawio path` | `drawio bg transparent|white`\n"
            "Start: cd next-ai-draw-io → npm install → copy env.example to .env.local → npm run dev.",
            0,
        )

    if low.startswith("web search "):
        from research_agent.env_agent import run_websearch_display

        q = raw[11:].strip()
        return run_websearch_display(q)

    if low.startswith("websearch"):
        rest = raw[9:].strip() if len(raw) > 9 else ""
        if not rest.strip():
            return ("Usage: websearch <query>  (or: web search <query>)", 1)
        from research_agent.env_agent import run_websearch_display

        return run_websearch_display(rest)

    m_env = re.match(r"env\s+setup\s+(\S+)", raw, re.I)
    if m_env:
        from research_agent.env_agent import run_env_setup

        return run_env_setup(runner, m_env.group(1))

    m_env2 = re.match(r"env_setup\s+(\S+)", raw, re.I)
    if m_env2:
        from research_agent.env_agent import run_env_setup

        return run_env_setup(runner, m_env2.group(1))

    os_hit = try_handle_os_command(raw, runner)
    if os_hit is not None:
        return os_hit

    parts = raw.split(None, 1)
    if parts and parts[0].lower() in ("claude", "llm"):
        prompt = parts[1].strip() if len(parts) > 1 else ""
        if not prompt:
            return (
                "Usage: llm <prompt>  (or claude <prompt>) — set LLM_PROVIDER=claude|ollama|qwen and keys in .env",
                1,
            )
        try:
            from research_agent.llm_client import llm_code_assist

            reply = llm_code_assist(prompt)
            return (reply or "(empty reply)", 0)
        except Exception as exc:
            return (f"LLM error: {exc}", 1)

    if low.startswith("cil ") or low.startswith("cil\t"):
        if sys.platform != "win32":
            return ("CIL (desktop UI automation) is only supported on Windows.", 1)
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

    # Default: treat whole line as extra args to CIL if it looks like flags (Windows only)
    if raw.startswith("--"):
        if sys.platform != "win32":
            return ("CIL is only supported on Windows.", 1)
        rc = runner.run_cil(*shlex.split(raw, posix=False))
        return (f"CIL finished with exit code {rc}", 0 if rc == 0 else 1)

    return (
        "Unknown command. Type `help`. You can say: train, prepare, cil discover --window-title ... --json",
        1,
    )


def _help_text() -> str:
    return """Commands (newest chat message is always handled before background research):
  shell <cmd>            — run raw shell on THIS machine (no LLM)
  os linux|ubuntu|win <cmd> — translate from named OS family, then run (no LLM)
  apt / winget / sudo …  — detected OS commands run locally (no LLM); cross-OS is translated when possible
  llm <prompt>           — chat model (LLM_PROVIDER: claude | ollama | qwen — see .env)
  claude <prompt>        — same as llm (alias); draw.io / Scrapling skill docs are added only if the prompt suggests diagrams or scraping/pages
  train / experiment     — run autoresearch train.py (uv run, fallback python)
  prepare / data prep    — run autoresearch prepare.py
  cil ...                — Windows only: pass-through to cil_anything.py
  uv ...                 — uv run in autoresearch (e.g. uv run train.py)
  websearch <q>          — Web search via ddgs (docs / install hints; no API key)
  web search <q>         — same as websearch
  env setup <preset>     — LLM + web plans shell steps; autoresearch | research_agent | all
  env_setup <preset>     — same as env setup
  drawio …               — Next AI Draw.io skill: guide, url, path, bg transparent|white, status
  kb …                   — local knowledge base: guide, add, list, remove, search, clear, status
  flowchart / draw.io    — short URL + pointer to `drawio guide`
  skills                 — list built-in agent skills (e.g. bundled Scrapling)
  skill <name> …         — run skill; try `skill scrapling guide`
  scrapling …            — skill shortcuts: guide / fetch / parse / refs (see `skills`)
  scrapling mcp --http … — vendored Scrapling MCP (FastMCP); use HTTP in chat, not stdio
  scrapling extract …    — upstream CLI extract (get/fetch/…); needs scrapling[fetchers]
  scrapling install      — Playwright browsers etc. (upstream installer)
  scrapling shell -c "…" — one-off shell eval; interactive shell → run scrapling_entry.py in terminal
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
