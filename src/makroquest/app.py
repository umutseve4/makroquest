"""FastAPI uygulaması — M1 iskeleti: retrieval + agent + vaka akışı."""

from fastapi import FastAPI

from makroquest import __version__
from makroquest.agent.api import router as agent_router
from makroquest.cases.api import router as cases_router
from makroquest.rag.api import router as rag_router

app = FastAPI(title="MakroQuest", version=__version__)
app.include_router(rag_router)
app.include_router(agent_router)
app.include_router(cases_router)


@app.get("/health")
def health() -> dict:
    """Canlılık kontrolü."""
    return {"status": "ok", "version": __version__}
