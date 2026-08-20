"""Graph wiring test — runs the real langgraph StateGraph (installed in CI)."""

import pytest

from makroquest.agent.graph import build_graph, run_agent
from makroquest.rag.chunking import Chunk
from makroquest.rag.store import MemoryStore

pytest.importorskip("langgraph")


def _store() -> MemoryStore:
    store = MemoryStore()
    store.index(
        [
            Chunk(
                source="data/corpus/doviz-kuru.md",
                heading="Kasım 2021 örneği",
                text="Kasım 2021'de TL, faiz indirimleri sonrasında hızla değer kaybetti.",
            ),
        ]
    )
    return store


def test_graph_invoke_end_to_end():
    result = build_graph(_store()).invoke({"question": "TL neden değer kaybetti", "k": 3})
    assert result["answer"].startswith("İpucu:")
    assert result["citations"] == ["data/corpus/doviz-kuru.md#Kasım 2021 örneği"]


def test_run_agent_matches_graph():
    result = run_agent(_store(), "TL neden değer kaybetti")
    assert result["citations"], "run_agent must return citations"
