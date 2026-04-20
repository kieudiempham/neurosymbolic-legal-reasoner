from __future__ import annotations

from typing import Any

from retrieval.rulebase_loader import RulebaseIndex
from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.reasoning import ReasoningState
from schemas.rule import RuleHead, RuleRecord
from schemas.verification import VerificationRecord
from verification.repair_loop import (
    run_answer_repair_loop,
    run_backward_repair_loop,
    run_forward_repair_loop,
    run_parse_repair_loop,
    run_retrieval_repair_loop,
)
from verification.repair_routing import repair_target_for_code


def _rec(mode: str, decision: str, code: str, target: str) -> VerificationRecord:
    return VerificationRecord(
        mode=mode,  # type: ignore[arg-type]
        symbolic_ok=False,
        symbolic_result="failed",
        final_decision=decision,  # type: ignore[arg-type]
        diagnostics=[code],
        diagnostic_errors=[code],
        repair_target_module=target,
        repair_hint=f"fix:{code}",
    )


def _rule(rid: str) -> RuleRecord:
    return RuleRecord(rule_id=rid, logic_form="obligation", head=RuleHead(predicate="obligation", args=["a", "b"]))


def _has_standard_fields(row: dict[str, Any]) -> bool:
    for key in (
        "verifier_mode",
        "verdict",
        "issue_type",
        "repair_target",
        "repair_action",
        "rerun_result",
    ):
        if key not in row:
            return False
    return True


def _has_materiality_fields(row: dict[str, Any]) -> bool:
    for key in ("repair_attempted", "material_gain", "fields_changed"):
        if key not in row:
            return False
    return True


def test_repair_target_mapping_explicit_modules() -> None:
    assert repair_target_for_code("parse_slot_error") == "parser"
    assert repair_target_for_code("retrieval_ranking_error") == "retrieval"
    assert repair_target_for_code("backward_rule_selection_error") == "selected_rule_ranking"
    assert repair_target_for_code("requirement_construction_error") == "backward_requirement_extraction"
    assert repair_target_for_code("forward_proof_error") == "forward_proof_construction"
    assert repair_target_for_code("answer_overclaim") == "answer_generation"


def test_parse_repair_logs_standard_action_contract() -> None:
    class E:
        def __init__(self) -> None:
            self.n = 0

        def verify_parse(self, *_a, **_k):
            self.n += 1
            if self.n == 1:
                return _rec("parse_verification", "REPAIR", "parse_slot_error", "parser")
            return _rec("parse_verification", "ACCEPT", "parse_slot_error", "parser")

    l1 = Layer1Parse(subject_text="a", action_text="b", modality_text="phai")
    l2 = Layer2Parse(goal={"predicate": "unknown", "args": []})
    _l1, _l2, rec, trace = run_parse_repair_loop(
        E(),  # type: ignore[arg-type]
        layer1=l1,
        layer2=l2,
        question_text="abcde",
        user_facts=[],
        max_repair_attempts_parse=1,
    )
    assert rec.final_decision == "REJECT"
    assert "repair_without_material_parse_gain" in rec.diagnostics
    assert any(_has_standard_fields(t) for t in trace if isinstance(t, dict))


def test_backward_selected_rule_repair_logs_standard_contract() -> None:
    class E:
        def __init__(self) -> None:
            self.n = 0

        def verify_backward(self, **_k):
            self.n += 1
            if self.n == 1:
                return _rec("backward_verification", "REPAIR", "backward_rule_selection_error", "selected_rule_ranking")
            return _rec("backward_verification", "ACCEPT", "backward_rule_selection_error", "selected_rule_ranking")

    r1 = _rule("R1")
    r2 = _rule("R2")
    st = ReasoningState(requirement_set=[], missing_facts=[], backward_plan={"candidates": [{"rule_id": "R1"}]}, can_continue_forward=True)

    def rb(**_k):
        return r2, ReasoningState(requirement_set=[], missing_facts=[], backward_plan={"candidates": [{"rule_id": "R2"}]}, can_continue_forward=True)

    _sel, _st, rec, trace = run_backward_repair_loop(
        E(),  # type: ignore[arg-type]
        goal={"predicate": "obligation", "args": ["a", "b"]},
        selected_rule=r1,
        bstate=st,
        ranked=[(r1, 1.0, {}), (r2, 0.9, {})],
        known_facts={},
        max_attempts=1,
        run_backward_fn=rb,
    )
    assert rec.final_decision == "ACCEPT"
    assert any(_has_standard_fields(t) for t in trace if isinstance(t, dict))


