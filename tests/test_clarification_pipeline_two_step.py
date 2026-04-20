from __future__ import annotations

from typing import Any

from reasoning.clarification_manager import filter_clarification_targets
from retrieval.rulebase_loader import RulebaseIndex
from runtime.qa_orchestrator import run_clarify
from runtime.verification_gates import ForwardGateOutcome, RuleBackwardGateOutcome
from schemas.proof import ProofObject
from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.reasoning import ReasoningState, RequirementItem
from schemas.rule import RuleHead, RuleRecord
from schemas.verification import VerificationRecord
from session.session_service import SessionService


def _ok_ver(mode: str = "parse_verification") -> VerificationRecord:
    return VerificationRecord(mode=mode, symbolic_ok=True, symbolic_result="ok", final_decision="ACCEPT")


def _rule() -> RuleRecord:
    return RuleRecord(
        rule_id="RULE_CLARIFY_01",
        logic_form="permission",
        head=RuleHead(predicate="permission", args=["a", "b", "c"]),
        body=[{"predicate": "applies_if", "args": ["a", "eligible"]}],
        metadata={"provenance": {"domain": "enterprise"}},
    )


def _reasoning_state(missing: list[str]) -> ReasoningState:
    req = RequirementItem(key="applies_if(a, eligible)", description="", requirement_kind="positive")
    req2 = RequirementItem(key="deadline(a, 2024)", description="", requirement_kind="constraint")
    return ReasoningState(
        requirement_set=[req, req2],
        missing_facts=list(missing),
        covered_requirements=[],
        backward_plan={"candidates": [{"rule_id": "RULE_CLARIFY_01"}]},
    )


def _reasoning_state_threshold(missing: list[str]) -> ReasoningState:
    req = RequirementItem(key="constraint:threshold::::", description="", requirement_kind="constraint")
    return ReasoningState(
        requirement_set=[req],
        missing_facts=list(missing),
        covered_requirements=[],
        backward_plan={"candidates": [{"rule_id": "RULE_CLARIFY_01"}]},
    )


class _Selector:
    def select(self, *_args, **_kwargs):
        return {
            "primary_domains": ["enterprise"],
            "secondary_domains": [],
            "include_shared": True,
            "allow_cross_domain_expansion": False,
            "routing_confidence": 1.0,
            "routing_reasons": ["test"],
            "triggered_bridges": [],
        }


class _Evidence:
    def retrieve(self, **_kwargs):
        return []


def _patch_common(monkeypatch, *, rule: RuleRecord) -> None:
    import runtime.qa_orchestrator as q

    monkeypatch.setattr(q, "parse_question_layer1", lambda _q: Layer1Parse(question_focus="permission"))
    monkeypatch.setattr(
        q,
        "build_layer2",
        lambda *_a, **_k: Layer2Parse(
            goal={"predicate": "permission", "args": ["a", "b", "c"]},
            condition_atoms=["applies_if(a, eligible)"],
            facts=["known(x)"],
        ),
    )
    monkeypatch.setattr(
        q,
        "run_parse_repair_loop",
        lambda *_a, **_k: (_k.get("layer1"), _k.get("layer2"), _ok_ver("parse_verification"), []),
    )
    monkeypatch.setattr(q, "retrieve_rules", lambda **_k: [(rule, 1.0, {"domain": "enterprise", "rulebase_id": "enterprise_core"})])
    monkeypatch.setattr(q, "enrich_ranked_with_retrieval_meta", lambda rows: rows)
    monkeypatch.setattr(q, "collect_rulebase_ids_from_index", lambda _rules: ["enterprise_core"])
    monkeypatch.setattr(
        q,
        "run_answer_repair_loop",
        lambda *_a, **_k: (
            _k.get("answer_text", ""),
            _ok_ver("answer_verification"),
            [{"attempts_used": 0, "phase": "answer"}],
        ),
    )


def test_no_clarification_needed_path(monkeypatch) -> None:
    import runtime.qa_orchestrator as q

    rule = _rule()
    _patch_common(monkeypatch, rule=rule)

    monkeypatch.setattr(
        q,
        "gate_rule_and_backward",
        lambda *_a, **_k: RuleBackwardGateOutcome(ok=True, clarification_needed=False, selected=rule, bstate=_reasoning_state([]), v_back=_ok_ver("backward_verification")),
    )
    monkeypatch.setattr(
        q,
        "gate_forward_reasoning",
        lambda *_a, **_k: ForwardGateOutcome(
            ok=True,
            conclusion="duoc",
            goal_achieved=True,
            fstate=ReasoningState(missing_facts=[]),
            proof_obj=ProofObject(proof_id="p1", conclusion="duoc", derived_conclusion="duoc", proof_steps=[]),
            v_fwd=_ok_ver("forward_verification"),
        ),
    )

    svc = SessionService()
    st = svc.create_session("q", [])
    st.layer1 = Layer1Parse(question_focus="permission")
    st.layer2 = Layer2Parse(goal={"predicate": "permission", "args": ["a", "b", "c"]})
    svc.save(st)

    resp = run_clarify(
        session_id=st.session_id,
        answers=[],
        session_svc=svc,
        domain_selector=_Selector(),
        evidence_retriever=_Evidence(),
        rule_index=RulebaseIndex([rule]),
    )
    assert not resp.needs_clarification
    gain = (resp.debug_trace or {}).get("clarification_gain") or {}
    assert gain.get("post_clarification_status") == "resolved_after_clarification"


