"""NeSy Verify Engine — orchestrates symbolic validation + NLI + fusion."""

from __future__ import annotations

from typing import Any

from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.verification import NLIResult, VerificationRecord
from verification.controlled_verbalizer import verbalize_goal, verbalize_layer1_subject
from verification.decision_fusion import fuse
from verification.mode_selector import use_nli_for
from verification.nli_verifier import NLIVerifier, MockNLIVerifier
from verification.symbolic_validator import check_parse_consistency


class NeSyEngine:
    def __init__(
        self,
        nli: NLIVerifier | None = None,
        *,
        nesy_nli_mock: bool = True,
    ) -> None:
        self._nli = nli or MockNLIVerifier()
        self._nesy_nli_mock = nesy_nli_mock

    def verify_parse(self, layer1: Layer1Parse, layer2: Layer2Parse) -> VerificationRecord:
        sym_ok, issues = check_parse_consistency(layer1, layer2)
        premise = verbalize_layer1_subject(layer1.subject_text or "người hỏi")
        hyp = verbalize_goal(layer2.goal)
        nli: NLIResult | None = None
        if use_nli_for("parse_verification", nesy_nli_mock=self._nesy_nli_mock):
            nli = self._nli.verify(premise, hyp)
        dec, diag = fuse(symbolic_ok=sym_ok, nli=nli, prefer_symbolic=True)
        diag.extend(issues)
        return VerificationRecord(
            mode="parse_verification",
            symbolic_result="ok" if sym_ok else "failed",
            symbolic_ok=sym_ok,
            nli_result=nli,
            final_decision=dec,
            diagnostics=diag,
            repair_target=None if dec != "REPAIR" else "layer2_goal",
        )

    def verify_backward(
        self,
        *,
        goal: dict[str, Any],
        selected_rule_id: str | None,
        requirements_ok: bool,
    ) -> VerificationRecord:
        sym_ok = bool(selected_rule_id) and requirements_ok
        hyp = verbalize_goal(goal)
        premise = f"Luật được chọn {selected_rule_id} bao phủ mục tiêu."
        nli: NLIResult | None = None
        if use_nli_for("backward_verification", nesy_nli_mock=self._nesy_nli_mock):
            nli = self._nli.verify(premise, hyp)
        dec, diag = fuse(symbolic_ok=sym_ok, nli=nli, prefer_symbolic=True)
        return VerificationRecord(
            mode="backward_verification",
            symbolic_result="ok" if sym_ok else "incomplete",
            symbolic_ok=sym_ok,
            nli_result=nli,
            final_decision=dec,
            diagnostics=diag,
            repair_target=None if dec != "REPAIR" else "rule_selection",
        )

    def verify_forward(
        self,
        *,
        goal: dict[str, Any],
        conclusion: str,
        goal_achieved: bool,
    ) -> VerificationRecord:
        sym_ok = goal_achieved
        nli = (
            self._nli.verify(verbalize_goal(goal), conclusion)
            if use_nli_for("forward_verification", nesy_nli_mock=self._nesy_nli_mock)
            else None
        )
        dec, diag = fuse(symbolic_ok=sym_ok, nli=nli, prefer_symbolic=True)
        return VerificationRecord(
            mode="forward_verification",
            symbolic_result="ok" if sym_ok else "mismatch",
            symbolic_ok=sym_ok,
            nli_result=nli,
            final_decision=dec,
            diagnostics=diag,
            repair_target=None if dec != "REPAIR" else "forward_unification",
        )

    def verify_answer(
        self,
        *,
        answer_text: str,
        conclusion: str,
        symbolic_ok: bool,
    ) -> VerificationRecord:
        premise = conclusion
        nli = (
            self._nli.verify(premise, answer_text)
            if use_nli_for("answer_verification", nesy_nli_mock=self._nesy_nli_mock)
            else None
        )
        dec, diag = fuse(symbolic_ok=symbolic_ok, nli=nli, prefer_symbolic=False)
        return VerificationRecord(
            mode="answer_verification",
            symbolic_result="ok" if symbolic_ok else "failed",
            symbolic_ok=symbolic_ok,
            nli_result=nli,
            final_decision=dec,
            diagnostics=diag,
            repair_target=None if dec != "REPAIR" else "answer_text",
        )


def nesy_engine_singleton() -> NeSyEngine:
    return NeSyEngine()
