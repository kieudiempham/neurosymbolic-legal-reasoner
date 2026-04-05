"""Active NeSy gates: rule/backward/forward must not silently pass."""

from __future__ import annotations

from pathlib import Path

import pytest

from retrieval.rulebase_loader import RulebaseIndex, configure_rulebase_path, load_rulebase
from runtime.verification_gates import gate_forward_reasoning, gate_rule_and_backward
from schemas.question_parse import Layer2Parse
from schemas.session import SessionState
from verification.engine import NeSyEngine

_REPO = Path(__file__).resolve().parents[1]


def test_gate_rule_backward_empty_ranked_fails() -> None:
    core = _REPO / "data" / "processed" / "rulebase" / "doanhnghiep" / "rulebase_reasoning_core.json"
    if not core.is_file():
        pytest.skip("rulebase fixture missing")
    configure_rulebase_path(core)
    idx = load_rulebase(core)
    eng = NeSyEngine(nesy_nli_mock=True)
    l2 = Layer2Parse(goal={"predicate": "obligation", "args": ["x", "y", "z"]}, query_rule_candidate="test")
    rg = gate_rule_and_backward(
        eng,
        goal=l2.goal,
        layer2=l2,
        ranked=[],
        known_facts={},
        rule_index=idx,
    )
    assert rg.ok is False
    assert rg.error == "no_candidates"


def test_nli_trace_recorded_on_verification_record() -> None:
    eng = NeSyEngine(nesy_nli_mock=True, nli_degraded=False)
    from schemas.question_parse import Layer1Parse

    l1 = Layer1Parse(
        question_focus="obligation",
        modality_text="phải",
        action_text="nộp báo cáo",
        subject_text="công ty",
    )
    l2 = Layer2Parse(
        goal={"predicate": "obligation", "args": ["company_x", "nop_bao_cao", "dung_han"]},
        query_rule_candidate="obligation:company_x,nop_bao_cao",
    )
    rec = eng.verify_parse(l1, l2, question_text="Công ty có phải nộp báo cáo đúng hạn không?")
    assert rec.extra.get("nli_trace")
    assert rec.extra["nli_trace"].get("mode") == "parse_verification"


def test_nli_degraded_marks_trace_degraded() -> None:
    eng = NeSyEngine(nesy_nli_mock=False, nli_degraded=True, nli_meta={"nli_provider": "none"})
    from schemas.question_parse import Layer1Parse

    l1 = Layer1Parse(
        question_focus="obligation",
        modality_text="phải",
        action_text="nộp",
        subject_text="công ty",
    )
    l2 = Layer2Parse(
        goal={"predicate": "obligation", "args": ["a", "b", "c"]},
        query_rule_candidate="x",
    )
    rec = eng.verify_rule(
        layer2_goal=l2.goal,
        rule_candidate=None,
        law_span="",
        legal_frame="",
    )
    assert rec.extra["nli_trace"]["nli_status"] == "degraded_symbolic_only"
    assert rec.extra["nli_trace"]["nli_enabled"] is False
