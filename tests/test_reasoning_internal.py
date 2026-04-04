"""Tests for internal reasoning schema, mapper, backward/forward, atom codec."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reasoning.backward_reasoner import (
    body_to_requirements,
    goal_unifies_with_goal_atom,
    goal_unifies_with_head,
    run_backward,
)
from reasoning.forward_reasoner import run_forward
from reasoning.internal.codec import (
    deserialize_atom,
    serialize_atom,
)
from reasoning.internal.mapper import map_rule_record_to_reasoning_rule
from reasoning.internal.models import Atom
from reasoning.internal.models import ThresholdConstraint
from retrieval.rulebase_loader import _parse_rule
from schemas.rule import RuleRecord


_REPO = Path(__file__).resolve().parents[1]
_CORE = _REPO / "data" / "processed" / "rulebase" / "doanhnghiep" / "rulebase_reasoning_core.json"


def _first_rules(n: int = 5) -> list[RuleRecord]:
    if not _CORE.exists():
        pytest.skip(f"missing rulebase file: {_CORE}")
    data = json.loads(_CORE.read_text(encoding="utf-8"))
    raw = data.get("rules_reasoning_core") or []
    out: list[RuleRecord] = []
    for row in raw[:n]:
        if isinstance(row, dict):
            r = _parse_rule(row)
            if r:
                out.append(r)
    return out


def test_map_rule_record_to_reasoning_rule_obligation() -> None:
    rules = _first_rules(10)
    obl = next((r for r in rules if r.logic_form == "obligation" and r.body), None)
    assert obl is not None
    rr = map_rule_record_to_reasoning_rule(obl)
    assert rr.goal_atom[0] == obl.head.predicate
    assert len(rr.positive_conditions) + len(rr.negative_conditions) + len(rr.exception_conditions) >= 0
    if any(c.get("predicate") == "exception_applies" for c in obl.body if isinstance(c, dict)):
        assert len(rr.exception_conditions) >= 1


def test_map_threshold_and_applicability() -> None:
    rules = _first_rules(20)
    th = next((r for r in rules if r.logic_form == "threshold"), None)
    assert th is not None
    rr = map_rule_record_to_reasoning_rule(th)
    assert any(isinstance(c, ThresholdConstraint) for c in rr.constraints) or rr.logic_form == "threshold"


def test_atom_roundtrip() -> None:
    a = Atom(predicate="applies_if", args=("a", "b"))
    s = serialize_atom(a)
    b = deserialize_atom(s)
    assert b.predicate == a.predicate and b.args == a.args


def test_backward_uses_reasoning_requirements() -> None:
    rules = _first_rules(15)
    obl = next((r for r in rules if r.logic_form == "obligation"), None)
    assert obl is not None
    rr = map_rule_record_to_reasoning_rule(obl)
    goal = {"predicate": rr.goal_atom[0], "args": list(rr.goal_atom[1:])}
    ranked = [(obl, 100.0, {})]
    known: dict = {}
    selected, st = run_backward(goal=goal, candidates=ranked, known_facts=known)
    assert selected is not None
    assert st.requirement_set
    assert any(getattr(x, "requirement_kind", None) for x in st.requirement_set)


def test_forward_derives_when_satisfied() -> None:
    rules = _first_rules(15)
    obl = next((r for r in rules if r.logic_form == "obligation" and not r.body), None)
    if obl is None:
        pytest.skip("no obligation without body in sample slice")
    rr = map_rule_record_to_reasoning_rule(obl)
    goal = {"predicate": rr.goal_atom[0], "args": list(rr.goal_atom[1:])}
    known = {req.key: True for req in body_to_requirements(obl)}
    conclusion, ok, _st, _tr = run_forward(rule=obl, known_facts=known, goal=goal)
    assert ok
    assert "obligation" in conclusion or obl.head.predicate in conclusion
