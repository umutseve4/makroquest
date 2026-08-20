"""Golden-set eval runner.

Three metrics, one threshold:

- **hit-rate@k** — expected citation appears in the top-k retrieval results.
  This is the PASS/FAIL gate (issue #2: >= 0.70).
- **citation accuracy** — expected citation appears in the citations of the
  *composed* answer (composer cites top-2 only, so this is stricter).
- **keyword coverage** — at least one expected answer keyword appears in the
  composed answer text (casefold match). Reported, not gated.

Deterministic: MemoryStore + HashingEmbedder, no network, no API keys.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from makroquest.agent.graph import run_agent
from makroquest.rag.chunking import load_corpus
from makroquest.rag.store import MemoryStore, VectorStore

HIT_RATE_THRESHOLD = 0.70
DEFAULT_K = 3


@dataclass(frozen=True)
class GoldenItem:
    question: str
    expected_citation: str
    answer_keywords: list[str]


@dataclass
class Report:
    total: int = 0
    retrieval_hits: int = 0
    citation_hits: int = 0
    keyword_hits: int = 0
    failures: list[str] = field(default_factory=list)

    @property
    def hit_rate(self) -> float:
        return self.retrieval_hits / self.total if self.total else 0.0

    @property
    def citation_accuracy(self) -> float:
        return self.citation_hits / self.total if self.total else 0.0

    @property
    def keyword_coverage(self) -> float:
        return self.keyword_hits / self.total if self.total else 0.0

    @property
    def passed(self) -> bool:
        return self.total > 0 and self.hit_rate >= HIT_RATE_THRESHOLD


def load_golden_set(path: str | Path) -> list[GoldenItem]:
    """Load and validate the JSONL golden set; bad rows fail loudly."""
    items: list[GoldenItem] = []
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        for key in ("question", "expected_citation", "answer_keywords"):
            if key not in row:
                raise ValueError(f"golden set line {line_no}: missing key {key!r}")
        if not row["answer_keywords"]:
            raise ValueError(f"golden set line {line_no}: answer_keywords is empty")
        items.append(
            GoldenItem(
                question=row["question"],
                expected_citation=row["expected_citation"],
                answer_keywords=list(row["answer_keywords"]),
            )
        )
    return items


def run_eval(
    items: list[GoldenItem], store: VectorStore, k: int = DEFAULT_K
) -> Report:
    report = Report(total=len(items))
    for item in items:
        hits = store.search(item.question, k=k)
        retrieved = [h.chunk.citation for h in hits]
        if item.expected_citation in retrieved:
            report.retrieval_hits += 1
        else:
            report.failures.append(
                f"MISS  {item.question!r} -> beklenen {item.expected_citation!r}, "
                f"gelen {retrieved!r}"
            )

        result = run_agent(store, item.question, k=k)
        if item.expected_citation in result.get("citations", []):
            report.citation_hits += 1
        answer = result.get("answer", "").casefold()
        if any(kw.casefold() in answer for kw in item.answer_keywords):
            report.keyword_hits += 1
    return report


def format_report(report: Report, k: int = DEFAULT_K) -> str:
    lines = [
        "===== GOLDEN-SET EVAL =====",
        f"sorular             : {report.total}",
        f"hit-rate@{k}          : {report.hit_rate:.2%}  (esik {HIT_RATE_THRESHOLD:.0%})",
        f"citation accuracy   : {report.citation_accuracy:.2%}",
        f"keyword coverage    : {report.keyword_coverage:.2%}",
        f"sonuc               : {'PASS' if report.passed else 'FAIL'}",
    ]
    if report.failures:
        lines.append("--- kacirilanlar ---")
        lines.extend(report.failures)
    return "\n".join(lines)


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    corpus_dir = root / "data" / "corpus"
    golden_path = root / "data" / "golden" / "golden_set.jsonl"

    chunks = load_corpus(corpus_dir)
    store = MemoryStore()
    store.index(chunks)

    items = load_golden_set(golden_path)
    report = run_eval(items, store)
    print(format_report(report))
    return 0 if report.passed else 1
