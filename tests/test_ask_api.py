"""POST /ask contract tests — MemoryStore (no DB), acceptance criterion of #1/#3."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from makroquest.rag import api as rag_api

    rag_api.get_store.cache_clear()
    from makroquest.app import app

    with TestClient(app) as c:
        yield c
    rag_api.get_store.cache_clear()


def test_ask_returns_answer_with_citation(client):
    resp = client.post("/ask", json={"question": "TL neden değer kaybetti?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"]
    assert len(body["citations"]) >= 1, "acceptance criterion: >=1 source reference"
    assert body["citations"][0] in body["answer"]


def test_ask_validates_input(client):
    assert client.post("/ask", json={"question": "x"}).status_code == 422
    assert client.post("/ask", json={}).status_code == 422
    assert (
        client.post("/ask", json={"question": "geçerli soru", "k": 99}).status_code == 422
    )
