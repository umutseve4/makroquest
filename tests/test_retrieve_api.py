"""/retrieve endpoint test — forces MemoryStore by clearing DATABASE_URL."""

from __future__ import annotations

from fastapi.testclient import TestClient

from makroquest.rag import api as rag_api


def _client(monkeypatch) -> TestClient:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    rag_api.get_store.cache_clear()
    from makroquest.app import app

    return TestClient(app)


def test_retrieve_returns_cited_chunks(monkeypatch):
    client = _client(monkeypatch)
    resp = client.get("/retrieve", params={"q": "enflasyon neden yükselir", "k": 3})
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "enflasyon neden yükselir"
    assert len(body["results"]) == 3
    top = body["results"][0]
    assert top["citation"]
    assert top["score"] > 0


def test_retrieve_validates_query(monkeypatch):
    client = _client(monkeypatch)
    assert client.get("/retrieve", params={"q": "a"}).status_code == 422
    assert client.get("/retrieve", params={"q": "enflasyon", "k": 0}).status_code == 422
