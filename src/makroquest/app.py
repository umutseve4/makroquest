"""FastAPI uygulaması — M1 iskeleti: retrieval + agent + vaka akışı."""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from makroquest import __version__
from makroquest.agent.api import router as agent_router
from makroquest.cases.api import router as cases_router
from makroquest.rag.api import router as rag_router

app = FastAPI(title="MakroQuest", version=__version__)
app.include_router(rag_router)
app.include_router(agent_router)
app.include_router(cases_router)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """Kök URL'yi API dokümantasyonuna yönlendir (M2'de landing sayfası gelecek)."""
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict:
    """Canlılık kontrolü."""
    return {"status": "ok", "version": __version__}
