from __future__ import annotations

from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.verification import NLIResult, VerificationRecord
from verification.engine import NeSyEngine
from verification.nli_verifier import NLIVerifier
from verification.repair_loop import run_parse_repair_loop


class StaticNLI(NLIVerifier):
    def __init__(self, result: NLIResult) -> None:
        self._result = result

    def verify(self, premise: str, hypothesis: str) -> NLIResult:  # noqa: ARG002
        return self._result


def _entailment_nli() -> StaticNLI:
    return StaticNLI(
        NLIResult(
            label="entailment",
            score=0.95,
            scores={"entailment": 0.95, "neutral": 0.03, "contradiction": 0.02},
        )
    )


def _contradiction_nli() -> StaticNLI:
    return StaticNLI(
        NLIResult(
            label="contradiction",
            score=0.92,
            scores={"entailment": 0.03, "neutral": 0.05, "contradiction": 0.92},
        )
    )


def test_parse_contradiction_guarded_repair_for_obligation_focus() -> None:
    engine = NeSyEngine(nli=_contradiction_nli(), nesy_nli_mock=False)
    layer1 = Layer1Parse(question_focus="obligation", subject_text="Công ty", action_text="nộp", modality_text="phải")
    layer2 = Layer2Parse(goal={"predicate": "obligation", "args": ["c", "a", "o"]})

    rec = engine.verify_parse(layer1, layer2, question_text="Công ty có phải nộp hồ sơ không?")

    assert rec.final_decision == "REPAIR"
    assert any("fusion_policy_parse_contradiction" in d for d in rec.diagnostics)


def test_backward_semantic_family_mismatch_rejects_even_with_high_nli() -> None:
    engine = NeSyEngine(nli=_entailment_nli(), nesy_nli_mock=False)
    rec = engine.verify_backward(
        goal={"predicate": "obligation", "args": ["c", "a", "o"]},
        selected_rule_id="R_deadline",
        requirements_ok=True,
        backward_plan={
            "candidates": [
                {
                    "rule_id": "R_deadline",
                    "rule_head_predicate": "deadline",
                    "rule_logic_form": "deadline",
                    "semantic_compatibility": -2.0,
                    "shared_generic_candidate": False,
                    "weak_grounding": False,
                }
            ]
        },
        missing_facts=[],
        requirement_artifact={"rule_id": "R_deadline", "goal_predicate": "obligation"},
    )

    assert rec.final_decision == "REJECT"
    assert "backward_semantic_family_mismatch" in rec.diagnostic_errors


def test_backward_shared_generic_weak_grounding_rejects() -> None:
    engine = NeSyEngine(nli=_entailment_nli(), nesy_nli_mock=False)
    rec = engine.verify_backward(
        goal={"predicate": "unknown", "args": ["c", "a", "o"]},
        selected_rule_id="shared_motif_deadline_01",
        requirements_ok=True,
        backward_plan={
            "candidates": [
                {
                    "rule_id": "shared_motif_deadline_01",
                    "rule_head_predicate": "deadline",
                    "rule_logic_form": "deadline",
                    "semantic_compatibility": 0.0,
                    "shared_generic_candidate": True,
                    "weak_grounding": True,
                }
            ]
        },
        missing_facts=[],
        requirement_artifact={"rule_id": "shared_motif_deadline_01", "goal_predicate": "unknown"},
    )

    assert rec.final_decision == "REJECT"
    assert "backward_weak_grounding" in rec.diagnostic_errors


def test_forward_proof_alignment_error_cannot_be_accepted() -> None:
    engine = NeSyEngine(nli=_entailment_nli(), nesy_nli_mock=False)
    rec = engine.verify_forward(
        goal={"predicate": "obligation", "args": ["c", "a", "o"]},
        conclusion="obligation(c,a,o)",
        goal_achieved=True,
        forward_result={"goal_reached": True, "failure_reason": "none"},
        proof={
            "proof_steps": [
                {
                    "rule_id": "R_other",
                    "description": "proof step",
                    "supporting_atoms": [{"predicate": "other", "args": ["x"]}],
                }
            ]
        },
        requirement_artifact={"required_predicates": ["obligation"]},
        selected_rule_id="R_expected",
    )

    assert rec.final_decision == "REJECT"
    assert "forward_proof_error" in rec.diagnostic_errors


def test_parse_repair_needs_material_gain_before_accept_promotion() -> None:
    class StubEngine:
        def __init__(self) -> None:
            self.calls = 0

        def verify_parse(self, *_args, **_kwargs) -> VerificationRecord:
            self.calls += 1
            if self.calls == 1:
                return VerificationRecord(
                    mode="parse_verification",
                    symbolic_ok=False,
                    symbolic_result="failed",
                    final_decision="REPAIR",
                    diagnostics=["parse_slot_error"],
                    diagnostic_errors=["parse_slot_error"],
                    repair_target_module="parser",
                    repair_hint="fix:parse_slot_error",
                )
            return VerificationRecord(
                mode="parse_verification",
                symbolic_ok=True,
                symbolic_result="ok",
                final_decision="ACCEPT",
                diagnostics=[],
                diagnostic_errors=[],
            )

    layer1 = Layer1Parse(question_focus="obligation", subject_text="Công ty", action_text="nộp", modality_text="phải")
    layer2 = Layer2Parse(goal={"predicate": "unknown", "args": []})

    def noop_repair(
        _q: str,
        l1: Layer1Parse,
        l2: Layer2Parse,
        _facts: list[str],
        _payload: dict[str, object],
        *,
        repair_hint: str,
    ) -> tuple[Layer1Parse, Layer2Parse, dict[str, object]]:  # noqa: ARG001
        return l1, l2, {"noop": True}

    _l1, _l2, rec, _trace = run_parse_repair_loop(
        StubEngine(),  # type: ignore[arg-type]
        layer1=layer1,
        layer2=layer2,
        question_text="Công ty có phải nộp hồ sơ không?",
        user_facts=[],
        max_repair_attempts_parse=1,
        repair_parse_fn=noop_repair,
    )

    assert rec.final_decision == "REJECT"
    assert "repair_without_material_parse_gain" in rec.diagnostics
