"""YAML case template loader with loud validation.

The template format is the M2 contract: five cases will reuse it, so a
malformed case must fail at load time, not mid-game.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


class CaseValidationError(ValueError):
    """Raised when a case YAML violates the template contract."""


@dataclass(frozen=True)
class Evidence:
    id: str
    label: str
    detail: str


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    choices: list[str]
    correct_index: int
    points: int
    hint_penalty: int
    hint_query: str
    explanation: str


@dataclass(frozen=True)
class Case:
    id: str
    title: str
    brief: str
    evidence: list[Evidence]
    questions: list[Question]

    @property
    def max_score(self) -> int:
        return sum(q.points for q in self.questions)


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise CaseValidationError(msg)


def load_case(path: str | Path) -> Case:
    """Parse and validate one case YAML; raises CaseValidationError."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    _require(isinstance(raw, dict), f"{path}: top level must be a mapping")
    for key in ("id", "title", "brief", "evidence", "questions"):
        _require(key in raw, f"{path}: missing key {key!r}")

    evidence = [Evidence(**e) for e in raw["evidence"]]
    _require(len(evidence) > 0, f"{path}: evidence is empty")
    ev_ids = [e.id for e in evidence]
    _require(len(ev_ids) == len(set(ev_ids)), f"{path}: duplicate evidence ids")

    questions: list[Question] = []
    for q in raw["questions"]:
        question = Question(**q)
        _require(len(question.choices) >= 2, f"{question.id}: needs >= 2 choices")
        _require(
            0 <= question.correct_index < len(question.choices),
            f"{question.id}: correct_index out of range",
        )
        _require(question.points > 0, f"{question.id}: points must be > 0")
        _require(
            0 <= question.hint_penalty <= question.points,
            f"{question.id}: hint_penalty must be within [0, points]",
        )
        _require(bool(question.hint_query.strip()), f"{question.id}: empty hint_query")
        questions.append(question)
    _require(len(questions) > 0, f"{path}: questions is empty")
    q_ids = [q.id for q in questions]
    _require(len(q_ids) == len(set(q_ids)), f"{path}: duplicate question ids")

    return Case(
        id=raw["id"],
        title=raw["title"],
        brief=raw["brief"],
        evidence=evidence,
        questions=questions,
    )


def load_cases(cases_dir: str | Path) -> dict[str, Case]:
    """Load every *.yaml under the cases dir, keyed by case id."""
    cases: dict[str, Case] = {}
    for path in sorted(Path(cases_dir).glob("*.yaml")):
        case = load_case(path)
        _require(case.id not in cases, f"duplicate case id {case.id!r}")
        cases[case.id] = case
    return cases
