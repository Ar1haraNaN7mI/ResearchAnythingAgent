# Next AI Draw.io (Research Agent skill)

Monorepo folder: `next-ai-draw-io/`. Exports (PNG/SVG/`.drawio`) should go to a **single output directory** so files stay out of the app tree.

## Output path

- **Default** (no env): `<repo>/drawio_exports/` (created on demand).
- Override: set **`DRAWIO_EXPORT_DIR`** in the workspace root `.env` to an absolute path.

The MCP server (`export_diagram`) resolves **relative** paths under `DRAWIO_EXPORT_DIR` when that variable is set. Start MCP with the same env (e.g. in `next-ai-draw-io/.env.local` copy the same `DRAWIO_EXPORT_DIR=` line as in the repo root `.env`).

## PNG background (transparent vs white)

- **Default: transparent** (alpha channel).
- **Env:** `DRAWIO_EXPORT_PNG_BACKGROUND=transparent` or `white`.
- **File (shared with MCP):** `DRAWIO_EXPORT_DIR` / `.png_background` containing one line: `transparent` or `white`.  
  Chat: `drawio bg transparent` / `drawio bg white` writes this file (and creates the export dir).

MCP tool `export_diagram` also accepts optional **`background`**: `"transparent"` | `"white"` (overrides env/file for that call).

## Chat commands

- `drawio guide` — this file.
- `drawio url` — app URL (`NEXT_DRAWIO_URL`, default `http://127.0.0.1:6002`).
- `drawio path` — resolved export directory.
- `drawio bg transparent` | `drawio bg white` — PNG default for MCP + embed export.
- `drawio status` — path + effective PNG background.

## Run the app

From `next-ai-draw-io/`: `npm install`, copy `env.example` → `.env.local`, set AI keys, then `npm run dev` (see upstream README).
