"""Requirement-set artifact stability tests across domains."""

from __future__ import annotations

from typing import Any

import pytest

from reasoning.backward_reasoner import run_backward
from reasoning.forward_reasoner import run_forward
from reasoning.internal.codec import serialize_atom
from reasoning.internal.mapper import map_rule_record_to_reasoning_rule
from schemas.rule import RuleHead, RuleRecord
from verification.symbolic_modes import symbolic_backward, symbolic_forward


DOMAINS = ("enterprise", "tax", "labor")


def _rule_for_domain(domain: str, *, with_unless: bool = False, with_exception: bool = False) -> RuleRecord:
    body: list[dict[str, Any]] = [{"predicate": "applies_if", "args": ["company_a", "eligible"]}]
    if with_unless:
        body.append({"predicate": "unless", "args": ["company_a", "blocked"]})
    if with_exception:
        body.append({"predicate": "exception_applies", "args": ["company_a", "special_exception"]})
    return RuleRecord(
        rule_id=f"RULE_{domain.upper()}_REQ_01",
        logic_form="obligation",
        head=RuleHead(predicate=f"{domain}_obligation", args=["company_a", "submit_file"]),
        body=body,
        metadata={"provenance": {"domain": domain}},
    )


def _goal(rule: RuleRecord) -> dict[str, Any]:
    return {"predicate": rule.head.predicate, "args": ["company_a", "submit_file"]}


def _known_facts(rule: RuleRecord, *, satisfy_positive: bool, satisfy_unless: bool, trigger_exception: bool) -> dict[str, Any]:
    rr = map_rule_record_to_reasoning_rule(rule)
    facts: dict[str, Any] = {}
    if rr.positive_conditions:
        facts[serialize_atom(rr.positive_conditions[0])] = satisfy_positive
    if rr.negative_conditions:
        facts[serialize_atom(rr.negative_conditions[0])] = satisfy_unless
    if rr.exception_conditions:
        facts[serialize_atom(rr.exception_conditions[0])] = trigger_exception
    return facts


@pytest.mark.parametrize("domain", DOMAINS)
def test_requirement_artifact_full_fact_cross_domain(domain: str) -> None:
    rule = _rule_for_domain(domain, with_unless=True)
    ranked = [(rule, 1.0, {})]
    known = _known_facts(rule, satisfy_positive=True, satisfy_unless=False, trigger_exception=False)

    selected, st = run_backward(goal=_goal(rule), candidates=ranked, known_facts=known)

    assert selected is not None
    assert selected.rule_id == rule.rule_id
    assert st.requirement_artifact is not None
    art = st.requirement_artifact
    assert art.rule_id == rule.rule_id
    assert art.goal_predicate == rule.head.predicate
    assert art.unmet_required == []
    assert art.unmet_optional == []
    assert st.missing_facts == []
    assert set(st.covered_requirements) == set(art.satisfied)


@pytest.mark.parametrize("domain", DOMAINS)
def test_requirement_artifact_missing_fact_cross_domain(domain: str) -> None:
    rule = _rule_for_domain(domain, with_unless=True)
    ranked = [(rule, 1.0, {})]
    known: dict[str, Any] = {}

    selected, st = run_backward(goal=_goal(rule), candidates=ranked, known_facts=known)

    assert selected is not None
    assert st.requirement_artifact is not None
    art = st.requirement_artifact
    assert art.rule_id == rule.rule_id
    assert art.unmet_required
    assert art.unmet_optional
    assert set(st.missing_facts) == set(art.unmet_required + art.unmet_optional)
    assert set(st.covered_requirements) == set(art.satisfied)


@pytest.mark.parametrize("domain", DOMAINS)
def test_requirement_artifact_exception_case_cross_domain(domain: str) -> None:
    rule = _rule_for_domain(domain, with_exception=True)
    ranked = [(rule, 1.0, {})]
    known = _known_facts(rule, satisfy_positive=True, satisfy_unless=False, trigger_exception=True)

    selected, st = run_backward(goal=_goal(rule), candidates=ranked, known_facts=known)

    assert selected is not None
    assert st.requirement_artifact is not None
    art = st.requirement_artifact
    assert art.exception_predicates
    assert art.unmet_required == []

    conclusion, ok, fstate, _ = run_forward(rule=rule, known_facts=known, goal=_goal(rule))
    assert not ok
    assert conclusion == ""
    assert fstate.failure_reason == "exception_triggered"


def test_symbolic_backward_detects_selected_rule_requirement_mismatch() -> None:
    sym = symbolic_backward(
        {"predicate": "obligation", "args": ["x", "y"]},
        "RULE_A",
        {"candidates": [{"rule_id": "RULE_A"}]},
        requirements_ok=False,
        missing_facts=["k1"],
        requirement_keys=["k1"],
        requirement_artifact={
            "rule_id": "RULE_B",
            "unmet_required": ["k1"],
            "unmet_optional": [],
        },
    )
    assert not sym.ok
    assert "requirement_construction_error" in sym.error_codes


def test_symbolic_forward_checks_requirement_vs_proof_skeleton() -> None:
    requirement_artifact = {
        "rule_id": "RULE_X",
        "required_predicates": ["applies_if"],
        "unmet_required": [],
        "unmet_optional": [],
    }
    bad = symbolic_forward(
        goal_achieved=True,
        forward_result={"goal_reached": True},
        proof={"proof_steps": [{"rule_id": "RULE_X", "supporting_atoms": []}]},
        conclusion="ok",
        goal={"predicate": "obligation", "args": ["a", "b"]},
        requirement_artifact=requirement_artifact,
        selected_rule_id="RULE_X",
    )
    assert not bad.ok
    assert "forward_proof_error" in bad.error_codes

    good = symbolic_forward(
        goal_achieved=True,
        forward_result={"goal_reached": True},
        proof={
            "proof_steps": [
                {
                    "rule_id": "RULE_X",
                    "supporting_atoms": [{"predicate": "applies_if", "args": ["a", "eligible"]}],
                    "description": "applied",
                }
            ]
        },
        conclusion="ok",
        goal={"predicate": "obligation", "args": ["a", "b"]},
        requirement_artifact=requirement_artifact,
        selected_rule_id="RULE_X",
    )
    assert good.ok
