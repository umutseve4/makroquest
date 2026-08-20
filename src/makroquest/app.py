"""FastAPI uygulaması — M1.1 iskeleti."""

from fastapi import FastAPI

from makroquest import __version__

app = FastAPI(title="MakroQuest", version=__version__)


@app.get("/health")
def health() -> dict:
    """Canlılık kontrolü."""
    return {"status": "ok", "version": __version__}
