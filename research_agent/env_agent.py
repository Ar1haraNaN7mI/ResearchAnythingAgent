from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from research_agent.executor import ProcessRunner
from research_agent.llm_client import llm_complete
from research_agent.llm_settings import env_setup_step_attempts
from research_agent.paths import AUTORESEARCH_DIR, ROOT
from research_agent.web_search import format_search_for_llm, search_web

PRESETS: dict[str, list[Path]] = {
    "autoresearch": [AUTORESEARCH_DIR],
    "research_agent": [ROOT / "research_agent"],
    "all": [ROOT / "research_agent", AUTORESEARCH_DIR],
}


def _read_manifests(dirs: list[Path]) -> str:
    chunks: list[str] = []
    for d in dirs:
        if not d.is_dir():
            chunks.append(f"(missing directory: {d})")
            continue
        for name in ("pyproject.toml", "requirements.txt", "package.json"):
            p = d / name
            if p.is_file():
                try:
                    text = p.read_text(encoding="utf-8", errors="replace")[:16000]
                except OSError as exc:
                    text = f"(read error: {exc})"
                rel = p.relative_to(ROOT)
                chunks.append(f"=== {rel} ===\n{text}")
    return "\n\n".join(chunks) if chunks else "(no manifest files found)"


def _search_queries_for_manifest(manifest: str) -> list[str]:
    qs: list[str] = []
    low = manifest.lower()
    if "torch" in low or "pytorch" in low:
        qs.append("PyTorch official install pip cuda")
    if "uv" in low or "pyproject.toml" in manifest:
        qs.append("uv sync python project official documentation")
    if "fastapi" in low:
        qs.append("FastAPI installation pip")
    qs.append("Python virtual environment best practices")
    seen: set[str] = set()
    out: list[str] = []
    for q in qs:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out[:4]


def _extract_json_array(text: str) -> list[Any]:
    text = text.strip()
    m = re.search(r"\[[\s\S]*\]", text)
    if not m:
        raise ValueError("No JSON array found in model output")
    return json.loads(m.group(0))


def _plan_commands(preset: str, dirs: list[Path], manifest: str) -> list[dict[str, Any]]:
    queries = _search_queries_for_manifest(manifest)
    search_blob = ""
    for q in queries:
        try:
            search_blob += format_search_for_llm(q, max_results=4) + "\n"
        except Exception as exc:
            search_blob += f"(web search failed for {q!r}: {exc})\n"

    scrapling_blob = ""
    try:
        from research_agent.env_scrapling_docs import scrapling_context_for_queries

        scrapling_blob = scrapling_context_for_queries(queries)
    except Exception as exc:
        scrapling_blob = f"(Scrapling doc deep-read failed: {exc})\n"

    plat = "Windows" if sys.platform == "win32" else "Unix-like"
    user = f"""You are preparing a reproducible dev environment for this workspace.

Preset: {preset}
Target OS for shell commands: {plat}

Workspace manifest excerpts:
{manifest}

Official / community hints (web search):
{search_blob}
{scrapling_blob}

Respond with ONLY a JSON array (no markdown fences). Each element must be an object:
{{"cmd": "<single shell command string>", "cwd": null | "autoresearch" | "research_agent"}}

Rules:
- Prefer install commands and flags that match the fetched official documentation above (web snippets + Scrapling pages).
- Use `uv sync` or `uv pip install` inside autoresearch when pyproject.toml is present.
- For research_agent use `pip install -r requirements.txt` from that folder (or `python -m pip`).
- Do not use interactive prompts; add non-interactive flags where needed.
- Order: create/sync venv dependencies before running heavy installs.
- Keep the list minimal but sufficient for importable code in each preset scope.
"""
    system = (
        "You output valid JSON only: one array of objects with keys cmd (string) and cwd "
        "(null or autoresearch or research_agent)."
    )
    raw = llm_complete(user, system=system)
    arr = _extract_json_array(raw)
    out: list[dict[str, Any]] = []
    for item in arr:
        if not isinstance(item, dict):
            continue
        cmd = item.get("cmd")
        if not isinstance(cmd, str) or not cmd.strip():
            continue
        cwd = item.get("cwd")
        if cwd not in (None, "autoresearch", "research_agent"):
            cwd = None
        out.append({"cmd": cmd.strip(), "cwd": cwd})
    return out


