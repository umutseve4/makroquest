"""FastAPI uygulaması — M1.1 iskeleti + M1.3 retrieval."""

from fastapi import FastAPI

from makroquest import __version__
from makroquest.rag.api import router as rag_router

app = FastAPI(title="MakroQuest", version=__version__)
app.include_router(rag_router)


@app.get("/health")
def health() -> dict:
    """Canlılık kontrolü."""
    return {"status": "ok", "version": __version__}
