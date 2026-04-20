from __future__ import annotations

from typing import Any

import pytest

from retrieval.rulebase_loader import RulebaseIndex
from runtime.qa_orchestrator import run_clarify
from runtime.verification_gates import RuleBackwardGateOutcome
from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.reasoning import ReasoningState, RequirementItem
from schemas.rule import RuleHead, RuleRecord
from schemas.verification import VerificationRecord
from session.session_service import SessionService


def _ok_ver(mode: str = "parse_verification") -> VerificationRecord:
    return VerificationRecord(mode=mode, symbolic_ok=True, symbolic_result="ok", final_decision="ACCEPT")


def _rule() -> RuleRecord:
    return RuleRecord(
        rule_id="RULE_CLARIFY_TYPED_01",
        logic_form="permission",
        head=RuleHead(predicate="permission", args=["a", "b", "c"]),
        body=[{"predicate": "applies_if", "args": ["a", "eligible"]}],
        metadata={"provenance": {"domain": "enterprise"}},
    )


def _reasoning_state(missing: list[str]) -> ReasoningState:
    reqs = [
        RequirementItem(key=k, description="", requirement_kind="constraint")
        for k in missing
    ]
    return ReasoningState(
        requirement_set=reqs,
        missing_facts=list(missing),
        covered_requirements=[],
        backward_plan={"candidates": [{"rule_id": "RULE_CLARIFY_TYPED_01"}]},
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
    monkeypatch.setattr(
        q,
        "retrieve_rules",
        lambda **_k: [(rule, 1.0, {"domain": "enterprise", "rulebase_id": "enterprise_core"})],
    )
    monkeypatch.setattr(q, "enrich_ranked_with_retrieval_meta", lambda rows: rows)
    monkeypatch.setattr(q, "collect_rulebase_ids_from_index", lambda _rules: ["enterprise_core"])


def _run_clarify_case(
    monkeypatch,
    *,
    prompt: dict[str, Any],
    answer_value: Any,
) -> tuple[dict[str, Any], SessionService, str, str]:
    import runtime.qa_orchestrator as q

    rule = _rule()
    _patch_common(monkeypatch, rule=rule)

    source_key = str(prompt.get("source_fact_key") or prompt["fact_key"])
    monkeypatch.setattr(
        q,
        "gate_rule_and_backward",
        lambda *_a, **_k: RuleBackwardGateOutcome(
            ok=True,
            clarification_needed=True,
            selected=rule,
            bstate=_reasoning_state([source_key]),
            v_back=_ok_ver("backward_verification"),
        ),
    )

    svc = SessionService()
    st = svc.create_session("q", [])
    st.reasoning = _reasoning_state([source_key])
    st.missing_facts = [source_key]
    st.clarification_questions = [prompt]
    svc.save(st)

    resp = run_clarify(
        session_id=st.session_id,
        answers=[{"fact_key": prompt["fact_key"], "value": answer_value}],
        session_svc=svc,
        domain_selector=_Selector(),
        evidence_retriever=_Evidence(),
        rule_index=RulebaseIndex([rule]),
    )
    return resp.debug_trace or {}, svc, source_key, st.session_id


@pytest.mark.parametrize(
    "prompt,value,expected",
    [
        (
            {
                "fact_key": "is_eligible",
                "source_fact_key": "applies_if(a, eligible)",
                "expected_type": "yes_no",
                "target_kind": "missing_fact",
            },
            "có",
            True,
        ),
        (
            {
                "fact_key": "is_eligible",
                "source_fact_key": "applies_if(a, eligible)",
                "expected_type": "yes_no",
                "target_kind": "missing_fact",
            },
            "không",
            False,
        ),
        (
            {
                "fact_key": "threshold_value",
                "source_fact_key": "constraint:threshold::::",
                "expected_type": "number",
                "target_kind": "missing_numeric_input",
            },
            "12,5",
            12.5,
        ),
        (
            {
                "fact_key": "deadline_date",
                "source_fact_key": "constraint:deadline:fixed",
                "expected_type": "date",
                "target_kind": "missing_time_input",
            },
            "10/04/2026",
            "2026-04-10",
        ),
        (
            {
                "fact_key": "duration_limit",
                "source_fact_key": "constraint:threshold:duration_limit",
                "expected_type": "duration",
                "target_kind": "missing_time_input",
            },
            "30 ngày",
            "30 ngày",
        ),
        (
            {
                "fact_key": "salary_basis",
                "source_fact_key": "constraint:threshold:salary",
                "expected_type": "choice",
                "target_kind": "missing_numeric_input",
                "options": ["luong_toi_thieu_vung", "luong_hop_dong"],
            },
            "LUONG_HOP_DONG",
            "luong_hop_dong",
        ),
    ],
)
def test_e2e_clarify_typed_matrix_valid(
    monkeypatch,
    prompt: dict[str, Any],
    value: Any,
    expected: Any,
) -> None:
    dbg, svc, source_key, sid = _run_clarify_case(monkeypatch, prompt=prompt, answer_value=value)

    saved = svc.get(sid)
    assert saved is not None
    assert source_key in saved.known_facts
    assert saved.known_facts[source_key] == expected
    assert dbg.get("invalid_clarification_answer") is False
    assert dbg.get("invalid_clarification_answers") == []


@pytest.mark.parametrize(
    "prompt,value,expected_type",
    [
        (
            {
                "fact_key": "is_eligible",
                "source_fact_key": "applies_if(a, eligible)",
                "expected_type": "yes_no",
                "target_kind": "missing_fact",
            },
            "30 ngày",
            "yes_no",
        ),
        (
            {
                "fact_key": "threshold_value",
                "source_fact_key": "constraint:threshold::::",
                "expected_type": "number",
                "target_kind": "missing_numeric_input",
            },
            "mười hai",
            "number",
        ),
        (
            {
                "fact_key": "deadline_date",
                "source_fact_key": "constraint:deadline:fixed",
                "expected_type": "date",
                "target_kind": "missing_time_input",
            },
            "tháng sau",
            "date",
        ),
        (
            {
                "fact_key": "duration_limit",
                "source_fact_key": "constraint:threshold:duration_limit",
                "expected_type": "duration",
                "target_kind": "missing_time_input",
            },
            "2026-04-10",
            "duration",
        ),
        (
            {
                "fact_key": "salary_basis",
                "source_fact_key": "constraint:threshold:salary",
                "expected_type": "choice",
                "target_kind": "missing_numeric_input",
                "options": ["luong_toi_thieu_vung", "luong_hop_dong"],
            },
            "muc_luong_thoa_thuan",
            "choice",
        ),
    ],
)
def test_e2e_clarify_typed_matrix_invalid(
    monkeypatch,
    prompt: dict[str, Any],
    value: Any,
    expected_type: str,
) -> None:
    dbg, svc, source_key, sid = _run_clarify_case(monkeypatch, prompt=prompt, answer_value=value)

    saved = svc.get(sid)
    assert saved is not None
    assert source_key not in saved.known_facts
    assert dbg.get("invalid_clarification_answer") is True
    invalid = dbg.get("invalid_clarification_answers") or []
    assert invalid
    assert invalid[0].get("expected_type") == expected_type
    assert invalid[0].get("error") == "invalid_type"


def test_e2e_clarify_unknown_public_fact_key_is_rejected(monkeypatch) -> None:
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
            bstate=_reasoning_state(["constraint:threshold::::"]),
            v_back=_ok_ver("backward_verification"),
        ),
    )

    svc = SessionService()
    st = svc.create_session("q", [])
    st.reasoning = _reasoning_state(["constraint:threshold::::"])
    st.missing_facts = ["constraint:threshold::::"]
    st.clarification_questions = [
        {
            "fact_key": "threshold_value",
            "source_fact_key": "constraint:threshold::::",
            "expected_type": "number",
            "target_kind": "missing_numeric_input",
        }
    ]
    svc.save(st)

    resp = run_clarify(
        session_id=st.session_id,
        answers=[{"fact_key": "wrong_key", "value": "10"}],
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
    invalid = dbg.get("invalid_clarification_answers") or []
    assert invalid
    assert invalid[0].get("error") == "unknown_fact_key"