def test_clarification_resolves_case(monkeypatch) -> None:
    import runtime.qa_orchestrator as q

    rule = _rule()
    _patch_common(monkeypatch, rule=rule)

    monkeypatch.setattr(
        q,
        "gate_rule_and_backward",
        lambda *_a, **_k: RuleBackwardGateOutcome(
            ok=True,
            clarification_needed=False,
            selected=rule,
            bstate=_reasoning_state([]),
            v_back=_ok_ver("backward_verification"),
        ),
    )
    monkeypatch.setattr(
        q,
        "gate_forward_reasoning",
        lambda *_a, **_k: ForwardGateOutcome(
            ok=True,
            conclusion="duoc",
            goal_achieved=True,
            fstate=ReasoningState(missing_facts=[]),
            proof_obj=ProofObject(proof_id="p2", conclusion="duoc", derived_conclusion="duoc", proof_steps=[]),
            v_fwd=_ok_ver("forward_verification"),
        ),
    )

    svc = SessionService()
    st = svc.create_session("q", [])
    st.reasoning = _reasoning_state(["applies_if(a, eligible)"])
    st.missing_facts = ["applies_if(a, eligible)"]
    st.clarification_questions = [
        {
            "fact_key": "applies_if(a, eligible)",
            "question_text": "?",
            "target_kind": "missing_fact",
            "expected_type": "yes_no",
            "reason": "need_input",
        }
    ]
    svc.save(st)

    resp = run_clarify(
        session_id=st.session_id,
        answers=[{"fact_key": "applies_if(a, eligible)", "value": "có"}],
        session_svc=svc,
        domain_selector=_Selector(),
        evidence_retriever=_Evidence(),
        rule_index=RulebaseIndex([rule]),
    )
    assert not resp.needs_clarification
    saved = svc.get(st.session_id)
    assert saved is not None
    assert saved.known_facts.get("applies_if(a, eligible)") is True
    gain = (resp.debug_trace or {}).get("clarification_gain") or {}
    assert "applies_if(a, eligible)" in set(gain.get("newly_satisfied_requirements") or [])


def test_clarification_still_insufficient_and_filters_known_or_parse(monkeypatch) -> None:
    import runtime.qa_orchestrator as q

    rule = _rule()
    _patch_common(monkeypatch, rule=rule)

    monkeypatch.setattr(
        q,
        "gate_rule_and_backward",
        lambda *_a, **_k: RuleBackwardGateOutcome(
            ok=True,
            clarification_needed=True,
            selected=rule,
            bstate=_reasoning_state(["applies_if(a, eligible)", "deadline(a, 2024)"]),
            v_back=_ok_ver("backward_verification"),
        ),
    )

    svc = SessionService()
    st = svc.create_session("q", [])
    st.reasoning = _reasoning_state(["applies_if(a, eligible)", "deadline(a, 2024)"])
    st.missing_facts = ["applies_if(a, eligible)", "deadline(a, 2024)"]
    st.known_facts["applies_if(a, eligible)"] = True
    st.clarification_questions = [
        {
            "fact_key": "applies_if(a, eligible)",
            "question_text": "?",
            "target_kind": "missing_fact",
            "expected_type": "yes_no",
            "reason": "need_input",
        }
    ]
    svc.save(st)

    resp = run_clarify(
        session_id=st.session_id,
        answers=[{"fact_key": "applies_if(a, eligible)", "value": True}],
        session_svc=svc,
        domain_selector=_Selector(),
        evidence_retriever=_Evidence(),
        rule_index=RulebaseIndex([rule]),
    )

    assert resp.needs_clarification
    asked = [q.fact_key for q in resp.clarification_questions]
    assert "applies_if(a, eligible)" not in asked
    assert "deadline(a, 2024)" in asked
    gain = (resp.debug_trace or {}).get("clarification_gain") or {}
    assert gain.get("post_clarification_status") == "needs_clarification"


def test_filter_clarification_targets_skips_known_and_parse() -> None:
    l2 = Layer2Parse(condition_atoms=["applies_if(a, eligible)"], facts=["deadline(a, 2024)"])
    out = filter_clarification_targets(
        ["applies_if(a, eligible)", "deadline(a, 2024)", "other(x)"],
        known_facts={"applies_if(a, eligible)": True},
        parse_layer2=l2,
    )
    assert out == ["other(x)"]


