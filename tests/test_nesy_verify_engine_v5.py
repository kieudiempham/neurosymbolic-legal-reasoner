"""NeSy Verify Engine v5: five modes, fusion matrix, diagnostics, repair hints."""

from __future__ import annotations

from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleHead, RuleRecord
from schemas.verification import NLIResult
from verification.decision_fusion import fuse_ne_sy_v5
from verification.engine import NeSyEngine
from verification.nli_verifier import MockNLIVerifier


def test_fusion_both_good_accept() -> None:
    nli = NLIResult(
        label="entailment",
        score=0.9,
        scores={"entailment": 0.9, "neutral": 0.05, "contradiction": 0.05},
    )
    d, _ = fuse_ne_sy_v5(symbolic_ok=True, nli=nli, entailment_threshold=0.7, contradiction_threshold=0.7)
    assert d == "ACCEPT"


def test_fusion_symbolic_pass_nli_contradiction_reject() -> None:
    nli = NLIResult(
        label="contradiction",
        score=0.85,
        scores={"entailment": 0.05, "neutral": 0.1, "contradiction": 0.85},
    )
    d, diag = fuse_ne_sy_v5(symbolic_ok=True, nli=nli)
    assert d == "REJECT"
    assert any("overrides" in x for x in diag)


def test_fusion_symbolic_fail_nli_entailment_repair() -> None:
    nli = NLIResult(
        label="entailment",
        score=0.92,
        scores={"entailment": 0.92, "neutral": 0.04, "contradiction": 0.04},
    )
    d, diag = fuse_ne_sy_v5(symbolic_ok=False, nli=nli)
    assert d == "REPAIR"
    assert "nli_entailment_despite_symbolic_fail" in diag


def test_fusion_both_bad_reject() -> None:
    nli = NLIResult(
        label="neutral",
        score=0.5,
        scores={"entailment": 0.2, "neutral": 0.5, "contradiction": 0.3},
    )
    d, _ = fuse_ne_sy_v5(symbolic_ok=False, nli=nli)
    assert d == "REJECT"


def test_parse_verification_record_fields() -> None:
    e = NeSyEngine(nesy_nli_mock=True)
    l1 = Layer1Parse(question_focus="obligation", subject_text="công ty")
    l2 = Layer2Parse(goal={"predicate": "obligation", "args": ["x", "y", "z"]})
    rec = e.verify_parse(l1, l2, question_text="Công ty có phải nộp báo cáo không?")
    assert rec.mode == "parse_verification"
    assert rec.final_decision in ("ACCEPT", "REJECT", "REPAIR")
    assert "hypothesis_goal" in rec.verbalized_texts


def test_rule_verification_mode() -> None:
    e = NeSyEngine(nesy_nli_mock=True)
    rule = RuleRecord(
        rule_id="R1",
        logic_form="obligation",
        head=RuleHead(predicate="obligation", args=["a", "b", "c"]),
        body=[],
    )
    rec = e.verify_rule(
        layer2_goal={"predicate": "obligation", "args": ["a", "b", "c"]},
        rule_candidate=rule,
        law_span="Điều 1 Luật X.",
        legal_frame="obligation",
    )
    assert rec.mode == "rule_verification"
    assert rec.symbolic_ok


def test_backward_forward_answer_have_diagnostics() -> None:
    e = NeSyEngine(nesy_nli_mock=True)
    b = e.verify_backward(
        goal={"predicate": "must", "args": ["c", "a"]},
        selected_rule_id="R1",
        requirements_ok=True,
        backward_plan={"candidates": [{"rule_id": "R1"}]},
        missing_facts=[],
    )
    assert b.mode == "backward_verification"
    f = e.verify_forward(
        goal={"predicate": "must", "args": ["c", "a"]},
        conclusion="must(c,a)",
        goal_achieved=True,
        forward_result={"goal_reached": True, "failure_reason": "none"},
        proof={"proof_steps": [{"step_id": 1}], "derived_conclusion": "must(c,a)"},
    )
    assert f.mode == "forward_verification"
    a = e.verify_answer(
        answer_text="Theo suy luận, kết luận phải là must(c,a).",
        conclusion="must(c,a)",
        proof={},
        modality_expected="phải",
        goal_action="a",
    )
    assert a.mode == "answer_verification"
    assert a.diagnostic_errors is not None


def test_engine_uses_real_nli_when_not_mock() -> None:
    inner = MockNLIVerifier()
    e = NeSyEngine(nli=inner, nesy_nli_mock=False)
    l1 = Layer1Parse(question_focus="obligation")
    l2 = Layer2Parse(goal={"predicate": "obligation", "args": ["s", "a", "o"]})
    rec = e.verify_parse(l1, l2, question_text="Đủ dài để không lỗi parse_slot.")
    assert rec.nli_result is not None
