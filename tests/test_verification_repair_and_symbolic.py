"""Symbolic checks list, repair loops, controlled verbalizer meta — NeSy v5 extensions."""

from __future__ import annotations

from unittest.mock import patch

from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleHead, RuleRecord
from schemas.verification import NLIResult
from verification.controlled_verbalizer import verbalization_guardrails, verbalize_parse_mode, verbalize_rule_mode
from verification.engine import NeSyEngine
from verification.nli_verifier import NLIVerifier
from verification.repair_loop import run_answer_repair_loop, run_parse_repair_loop
from verification.symbolic_modes import (
    symbolic_answer_checks,
    symbolic_backward,
    symbolic_forward,
    symbolic_parse,
    symbolic_rule,
)


class AlwaysEntailNLI(NLIVerifier):
    """NLI always high entailment — drives REPAIR when symbolic fails (fuse v5)."""

    def verify(self, premise: str, hypothesis: str) -> NLIResult:  # noqa: ARG002
        return NLIResult(
            label="entailment",
            score=0.92,
            scores={"entailment": 0.92, "neutral": 0.04, "contradiction": 0.04},
        )


def test_symbolic_parse_checks_not_single_bool() -> None:
    l1 = Layer1Parse(
        question_focus="obligation",
        subject_text="Công ty A",
        action_text="nộp hồ sơ",
        modality_text="phải",
    )
    l2 = Layer2Parse(goal={"predicate": "unknown", "args": []})
    sym = symbolic_parse("Công ty có nghĩa vụ nộp hồ sơ đúng hạn không?", l1, l2)
    assert sym.ok is False
    assert any(c.get("status") == "fail" for c in sym.checks)
    assert sym.error_codes


def test_symbolic_rule_missing_deadline_structure() -> None:
    rule = RuleRecord(
        rule_id="Rd",
        logic_form="deadline",
        head=RuleHead(predicate="deadline", args=["a"]),
        body=[{"predicate": "other", "args": []}],
    )
    sym = symbolic_rule({"predicate": "deadline", "args": []}, rule)
    assert sym.ok is False
    assert "rule_deadline_error" in sym.error_codes


def test_symbolic_backward_requirement_mismatch() -> None:
    sym = symbolic_backward(
        {"predicate": "obligation", "args": ["s", "a", "o"]},
        "R1",
        {"candidates": [{"rule_id": "R1"}]},
        requirements_ok=True,
        missing_facts=["fact_x"],
        requirement_keys=["other_key"],
    )
    assert sym.ok is False
    assert "requirement_construction_error" in sym.error_codes


def test_symbolic_forward_missing_proof_steps_on_success() -> None:
    sym = symbolic_forward(
        goal_achieved=True,
        forward_result={"goal_reached": True, "failure_reason": "none"},
        proof={"proof_steps": []},
        conclusion="c",
        goal={"predicate": "obligation", "args": []},
    )
    assert sym.ok is False
    assert "forward_proof_error" in sym.error_codes


def test_symbolic_answer_mismatch() -> None:
    sa = symbolic_answer_checks(
        symbolic_ok=False,
        diag_from_validator=["action không khớp goal"],
        answer_text="Trả lời ngắn",
        conclusion="Kết luận phải giữ trong answer",
        proof={"proof_steps": [{}, {}, {}, {}]},
    )
    assert sa.ok is False
    assert sa.checks


def test_parse_repair_loop_round2_accept() -> None:
    l1 = Layer1Parse(
        question_focus="obligation",
        subject_text="Công ty",
        action_text="nộp",
        modality_text="phải",
    )
    l2 = Layer2Parse(goal={"predicate": "unknown", "args": []})
    eng = NeSyEngine(nli=AlwaysEntailNLI(), nesy_nli_mock=False)
    _l1_out, layer2_out, rec, trace = run_parse_repair_loop(
        eng,
        layer1=l1,
        layer2=l2,
        question_text="Công ty có nghĩa vụ nộp đúng hạn không?",
        user_facts=[],
        max_repair_attempts_parse=3,
    )
    assert rec.final_decision == "ACCEPT"
    assert layer2_out.goal.get("predicate") != "unknown"
    assert any(t.get("attempt", -1) >= 1 for t in trace if t.get("phase") == "parse")


def test_parse_repair_stops_at_max_without_fix() -> None:
    l1 = Layer1Parse(
        question_focus="obligation",
        subject_text="Công ty",
        action_text="nộp",
        modality_text="phải",
    )
    bad = Layer2Parse(goal={"predicate": "unknown", "args": []})
    eng = NeSyEngine(nli=AlwaysEntailNLI(), nesy_nli_mock=False)

    def noop_repair(
        layer1: Layer1Parse,
        user_facts: list[str],
        payload: dict,
    ) -> Layer2Parse:
        return bad

    with patch("verification.repair_handlers.repair_layer2_from_payload", side_effect=noop_repair):
        _, _, rec, trace = run_parse_repair_loop(
            eng,
            layer1=l1,
            layer2=bad,
            question_text="Công ty có nghĩa vụ nộp đúng hạn không?",
            user_facts=[],
            max_repair_attempts_parse=2,
        )
    assert rec.final_decision == "REPAIR"
    final_meta = [t for t in trace if t.get("attempts_used") is not None][-1]
    assert final_meta.get("attempts_used") == 2


