"""M1.6 tests: YAML case loader, engine rules, and the full API flow.

Acceptance (issue #4): start case -> evidence -> hint -> answer -> score,
exercised end-to-end over the HTTP API.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from makroquest.app import app
from makroquest.cases.engine import CaseEngine, SessionError
from makroquest.cases.loader import CaseValidationError, load_case, load_cases

ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT / "data" / "cases"
CASE_YAML = CASES_DIR / "kasim-2021.yaml"


# ---------- loader ----------


def test_load_case_valid():
    case = load_case(CASE_YAML)
    assert case.id == "kasim-2021"
    assert case.max_score == 100
    assert len(case.evidence) >= 3
    assert all(len(q.choices) >= 2 for q in case.questions)


def test_load_cases_dir():
    cases = load_cases(CASES_DIR)
    assert "kasim-2021" in cases


def test_load_case_rejects_bad_correct_index(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "id: bad\ntitle: t\nbrief: b\n"
        "evidence:\n  - {id: e1, label: l, detail: d}\n"
        "questions:\n"
        "  - {id: q1, text: t, choices: [a, b], correct_index: 5,\n"
        "     points: 10, hint_penalty: 2, hint_query: soru, explanation: e}\n",
        encoding="utf-8",
    )
    with pytest.raises(CaseValidationError, match="correct_index"):
        load_case(bad)


# ---------- engine ----------


def _engine() -> CaseEngine:
    return CaseEngine(load_cases(CASES_DIR))


def test_engine_full_correct_run_no_hints():
    eng = _engine()
    s = eng.start("kasim-2021")
    for q in s.case.questions:
        record = eng.answer(s.session_id, q.id, q.correct_index)
        assert record.correct and record.earned == q.points
    score = eng.score(s.session_id)
    assert score["completed"] is True
    assert score["total_earned"] == score["max_score"] == 100


def test_engine_hint_penalty_and_reanswer_blocked():
    eng = _engine()
    s = eng.start("kasim-2021")
    q1 = s.case.questions[0]
    eng.use_hint(s.session_id, q1.id)
    eng.use_hint(s.session_id, q1.id)  # idempotent, no double penalty
    record = eng.answer(s.session_id, q1.id, q1.correct_index)
    assert record.earned == q1.points - q1.hint_penalty
    with pytest.raises(SessionError, match="already answered"):
        eng.answer(s.session_id, q1.id, q1.correct_index)
    with pytest.raises(SessionError, match="already answered"):
        eng.use_hint(s.session_id, q1.id)


def test_engine_wrong_answer_earns_zero():
    eng = _engine()
    s = eng.start("kasim-2021")
    q1 = s.case.questions[0]
    wrong = (q1.correct_index + 1) % len(q1.choices)
    record = eng.answer(s.session_id, q1.id, wrong)
    assert record.correct is False and record.earned == 0


def test_engine_unknown_ids_raise():
    eng = _engine()
    with pytest.raises(SessionError, match="unknown case"):
        eng.start("yok-boyle-vaka")
    with pytest.raises(SessionError, match="unknown session"):
        eng.get("nope")


# ---------- API flow (issue #4 acceptance) ----------


def test_api_full_case_flow():
    client = TestClient(app)

    # 1) vaka başlat
    start = client.post("/case/kasim-2021/start")
    assert start.status_code == 200
    body = start.json()
    sid = body["session_id"]
    assert body["max_score"] == 100
    # cevap/açıklama sızıntısı yok
    assert "correct_index" not in str(body) and "explanation" not in str(body)

    # 2) delil al
    ev = client.get(f"/case/session/{sid}/evidence")
    assert ev.status_code == 200 and len(ev.json()) >= 3

    # 3) ipucu iste (q2 için) — ajan cevabı + atıf döner
    hint = client.post(f"/case/session/{sid}/hint", json={"question_id": "q2"})
    assert hint.status_code == 200
    hint_body = hint.json()
    assert hint_body["penalty"] == 10 and len(hint_body["citations"]) > 0

    # 4) cevap ver: q1 doğru, q2 doğru (ipuculu), q3 yanlış
    a1 = client.post(f"/case/session/{sid}/answer", json={"question_id": "q1", "choice_index": 0})
    a2 = client.post(f"/case/session/{sid}/answer", json={"question_id": "q2", "choice_index": 1})
    a3 = client.post(f"/case/session/{sid}/answer", json={"question_id": "q3", "choice_index": 0})
    assert a1.json()["earned"] == 30
    assert a2.json()["earned"] == 20  # 30 - 10 ipucu cezası
    assert a3.json()["correct"] is False and a3.json()["earned"] == 0

    # 5) skor döner
    score = client.get(f"/case/session/{sid}/score").json()
    assert score["completed"] is True
    assert score["total_earned"] == 50
    assert score["max_score"] == 100


def test_api_unknown_case_404_and_reanswer_409():
    client = TestClient(app)
    assert client.post("/case/yok/start").status_code == 404

    sid = client.post("/case/kasim-2021/start").json()["session_id"]
    ok = client.post(f"/case/session/{sid}/answer", json={"question_id": "q1", "choice_index": 0})
    assert ok.status_code == 200
    again = client.post(
        f"/case/session/{sid}/answer", json={"question_id": "q1", "choice_index": 0}
    )
    assert again.status_code == 409

