"""OpenMemory MCP server (mcp >= 2.0 API).

Exposes Richard's OpenMemory store to Claude Desktop / Claude Code over stdio.
Configuration via environment (or a .env next to the working directory):

    OPENMEMORY_URL      default http://richard-XPS-15-9560.local:8892
    OPENMEMORY_API_KEY  optional bearer token (backend currently ignores it)
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

from .client import SECTORS, OpenMemoryClient, OpenMemoryError

load_dotenv()
logging.getLogger("httpx").setLevel(logging.WARNING)  # stdio transport: keep stderr quiet

DEFAULT_URL = "http://richard-XPS-15-9560.local:8892"
OPENMEMORY_URL = os.getenv("OPENMEMORY_URL", DEFAULT_URL)
OPENMEMORY_API_KEY = os.getenv("OPENMEMORY_API_KEY") or None

INSTRUCTIONS = (
    "Long-term memory store shared by Richard's Claude sessions. "
    "Search it before answering questions about Richard's machines, services, preferences or past decisions. "
    "Use search_memories for exact terms (hostnames, ports, names, error text) and semantic_search for "
    "questions in your own words; both are cheap, use both when the first comes back thin. "
    "semantic_search is only meaningful when health_check shows a real embedding provider (not 'synthetic'). "
    "When you learn something durable, store it with add_memory: one fact per memory, include dates as "
    "absolute YYYY-MM-DD, and use the hostname richard-XPS-15-9560.local rather than IP addresses, which change."
)

server = MCPServer("openmemory", instructions=INSTRUCTIONS, version="0.2.0")
_client: Optional[OpenMemoryClient] = None


def client() -> OpenMemoryClient:
    global _client
    if _client is None:
        _client = OpenMemoryClient(OPENMEMORY_URL, OPENMEMORY_API_KEY)
    return _client


def _fmt(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def _brief(m: dict) -> dict:
    """Trim a memory record to what the model needs to decide relevance."""
    keep = ("id", "content", "primary_sector", "tags", "metadata", "score", "salience", "created_at", "last_seen_at")
    return {k: m[k] for k in keep if k in m and m[k] not in (None, [], {})}


@server.tool()
async def search_memories(query: str, k: int = 8, sector: Optional[str] = None, require_all: bool = False) -> str:
    """Keyword (BM25) search over all memories: best for exact terms such as hostnames, ports, file paths, names.
    Works regardless of embedding provider; no side effects.

    query: words to look for. sector: optional filter (episodic, semantic, procedural, emotional, reflective).
    require_all: if true, every query word must appear."""
    try:
        hits = await client().keyword_search(query, k=k, sector=sector, require_all=require_all)
        return _fmt([_brief(h) for h in hits]) if hits else "No memories matched."
    except OpenMemoryError as e:
        return f"Error: {e}"


@server.tool()
async def semantic_search(query: str, k: int = 8, sector: Optional[str] = None) -> str:
    """Meaning-based search via the backend's /memory/query (embeddings + salience + recency + links). Good for
    questions phrased in your own words. Only meaningful when health_check shows a real embedding provider
    (openai, gemini, ollama); with 'synthetic' results are random. The backend marks every returned memory as
    seen and raises its salience slightly, so it also acts as reinforcement."""
    try:
        hits = await client().semantic_query(query, k=k, sector=sector)
        return _fmt([_brief(h) for h in hits]) if hits else "No memories matched."
    except OpenMemoryError as e:
        return f"Error: {e}"


@server.tool()
async def add_memory(content: str, sector: Optional[str] = None, tags: Optional[list[str]] = None,
                     metadata: Optional[dict] = None) -> str:
    """Store a new memory. content: one self-contained fact, with absolute dates. sector: optional override of the
    automatic classification (episodic, semantic, procedural, emotional, reflective). tags/metadata optional;
    a metadata 'type' such as system_info, preference, decision, troubleshooting helps later filtering."""
    try:
        r = await client().add_memory(content, sector=sector, tags=tags, metadata=metadata)
        return f"Stored memory {r.get('id')} in sector {r.get('primary_sector')} (sectors: {', '.join(r.get('sectors', []))})."
    except OpenMemoryError as e:
        return f"Error: {e}"


@server.tool()
async def list_memories(limit: int = 20, offset: int = 0, sector: Optional[str] = None) -> str:
    """List memories newest first, with pagination. sector optionally filters by primary sector."""
    try:
        items = await client().list_memories(limit=limit, offset=offset, sector=sector)
        return _fmt([_brief(m) for m in items]) if items else "No memories."
    except OpenMemoryError as e:
        return f"Error: {e}"


@server.tool()
async def get_memory(memory_id: str) -> str:
    """Fetch one memory by id, with full metadata."""
    try:
        return _fmt(await client().get_memory(memory_id))
    except OpenMemoryError as e:
        return f"Error: {e}"


@server.tool()
async def reinforce_memory(memory_id: str, boost: float = 0.1) -> str:
    """Raise a memory's salience (importance) by boost (0..1, default 0.1) and mark it as seen now."""
    try:
        await client().reinforce(memory_id, boost)
        return f"Reinforced {memory_id} by {boost}."
    except OpenMemoryError as e:
        return f"Error: {e}"


@server.tool()
async def delete_memory(memory_id: str) -> str:
    """Permanently delete a memory and its vectors/links. Prefer adding a corrected memory over deleting."""
    try:
        await client().delete(memory_id)
        return f"Deleted {memory_id}."
    except OpenMemoryError as e:
        return f"Error: {e}"


@server.tool()
async def health_check() -> str:
    """Backend health, embedding provider in use, and per-sector counts/average salience."""
    try:
        h = await client().health()
        s = await client().sectors()
        return _fmt({"url": OPENMEMORY_URL, "health": h, "sector_stats": s.get("stats")})
    except OpenMemoryError as e:
        return f"Error: {e}"


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
