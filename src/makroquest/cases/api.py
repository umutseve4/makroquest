"""Case play endpoints (issue #4 acceptance criteria).

Flow: POST /case/{id}/start -> GET evidence -> POST hint -> POST answer
-> GET score. Answers/explanations are never leaked before answering.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from makroquest.agent.graph import run_agent
from makroquest.cases.engine import CaseEngine, SessionError
from makroquest.cases.loader import load_cases
from makroquest.paths import data_dir
from makroquest.rag.api import get_store

router = APIRouter(prefix="/case")


def _cases_dir() -> Path:
    return data_dir() / "cases"


@lru_cache(maxsize=1)
def get_engine() -> CaseEngine:
    """Load case templates once per process."""
    return CaseEngine(load_cases(_cases_dir()))


class CaseSummary(BaseModel):
    id: str
    title: str
    max_score: int


class PublicQuestion(BaseModel):
    id: str
    text: str
    choices: list[str]
    points: int
    hint_penalty: int


class EvidenceItem(BaseModel):
    id: str
    label: str
    detail: str


class StartResponse(BaseModel):
    session_id: str
    case_id: str
    title: str
    brief: str
    max_score: int
    evidence: list[EvidenceItem]
    questions: list[PublicQuestion]


class HintRequest(BaseModel):
    question_id: str = Field(min_length=1, max_length=100)


class HintResponse(BaseModel):
    question_id: str
    hint: str
    citations: list[str]
    penalty: int


class AnswerRequest(BaseModel):
    question_id: str = Field(min_length=1, max_length=100)
    choice_index: int = Field(ge=0)


class AnswerResponse(BaseModel):
    question_id: str
    correct: bool
    earned: int
    explanation: str


def _fail(exc: SessionError) -> HTTPException:
    msg = str(exc)
    status = 404 if "unknown" in msg else 409
    return HTTPException(status_code=status, detail=msg)


@router.get("", response_model=list[CaseSummary])
def list_cases() -> list[CaseSummary]:
    return [
        CaseSummary(id=c.id, title=c.title, max_score=c.max_score)
        for c in get_engine().cases.values()
    ]


@router.post("/{case_id}/start", response_model=StartResponse)
def start_case(case_id: str) -> StartResponse:
    try:
        session = get_engine().start(case_id)
    except SessionError as exc:
        raise _fail(exc) from exc
    case = session.case
    return StartResponse(
        session_id=session.session_id,
        case_id=case.id,
        title=case.title,
        brief=case.brief,
        max_score=case.max_score,
        evidence=[EvidenceItem(id=e.id, label=e.label, detail=e.detail) for e in case.evidence],
        questions=[
            PublicQuestion(
                id=q.id,
                text=q.text,
                choices=q.choices,
                points=q.points,
                hint_penalty=q.hint_penalty,
            )
            for q in case.questions
        ],
    )


@router.get("/session/{session_id}/evidence", response_model=list[EvidenceItem])
def get_evidence(session_id: str) -> list[EvidenceItem]:
    try:
        session = get_engine().get(session_id)
    except SessionError as exc:
        raise _fail(exc) from exc
    return [
        EvidenceItem(id=e.id, label=e.label, detail=e.detail) for e in session.case.evidence
    ]


@router.post("/session/{session_id}/hint", response_model=HintResponse)
def request_hint(session_id: str, req: HintRequest) -> HintResponse:
    try:
        question = get_engine().use_hint(session_id, req.question_id)
    except SessionError as exc:
        raise _fail(exc) from exc
    result = run_agent(get_store(), question.hint_query, k=3)
    return HintResponse(
        question_id=question.id,
        hint=result["answer"],
        citations=result.get("citations", []),
        penalty=question.hint_penalty,
    )


@router.post("/session/{session_id}/answer", response_model=AnswerResponse)
def submit_answer(session_id: str, req: AnswerRequest) -> AnswerResponse:
    engine = get_engine()
    try:
        record = engine.answer(session_id, req.question_id, req.choice_index)
        session = engine.get(session_id)
    except SessionError as exc:
        raise _fail(exc) from exc
    question = next(q for q in session.case.questions if q.id == req.question_id)
    return AnswerResponse(
        question_id=req.question_id,
        correct=record.correct,
        earned=record.earned,
        explanation=question.explanation,
    )


@router.get("/session/{session_id}/score")
def get_score(session_id: str) -> dict:
    try:
        return get_engine().score(session_id)
    except SessionError as exc:
        raise _fail(exc) from exc
