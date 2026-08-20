"""LangGraph wiring for the hint agent.

Thin layer: nodes live in `nodes.py` as pure functions; this module only
builds the `retrieve -> compose` StateGraph. If langgraph is not
installed (e.g. minimal envs), `run_agent` falls back to calling the
nodes sequentially — same behavior, no graph runtime.
"""

from __future__ import annotations

from functools import lru_cache

from makroquest.agent.nodes import AgentState, compose_node, retrieve_node
from makroquest.rag.store import VectorStore


def build_graph(store: VectorStore):
    """Compile the retrieve->compose StateGraph (requires langgraph)."""
    from langgraph.graph import END, START, StateGraph

    graph = StateGraph(AgentState)
    graph.add_node("retrieve", lambda state: retrieve_node(state, store))
    graph.add_node("compose", compose_node)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "compose")
    graph.add_edge("compose", END)
    return graph.compile()


@lru_cache(maxsize=1)
def _langgraph_available() -> bool:
    try:
        import langgraph.graph  # noqa: F401
    except ImportError:
        return False
    return True


def run_agent(store: VectorStore, question: str, k: int = 3) -> AgentState:
    """Run the agent on one question; graph if available, else sequential."""
    state: AgentState = {"question": question, "k": k}
    if _langgraph_available():
        return build_graph(store).invoke(state)
    state.update(retrieve_node(state, store))
    state.update(compose_node(state))
    return state
