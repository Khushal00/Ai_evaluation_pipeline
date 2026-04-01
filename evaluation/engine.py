"""Evaluation engine: run evaluators and aggregate outcome."""

from __future__ import annotations

from evaluation.evaluators.keyword import evaluate_keyword
from evaluation.evaluators.length import evaluate_length
from evaluation.scorer import aggregate_scores, assign_flag


def evaluate(task: dict) -> dict:
    """
    Run configured evaluators on ``task``.

    Expected keys:
        * ``input`` — optional prompt/context (not used by current evaluators)
        * ``output`` — model/system output text to score
        * ``rules`` — client-provided evaluator configuration
    """
    output = task["output"]
    rules = task.get("rules") or {}
    keyword_rule = rules.get("keyword") or {}
    length_rule = rules.get("length") or {}

    results = []
    if keyword_rule.get("enabled"):
        results.append(
            evaluate_keyword(
                output,
                keyword_rule.get("keywords"),
                match_mode=keyword_rule.get("match_mode", "any"),
                case_sensitive=bool(keyword_rule.get("case_sensitive", False)),
                critical=bool(keyword_rule.get("critical", True)),
            ),
        )
    if length_rule.get("enabled"):
        max_length = length_rule.get("max_length", 10_000)
        results.append(
            evaluate_length(
                output,
                int(max_length),
                critical=bool(length_rule.get("critical", False)),
            ),
        )

    final_score = aggregate_scores(results)
    flag = assign_flag(results)

    return {
        "results": results,
        "final_score": final_score,
        "flag": flag,
    }
