"""Score aggregation and flag assignment."""

from __future__ import annotations

KEYWORD_METRIC = "keyword"


def aggregate_scores(results: list[dict]) -> float:
    """Return the average of ``score`` values in ``results``."""
    if not results:
        return 0.0
    return sum(float(r["score"]) for r in results) / len(results)


def assign_flag(results: list[dict]) -> str:
    """
    Assign outcome flag from evaluator results.

    * Keyword failure → INCORRECT (critical)
    * All pass → GOOD
    * Any other failure → BAD
    """
    for r in results:
        if r.get("metric") == KEYWORD_METRIC and not r.get("passed"):
            return "INCORRECT"

    if results and all(r.get("passed") for r in results):
        return "GOOD"

    return "BAD"
