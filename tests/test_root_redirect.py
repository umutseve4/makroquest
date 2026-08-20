"""Kök URL yönlendirme testi — / artık 404 değil, /docs'a redirect."""

from fastapi.testclient import TestClient

from makroquest.app import app

client = TestClient(app)


def test_root_redirects_to_docs() -> None:
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/docs"


def test_root_followed_lands_on_docs() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert "swagger" in resp.text.lower()
