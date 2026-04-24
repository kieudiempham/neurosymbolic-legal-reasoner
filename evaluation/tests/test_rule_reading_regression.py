from __future__ import annotations

from question_side.question_normalizer import build_layer2
from runtime.qa_orchestrator import (
    _collect_application_policy_missing_facts,
    _infer_question_mode,
    _infer_legal_missing_facts_from_reasoning_failure,
    _is_internal_diagnostic,
    _synthesize_canonical_missing_facts,
)
from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.reasoning import ReasoningState


def _mk_rule_reading_layer1(question: str) -> Layer1Parse:
    return Layer1Parse(
        utterance_type="direct_question",
        subject_text="doanh nghiep",
        action_text="thong bao thay doi noi dung dang ky doanh nghiep",
        condition_text="thay doi noi dung dang ky doanh nghiep",
        modality_text=question,
        question_focus="deadline",
        assertion_status="unknown",
    )


def _mk_generic_layer2() -> Layer2Parse:
    return Layer2Parse(
        subject_normalized="company_x",
        condition_atoms=["stated_condition(company_x,thay_doi_noi_dung_dang_ky_doanh_nghiep)"],
        facts=["domain:enterprise_registration"],
        goal={"predicate": "deadline", "args": ["gui_thong_bao", 0, "ngay", "moc_thoi_gian"]},
        diagnostics={},
    )


def test_q1_and_variants_stay_rule_reading_even_with_generic_fact_signals() -> None:
    questions = [
        "Thoi han thong bao thay doi noi dung dang ky doanh nghiep la bao nhieu ngay?",
        "Thoi han thong bao thay doi dang ky doanh nghiep la bao lau?",
        "Doanh nghiep phai thong bao thay doi noi dung dang ky trong may ngay?",
        "Theo luat, thoi han thong bao thay doi noi dung dang ky doanh nghiep la gi?",
    ]

    for q in questions:
        layer1 = _mk_rule_reading_layer1(q)
        mode = _infer_question_mode(layer1, _mk_generic_layer2())
        assert mode == "rule_reading", q


def test_rule_reading_not_downgraded_by_multi_intent_noise() -> None:
    layer1 = Layer1Parse(
        utterance_type="direct_question",
        subject_text="doanh nghiep",
        action_text="thong bao thay doi noi dung dang ky doanh nghiep",
        condition_text="",
        modality_text="Thoi han thong bao thay doi noi dung dang ky doanh nghiep la bao nhieu ngay?",
        question_focus="deadline",
        assertion_status="unknown",
        parse_metadata={
            "has_multi_intent": True,
            "intent_units": [
                {"focus": "obligation", "text": "doanh nghiep phai thong bao thay doi noi dung dang ky"},
                {"focus": "deadline", "text": "thoi han la bao nhieu ngay"},
            ],
        },
    )

    layer2 = build_layer2(layer1, user_facts=[])

    assert str(layer2.goal.get("predicate") or "") == "deadline"
    intent_diag = (layer2.diagnostics or {}).get("intent_structure") or {}
    assert bool(intent_diag.get("rule_reading_deadline_locked")) is True


def test_case_specific_application_question_still_fact_application() -> None:
    layer1 = Layer1Parse(
        utterance_type="conditional_legal_question",
        subject_text="cong ty toi",
        action_text="gui thong bao",
        condition_text="chua ro thoi diem gui",
        modality_text="co bi qua han khong",
        question_focus="deadline",
        assertion_status="hypothetical",
    )

    mode = _infer_question_mode(layer1, _mk_generic_layer2())
    assert mode == "fact_application"


# ---------------------------------------------------------------------------
# Q2: fact_application + missing temporal facts policy
# ---------------------------------------------------------------------------

def _mk_fstate_unification_broken() -> ReasoningState:
    """Simulate a forward state where unification failed (temporal facts missing)."""
    return ReasoningState(
        requirement_set=[],
        missing_facts=[],
        selected_rule_ids=["RULE_TEST"],
        forward_result={"failure_reason": "unification_broken", "failure_detail": ""},
    )


def _mk_goal_notification_deadline() -> dict:
    return {
        "predicate": "applies_if",
        "args": ["company_x", "gui_thong_bao", "thong_bao"],
    }


