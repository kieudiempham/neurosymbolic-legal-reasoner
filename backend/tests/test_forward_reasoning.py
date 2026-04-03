from __future__ import annotations

from reasoning.forward_reasoner import run_forward
from schemas.rule import RuleHead, RuleRecord


def test_forward_derives_conclusion_when_facts_complete():
    rule = RuleRecord(
        rule_id="R_FWD",
        logic_form="permission",
        head=RuleHead(predicate="permission", args=["cong_ty", "gui_phieu_lay_y_kien", "phieu_lay_y_kien"]),
        body=[],
        metadata={},
    )
    goal = {"predicate": "permission", "args": ["company_x", "gui_phieu_lay_y_kien", "phieu_lay_y_kien"]}
    conclusion, ok, st, _ = run_forward(rule=rule, known_facts={}, goal=goal)
    assert "permission(" in conclusion
    assert ok is True
    assert st.goal_status == "satisfied"