def _resolve_cwd(token: Any) -> Path:
    if token is None or token == "":
        return ROOT
    if token == "autoresearch":
        return AUTORESEARCH_DIR
    if token == "research_agent":
        return ROOT / "research_agent"
    return ROOT


def _repair_command(
    *,
    failed_cmd: str,
    exit_code: int,
    output: str,
    preset: str,
    manifest: str,
) -> str | None:
    tail = output[-4500:] if len(output) > 4500 else output
    q = f"{failed_cmd} {tail[:400]}".replace("\n", " ")[:480]
    hint = ""
    try:
        hint = format_search_for_llm(q, max_results=3)
    except Exception as exc:
        hint = f"(search unavailable: {exc})"

    scrapling_repair = ""
    try:
        from research_agent.env_scrapling_docs import scrapling_context_for_queries

        scrapling_repair = scrapling_context_for_queries([q], max_urls_override=3)
    except Exception as exc:
        scrapling_repair = f"(Scrapling doc deep-read failed: {exc})\n"

    plat = "Windows (cmd.exe / PowerShell)" if sys.platform == "win32" else "Unix shell"
    user = f"""A shell command failed while setting up the environment.

Preset: {preset}
Platform: {plat}
Failed command: {failed_cmd}
Exit code: {exit_code}
Output:
{tail}

Manifest context (truncated):
{manifest[:6000]}

Error-oriented web hints:
{hint}
{scrapling_repair}

Reply with exactly one line: the next shell command to fix or work around the failure.
If the failure cannot be fixed automatically, reply with the single word SKIP (uppercase).
"""
    system = "You suggest one non-interactive shell command, or SKIP."
    text = llm_complete(user, system=system).strip()
    first = text.split("\n", 1)[0].strip()
    if first.upper() == "SKIP" or first.upper().startswith("SKIP "):
        return None
    return first


def run_env_setup(runner: ProcessRunner, preset: str) -> tuple[str, int]:
    key = preset.strip().lower()
    if key not in PRESETS:
        return (
            f"Unknown preset {preset!r}. Use: autoresearch | research_agent | all",
            1,
        )

    dirs = PRESETS[key]
    manifest = _read_manifests(dirs)
    try:
        steps = _plan_commands(key, dirs, manifest)
    except Exception as exc:
        return (f"env setup plan failed: {exc}", 1)

    if not steps:
        return ("LLM returned no commands to run.", 1)

    attempts = env_setup_step_attempts()
    log_lines: list[str] = [f"[env setup] preset={key} steps={len(steps)}"]

    for i, step in enumerate(steps, 1):
        cmd = str(step["cmd"])
        cwd = _resolve_cwd(step.get("cwd"))
        cur = cmd
        last_err = ""
        for attempt in range(attempts):
            rc, out = runner.run_shell_capture(cur, cwd=cwd)
            if rc == 0:
                log_lines.append(f"  ok [{i}] {cur}")
                break
            last_err = out
            if attempt + 1 >= attempts:
                log_lines.append(f"  fail [{i}] {cur} rc={rc}")
                msg = "\n".join(log_lines)
                msg += f"\n\nStopped at step {i}/{len(steps)} after {attempts} attempt(s).\nLast output:\n{last_err[-3500:]}"
                return (msg, 1)
            nxt = _repair_command(
                failed_cmd=cur,
                exit_code=rc,
                output=out,
                preset=key,
                manifest=manifest,
            )
            if nxt is None:
                log_lines.append(f"  repair SKIP [{i}] after: {cur}")
                msg = "\n".join(log_lines)
                msg += f"\n\nRepair aborted at step {i}.\nLast output:\n{last_err[-3500:]}"
                return (msg, 1)
            log_lines.append(f"  repair [{i}] try: {nxt}")
            cur = nxt

    msg = "\n".join(log_lines) + "\n[env setup] done."
    return (msg, 0)


def run_websearch_display(query: str) -> tuple[str, int]:
    q = query.strip()
    if not q:
        return ("Usage: websearch <query>  (or: web search <query>)", 1)
    try:
        rows = search_web(q, max_results=6)
    except Exception as exc:
        return (f"Web search error: {exc}", 1)
    lines = [f"Results for: {q}\n"]
    for i, r in enumerate(rows, 1):
        title = r.get("title", "")
        href = r.get("href", "")
        body = (r.get("body") or "")[:400]
        lines.append(f"{i}. {title}\n   {href}\n   {body}\n")
    return ("\n".join(lines), 0)
