"""Keyword presence evaluator."""

from __future__ import annotations

METRIC_NAME = "keyword"


def evaluate_keyword(output: str, keyword: str | None) -> dict:
    """
    Return whether ``keyword`` appears in ``output`` (substring, case-sensitive).

    Result shape: metric, score (0 or 1), passed, reason.
    """
    if keyword is None or keyword == "":
        return {
            "metric": METRIC_NAME,
            "score": 0.0,
            "passed": False,
            "reason": "no keyword configured",
        }

    passed = keyword in output
    score = 1.0 if passed else 0.0
    if passed:
        reason = f"keyword {keyword!r} found in output"
    else:
        reason = f"keyword {keyword!r} not found in output"

    return {
        "metric": METRIC_NAME,
        "score": score,
        "passed": passed,
        "reason": reason,
    }
