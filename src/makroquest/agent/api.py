"""POST /ask — cited hint from the agent (issue #1 acceptance criterion)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from makroquest.agent.graph import run_agent
from makroquest.rag.api import get_store

router = APIRouter()


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    k: int = Field(default=3, ge=1, le=10)


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[str]


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    result = run_agent(get_store(), req.question, k=req.k)
    return AskResponse(
        question=req.question,
        answer=result["answer"],
        citations=result.get("citations", []),
    )
