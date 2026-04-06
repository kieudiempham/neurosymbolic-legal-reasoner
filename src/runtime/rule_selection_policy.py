"""Helper functions for metadata-aware rule selection (Part B: Legal Policy Core)."""

from __future__ import annotations

from typing import Any

from schemas.rule import RuleRecord


def score_rule_with_metadata(
    rule: RuleRecord,
    question_time: str | None = None,
    base_score: float = 1.0,
) -> float:
    """Score rule with legal metadata bonuses (temporal/conflict/exception/override)."""
    score = base_score
    
    # Temporal validity bonus
    if question_time:
        from runtime.temporal_policy import rule_temporally_valid
        if rule_temporally_valid(rule, question_time):
            score += 0.2  # Bonus for temporal validity
        else:
            score -= 0.5  # Penalty for temporal invalidity
    
    # Exception/override bonuses
    metadata = rule.metadata or {}
    if metadata.get("exception_rules"):
        score += 0.1  # Small bonus for having exceptions
    if metadata.get("override_rules"):
        score += 0.1  # Small bonus for having overrides
    
    # Priority from metadata
    priority = metadata.get("priority", 50)
    score += (priority - 50) * 0.01  # Small adjustment based on priority
    
    return score


def select_best_candidates_with_policy(
    candidates: list[tuple[RuleRecord, float, dict[str, Any]]],
    question_time: str | None = None,
) -> list[tuple[RuleRecord, float, dict[str, Any]]]:
    """Re-score candidates with legal policy metadata and return sorted."""
    rescored = []
    for rule, base_score, meta in candidates:
        new_score = score_rule_with_metadata(rule, question_time, base_score)
        rescored.append((rule, new_score, meta))
    
    # Sort by score descending
    rescored.sort(key=lambda x: x[1], reverse=True)
    return rescored