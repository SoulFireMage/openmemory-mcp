"""HTTP client for the OpenMemory backend (CaviraOSS OpenMemory 2.0-hsg fork).

Endpoint paths here match backend/src/server/index.ts exactly:

    GET    /health
    GET    /sectors
    GET    /memory/all?l=<limit>&u=<offset>[&sector=]
    GET    /memory/<id>
    POST   /memory/add          {content, tags, metadata}
    POST   /memory/query        {query, k, filters:{sector, min_score}}
    POST   /memory/reinforce    {id, boost}
    DELETE /memory/<id>
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Optional

import httpx

SECTORS = ("episodic", "semantic", "procedural", "emotional", "reflective")


class OpenMemoryError(RuntimeError):
    """Raised for HTTP or API-level failures, with a message safe to show the model."""


class OpenMemoryClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._http = httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=timeout)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _req(self, method: str, path: str, what: str = "", **kw: Any) -> Any:
        try:
            r = await self._http.request(method, path, **kw)
        except httpx.HTTPError as e:
            raise OpenMemoryError(f"cannot reach OpenMemory at {self.base_url}: {e}") from e
        if r.status_code == 404:
            raise OpenMemoryError(f"not found: {what or method + ' ' + path}")
        if r.status_code == 401:
            raise OpenMemoryError("unauthorised: check OPENMEMORY_API_KEY")
        if r.status_code >= 400:
            raise OpenMemoryError(f"OpenMemory returned {r.status_code}: {r.text[:300]}")
        try:
            return r.json()
        except ValueError:
            raise OpenMemoryError(f"non-JSON response from {path}: {r.text[:200]}")

    # ---- read ---------------------------------------------------------------
    async def health(self) -> dict:
        return await self._req("GET", "/health")

    async def sectors(self) -> dict:
        return await self._req("GET", "/sectors")

    async def list_memories(self, limit: int = 20, offset: int = 0, sector: Optional[str] = None) -> list[dict]:
        params: dict[str, Any] = {"l": limit, "u": offset}
        if sector:
            params["sector"] = sector
        data = await self._req("GET", "/memory/all", params=params)
        return data.get("items", [])  # NB: key is "items", not "memories"

    async def get_memory(self, memory_id: str) -> dict:
        return await self._req("GET", f"/memory/{memory_id}", what=f"memory {memory_id}")

    async def semantic_query(self, query: str, k: int = 10, sector: Optional[str] = None,
                             min_score: Optional[float] = None) -> list[dict]:
        filters: dict[str, Any] = {}
        if sector:
            filters["sector"] = sector
        if min_score is not None:
            filters["min_score"] = min_score
        payload: dict[str, Any] = {"query": query, "k": k}
        if filters:
            payload["filters"] = filters
        data = await self._req("POST", "/memory/query", json=payload)
        return data.get("matches", [])  # NB: key is "matches"

    async def keyword_search(self, query: str, k: int = 10, sector: Optional[str] = None,
                             require_all: bool = False) -> list[dict]:
        """BM25-style ranking over the full store, done client-side.

        The backend's /memory/query ranks by cosine similarity over whatever
        embedding provider it was started with. With OM_EMBEDDINGS=synthetic
        (the default) those vectors are a function of text *length* only, so
        semantic ranking is noise. This path works regardless of the provider
        and has no side effects (the backend's query path reinforces salience
        on whatever it returns).
        """
        terms = [t for t in _tokens(query) if len(t) > 1]
        if not terms:
            return []
        docs = await self.list_memories(limit=5000, offset=0, sector=sector)
        n = len(docs) or 1
        tokenised = [(_tokens(d.get("content", "")) + _tokens(" ".join(d.get("tags") or []))) for d in docs]
        df = Counter()
        for toks in tokenised:
            df.update(set(toks))
        avgdl = sum(len(t) for t in tokenised) / n
        k1, b = 1.2, 0.75
        scored = []
        for d, toks in zip(docs, tokenised):
            tf = Counter(toks)
            hit = [t for t in terms if tf.get(t)]
            if not hit or (require_all and len(hit) < len(set(terms))):
                continue
            s = 0.0
            for t in hit:
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                s += idf * (tf[t] * (k1 + 1)) / (tf[t] + k1 * (1 - b + b * len(toks) / avgdl))
            scored.append((s, d))
        scored.sort(key=lambda x: -x[0])
        return [dict(d, score=round(s, 3)) for s, d in scored[:k]]

    # ---- write --------------------------------------------------------------
    async def add_memory(self, content: str, sector: Optional[str] = None,
                         tags: Optional[list[str]] = None, metadata: Optional[dict] = None) -> dict:
        meta = dict(metadata or {})
        if sector:
            if sector not in SECTORS:
                raise OpenMemoryError(f"unknown sector {sector!r}; choose one of {', '.join(SECTORS)}")
            meta["sector"] = sector  # backend honours metadata.sector to override auto-classification
        return await self._req("POST", "/memory/add", json={"content": content, "tags": tags or [], "metadata": meta})

    async def reinforce(self, memory_id: str, boost: float = 0.1) -> dict:
        return await self._req("POST", "/memory/reinforce", what=f"memory {memory_id}", json={"id": memory_id, "boost": boost})

    async def delete(self, memory_id: str) -> dict:
        return await self._req("DELETE", f"/memory/{memory_id}", what=f"memory {memory_id}")


_STOP = {"the", "and", "for", "with", "that", "this", "from", "are", "was", "not", "but", "its", "has", "have"}


def _tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9][a-z0-9_.\-]*", text.lower()) if w not in _STOP]
