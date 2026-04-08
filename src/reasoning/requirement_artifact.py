"""Single source of truth for normalized requirement-set artifacts."""

from __future__ import annotations

from typing import Iterable

from schemas.reasoning import RequirementItem, RequirementSetArtifact
from schemas.rule import RuleRecord


def _dedupe_keep_order(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        v = str(raw or "").strip()
        if not v or v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


def _predicate_for_requirement(req: RequirementItem) -> str:
    if req.predicate:
        return req.predicate
    key = str(req.key or "")
    if "(" in key:
        return key.split("(", 1)[0]
    return key


def build_requirement_set_artifact(
    *,
    selected_rule: RuleRecord,
    goal_predicate: str,
    requirement_items: list[RequirementItem],
    missing_keys: list[str],
) -> RequirementSetArtifact:
    """
    Normalize requirement-set for one selected rule.

    Mapping policy:
    - required: positive + constraint + exception checks (missing exception is clarifying critical)
    - optional: negative / unless checks
    """
    by_key = {r.key: r for r in requirement_items}

    required_keys: list[str] = []
    optional_keys: list[str] = []
    exception_keys: list[str] = []

    required_preds: list[str] = []
    optional_preds: list[str] = []
    exception_preds: list[str] = []

    for req in requirement_items:
        kind = (req.requirement_kind or "positive").strip().lower()
        pred = _predicate_for_requirement(req)
        key = req.key

        if kind == "negative":
            optional_keys.append(key)
            optional_preds.append(pred)
            continue

        if kind == "exception":
            exception_keys.append(key)
            exception_preds.append(pred)
            required_keys.append(key)
            required_preds.append(pred)
            continue

        required_keys.append(key)
        required_preds.append(pred)

    missing = set(_dedupe_keep_order(missing_keys))
    unmet_required = [k for k in _dedupe_keep_order(required_keys) if k in missing]
    unmet_optional = [k for k in _dedupe_keep_order(optional_keys) if k in missing]
    all_keys = _dedupe_keep_order([r.key for r in requirement_items])
    satisfied = [k for k in all_keys if k not in missing]

    return RequirementSetArtifact(
        rule_id=selected_rule.rule_id,
        goal_predicate=str(goal_predicate or selected_rule.head.predicate or "unknown"),
        required_predicates=_dedupe_keep_order(required_preds),
        optional_predicates=_dedupe_keep_order(optional_preds),
        exception_predicates=_dedupe_keep_order(exception_preds),
        unmet_required=unmet_required,
        unmet_optional=unmet_optional,
        satisfied=satisfied,
    )


def requirement_missing_fact_keys(artifact: RequirementSetArtifact) -> list[str]:
    """Stable source for missing facts used by clarification and verification."""
    return _dedupe_keep_order([*artifact.unmet_required, *artifact.unmet_optional])
