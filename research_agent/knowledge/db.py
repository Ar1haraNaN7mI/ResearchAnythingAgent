from __future__ import annotations

import sqlite3
from pathlib import Path

from research_agent.paths import knowledge_base_dir


def _sqlite_path() -> Path:
    d = knowledge_base_dir() / "index"
    d.mkdir(parents=True, exist_ok=True)
    return d / "kb.sqlite"


def _connect() -> sqlite3.Connection:
    path = _sqlite_path()
    conn = sqlite3.connect(str(path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS kb_fts USING fts5(
            source_key UNINDEXED,
            chunk_text,
            tokenize = 'unicode61 remove_diacritics 1'
        );
        """
    )
    conn.commit()


def has_any_chunks() -> bool:
    with _connect() as conn:
        _ensure_schema(conn)
        row = conn.execute("SELECT 1 FROM kb_fts LIMIT 1").fetchone()
        return row is not None


def insert_chunks(source_key: str, chunks: list[str]) -> int:
    if not chunks:
        return 0
    with _connect() as conn:
        _ensure_schema(conn)
        conn.executemany(
            "INSERT INTO kb_fts (source_key, chunk_text) VALUES (?, ?)",
            [(source_key, c) for c in chunks],
        )
        conn.commit()
    return len(chunks)


def delete_source(source_key: str) -> int:
    with _connect() as conn:
        _ensure_schema(conn)
        cur = conn.execute("DELETE FROM kb_fts WHERE source_key = ?", (source_key,))
        conn.commit()
        return cur.rowcount or 0


def clear_all() -> None:
    with _connect() as conn:
        _ensure_schema(conn)
        conn.execute("DELETE FROM kb_fts")
        conn.commit()


def list_sources() -> list[tuple[str, int]]:
    """Ordered (source_key, chunk_count)."""
    with _connect() as conn:
        _ensure_schema(conn)
        rows = conn.execute(
            """
            SELECT source_key, COUNT(*) AS n
            FROM kb_fts
            GROUP BY source_key
            ORDER BY MIN(rowid)
            """
        ).fetchall()
        return [(str(r["source_key"]), int(r["n"])) for r in rows]


def total_chunk_count() -> int:
    with _connect() as conn:
        _ensure_schema(conn)
        row = conn.execute("SELECT COUNT(*) AS n FROM kb_fts").fetchone()
        return int(row["n"]) if row else 0


def search_fts(match_query: str, *, limit: int = 24) -> list[tuple[str, str, float]]:
    """
    Returns (source_key, chunk_text, bm25_rank).
    bm25: lower is better (SQLite bm25() auxiliary).
    """
    if not match_query.strip():
        return []
    with _connect() as conn:
        _ensure_schema(conn)
        sql_ranked = """
            SELECT source_key, chunk_text, bm25(kb_fts) AS r
            FROM kb_fts
            WHERE kb_fts MATCH ?
            ORDER BY r
            LIMIT ?
            """
        sql_plain = """
            SELECT source_key, chunk_text, 0.0 AS r
            FROM kb_fts
            WHERE kb_fts MATCH ?
            LIMIT ?
            """
        try:
            rows = conn.execute(sql_ranked, (match_query, limit)).fetchall()
        except sqlite3.OperationalError:
            try:
                rows = conn.execute(sql_plain, (match_query, limit)).fetchall()
            except sqlite3.OperationalError:
                return []
        out: list[tuple[str, str, float]] = []
        for row in rows:
            out.append(
                (
                    str(row["source_key"]),
                    str(row["chunk_text"]),
                    float(row["r"]) if row["r"] is not None else 0.0,
                )
            )
        return out
