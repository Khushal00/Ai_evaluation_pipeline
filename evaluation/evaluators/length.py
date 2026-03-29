"""Output length evaluator."""

from __future__ import annotations

METRIC_NAME = "length"


def evaluate_length(output: str, max_length: int) -> dict:
    """
    Return whether ``output`` length is at or below ``max_length``.

    Result shape: metric, score (0 or 1), passed, reason.
    """
    if max_length < 0:
        return {
            "metric": METRIC_NAME,
            "score": 0.0,
            "passed": False,
            "reason": "max_length must be non-negative",
        }

    length = len(output)
    passed = length <= max_length
    score = 1.0 if passed else 0.0
    if passed:
        reason = f"length {length} is within limit {max_length}"
    else:
        reason = f"length {length} exceeds limit {max_length}"

    return {
        "metric": METRIC_NAME,
        "score": score,
        "passed": passed,
        "reason": reason,
    }
