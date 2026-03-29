"""Evaluation engine: run evaluators and aggregate outcome."""

from __future__ import annotations

from evaluation.evaluators.keyword import evaluate_keyword
from evaluation.evaluators.length import evaluate_length
from evaluation.scorer import aggregate_scores, assign_flag


def evaluate(task: dict) -> dict:
    """
    Run keyword and length evaluators on ``task``.

    Expected keys:
        * ``input`` — optional prompt/context (not used by current evaluators)
        * ``output`` — model/system output text to score
        * ``keyword`` — substring that must appear in ``output``
        * ``max_length`` — maximum allowed length of ``output`` (characters)
    """
    output = task["output"]
    keyword = task.get("keyword")
    max_length = task.get("max_length", 10_000)

    results = [
        evaluate_keyword(output, keyword),
        evaluate_length(output, int(max_length)),
    ]

    final_score = aggregate_scores(results)
    flag = assign_flag(results)

    return {
        "results": results,
        "final_score": final_score,
        "flag": flag,
    }
