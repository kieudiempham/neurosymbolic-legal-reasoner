"""Backward chaining: pick rule, derive requirements, find missing facts."""

from __future__ import annotations

import logging
from typing import Any

from schemas.reasoning import ReasoningState, RequirementItem
from schemas.rule import RuleRecord
from utils.text import lower_fold

logger = logging.getLogger(__name__)


def _serialize_body(pred: str, args: list[Any]) -> str:
    inner = ",".join(str(a) for a in args)
    return f"{pred}({inner})"


def body_to_requirements(rule: RuleRecord) -> list[RequirementItem]:
    req: list[RequirementItem] = []
    for i, clause in enumerate(rule.body or []):
        if not isinstance(clause, dict):
            continue
        p = clause.get("predicate")
        a = clause.get("args") or []
        if not p:
            continue
        key = _serialize_body(str(p), list(a))
        req.append(
            RequirementItem(
                key=key,
                description=f"Requirement from body[{i}]",
                predicate=str(p),
                args=list(a),
            )
        )
    return req


def _args_match(goal_arg: Any, head_arg: Any) -> bool:
    gs, hs = str(goal_arg), str(head_arg)
    if gs in ("company_x", "doanh_nghiep_x", "subject_x"):
        return True
    if gs == hs:
        return True
    tg = set(lower_fold(gs.replace("_", " ")).split())
    th = set(lower_fold(hs.replace("_", " ")).split())
    if not tg or not th:
        return False
    return len(tg & th) / max(1, len(tg | th)) >= 0.34


def goal_unifies_with_head(goal: dict[str, Any], rule: RuleRecord) -> bool:
    if goal.get("predicate") != rule.head.predicate:
        return False
    ga = goal.get("args") or []
    ha = rule.head.args
    if len(ga) != len(ha):
        return False
    for g, h in zip(ga, ha):
        if not _args_match(g, h):
            return False
    return True


def fact_satisfies_requirement(req_key: str, known_facts: dict[str, Any]) -> bool:
    for k, v in known_facts.items():
        if v is False:
            continue
        if v is None or v is True:
            if k == req_key:
                return True
            if req_key in k or k in req_key:
                return True
    return False


def run_backward(
    *,
    goal: dict[str, Any],
    candidates: list[tuple[RuleRecord, float, dict[str, Any]]],
    known_facts: dict[str, Any],
) -> tuple[RuleRecord | None, ReasoningState]:
    trace: list[str] = []
    for rule, score, _d in candidates:
        trace.append(f"try_rule {rule.rule_id} score={score:.2f}")
        if not goal_unifies_with_head(goal, rule):
            trace.append("  skip: head_unification_failed")
            continue
        reqs = body_to_requirements(rule)
        missing: list[str] = []
        covered: list[str] = []
        for r in reqs:
            if fact_satisfies_requirement(r.key, known_facts):
                covered.append(r.key)
            else:
                missing.append(r.key)
        can_forward = len(missing) == 0
        st = ReasoningState(
            requirement_set=reqs,
            missing_facts=missing,
            selected_rule_ids=[rule.rule_id],
            derived_facts=[],
            goal_status="open",
            covered_requirements=covered,
            can_continue_forward=can_forward,
            trace=trace + [f"selected {rule.rule_id}", f"missing={len(missing)}"],
        )
        return rule, st

    return None, ReasoningState(
        requirement_set=[],
        missing_facts=[],
        selected_rule_ids=[],
        trace=trace + ["no_rule_unified"],
        can_continue_forward=False,
    )
