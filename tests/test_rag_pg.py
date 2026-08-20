"""pgvector integration tests.

Run only when DATABASE_URL is set (CI provides a pgvector service
container; locally you can point at Neon). Skipped otherwise.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from makroquest.rag.chunking import load_corpus

DSN = os.environ.get("DATABASE_URL", "")
CORPUS = Path(__file__).resolve().parents[1] / "data" / "corpus"

pytestmark = pytest.mark.skipif(not DSN, reason="DATABASE_URL not set")


@pytest.fixture()
def store():
    from makroquest.rag.store import PgVectorStore

    s = PgVectorStore(DSN)
    yield s
    s.close()


def test_index_is_idempotent(store):
    chunks = load_corpus(CORPUS)
    n1 = store.index(chunks)
    n2 = store.index(chunks)
    assert n1 == n2 == len(chunks)


def test_pg_search_matches_expectations(store):
    store.index(load_corpus(CORPUS))
    hits = store.search("TL neden değer kaybetti", k=3)
    assert len(hits) == 3
    assert hits[0].score >= hits[-1].score
    assert any(h.chunk.source == "doviz-kuru.md" for h in hits)
