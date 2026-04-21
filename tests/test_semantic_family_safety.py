from __future__ import annotations

from schemas.rule import RuleHead, RuleRecord
from reasoning.semantics.unification import unify_goal_dict_with_goal_atom
from runtime.verification_gates import _semantic_soft_match_info


def test_unification_rejects_weak_action_overlap() -> None:
    goal = {
        "predicate": "obligation",
        "args": ["enterprise_x", "nop_thue", "co_quan_thue"],
    }
    goal_atom = ("must", "enterprise_x", "nop_ho_so", "co_quan_thue")

    subst, fail = unify_goal_dict_with_goal_atom(goal, goal_atom)

    assert subst is None
    assert fail == "event_mismatch"


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
