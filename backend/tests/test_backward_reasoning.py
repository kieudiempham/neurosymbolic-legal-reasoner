from __future__ import annotations

from reasoning.backward_reasoner import run_backward
from schemas.rule import RuleHead, RuleRecord


def _rule_with_body() -> RuleRecord:
    return RuleRecord(
        rule_id="R_TEST",
        logic_form="obligation",
        head=RuleHead(predicate="obligation", args=["cong_ty", "nop_ho_so", "ket_qua"]),
        body=[{"predicate": "applies_if", "args": ["nop_ho_so", "dieu_kien_x"]}],
        metadata={},
    )


def test_backward_finds_missing_fact():
    rule = _rule_with_body()
    goal = {"predicate": "obligation", "args": ["company_x", "nop_ho_so", "ket_qua"]}
    ranked = [(rule, 10.0, {})]
    selected, st = run_backward(goal=goal, candidates=ranked, known_facts={})
    assert selected is not None
    assert st.missing_facts
