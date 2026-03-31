"""User knowledge base: ingest (PDF via OpenDataLoader, text/Markdown), SQLite FTS5, retrieval."""

from research_agent.knowledge.ingest import ingest_path
from research_agent.knowledge.retrieve import retrieve_for_prompt

__all__ = ["ingest_path", "retrieve_for_prompt"]
