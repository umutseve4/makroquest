"""RAG retrieval endpoint.

GET /retrieve?q=...&k=5  ->  top-k corpus chunks with citations.

Store selection at startup:
- DATABASE_URL set  -> PgVectorStore (Neon in prod, service container in CI)
- otherwise         -> MemoryStore over the same corpus (dev fallback)
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Query
from pydantic import BaseModel

from makroquest.rag.chunking import load_corpus

router = APIRouter()

CORPUS_DIR = Path(__file__).resolve().parents[3] / "data" / "corpus"


class RetrievedChunk(BaseModel):
    source: str
    heading: str
    citation: str
    score: float
    text: str


class RetrieveResponse(BaseModel):
    query: str
    results: list[RetrievedChunk]


@lru_cache(maxsize=1)
def get_store():
    """Build (and index) the store once per process."""
    chunks = load_corpus(CORPUS_DIR)
    dsn = os.environ.get("DATABASE_URL", "")
    if dsn:
        from makroquest.rag.store import PgVectorStore

        store = PgVectorStore(dsn)
    else:
        from makroquest.rag.store import MemoryStore

        store = MemoryStore()
    store.index(chunks)
    return store


@router.get("/retrieve", response_model=RetrieveResponse)
def retrieve(
    q: str = Query(min_length=2, max_length=500),
    k: int = Query(default=5, ge=1, le=20),
) -> RetrieveResponse:
    hits = get_store().search(q, k=k)
    return RetrieveResponse(
        query=q,
        results=[
            RetrievedChunk(
                source=h.chunk.source,
                heading=h.chunk.heading,
                citation=h.chunk.citation,
                score=round(h.score, 4),
                text=h.chunk.text,
            )
            for h in hits
        ],
    )
