"""Golden-set RAG evaluation (M1.5).

Measures whether the retrieval + hint pipeline actually finds the right
evidence, instead of assuming it does. Run with `python -m makroquest.eval`.
"""

from makroquest.eval.runner import GoldenItem, Report, load_golden_set, run_eval

__all__ = ["GoldenItem", "Report", "load_golden_set", "run_eval"]
