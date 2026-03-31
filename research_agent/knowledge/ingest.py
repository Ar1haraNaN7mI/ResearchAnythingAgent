from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path

from research_agent.knowledge.chunking import chunk_text
from research_agent.knowledge.db import delete_source, insert_chunks
from research_agent.paths import knowledge_base_dir


def _safe_stem(name: str) -> str:
    base = Path(name).name
    base = re.sub(r"[^\w.\-]", "_", base, flags=re.UNICODE)
    return base[:120] if base else "doc"


def _read_plain(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_pdf_markdown(pdf_path: Path) -> str:
    import opendataloader_pdf

    tmp_root = knowledge_base_dir() / "tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    session = uuid.uuid4().hex[:12]
    out_dir = tmp_root / f"odl_{session}"
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        opendataloader_pdf.convert(
            input_path=[str(pdf_path.resolve())],
            output_dir=str(out_dir),
            format="markdown",
        )
        md_files = sorted(out_dir.rglob("*.md"))
        if not md_files:
            raise RuntimeError(
                "OpenDataLoader produced no .md files (check Java 11+ and PDF path)."
            )
        parts = [_read_plain(p) for p in md_files]
        return "\n\n".join(parts)
    finally:
        try:
            shutil.rmtree(out_dir, ignore_errors=True)
        except OSError:
            pass


def _load_textual(path: Path) -> str:
    suf = path.suffix.lower()
    if suf == ".pdf":
        return _extract_pdf_markdown(path)
    return _read_plain(path)


def ingest_path(src: Path) -> tuple[str, int]:
    """
    Copy file into knowledge_base/files/, chunk, index. Returns (source_key, chunk_count).
    """
    src = src.expanduser().resolve()
    if not src.is_file():
        raise FileNotFoundError(str(src))

    suf = src.suffix.lower()
    allowed = {".pdf", ".md", ".txt", ".markdown", ".html", ".htm"}
    if suf not in allowed:
        raise ValueError(f"Unsupported type {suf!r}; use: {', '.join(sorted(allowed))}")

    files_dir = knowledge_base_dir() / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    uid = uuid.uuid4().hex[:10]
    dest_name = f"{uid}_{_safe_stem(src.name)}"
    dest = files_dir / dest_name
    shutil.copy2(src, dest)

    source_key = f"files/{dest_name}"
    delete_source(source_key)

    body = _load_textual(dest)
    chunks = chunk_text(body)
    n = insert_chunks(source_key, chunks)
    return source_key, n


__all__ = ["ingest_path"]
