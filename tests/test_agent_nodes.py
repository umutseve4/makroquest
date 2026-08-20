"""Unit tests for pure agent nodes — no langgraph, no DB."""

from makroquest.agent.nodes import NO_HIT_ANSWER, _trim, compose_node, retrieve_node
from makroquest.rag.chunking import Chunk
from makroquest.rag.store import MemoryStore


def _store() -> MemoryStore:
    store = MemoryStore()
    store.index(
        [
            Chunk(
                source="data/corpus/doviz-kuru.md",
                heading="Kasım 2021 örneği",
                text="Kasım 2021'de TL, faiz indirimleri sonrasında hızla değer kaybetti.",
            ),
            Chunk(
                source="data/corpus/enflasyon.md",
                heading="TÜFE nedir",
                text="TÜFE, hanehalkının tükettiği mal ve hizmet sepetinin fiyat değişimini ölçer.",
            ),
        ]
    )
    return store


def test_retrieve_node_returns_serializable_hits():
    update = retrieve_node({"question": "TL neden değer kaybetti", "k": 2}, _store())
    hits = update["hits"]
    assert hits, "expected at least one hit"
    top = hits[0]
    assert top["citation"] == "data/corpus/doviz-kuru.md#Kasım 2021 örneği"
    assert set(top) == {"source", "heading", "citation", "score", "text"}
    assert isinstance(top["score"], float)


def test_compose_node_cites_sources():
    update = retrieve_node({"question": "TL neden değer kaybetti", "k": 2}, _store())
    result = compose_node(update)
    assert result["citations"], "answer must carry at least one citation"
    assert result["citations"][0] in result["answer"]
    assert result["answer"].startswith("İpucu:")


def test_compose_node_empty_hits():
    result = compose_node({"hits": []})
    assert result["answer"] == NO_HIT_ANSWER
    assert result["citations"] == []


def test_trim_respects_word_boundary():
    text = "kelime " * 100
    out = _trim(text.strip(), 50)
    assert len(out) <= 51  # boundary cut + ellipsis
    assert not out.rstrip("…").endswith("kelim")  # never mid-word
