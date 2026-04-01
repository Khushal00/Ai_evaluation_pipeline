"""Score aggregation and flag assignment."""

from __future__ import annotations

def aggregate_scores(results: list[dict]) -> float:
    """Return the average of ``score`` values in ``results``."""
    if not results:
        return 1.0
    return sum(float(r["score"]) for r in results) / len(results)


def assign_flag(results: list[dict]) -> str:
    """
    Assign outcome flag from evaluator results.

    * Any critical failure → INCORRECT
    * All pass → GOOD
    * Any other failure → BAD
    """
    for r in results:
        if r.get("critical") and not r.get("passed"):
            return "INCORRECT"

    if all(r.get("passed") for r in results):
        return "GOOD"

    return "BAD"
