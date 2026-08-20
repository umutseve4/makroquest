"""Pure agent nodes.

Each node is a plain function `state -> partial state update` with **no
langgraph imports**, so the logic is unit-testable anywhere. The graph
wiring in `graph.py` is a thin layer over these functions.

Composer v0 is template-based (no LLM, no API key): it turns the top
retrieved chunks into a cited hint. M1.5's golden-set eval will produce
the numbers that justify (or reject) an LLM upgrade.
"""

from __future__ import annotations

from typing import Any, TypedDict

from makroquest.rag.store import VectorStore

MAX_SNIPPET_CHARS = 320
NO_HIT_ANSWER = "Bu soru için corpus'ta ipucu bulunamadı. Soruyu farklı kelimelerle dene."
MIN_SCORE = 0.05  # below this, lexical overlap is noise, not evidence


class AgentState(TypedDict, total=False):
    question: str
    k: int
    hits: list[dict[str, Any]]  # serializable: source/heading/citation/score/text
    answer: str
    citations: list[str]


def retrieve_node(state: AgentState, store: VectorStore) -> AgentState:
    """Search the store; keep hits as plain dicts so state stays serializable."""
    k = state.get("k", 3)
    hits = store.search(state["question"], k=k)
    return {
        "hits": [
            {
                "source": h.chunk.source,
                "heading": h.chunk.heading,
                "citation": h.chunk.citation,
                "score": round(h.score, 4),
                "text": h.chunk.text,
            }
            for h in hits
            if h.score >= MIN_SCORE
        ]
    }


def compose_node(state: AgentState) -> AgentState:
    """Template composer: cited hint from the top chunks (keyless v0)."""
    hits = state.get("hits", [])
    if not hits:
        return {"answer": NO_HIT_ANSWER, "citations": []}

    parts: list[str] = []
    citations: list[str] = []
    for hit in hits[:2]:
        snippet = _trim(hit["text"], MAX_SNIPPET_CHARS)
        parts.append(f"{snippet}\n(Kaynak: {hit['citation']})")
        citations.append(hit["citation"])

    answer = "İpucu:\n\n" + "\n\n".join(parts)
    return {"answer": answer, "citations": citations}


def _trim(text: str, max_chars: int) -> str:
    """Cut at a sentence/word boundary, never mid-word."""
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    for sep in (". ", "! ", "? "):
        idx = cut.rfind(sep)
        if idx > max_chars // 2:
            return cut[: idx + 1]
    return cut[: cut.rfind(" ")] + "…"
