"""M1.5 golden-set eval tests.

Guards three things: the golden set is well-formed, every expected citation
actually exists in the chunked corpus (no phantom targets), and the eval
gate passes on the real corpus with the deterministic MemoryStore.
"""

from pathlib import Path

from makroquest.eval.runner import (
    HIT_RATE_THRESHOLD,
    format_report,
    load_golden_set,
    run_eval,
)
from makroquest.rag.chunking import load_corpus
from makroquest.rag.store import MemoryStore

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "data" / "golden" / "golden_set.jsonl"
CORPUS = ROOT / "data" / "corpus"


def _store() -> MemoryStore:
    store = MemoryStore()
    store.index(load_corpus(CORPUS))
    return store


def test_golden_set_has_30_valid_items():
    items = load_golden_set(GOLDEN)
    assert len(items) == 30
    assert all(i.question and i.expected_citation and i.answer_keywords for i in items)


def test_expected_citations_exist_in_corpus():
    valid = {c.citation for c in load_corpus(CORPUS)}
    items = load_golden_set(GOLDEN)
    missing = [i.expected_citation for i in items if i.expected_citation not in valid]
    assert missing == []


def test_eval_passes_threshold_on_real_corpus():
    report = run_eval(load_golden_set(GOLDEN), _store())
    assert report.total == 30
    assert report.hit_rate >= HIT_RATE_THRESHOLD, format_report(report)


def test_report_metrics_are_consistent():
    report = run_eval(load_golden_set(GOLDEN), _store())
    assert 0.0 <= report.citation_accuracy <= 1.0
    assert 0.0 <= report.keyword_coverage <= 1.0
    assert len(report.failures) == report.total - report.retrieval_hits
    assert "PASS" in format_report(report) or "FAIL" in format_report(report)
