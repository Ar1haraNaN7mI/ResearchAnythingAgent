# Knowledge base directory

This folder stores **your** documents and search index:

- `files/` — copies created by `kb add` (gitignored).
- `index/kb.sqlite` — SQLite FTS5 index (gitignored).

Configure an alternate root with `KNOWLEDGE_BASE_DIR` in the workspace `.env`.

See the skill doc: `kb guide` or `research_agent/skills/knowledge/SKILL.md`.

PDF ingestion uses [OpenDataLoader PDF](https://github.com/opendataloader-project/opendataloader-pdf) and needs **Java 11+**.
