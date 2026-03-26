# Research Agent (autoresearch + CIL Anything)

## Claude API (preconfigured)

1. Copy `.env.example` to `.env` in the workspace root.
2. Set `ANTHROPIC_API_KEY` (get a key from [Anthropic](https://console.anthropic.com/)).
3. Optional: set `CLAUDE_MODEL`, `ANTHROPIC_BASE_URL`, `CLAUDE_MAX_TOKENS` in `.env`.

In the chatboard, use: `claude <your prompt>` to call the Messages API with the built-in research/CIL system prompt.

Code entry points for other tools:

- `research_agent.claude_client.claude_complete()` — generic one-shot message
- `research_agent.claude_client.claude_code_assist()` — same system prompt as chat `claude` command

## Start

From this folder (workspace root), run:

- `run_research_chat.bat`

Then open:

- `http://127.0.0.1:8765`

## Chatboard rules

- New chat messages are **always queued first** (ahead of background research).
- Sending a message **cancels** the currently running subprocess so the next command can run.
- Say `auto on` to loop `train.py` when idle; `auto off` stops scheduling.

## Examples

- `train` — run `autoresearch/train.py` (prefers `uv run`, falls back to `python`)
- `prepare` — run `autoresearch/prepare.py`
- `cil discover --window-title "IBM SPSS" --json`
- `cil auto --app "C:\path\app.exe" --name spss --window-title "IBM SPSS" --json`
- `stop` — cancel current job
- `help`

## Layout

- `autoresearch/` — LLM training research project
- `cil_anything.py` — desktop CIL tool
- `research_agent/` — chat server + priority queue + worker
