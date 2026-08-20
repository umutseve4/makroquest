"""RAG unit tests — no network, no Postgres (MemoryStore + fixtures)."""

from __future__ import annotations

from pathlib import Path

from makroquest.rag.chunking import load_corpus, split_markdown
from makroquest.rag.embeddings import HashingEmbedder, cosine
from makroquest.rag.store import MemoryStore

CORPUS = Path(__file__).resolve().parents[1] / "data" / "corpus"


def test_split_markdown_headings_and_limit():
    md = "# A\n\npara one\n\n# B\n\n" + "x" * 900
    chunks = split_markdown("doc.md", md, max_chars=800)
    assert [c.heading for c in chunks][:2] == ["A", "B"]
    assert all(len(c.text) <= 800 for c in chunks)
    assert chunks[0].citation == "doc.md#A"


def test_load_corpus_nonempty_and_deterministic():
    a = load_corpus(CORPUS)
    b = load_corpus(CORPUS)
    assert len(a) >= 5
    assert a == b


def test_embedding_deterministic_and_normalized():
    e = HashingEmbedder()
    v1, v2 = e.embed(["enflasyon nedir", "enflasyon nedir"])
    assert v1 == v2
    assert abs(cosine(v1, v2) - 1.0) < 1e-9
    assert len(v1) == e.dim


def test_similar_text_scores_higher_than_unrelated():
    e = HashingEmbedder()
    q, near, far = e.embed(
        [
            "enflasyon neden yükselir",
            "enflasyonun nedenleri talep ve maliyet baskılarıdır",
            "futbol maçında hakem penaltı verdi",
        ]
    )
    assert cosine(q, near) > cosine(q, far)


def test_memory_store_retrieves_relevant_chunk():
    store = MemoryStore()
    n = store.index(load_corpus(CORPUS))
    assert n >= 5
    hits = store.search("TL neden değer kaybetti", k=3)
    assert len(hits) == 3
    assert hits[0].score >= hits[-1].score
    top_sources = {h.chunk.source for h in hits}
    assert "doviz-kuru.md" in top_sources
