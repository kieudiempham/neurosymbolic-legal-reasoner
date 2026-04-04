"""Semantic reasoning: atoms, unification, backward plan, forward paths, constraints, proof hooks."""

from __future__ import annotations

from typing import Any

from reasoning.internal.codec import atoms_equal, canonicalize_atom, deserialize_atom, serialize_atom
from reasoning.internal.mapper import map_rule_record_to_reasoning_rule
from reasoning.internal.models import Atom, ReasoningRule, ThresholdConstraint
from reasoning.semantics.backward_plan import build_backward_plan
from reasoning.semantics.constraint_eval import evaluate_threshold_constraint
from reasoning.semantics.failed_path_hints import build_user_message_hint
from reasoning.semantics.forward_engine import run_forward_best_path, run_forward_path
from reasoning.semantics.numeric_lookup import resolve_numeric_value_for_threshold
from reasoning.semantics.proof_validate import validate_proof_chain, validate_proof_step
from reasoning.semantics.unification import (
    apply_substitution_to_reasoning_rule,
    is_variable,
    unify_goal_dict_with_goal_atom,
)
from schemas.rule import RuleHead, RuleRecord


def _rule(
    rid: str,
    head_pred: str,
    head_args: list[Any],
    body: list[dict[str, Any]],
    logic_form: str = "obligation",
) -> RuleRecord:
    return RuleRecord(rule_id=rid, logic_form=logic_form, head=RuleHead(predicate=head_pred, args=head_args), body=body)


# --- Test 1: atom boundary ---
def test_atom_boundary_roundtrip_and_compare() -> None:
    a = Atom(predicate="applies_if", args=("a", "b"))
    c = canonicalize_atom(a)
    s = serialize_atom(c)
    d = deserialize_atom(s)
    assert atoms_equal(c, d)
    assert atoms_equal(a, d)


# --- Test 2: unification ---
def test_unification_binds_variable_and_applies_to_rule() -> None:
    rr = ReasoningRule(
        rule_id="U1",
        logic_form="obligation",
        goal_atom=("must", "company_x", "file_report"),
        positive_conditions=(
            Atom(predicate="applies_if", args=("company_x", "listed")),
        ),
        negative_conditions=(),
        exception_conditions=(),
        constraints=(),
    )
    goal = {"predicate": "must", "args": ["cong_ty_a", "file_report"]}
    subst, fail = unify_goal_dict_with_goal_atom(goal, rr.goal_atom)
    assert subst is not None and fail is None
    assert subst.mapping.get("company_x") == "cong_ty_a"
    rr2 = apply_substitution_to_reasoning_rule(rr, subst)
    assert rr2.positive_conditions[0].args[0] == "cong_ty_a"


# --- Test 3: backward structured plan ---
def test_backward_plan_has_candidates_scores_and_missing() -> None:
    r1 = _rule(
        "R1",
        "must",
        ["company_x", "do_y"],
        [{"predicate": "applies_if", "args": ["company_x", "cond1"]}],
    )
    goal = {"predicate": "must", "args": ["c1", "do_y"]}
    ranked = [(r1, 10.0, {})]
    plan = build_backward_plan(goal=goal, candidates=ranked, known_facts={}, max_paths=3)
    assert plan.candidates
    c0 = plan.candidates[0]
    assert c0.rule_id == "R1"
    assert c0.total_score > 0
    assert c0.missing_atoms


# --- Test 4: forward success ---
def test_forward_success_derives_goal_and_proof() -> None:
    r = _rule(
        "FS",
        "must",
        ["c1", "act"],
        [{"predicate": "applies_if", "args": ["c1", "ok"]}],
    )
    rr = map_rule_record_to_reasoning_rule(r)
    k = serialize_atom(rr.positive_conditions[0])
    known = {k: True}
    goal = {"predicate": "must", "args": ["c1", "act"]}
    res = run_forward_path(rule=r, goal=goal, known_facts=known, substitution={})
    assert res.goal_reached
    assert res.proof_steps
    assert res.conclusion.startswith("must(")


# --- Test 5: exception triggered ---
def test_forward_exception_triggered() -> None:
    r = _rule(
        "EX",
        "must",
        ["c1", "act"],
        [
            {"predicate": "applies_if", "args": ["c1", "ok"]},
            {"predicate": "exception_applies", "args": ["c1", "exc"]},
        ],
    )
    rr = map_rule_record_to_reasoning_rule(r)
    k1 = serialize_atom(rr.positive_conditions[0])
    k2 = serialize_atom(rr.exception_conditions[0])
    known = {k1: True, k2: True}
    goal = {"predicate": "must", "args": ["c1", "act"]}
    res = run_forward_path(rule=r, goal=goal, known_facts=known, substitution={})
    assert not res.goal_reached
    assert res.failure_reason == "exception_triggered"


