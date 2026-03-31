from __future__ import annotations

import os
import uuid
from pathlib import Path

from research_agent.knowledge.ingest import _safe_stem, ingest_path
from research_agent.paths import knowledge_base_dir


def knowledge_upload_max_bytes() -> int:
    raw = os.environ.get("KNOWLEDGE_UPLOAD_MAX_BYTES", str(50 * 1024 * 1024)).strip()
    try:
        return max(1024, min(200 * 1024 * 1024, int(raw)))
    except ValueError:
        return 50 * 1024 * 1024


def github_sync_dir() -> Path:
    d = knowledge_base_dir() / "github_sync"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_upload_and_ingest(original_filename: str, data: bytes) -> tuple[str, int]:
    """
    Write under knowledge_base/github_sync/ (git-tracked when synced), then ingest into FTS.
    Returns (source_key, chunk_count).
    """
    max_b = knowledge_upload_max_bytes()
    if len(data) > max_b:
        raise ValueError(f"File too large (max {max_b} bytes).")
    uid = uuid.uuid4().hex[:10]
    name = f"{uid}_{_safe_stem(original_filename)}"
    dest = github_sync_dir() / name
    dest.write_bytes(data)
    return ingest_path(dest)