def test_q2_unification_broken_triggers_missing_signal_for_fact_application() -> None:
    """unification_broken + fact_application MUST produce has_missing_signal=True."""
    fstate = _mk_fstate_unification_broken()
    facts, has_signal = _collect_application_policy_missing_facts(
        bstate=None,
        fstate=fstate,
        question_mode="fact_application",
        goal=_mk_goal_notification_deadline(),
    )
    assert has_signal is True, "unification_broken in fact_application must set has_missing_signal"
    assert len(facts) > 0, "missing_facts must be non-empty for deadline-compliance goal"


def test_q2_synthesized_facts_are_temporal_for_notification_goal() -> None:
    """Notification-deadline goal → synthesized facts must include canonical temporal keys."""
    facts = _synthesize_canonical_missing_facts(
        goal=_mk_goal_notification_deadline(),
        fail_key="unification_broken",
    )
    # Canonical keys from family-level policy (change_effective_date / notification_submission_date)
    assert any(k in facts for k in ("change_date", "change_effective_date")), facts
    assert any(k in facts for k in ("submission_date", "notification_submission_date")), facts


def test_q2_unification_broken_hybrid_mode_no_signal_without_facts() -> None:
    """In hybrid mode, unification_broken without explicit facts should NOT force signal (to avoid regression)."""
    fstate = _mk_fstate_unification_broken()
    _facts, has_signal = _collect_application_policy_missing_facts(
        bstate=None,
        fstate=fstate,
        question_mode="hybrid",
        goal=_mk_goal_notification_deadline(),
    )
    # hybrid: no forced signal from unification_broken alone (only fact_application gets this)
    assert has_signal is False


def test_q2_explicit_missing_facts_still_collected_normally() -> None:
    """When backward reasoning surfaces explicit missing facts, they must survive."""
    bstate = ReasoningState(
        requirement_set=[],
        missing_facts=["change_date", "submission_date"],
        selected_rule_ids=["RULE_TEST"],
    )
    facts, has_signal = _collect_application_policy_missing_facts(
        bstate=bstate,
        fstate=None,
        question_mode="fact_application",
        goal=_mk_goal_notification_deadline(),
    )
    assert "change_date" in facts
    assert "submission_date" in facts


def test_q2_variants_infer_fact_application() -> None:
    """Q2 variants with case-specific signals must be classified as fact_application or hybrid."""
    case_signals = [
        # "công ty tôi" + application modal → fact_application
        Layer1Parse(
            utterance_type="conditional_legal_question",
            subject_text="cong ty toi",
            action_text="thay doi dang ky",
            condition_text="chua biet ngay nop thong bao",
            modality_text="co qua han chua",
            question_focus="deadline",
            assertion_status="hypothetical",
        ),
        # Explicit hypothetical about time gap → fact_application
        Layer1Parse(
            utterance_type="conditional_legal_question",
            subject_text="doanh nghiep",
            action_text="gui thong bao thay doi dang ky",
            condition_text="chua ro ngay gui thong bao",
            modality_text="co xac dinh qua han duoc khong",
            question_focus="legal_effect",
            assertion_status="hypothetical",
        ),
    ]
    for layer1 in case_signals:
        mode = _infer_question_mode(layer1, _mk_generic_layer2())
        assert mode in {"fact_application", "hybrid"}, (
            f"Expected fact_application or hybrid but got {mode!r} for: {layer1.subject_text}"
        )


# ---------------------------------------------------------------------------
# Task 3: Missing-fact normalization — no internal tokens must surface
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Q3: hybrid classification — consequence signal must prevent early rule_reading lock
# ---------------------------------------------------------------------------

def _mk_locked_layer2() -> Layer2Parse:
    return Layer2Parse(
        subject_normalized="company_x",
        condition_atoms=[],
        facts=[],
        goal={"predicate": "deadline", "args": ["gui_thong_bao", 0, "ngay", "moc_thoi_gian"]},
        diagnostics={"intent_structure": {"rule_reading_deadline_locked": True}},
    )


def test_q3_consequence_signal_overrides_deadline_lock_to_hybrid() -> None:
    """Q3 pattern: deadline question + consequence sub-question must be classified as hybrid."""
    consequence_modalities = [
        "co bi xu ly gi khong",
        "có bị xử lý gì không",
        "co bi phat khong",
        "có bị phạt không",
        "neu nop sau thi co bi xu ly khong",
    ]
    layer2 = _mk_locked_layer2()
    for modality in consequence_modalities:
        layer1 = Layer1Parse(
            utterance_type="direct_question",
            subject_text="cong ty",
            action_text="thong bao thay doi noi dung dang ky",
            condition_text="",
            modality_text=modality,
            question_focus="deadline",
            assertion_status="unknown",
        )
        mode = _infer_question_mode(layer1, layer2)
        assert mode == "hybrid", f"Expected hybrid for consequence modality {modality!r}, got {mode!r}"