# --- Test 6: constraint missing input ---
def test_forward_constraint_missing_input_and_eval() -> None:
    tc = ThresholdConstraint(metric="ty_le_so_huu", operator=">=", value=50.0, unit="%", raw_args=("ty_le_so_huu", ">=", 50, "%"))
    ev = evaluate_threshold_constraint(tc, {})
    assert ev.status == "missing_input"
    r = RuleRecord(
        rule_id="TH",
        logic_form="threshold",
        head=RuleHead(predicate="must", args=["a", "b"]),
        body=[],
    )
    rr = map_rule_record_to_reasoning_rule(r)
    assert any(isinstance(x, ThresholdConstraint) for x in rr.constraints)
    res = run_forward_path(
        rule=r, goal={"predicate": "must", "args": ["a", "b"]}, known_facts={}, substitution={}
    )
    assert res.failure_reason == "constraint_missing_input"


# --- Test 7: multiple paths second succeeds ---
def test_multi_path_first_fails_second_succeeds() -> None:
    bad = _rule(
        "BAD",
        "must",
        ["c", "x"],
        [{"predicate": "applies_if", "args": ["c", "only_bad"]}],
    )
    good = _rule(
        "GOOD",
        "must",
        ["c", "x"],
        [{"predicate": "applies_if", "args": ["c", "only_good"]}],
    )
    goal = {"predicate": "must", "args": ["c", "x"]}
    ranked = [(bad, 100.0, {}), (good, 90.0, {})]
    plan = build_backward_plan(goal=goal, candidates=ranked, known_facts={}, max_paths=3)
    rr_good = map_rule_record_to_reasoning_rule(good)
    kg = serialize_atom(rr_good.positive_conditions[0])
    known = {kg: True}
    res = run_forward_best_path(plan=plan, candidates=ranked, goal=goal, known_facts=known)
    assert res.goal_reached
    assert res.rule_id == "GOOD"
    assert "BAD" in res.failed_paths


# --- Test 8: proof validation hooks ---
def test_proof_validate_and_failure_trace() -> None:
    from reasoning.semantics.plan_models import ProofStepRecord

    ok, issues = validate_proof_step(
        ProofStepRecord(derived_atom=["must", "a"], rule_id="R", status="ok")
    )
    assert ok
    bad, iss2 = validate_proof_step(ProofStepRecord(status="ok"))
    assert not bad
    chain_ok, _ = validate_proof_chain(
        [ProofStepRecord(derived_atom=["p"], rule_id="R", status="ok")]
    )
    assert chain_ok


# --- Test 9: goal achievement trace ---
def test_goal_achievement_trace_in_forward_result() -> None:
    r = _rule("G1", "must", ["c", "a"], [{"predicate": "applies_if", "args": ["c", "t"]}])
    rr = map_rule_record_to_reasoning_rule(r)
    k = serialize_atom(rr.positive_conditions[0])
    res = run_forward_path(
        rule=r,
        goal={"predicate": "must", "args": ["c", "a"]},
        known_facts={k: True},
        substitution={},
    )
    assert res.goal_reached
    assert res.rule_id == "G1"
    assert not res.failed_paths


def test_is_variable() -> None:
    assert is_variable("company_x")
    assert not is_variable("concrete_slug")


# --- unless → negative_condition_blocked ---
def test_unless_positive_true_and_unless_true_blocks_path() -> None:
    r = _rule(
        "UNL",
        "must",
        ["c", "act"],
        [
            {"predicate": "applies_if", "args": ["c", "A_hold"]},
            {"predicate": "unless", "args": ["c", "B_exc"]},
        ],
    )
    rr = map_rule_record_to_reasoning_rule(r)
    k_pos = serialize_atom(rr.positive_conditions[0])
    k_unless = serialize_atom(rr.negative_conditions[0])
    known = {k_pos: True, k_unless: True}
    res = run_forward_path(
        rule=r, goal={"predicate": "must", "args": ["c", "act"]}, known_facts=known, substitution={}
    )
    assert not res.goal_reached
    assert res.failure_reason == "negative_condition_blocked"
    assert res.blocking_negative_atoms
    assert res.blocking_negative_atoms[0].get("serialized") == k_unless
    assert res.goal_atom[0] == "must"


