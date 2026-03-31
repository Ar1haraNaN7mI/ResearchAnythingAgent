# Knowledge base directory

This folder stores **your** documents and search index:

- `files/` — copies created by `kb add` / ingest (gitignored).
- `github_sync/` — uploads from the web UI (`POST /api/knowledge/upload` or **Upload** button); **tracked by git** so you can `?sync` / `kb sync` to push (requires `KNOWLEDGE_GIT_SYNC_ALLOW=1`).
- `index/kb.sqlite` — SQLite FTS5 index (gitignored).

Configure an alternate root with `KNOWLEDGE_BASE_DIR` in the workspace `.env`.

Handbook: chat command **`kb manual`**, or `research_agent/skills/knowledge/MANUAL.md`.

PDF ingestion uses [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf) and needs **Java 11+**.