def test_q1_locked_without_consequence_stays_rule_reading() -> None:
    """Q1 with deadline lock and no consequence signal must remain rule_reading."""
    layer2 = _mk_locked_layer2()
    layer1 = Layer1Parse(
        utterance_type="direct_question",
        subject_text="doanh nghiep",
        action_text="thong bao thay doi noi dung dang ky doanh nghiep",
        condition_text="",
        modality_text="bao nhieu ngay",
        question_focus="deadline",
        assertion_status="unknown",
    )
    mode = _infer_question_mode(layer1, layer2)
    assert mode == "rule_reading", f"Q1 locked must remain rule_reading, got {mode!r}"


# ---------------------------------------------------------------------------
# Task 3: Missing-fact normalization — no internal tokens must surface
# ---------------------------------------------------------------------------

def test_internal_diagnostic_tokens_not_in_missing_facts() -> None:
    """event_mismatch and other internal tokens must never appear in output facts."""
    internal_tokens = [
        "event_mismatch",
        "predicate_mismatch",
        "unification_broken",
        "actor_role_mismatch",
        "forward_gate_failure",
        "rule_backward_gate_failure",
    ]
    for token in internal_tokens:
        assert _is_internal_diagnostic(token), f"{token!r} must be recognized as internal diagnostic"


def test_collect_missing_facts_blocks_event_mismatch_from_failure_detail() -> None:
    """failure_detail='event_mismatch' must be filtered; output must use canonical keys."""
    fstate = ReasoningState(
        requirement_set=[],
        missing_facts=[],
        selected_rule_ids=["RULE_TEST"],
        forward_result={
            "failure_reason": "unification_broken",
            "failure_detail": "event_mismatch",
        },
    )
    facts, has_signal = _collect_application_policy_missing_facts(
        bstate=None,
        fstate=fstate,
        question_mode="fact_application",
        goal={"predicate": "applies_if", "args": ["company_x", "gui_thong_bao", "thong_bao"]},
    )
    assert has_signal is True
    assert "event_mismatch" not in facts, "event_mismatch must be filtered from user-facing facts"
    for f in facts:
        assert not _is_internal_diagnostic(f), f"Internal diagnostic token {f!r} leaked into facts"


def test_temporal_family_produces_canonical_keys_for_notification_goal() -> None:
    """Temporal compliance family → change_effective_date + notification_submission_date."""
    facts = _infer_legal_missing_facts_from_reasoning_failure(
        fail_key="unification_broken",
        goal={"predicate": "applies_if", "args": ["company_x", "gui_thong_bao", "thong_bao"]},
        selected_rule=None,
    )
    assert "change_effective_date" in facts
    assert "notification_submission_date" in facts
    for f in facts:
        assert not _is_internal_diagnostic(f), f"Internal diagnostic token {f!r} in canonical output"


def test_actor_role_family_produces_canonical_keys() -> None:
    """actor_role_mismatch failure → actor_role + actor_identity."""
    facts = _infer_legal_missing_facts_from_reasoning_failure(
        fail_key="actor_role_mismatch",
        goal={"predicate": "obligation", "args": ["company_x", "nop_ho_so"]},
        selected_rule=None,
    )
    assert "actor_role" in facts
    assert "actor_identity" in facts
    for f in facts:
        assert not _is_internal_diagnostic(f), f"Internal diagnostic token {f!r} in canonical output"


def test_condition_family_produces_canonical_keys() -> None:
    """positive_condition_missing failure → required_condition_fact + exception_applicability_fact."""
    facts = _infer_legal_missing_facts_from_reasoning_failure(
        fail_key="positive_condition_missing",
        goal={"predicate": "legal_effect", "args": ["company_x", "dang_ky"]},
        selected_rule=None,
    )
    assert "required_condition_fact" in facts
    assert "exception_applicability_fact" in facts
    for f in facts:
        assert not _is_internal_diagnostic(f), f"Internal diagnostic token {f!r} in canonical output"