def test_clarify_invalid_typed_answer_does_not_merge_known_fact(monkeypatch) -> None:
    import runtime.qa_orchestrator as q

    rule = _rule()
    _patch_common(monkeypatch, rule=rule)

    monkeypatch.setattr(
        q,
        "gate_rule_and_backward",
        lambda *_a, **_k: RuleBackwardGateOutcome(
            ok=True,
            clarification_needed=True,
            selected=rule,
            bstate=_reasoning_state_threshold(["constraint:threshold::::"]),
            v_back=_ok_ver("backward_verification"),
        ),
    )

    svc = SessionService()
    st = svc.create_session("q", [])
    st.reasoning = _reasoning_state_threshold(["constraint:threshold::::"])
    st.missing_facts = ["constraint:threshold::::"]
    st.clarification_questions = [
        {
            "fact_key": "threshold_value",
            "source_fact_key": "constraint:threshold::::",
            "question_text": "?",
            "target_kind": "missing_numeric_input",
            "expected_type": "number",
            "reason": "need_input",
        }
    ]
    svc.save(st)

    resp = run_clarify(
        session_id=st.session_id,
        answers=[{"fact_key": "threshold_value", "value": "co"}],
        session_svc=svc,
        domain_selector=_Selector(),
        evidence_retriever=_Evidence(),
        rule_index=RulebaseIndex([rule]),
    )

    saved = svc.get(st.session_id)
    assert saved is not None
    assert "constraint:threshold::::" not in saved.known_facts
    dbg = resp.debug_trace or {}
    assert dbg.get("invalid_clarification_answer") is True
    assert (dbg.get("invalid_clarification_answers") or [])[0].get("expected_type") == "number"


def test_clarify_no_grounded_rule_found_returns_honest_degraded_answer(monkeypatch) -> None:
    import runtime.qa_orchestrator as q

    rule = _rule()
    _patch_common(monkeypatch, rule=rule)

    monkeypatch.setattr(
        q,
        "gate_rule_and_backward",
        lambda *_a, **_k: RuleBackwardGateOutcome(
            ok=False,
            error="no_grounded_rule_found",
            tried_rule_ids=["shared_motif_deadline_1"],
        ),
    )

    svc = SessionService()
    st = svc.create_session("q", [])
    st.reasoning = _reasoning_state(["applies_if(a, eligible)"])
    st.missing_facts = ["applies_if(a, eligible)"]
    st.clarification_questions = [
        {
            "fact_key": "applies_if(a, eligible)",
            "question_text": "?",
            "target_kind": "missing_fact",
            "expected_type": "yes_no",
            "reason": "need_input",
        }
    ]
    svc.save(st)

    resp = run_clarify(
        session_id=st.session_id,
        answers=[{"fact_key": "applies_if(a, eligible)", "value": True}],
        session_svc=svc,
        domain_selector=_Selector(),
        evidence_retriever=_Evidence(),
        rule_index=RulebaseIndex([rule]),
    )

    assert resp.answer is not None
    assert resp.answer.generation_mode == "degraded_honest"
    assert "chưa tìm được quy tắc pháp lý đủ khớp" in resp.answer.answer_text.lower()
    assert "Kết luận tạm thời theo quy tắc" not in resp.answer.answer_text


def test_clarify_forward_unification_fail_uses_honest_degraded_not_pseudo_grounded(monkeypatch) -> None:
    import runtime.qa_orchestrator as q

    rule = RuleRecord(
        rule_id="shared_motif_deadline_1",
        logic_form="deadline",
        head=RuleHead(predicate="unknown", args=["X"]),
        body=[],
        metadata={"domain": "shared", "layer": "shared"},
    )
    _patch_common(monkeypatch, rule=rule)

    monkeypatch.setattr(
        q,
        "gate_rule_and_backward",
        lambda *_a, **_k: RuleBackwardGateOutcome(
            ok=True,
            clarification_needed=False,
            selected=rule,
            bstate=_reasoning_state([]),
            v_back=_ok_ver("backward_verification"),
        ),
    )
    monkeypatch.setattr(
        q,
        "gate_forward_reasoning",
        lambda *_a, **_k: ForwardGateOutcome(
            ok=False,
            error="forward_unification_fail",
            fstate=ReasoningState(missing_facts=[]),
            proof_obj=None,
        ),
    )

    svc = SessionService()
    st = svc.create_session("q", [])
    st.reasoning = _reasoning_state(["applies_if(a, eligible)"])
    st.missing_facts = ["applies_if(a, eligible)"]
    st.clarification_questions = [
        {
            "fact_key": "applies_if(a, eligible)",
            "question_text": "?",
            "target_kind": "missing_fact",
            "expected_type": "yes_no",
            "reason": "need_input",
        }
    ]
    svc.save(st)

    resp = run_clarify(
        session_id=st.session_id,
        answers=[{"fact_key": "applies_if(a, eligible)", "value": True}],
        session_svc=svc,
        domain_selector=_Selector(),
        evidence_retriever=_Evidence(),
        rule_index=RulebaseIndex([rule]),
    )

    assert resp.answer is not None
    assert resp.answer.generation_mode == "degraded_honest"
    assert "suy luận chưa hoàn tất" in resp.answer.answer_text.lower()
    assert "Kết luận tạm thời theo quy tắc" not in resp.answer.answer_text
