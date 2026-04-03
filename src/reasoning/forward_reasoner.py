"""Forward chaining — apply selected rule when requirements are satisfied."""

from __future__ import annotations

from typing import Any

from schemas.reasoning import ReasoningState
from schemas.rule import RuleRecord
from reasoning.backward_reasoner import (
    body_to_requirements,
    fact_satisfies_requirement,
    goal_unifies_with_head,
)


def _head_string(rule: RuleRecord) -> str:
    args = ",".join(str(a) for a in rule.head.args)
    return f"{rule.head.predicate}({args})"


def run_forward(
    *,
    rule: RuleRecord,
    known_facts: dict[str, Any],
    goal: dict[str, Any],
) -> tuple[str, bool, ReasoningState, list[str]]:
    reqs = body_to_requirements(rule)
    missing: list[str] = []
    covered: list[str] = []
    for r in reqs:
        if fact_satisfies_requirement(r.key, known_facts):
            covered.append(r.key)
        else:
            missing.append(r.key)

    trace: list[str] = []
    if missing:
        st = ReasoningState(
            requirement_set=reqs,
            missing_facts=missing,
            selected_rule_ids=[rule.rule_id],
            goal_status="open",
            covered_requirements=covered,
            can_continue_forward=False,
            trace=trace + ["forward_blocked_missing"],
        )
        return "", False, st, trace

    conclusion = _head_string(rule)
    derived = [f"derived:{conclusion}"]
    goal_ok = goal_unifies_with_head(goal, rule)
    st = ReasoningState(
        requirement_set=reqs,
        missing_facts=[],
        selected_rule_ids=[rule.rule_id],
        derived_facts=derived,
        goal_status="satisfied" if goal_ok else "failed",
        covered_requirements=covered,
        can_continue_forward=True,
        trace=trace + ["forward_ok", f"conclusion={conclusion}"],
    )
    return conclusion, goal_ok, st, trace
