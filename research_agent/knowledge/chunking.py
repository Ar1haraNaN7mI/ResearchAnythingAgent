from __future__ import annotations


def chunk_text(text: str, *, size: int = 1200, overlap: int = 200) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    chunks: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        end = min(i + size, n)
        chunks.append(text[i:end])
        if end >= n:
            break
        i = max(0, end - overlap)
    return chunks