# --- Numeric lookup + threshold ---
def test_resolve_numeric_explicit_and_metric_prefix() -> None:
    c = ThresholdConstraint(metric="ty_le_so_huu", operator=">=", value=10.0, unit="phan_tram", raw_args=())
    r1 = resolve_numeric_value_for_threshold(c, {"numeric:ty_le_so_huu": 25.5})
    assert r1.found and r1.value == 25.5 and r1.source == "explicit_numeric_key"
    r2 = resolve_numeric_value_for_threshold(c, {"metric:ty_le_so_huu": 30.0})
    assert r2.found and r2.value == 30.0 and r2.source == "metric_session_key"


def test_threshold_evaluate_pass_fail_missing_unknown_unit() -> None:
    c = ThresholdConstraint(metric="m_thr", operator=">=", value=50.0, unit="phan_tram", raw_args=())
    assert evaluate_threshold_constraint(c, {"numeric:m_thr": 60.0}).status == "satisfied"
    assert evaluate_threshold_constraint(c, {"numeric:m_thr": 40.0}).status == "failed"
    assert evaluate_threshold_constraint(c, {}).status == "missing_input"
    ev_um = evaluate_threshold_constraint(c, {"numeric:m_thr": 0.4})
    assert ev_um.status == "unknown"
    assert ev_um.numeric_lookup


# --- Failed path records + user-facing hint ---
def test_multi_path_failed_path_records_contain_rich_fields() -> None:
    bad = _rule("BAD", "must", ["c", "x"], [{"predicate": "applies_if", "args": ["c", "bad_k"]}])
    good = _rule("GOOD", "must", ["c", "x"], [{"predicate": "applies_if", "args": ["c", "good_k"]}])
    goal = {"predicate": "must", "args": ["c", "x"]}
    ranked = [(bad, 100.0, {}), (good, 90.0, {})]
    plan = build_backward_plan(goal=goal, candidates=ranked, known_facts={}, max_paths=3)
    rr_good = map_rule_record_to_reasoning_rule(good)
    kg = serialize_atom(rr_good.positive_conditions[0])
    res = run_forward_best_path(plan=plan, candidates=ranked, goal=goal, known_facts={kg: True})
    assert res.goal_reached
    assert len(res.failed_path_records) == 1
    bad_rec = res.failed_path_records[0]
    assert bad_rec.rule_id == "BAD"
    assert bad_rec.user_message_hint
    assert bad_rec.goal_atom


def test_user_message_hint_formats_negative_blocked_and_constraint_missing() -> None:
    from reasoning.semantics.plan_models import ForwardPathResult

    r_neg = ForwardPathResult(
        rule_id="R1",
        goal_reached=False,
        failure_reason="negative_condition_blocked",
        failure_detail="unless(a,b)",
        blocking_negative_atoms=[{"serialized": "unless(a,b)"}],
        goal_atom=["must", "x", "y"],
    )
    h1 = build_user_message_hint(r_neg, None)
    assert "loại trừ" in h1 or "unless" in h1.lower()

    r_mi = ForwardPathResult(
        rule_id="R2",
        goal_reached=False,
        failure_reason="constraint_missing_input",
        failure_detail="constraint:threshold:...",
        goal_atom=["must", "a", "b"],
    )
    h2 = build_user_message_hint(r_mi, None)
    assert "ngưỡng" in h2.lower() or "định lượng" in h2.lower() or "thiếu" in h2.lower()


def test_clarification_manager_sort_keys_with_forward_result() -> None:
    from reasoning.clarification_manager import build_clarification_prompts_from_requirements
    from schemas.reasoning import RequirementItem

    fwd = {
        "failed_path_records": [
            {
                "rule_id": "R",
                "goal_atom": ["must", "a"],
                "failure_reason": "constraint_missing_input",
                "failure_detail": "constraint:threshold:x",
                "missing_atoms": [],
                "missing_constraint_inputs": ["constraint:threshold:ty_le::"],
                "blocking_negative_atoms": [],
                "triggered_exception_atoms": [],
                "failed_constraints": [],
                "supporting_atoms": [],
                "source_ref": None,
                "user_message_hint": "need number",
                "clarification_priority": 8,
            }
        ]
    }
    keys = ["applies_if(a)", "constraint:threshold:ty_le::"]
    reqs = [RequirementItem(key=k, description="", predicate=None, args=[]) for k in keys]
    prompts = build_clarification_prompts_from_requirements(
        keys, reqs, backward_plan=None, forward_result=fwd
    )
    assert prompts[0]["fact_key"].startswith("constraint:")
    assert prompts[0].get("reason_hint") == "need number"