def test_answer_repair_loop_regenerate_accept() -> None:
    eng = NeSyEngine(nli=AlwaysEntailNLI(), nesy_nli_mock=True)
    calls = {"n": 0}

    def regen(attempt: int, hint: str, payload: dict) -> str:
        calls["n"] += 1
        if attempt == 1:
            return "Trả lời tạm, chưa khớp kết luận."
        return "Theo suy luận, kết luận phải là must(c,a) và khớp kết luận must(c,a)."

    text, rec, trace = run_answer_repair_loop(
        eng,
        answer_text="x",
        conclusion="must(c,a)",
        proof={},
        modality_expected="phải",
        goal_action="a",
        action_token_in_answer="x",
        max_repair_attempts_answer=3,
        regenerate_fn=regen,
    )
    assert "must(c,a)" in text
    assert rec.final_decision in ("ACCEPT", "REJECT", "REPAIR")
    assert trace[-1].get("attempts_used", 0) >= 1


def test_answer_repair_no_handler_fallback() -> None:
    """Khi fusion là REPAIR nhưng target không phải answer_generator → không auto-loop."""

    eng = NeSyEngine(nli=AlwaysEntailNLI(), nesy_nli_mock=True)
    with patch("verification.repair_loop.repair_target_for_code", return_value="forward_reasoner"):
        text, rec, trace = run_answer_repair_loop(
            eng,
            answer_text="Không khớp kết luận",
            conclusion="must(c,a)",
            proof={"proof_steps": [{}, {}, {}, {}]},
            modality_expected="phải",
            goal_action="z",
            action_token_in_answer="Không khớp kết luận",
            max_repair_attempts_answer=3,
        )
    assert rec.final_decision == "REPAIR" or rec.final_decision == "REJECT"
    assert trace[0].get("note") == "no_auto_repair_handler_or_wrong_target" or trace[0].get("auto_repair_eligible") is False
    assert trace[-1].get("attempts_used") == 0


def test_verbalization_meta_and_guardrails() -> None:
    eng = NeSyEngine(nesy_nli_mock=True)
    l1 = Layer1Parse(
        question_focus="obligation",
        subject_text="Công ty",
        action_text="nộp",
        modality_text="phải",
    )
    l2 = Layer2Parse(goal={"predicate": "obligation", "args": ["c", "a", "o"]})
    rec = eng.verify_parse(l1, l2, question_text="Công ty có phải nộp báo cáo không?")
    meta = rec.extra.get("verbalization_meta") or {}
    assert meta.get("template") == "parse_v2_question_layer1_vs_goal_facts"
    assert "premise" in meta and "hypothesis" in meta
    assert "symbolic_checks" in rec.model_dump()
    assert rec.symbolic_checks.get("checks")


def test_parse_verbalization_has_subject_modality() -> None:
    l1 = Layer1Parse(
        question_focus="obligation",
        subject_text="Công ty X",
        action_text="đăng ký",
        modality_text="phải",
    )
    l2 = Layer2Parse(goal={"predicate": "obligation", "args": ["c", "đăng ký", "o"]})
    p, h, _ = verbalize_parse_mode("Hỏi về nghĩa vụ?", l1, l2)
    assert "Công ty X" in p or "subject" in p.lower()
    assert "modality" in p.lower() or "phải" in p
    gr = verbalization_guardrails(mode="parse_verification", layer1=l1, layer2=l2, premise=p, hypothesis=h)
    assert isinstance(gr, list)


def test_rule_verbalization_keeps_exception_context() -> None:
    rule = RuleRecord(
        rule_id="R1",
        logic_form="obligation",
        head=RuleHead(predicate="obligation", args=["a", "b", "c"]),
        body=[{"predicate": "exception_applies", "args": []}],
    )
    p, h, tid = verbalize_rule_mode("Điều 1.", "obligation", rule)
    assert "exception" in p.lower() or "exception_applies" in p.lower()
    assert "R1" in h
    assert tid.startswith("rule_v2")


def test_answer_verbalization_keeps_conclusion() -> None:
    from verification.controlled_verbalizer import verbalize_answer_mode

    p, h, _ = verbalize_answer_mode("Trả lời ngắn", "Kết luận K", {"proof_steps": [{"description": "b1"}]})
    assert "Kết luận K" in p
    assert "Trả lời ngắn" in h
