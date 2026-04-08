"""Forward-proof normalization and stability checks across domains."""

from __future__ import annotations

from typing import Any

import pytest

from reasoning.backward_reasoner import run_backward
from reasoning.forward_reasoner import run_forward
from reasoning.internal.codec import serialize_atom
from reasoning.internal.mapper import map_rule_record_to_reasoning_rule
from reasoning.proof_builder import build_partial_proof, build_proof
from schemas.rule import RuleHead, RuleRecord

DOMAINS = ("enterprise", "tax", "labor")


def _rule_for_domain(domain: str, *, with_exception: bool = False) -> RuleRecord:
    body: list[dict[str, Any]] = [{"predicate": "applies_if", "args": ["company_a", "eligible"]}]
    if with_exception:
        body.append({"predicate": "exception_applies", "args": ["company_a", "special_exception"]})
    return RuleRecord(
        rule_id=f"RULE_{domain.upper()}_FWD_01",
        logic_form="obligation",
        head=RuleHead(predicate=f"{domain}_obligation", args=["company_a", "submit_file"]),
        body=body,
        metadata={"provenance": {"domain": domain}},
    )


def _goal(rule: RuleRecord) -> dict[str, Any]:
    return {"predicate": rule.head.predicate, "args": ["company_a", "submit_file"]}


def _known_facts(rule: RuleRecord, *, satisfy_positive: bool, trigger_exception: bool) -> dict[str, Any]:
    rr = map_rule_record_to_reasoning_rule(rule)
    facts: dict[str, Any] = {}
    if rr.positive_conditions:
        facts[serialize_atom(rr.positive_conditions[0])] = satisfy_positive
    if rr.exception_conditions:
        facts[serialize_atom(rr.exception_conditions[0])] = trigger_exception
    return facts


@pytest.mark.parametrize("domain", DOMAINS)
def test_forward_proof_success_normalized_fields(domain: str) -> None:
    rule = _rule_for_domain(domain)
    ranked = [(rule, 1.0, {})]
    known = _known_facts(rule, satisfy_positive=True, trigger_exception=False)

    selected, bstate = run_backward(goal=_goal(rule), candidates=ranked, known_facts=known)
    assert selected is not None
    assert bstate.requirement_artifact is not None

    conclusion, ok, fstate, _ = run_forward(
        rule=rule,
        known_facts=known,
        goal=_goal(rule),
        requirement_artifact=bstate.requirement_artifact.model_dump(mode="json"),
    )

    assert ok
    assert conclusion
    assert fstate.requirement_artifact is not None
    assert fstate.requirement_artifact.rule_id == rule.rule_id

    proof = build_proof(
        rule=rule,
        used_facts=list(known.keys()),
        conclusion=conclusion,
        forward_result=fstate.forward_result,
        requirement_artifact=fstate.requirement_artifact.model_dump(mode="json"),
    )

    assert proof.selected_rule == rule.rule_id
    assert proof.conclusion == conclusion
    assert proof.derived_conclusion == conclusion
    assert proof.missing_premises == []
    assert set(proof.satisfied_premises) == set(fstate.requirement_artifact.satisfied)
    assert proof.exception_status == "none"


@pytest.mark.parametrize("domain", DOMAINS)
def test_forward_partial_proof_missing_fact_is_structured(domain: str) -> None:
    rule = _rule_for_domain(domain)

    conclusion, ok, fstate, _ = run_forward(rule=rule, known_facts={}, goal=_goal(rule))

    assert not ok
    assert conclusion == ""
    assert fstate.failure_reason == "positive_condition_missing"
    assert fstate.requirement_artifact is not None
    assert fstate.requirement_artifact.unmet_required

    partial = build_partial_proof(
        rule=rule,
        used_facts=[],
        conclusion=f"Kết luận tạm thời theo quy tắc {rule.rule_id}: cần làm rõ thêm điều kiện.",
        forward_result=fstate.forward_result,
        requirement_artifact=fstate.requirement_artifact.model_dump(mode="json"),
    )

    assert partial.selected_rule == rule.rule_id
    assert partial.fail_stage == "premise_match"
    assert partial.missing_premises
    assert partial.exception_status == "none"
    assert partial.proof_steps
    assert partial.proof_steps[0].step_type == "forward_failure"


@pytest.mark.parametrize("domain", DOMAINS)
def test_forward_partial_proof_exception_blocked(domain: str) -> None:
    rule = _rule_for_domain(domain, with_exception=True)
    known = _known_facts(rule, satisfy_positive=True, trigger_exception=True)

    conclusion, ok, fstate, _ = run_forward(rule=rule, known_facts=known, goal=_goal(rule))

    assert not ok
    assert conclusion == ""
    assert fstate.failure_reason == "exception_triggered"

    partial = build_partial_proof(
        rule=rule,
        used_facts=list(known.keys()),
        conclusion=f"Kết luận tạm thời theo quy tắc {rule.rule_id}: xuất hiện ngoại lệ cần xác minh.",
        forward_result=fstate.forward_result,
        requirement_artifact=(fstate.requirement_artifact.model_dump(mode="json") if fstate.requirement_artifact else None),
    )

    assert partial.selected_rule == rule.rule_id
    assert partial.exception_status == "triggered"
    assert partial.fail_stage == "exception_check"
    assert partial.proof_steps and partial.proof_steps[0].failure_reason == "exception_triggered"
