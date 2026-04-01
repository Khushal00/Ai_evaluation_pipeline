"""Keyword presence evaluator."""

from __future__ import annotations

from typing import Optional

METRIC_NAME = "keyword"


def evaluate_keyword(
    output: str,
    keywords: Optional[list[str]],
    *,
    match_mode: str = "any",
    case_sensitive: bool = False,
    critical: bool = True,
) -> dict:
    """
    Return whether configured keywords appear in ``output``.

    Result shape: metric, score (0 or 1), passed, reason.
    """
    clean_keywords = [keyword for keyword in (keywords or []) if keyword]
    if not clean_keywords:
        return {
            "metric": METRIC_NAME,
            "score": 0.0,
            "passed": False,
            "reason": "keyword rule enabled but no keywords configured",
            "critical": critical,
        }

    haystack = output if case_sensitive else output.lower()
    needles = clean_keywords if case_sensitive else [keyword.lower() for keyword in clean_keywords]
    matches = [keyword for keyword in needles if keyword in haystack]

    if match_mode == "all":
        passed = len(matches) == len(needles)
    else:
        passed = bool(matches)

    score = 1.0 if passed else 0.0
    if passed:
        reason = f"keyword rule passed with match_mode={match_mode!r}"
    else:
        reason = f"keyword rule failed with match_mode={match_mode!r}"

    return {
        "metric": METRIC_NAME,
        "score": score,
        "passed": passed,
        "reason": reason,
        "critical": critical,
    }
