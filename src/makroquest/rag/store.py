"""Vector store.

Two backends behind one duck-typed interface (`index`, `search`):

- `MemoryStore` — stdlib-only, used in unit tests and as a no-DB fallback.
- `PgVectorStore` — Postgres + pgvector (Neon in prod, service container
  in CI). Imported lazily so the package works without psycopg installed.

Schema is created idempotently; re-indexing a corpus replaces rows keyed by
(source, heading, chunk_no), so runs are repeatable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from makroquest.rag.chunking import Chunk
from makroquest.rag.embeddings import HashingEmbedder, cosine


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


class VectorStore(Protocol):
    def index(self, chunks: list[Chunk]) -> int: ...
    def search(self, query: str, k: int = 5) -> list[Hit]: ...


class MemoryStore:
    """In-process store — exact cosine over all chunks."""

    def __init__(self, embedder: HashingEmbedder | None = None) -> None:
        self.embedder = embedder or HashingEmbedder()
        self._rows: list[tuple[Chunk, list[float]]] = []

    def index(self, chunks: list[Chunk]) -> int:
        vectors = self.embedder.embed([c.text for c in chunks])
        self._rows = list(zip(chunks, vectors, strict=True))
        return len(self._rows)

    def search(self, query: str, k: int = 5) -> list[Hit]:
        if not self._rows:
            return []
        qv = self.embedder.embed([query])[0]
        scored = [Hit(chunk=c, score=cosine(qv, v)) for c, v in self._rows]
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:k]


SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS chunks (
    id        BIGSERIAL PRIMARY KEY,
    source    TEXT NOT NULL,
    heading   TEXT NOT NULL DEFAULT '',
    chunk_no  INT  NOT NULL,
    text      TEXT NOT NULL,
    embedder  TEXT NOT NULL,
    embedding vector({dim}) NOT NULL,
    UNIQUE (source, heading, chunk_no)
);
"""


class PgVectorStore:
    """pgvector-backed store. Requires `psycopg` and a DATABASE_URL."""

    def __init__(self, dsn: str, embedder: HashingEmbedder | None = None) -> None:
        import psycopg  # lazy: optional dependency

        self.embedder = embedder or HashingEmbedder()
        self._conn: Any = psycopg.connect(dsn, autocommit=True)
        self._conn.execute(SCHEMA.format(dim=self.embedder.dim))

    def index(self, chunks: list[Chunk]) -> int:
        vectors = self.embedder.embed([c.text for c in chunks])
        counters: dict[tuple[str, str], int] = {}
        rows = []
        for chunk, vec in zip(chunks, vectors, strict=True):
            key = (chunk.source, chunk.heading)
            no = counters.get(key, 0)
            counters[key] = no + 1
            rows.append(
                (chunk.source, chunk.heading, no, chunk.text, self.embedder.name, _lit(vec))
            )
        with self._conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO chunks (source, heading, chunk_no, text, embedder, embedding) "
                "VALUES (%s, %s, %s, %s, %s, %s::vector) "
                "ON CONFLICT (source, heading, chunk_no) DO UPDATE SET "
                "text = EXCLUDED.text, embedder = EXCLUDED.embedder, "
                "embedding = EXCLUDED.embedding",
                rows,
            )
        return len(rows)

    def search(self, query: str, k: int = 5) -> list[Hit]:
        qv = _lit(self.embedder.embed([query])[0])
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT source, heading, text, 1 - (embedding <=> %s::vector) AS score "
                "FROM chunks ORDER BY embedding <=> %s::vector LIMIT %s",
                (qv, qv, k),
            )
            rows = cur.fetchall()
        return [
            Hit(chunk=Chunk(source=s, heading=h, text=t), score=float(score))
            for s, h, t, score in rows
        ]

    def close(self) -> None:
        self._conn.close()


def _lit(vec: list[float]) -> str:
    """pgvector literal: '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{v:.8f}" for v in vec) + "]"
