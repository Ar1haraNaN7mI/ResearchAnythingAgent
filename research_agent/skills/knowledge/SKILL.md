# Knowledge base (`kb`)

Build a **local** knowledge base from **PDF**, **Markdown**, **plain text**, and **HTML**. Indexed chunks live in **SQLite FTS5** under `knowledge_base/index/`. After you add documents, **every** `llm_complete` call (chat LLM, env agent planning, etc.) **prepends** retrieved excerpts when the index is non-empty, unless you disable retrieval.

## Requirements

- **PDF**: `pip install opendataloader-pdf` (see [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf)). The Python package shells out to a **Java 11+** runtime — run `java -version` before relying on PDF ingest.
- **Optional hybrid / OCR**: install `opendataloader-pdf[hybrid]` and run the hybrid server per upstream docs; this skill uses the default **local** `convert(..., format="markdown")` path only.

## Layout

- `knowledge_base/files/` — copies of ingested originals (gitignored by default).
- `knowledge_base/github_sync/` — web uploads land here first, then index; this folder is **git-tracked** for optional `kb sync` / `?sync`.
- `knowledge_base/index/kb.sqlite` — FTS index (gitignored).
- Override root with **`KNOWLEDGE_BASE_DIR`** in `.env` if needed.

## Commands

| Command | Purpose |
|--------|---------|
| `kb manual` | **Full handbook** (web upload, `?` shortcuts, REST, Git sync) |
| `kb guide` | This short document |
| `kb status` | Chunk count, paths, retrieve budget |
| `kb list` | Numbered sources |
| `kb add <path>` | Ingest one file |
| `kb remove <n>` | Drop source `#n` from `kb list` |
| `kb search <q>` | Debug retrieval (same pipeline as LLM) |
| `kb clear` | Wipe the FTS index only |
| `kb sync` | `git add` / `commit` / `push` for `github_sync/` (needs `KNOWLEDGE_GIT_SYNC_ALLOW=1`) |

Chat shortcuts: **`?upload`**, **`?delete <n>`**, **`?sync`** (half- or full-width `?`).

Shortcuts: `skill kb …` or `kb …` in the chat dispatcher.

**Web upload:** `POST /api/knowledge/upload` with multipart field **`file`**, or use the chat UI **Upload** button / `?upload`.

## LLM retrieval

- Each user message is tokenized into an **OR** FTS query; top chunks are concatenated up to **`KB_RETRIEVE_MAX_CHARS`** (default `6000`).
- **`KB_RETRIEVE_DISABLE=1`** — skip injection entirely.
- **`skip_kb=True`** on `llm_complete` is reserved for internal callers (not used by default).

## Tips

- Batch many PDFs by running `kb add` once per file (OpenDataLoader spawns JVM per batch upstream; this wrapper calls `convert` per file for predictable paths).
- Prefer short, self-contained filenames; stored keys look like `files/<id>_<name>.pdf`.
