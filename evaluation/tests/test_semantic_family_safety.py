from __future__ import annotations

from schemas.rule import RuleHead, RuleRecord
from reasoning.semantics.unification import unify_goal_dict_with_goal_atom
from reasoning.semantics.forward_engine import _semantic_goal_head_bridge_failure
from runtime.verification_gates import _semantic_soft_match_info


def test_unification_rejects_weak_action_overlap() -> None:
    goal = {
        "predicate": "obligation",
        "args": ["enterprise_x", "nop_thue", "co_quan_thue"],
    }
    goal_atom = ("must", "enterprise_x", "nop_ho_so", "co_quan_thue")

    subst, fail = unify_goal_dict_with_goal_atom(goal, goal_atom)

    assert subst is None
    assert fail == "term_unification_failed"


def test_soft_match_does_not_rescue_threshold_deadline() -> None:
    goal = {"predicate": "deadline"}
    rule = RuleRecord(
        rule_id="R1",
        logic_form="threshold",
        head=RuleHead(predicate="nguong", args=["X"]),
        body=[],
        metadata={"domain": "shared"},
    )

    ok, reason, meta = _semantic_soft_match_info(goal=goal, rule=rule)

    assert ok is False
    assert reason == "unrelated_family"
    assert meta["goal_family"] == "deadline"


def test_deadline_notification_bridge_requires_matching_event_scope() -> None:
    goal_atom = ("deadline", "gui_thong_bao", 0, "ngay", "moc_thoi_gian")
    head_atom = ("thong_bao_thay_doi_noi_dung_dang_ky_doanh_nghiep", "company_x")

    fail_ok = _semantic_goal_head_bridge_failure(
        goal_atom,
        head_atom,
        goal_context={
            "event_scope": "thay_doi_noi_dung_dang_ky_doanh_nghiep",
            "procedural_subtype": "notification",
        },
    )
    fail_bad_scope = _semantic_goal_head_bridge_failure(
        goal_atom,
        head_atom,
        goal_context={
            "event_scope": "lap_dia_diem_kinh_doanh",
            "procedural_subtype": "notification",
        },
    )
    fail_no_scope = _semantic_goal_head_bridge_failure(
        goal_atom,
        head_atom,
        goal_context={"procedural_subtype": "notification"},
    )

    assert fail_ok is None
    assert fail_bad_scope == "event_mismatch"
    assert fail_no_scope == "event_mismatch"
