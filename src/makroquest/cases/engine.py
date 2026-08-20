"""Pure case-session state machine: start -> hint -> answer -> score.

Rules:
- One answer per question; re-answering raises.
- A hint before answering costs `hint_penalty` (once per question,
  idempotent); hints after answering are refused.
- Earned points: correct -> points - penalty(if hint used), wrong -> 0.

Sessions live in memory (M1.6 scope); persistent player state is a later
milestone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from makroquest.cases.loader import Case, Question


class SessionError(Exception):
    """Invalid session operation (unknown id, re-answer, late hint)."""


@dataclass
class AnswerRecord:
    choice_index: int
    correct: bool
    earned: int


@dataclass
class CaseSession:
    session_id: str
    case: Case
    answers: dict[str, AnswerRecord] = field(default_factory=dict)
    hints_used: set[str] = field(default_factory=set)

    @property
    def completed(self) -> bool:
        return len(self.answers) == len(self.case.questions)

    @property
    def total_earned(self) -> int:
        return sum(a.earned for a in self.answers.values())


class CaseEngine:
    """Holds cases and in-memory sessions."""

    def __init__(self, cases: dict[str, Case]) -> None:
        self._cases = cases
        self._sessions: dict[str, CaseSession] = {}

    @property
    def cases(self) -> dict[str, Case]:
        return self._cases

    def start(self, case_id: str) -> CaseSession:
        if case_id not in self._cases:
            raise SessionError(f"unknown case {case_id!r}")
        session = CaseSession(session_id=uuid4().hex, case=self._cases[case_id])
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> CaseSession:
        if session_id not in self._sessions:
            raise SessionError(f"unknown session {session_id!r}")
        return self._sessions[session_id]

    def _question(self, session: CaseSession, question_id: str) -> Question:
        for q in session.case.questions:
            if q.id == question_id:
                return q
        raise SessionError(f"unknown question {question_id!r}")

    def use_hint(self, session_id: str, question_id: str) -> Question:
        """Mark the hint as used (idempotent) and return the question."""
        session = self.get(session_id)
        question = self._question(session, question_id)
        if question.id in session.answers:
            raise SessionError(f"question {question_id!r} already answered")
        session.hints_used.add(question.id)
        return question

    def answer(self, session_id: str, question_id: str, choice_index: int) -> AnswerRecord:
        session = self.get(session_id)
        question = self._question(session, question_id)
        if question.id in session.answers:
            raise SessionError(f"question {question_id!r} already answered")
        if not 0 <= choice_index < len(question.choices):
            raise SessionError(f"choice_index {choice_index} out of range")
        correct = choice_index == question.correct_index
        earned = 0
        if correct:
            earned = question.points
            if question.id in session.hints_used:
                earned -= question.hint_penalty
        record = AnswerRecord(choice_index=choice_index, correct=correct, earned=earned)
        session.answers[question.id] = record
        return record

    def score(self, session_id: str) -> dict:
        session = self.get(session_id)
        breakdown = []
        for q in session.case.questions:
            record = session.answers.get(q.id)
            breakdown.append(
                {
                    "question_id": q.id,
                    "answered": record is not None,
                    "correct": record.correct if record else None,
                    "hint_used": q.id in session.hints_used,
                    "earned": record.earned if record else 0,
                    "max_points": q.points,
                }
            )
        return {
            "session_id": session.session_id,
            "case_id": session.case.id,
            "completed": session.completed,
            "total_earned": session.total_earned,
            "max_score": session.case.max_score,
            "breakdown": breakdown,
        }