def test_forward_proof_repair_logs_standard_contract() -> None:
    class E:
        def __init__(self) -> None:
            self.n = 0

        def verify_forward(self, **_k):
            self.n += 1
            if self.n == 1:
                return _rec("forward_verification", "REPAIR", "forward_proof_error", "forward_proof_construction")
            return _rec("forward_verification", "ACCEPT", "forward_proof_error", "forward_proof_construction")

    def retry_fn():
        st = ReasoningState(forward_result={"goal_reached": True})
        return "ok", True, st, {"proof_steps": [{"description": "x"}]}

    st0 = ReasoningState(forward_result={"goal_reached": True})
    _c, _g, _s, _p, rec, trace = run_forward_repair_loop(
        E(),  # type: ignore[arg-type]
        goal={"predicate": "obligation", "args": ["a", "b"]},
        conclusion="",
        goal_achieved=True,
        known_facts={},
        forward_state=st0,
        proof_obj={"proof_steps": []},
        forward_retry_fn=retry_fn,
        max_attempts=1,
    )
    assert rec.final_decision == "ACCEPT"
    assert any(_has_standard_fields(t) for t in trace if isinstance(t, dict))


def test_answer_and_retrieval_repair_logs_standard_contract() -> None:
    class E:
        def __init__(self) -> None:
            self.n = 0

        def verify_answer(self, **_k):
            self.n += 1
            if self.n == 1:
                return _rec("answer_verification", "REPAIR", "answer_semantic_drift", "answer_generation")
            return _rec("answer_verification", "ACCEPT", "answer_semantic_drift", "answer_generation")

    _t, rec, trace = run_answer_repair_loop(
        E(),  # type: ignore[arg-type]
        answer_text="x",
        conclusion="c",
        proof={},
        modality_expected="phai",
        goal_action="a",
        action_token_in_answer="x",
        max_repair_attempts_answer=1,
        regenerate_fn=lambda *_a, **_k: "fixed",
    )
    assert rec.final_decision == "ACCEPT"
    assert any(_has_standard_fields(t) for t in trace if isinstance(t, dict))

    ranked, rtrace, _summary = run_retrieval_repair_loop(
        ranked=[],
        top_k_before=4,
        repair_reason="retrieval_ranking_error",
        retrieve_retry_fn=lambda _attempt: [(_rule("R1"), 1.0, {})],
        max_attempts=1,
    )
    assert ranked
    assert any(_has_standard_fields(t) for t in rtrace if isinstance(t, dict))


def test_rule_repair_without_material_change_is_not_promoted() -> None:
    class E:
        def __init__(self) -> None:
            self.n = 0

        def verify_rule(self, **_k):
            self.n += 1
            if self.n == 1:
                return _rec("rule_verification", "REPAIR", "rule_schema_error", "legal_frame_extractor_or_rule_builder")
            return _rec("rule_verification", "ACCEPT", "rule_schema_error", "legal_frame_extractor_or_rule_builder")

    from verification.repair_loop import run_rule_repair_loop

    r1 = _rule("R1")
    idx = RulebaseIndex([r1])
    repaired_rule, rec, trace = run_rule_repair_loop(
        E(),  # type: ignore[arg-type]
        layer2_goal={"predicate": "obligation", "args": ["a", "b"]},
        rule_candidate=r1,
        law_span="",
        legal_frame="",
        rule_index=idx,
        max_attempts=1,
    )

    assert repaired_rule.rule_id == "R1"
    assert rec.final_decision == "REJECT"
    assert "repair_without_material_rule_gain" in rec.diagnostics
    assert any(_has_materiality_fields(t) for t in trace if isinstance(t, dict) and t.get("phase") == "rule")


def test_backward_repair_without_material_change_is_not_promoted() -> None:
    class E:
        def __init__(self) -> None:
            self.n = 0

        def verify_backward(self, **_k):
            self.n += 1
            if self.n == 1:
                return _rec("backward_verification", "REPAIR", "backward_rule_selection_error", "selected_rule_ranking")
            return _rec("backward_verification", "REPAIR", "backward_rule_selection_error", "selected_rule_ranking")

    r1 = _rule("R1")
    st = ReasoningState(requirement_set=[], missing_facts=[], backward_plan={"candidates": [{"rule_id": "R1"}]}, can_continue_forward=True)

    def rb(**_k):
        # No material change: still returns same rule + same state shape.
        return r1, ReasoningState(requirement_set=[], missing_facts=[], backward_plan={"candidates": [{"rule_id": "R1"}]}, can_continue_forward=True)

    _sel, _st, rec, trace = run_backward_repair_loop(
        E(),  # type: ignore[arg-type]
        goal={"predicate": "obligation", "args": ["a", "b"]},
        selected_rule=r1,
        bstate=st,
        ranked=[(r1, 1.0, {})],
        known_facts={},
        max_attempts=1,
        run_backward_fn=rb,
    )

    assert rec.final_decision == "REJECT"
    assert "repair_without_material_backward_gain" in rec.diagnostics
    assert any(_has_materiality_fields(t) for t in trace if isinstance(t, dict) and t.get("phase") == "backward")
