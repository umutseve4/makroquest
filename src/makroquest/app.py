"""FastAPI uygulaması — M1.1 iskeleti + M1.3 retrieval + M1.4 agent."""

from fastapi import FastAPI

from makroquest import __version__
from makroquest.agent.api import router as agent_router
from makroquest.rag.api import router as rag_router

app = FastAPI(title="MakroQuest", version=__version__)
app.include_router(rag_router)
app.include_router(agent_router)


@app.get("/health")
def health() -> dict:
    """Canlılık kontrolü."""
    return {"status": "ok", "version": __version__}
