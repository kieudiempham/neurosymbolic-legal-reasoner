"""NeSy Verify Engine v5 — multi-mode: NLI + symbolic + fusion + diagnostics + repair routing."""

from __future__ import annotations

from typing import Any

from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord
from schemas.verification import FusionDecision, NLIResult, VerificationMode, VerificationRecord
from verification.controlled_verbalizer import (
    verbalize_backward_plan,
    verbalize_forward_failure,
    verbalize_goal,
    verbalize_law_span,
    verbalize_layer1_subject,
    verbalize_proof_brief,
    verbalize_question_text,
    verbalize_rule_candidate,
)
from verification.decision_fusion import fuse_ne_sy_v5
from verification.mode_selector import use_nli_for
from verification.nli_verifier import NLIVerifier, MockNLIVerifier
from verification.object_normalizer import (
    normalize_answer_bundle,
    normalize_backward_bundle,
    normalize_forward_bundle,
    normalize_parse_bundle,
    normalize_rule_bundle,
)
from verification.repair_routing import build_repair_payload, repair_hint_for, repair_target_for_code
from verification.symbolic_modes import (
    symbolic_backward,
    symbolic_forward,
    symbolic_parse,
    symbolic_rule,
    symbolic_answer_checks,
)
from verification.symbolic_validator import check_answer_vs_goal


def _first_code(codes: list[str]) -> str | None:
    return codes[0] if codes else None


def _repair_fields(mode: str, codes: list[str]) -> tuple[str | None, str, dict[str, Any]]:
    c0 = _first_code(codes)
    mod = repair_target_for_code(c0) if c0 else None
    hint = repair_hint_for(c0 or "unknown", mode=mode) if c0 else ""
    payload = build_repair_payload(codes=codes, mode=mode)
    return mod, hint, payload


def _finalize_record(
    *,
    mode: VerificationMode,
    symbolic_ok: bool,
    sym_issues: list[str],
    error_codes: list[str],
    nli: NLIResult | None,
    decision: FusionDecision,
    fusion_diag: list[str],
    verbalized: dict[str, str],
    normalized: dict[str, Any],
    trace: list[str],
    symbolic_checks: dict[str, Any],
    semantic_scores: dict[str, float] | None = None,
) -> VerificationRecord:
    rt_mod, hint, payload = _repair_fields(mode, error_codes)
    diag = list(sym_issues) + list(fusion_diag)
    repair_legacy = None
    if decision == "REPAIR":
        repair_legacy = rt_mod or "unspecified"
    nli_scores = {}
    if nli and nli.scores:
        nli_scores = dict(nli.scores)
    elif nli:
        nli_scores = {nli.label: float(nli.score)}
    return VerificationRecord(
        mode=mode,
        symbolic_result="ok" if symbolic_ok else "failed",
        symbolic_ok=symbolic_ok,
        nli_result=nli,
        final_decision=decision,
        diagnostics=diag,
        repair_target=repair_legacy,
        diagnostic_errors=list(error_codes),
        repair_target_module=rt_mod,
        repair_hint=hint,
        repair_payload=payload,
        semantic_scores=semantic_scores or nli_scores,
        symbolic_checks=symbolic_checks,
        normalized_inputs=normalized,
        verbalized_texts=verbalized,
        trace=trace,
    )


class NeSyEngine:
    """Multi-mode NeSy verification — single source of truth for runtime."""

    def __init__(
        self,
        nli: NLIVerifier | None = None,
        *,
        nesy_nli_mock: bool = True,
        entailment_threshold: float = 0.70,
        contradiction_threshold: float = 0.70,
    ) -> None:
        self._nli = nli or MockNLIVerifier()
        self._nesy_nli_mock = nesy_nli_mock
        self._entailment_threshold = entailment_threshold
        self._contradiction_threshold = contradiction_threshold

    def verify_parse(
        self,
        layer1: Layer1Parse,
        layer2: Layer2Parse,
        *,
        question_text: str = "",
    ) -> VerificationRecord:
        sym = symbolic_parse(question_text, layer1, layer2)
        trace = ["symbolic_parse_done"]
        verbalized: dict[str, str] = {
            "premise_alignment": verbalize_question_text(question_text),
            "hypothesis_goal": verbalize_goal(layer2.goal),
            "layer1_subject": verbalize_layer1_subject(layer1.subject_text or "chủ_thể"),
        }
        nli: NLIResult | None = None
        if use_nli_for("parse_verification", nesy_nli_mock=self._nesy_nli_mock):
            nli = self._nli.verify(verbalized["premise_alignment"], verbalized["hypothesis_goal"])
            trace.append("nli_parse")
        dec, fusion_diag = fuse_ne_sy_v5(
            symbolic_ok=sym.ok,
            nli=nli,
            entailment_threshold=self._entailment_threshold,
            contradiction_threshold=self._contradiction_threshold,
        )
        return _finalize_record(
            mode="parse_verification",
            symbolic_ok=sym.ok,
            sym_issues=sym.issues,
            error_codes=sym.error_codes,
            nli=nli,
            decision=dec,
            fusion_diag=fusion_diag,
            verbalized=verbalized,
            normalized=normalize_parse_bundle(question_text=question_text, layer1=layer1, layer2=layer2),
            trace=trace,
            symbolic_checks={"issues": sym.issues, "codes": sym.error_codes},
        )

    def verify_rule(
        self,
        *,
        layer2_goal: dict[str, Any],
        rule_candidate: RuleRecord | None,
        law_span: str | None = None,
        legal_frame: str | None = None,
    ) -> VerificationRecord:
        sym = symbolic_rule(layer2_goal, rule_candidate, _legal_frame=legal_frame)
        trace = ["symbolic_rule_done"]
        verbalized: dict[str, str] = {}
        if rule_candidate:
            verbalized["hypothesis_rule"] = verbalize_rule_candidate(
                rule_candidate.rule_id, rule_candidate.logic_form, rule_candidate.head.predicate
            )
        else:
            verbalized["hypothesis_rule"] = "Không có luật ứng viên."
        verbalized["premise_law"] = verbalize_law_span(law_span) if law_span else "Không có đoạn văn bản luật đính kèm."
        nli: NLIResult | None = None
        if use_nli_for("rule_verification", nesy_nli_mock=self._nesy_nli_mock):
            nli = self._nli.verify(verbalized["premise_law"], verbalized["hypothesis_rule"])
            trace.append("nli_rule")
        dec, fusion_diag = fuse_ne_sy_v5(
            symbolic_ok=sym.ok,
            nli=nli,
            entailment_threshold=self._entailment_threshold,
            contradiction_threshold=self._contradiction_threshold,
        )
        return _finalize_record(
            mode="rule_verification",
            symbolic_ok=sym.ok,
            sym_issues=sym.issues,
            error_codes=sym.error_codes,
            nli=nli,
            decision=dec,
            fusion_diag=fusion_diag,
            verbalized=verbalized,
            normalized=normalize_rule_bundle(
                layer2_goal=layer2_goal,
                rule_candidate=rule_candidate,
                law_span=law_span,
                legal_frame=legal_frame,
            ),
            trace=trace,
            symbolic_checks={"issues": sym.issues, "codes": sym.error_codes},
        )

    def verify_backward(
        self,
        *,
        goal: dict[str, Any],
        selected_rule_id: str | None,
        requirements_ok: bool,
        backward_plan: dict[str, Any] | None = None,
        missing_facts: list[str] | None = None,
    ) -> VerificationRecord:
        sym = symbolic_backward(
            goal,
            selected_rule_id,
            backward_plan,
            requirements_ok=requirements_ok,
            missing_facts=missing_facts,
        )
        trace = ["symbolic_backward_done"]
        verbalized = {
            "premise": verbalize_backward_plan(goal, selected_rule_id),
            "hypothesis": verbalize_goal(goal),
        }
        nli: NLIResult | None = None
        if use_nli_for("backward_verification", nesy_nli_mock=self._nesy_nli_mock):
            nli = self._nli.verify(verbalized["premise"], verbalized["hypothesis"])
            trace.append("nli_backward")
        dec, fusion_diag = fuse_ne_sy_v5(
            symbolic_ok=sym.ok,
            nli=nli,
            entailment_threshold=self._entailment_threshold,
            contradiction_threshold=self._contradiction_threshold,
        )
        return _finalize_record(
            mode="backward_verification",
            symbolic_ok=sym.ok,
            sym_issues=sym.issues,
            error_codes=sym.error_codes,
            nli=nli,
            decision=dec,
            fusion_diag=fusion_diag,
            verbalized=verbalized,
            normalized=normalize_backward_bundle(
                goal=goal,
                selected_rule_id=selected_rule_id,
                backward_plan=backward_plan,
                missing_facts=missing_facts,
                requirements_ok=requirements_ok,
            ),
            trace=trace,
            symbolic_checks={"issues": sym.issues, "codes": sym.error_codes},
        )

    def verify_forward(
        self,
        *,
        goal: dict[str, Any],
        conclusion: str,
        goal_achieved: bool,
        known_facts: dict[str, Any] | None = None,
        forward_result: dict[str, Any] | None = None,
        proof: dict[str, Any] | None = None,
    ) -> VerificationRecord:
        sym = symbolic_forward(
            goal_achieved=goal_achieved,
            forward_result=forward_result,
            proof=proof,
            conclusion=conclusion,
        )
        trace = ["symbolic_forward_done"]
        verbalized = {
            "premise_goal": verbalize_goal(goal),
            "hypothesis_conclusion": conclusion,
            "forward_status": verbalize_forward_failure(forward_result or {}),
            "proof": verbalize_proof_brief(proof or {}),
        }
        premise = f"{verbalized['premise_goal']} {verbalized['forward_status']} {verbalized['proof']}"
        nli: NLIResult | None = None
        if use_nli_for("forward_verification", nesy_nli_mock=self._nesy_nli_mock):
            nli = self._nli.verify(premise, verbalized["hypothesis_conclusion"])
            trace.append("nli_forward")
        dec, fusion_diag = fuse_ne_sy_v5(
            symbolic_ok=sym.ok,
            nli=nli,
            entailment_threshold=self._entailment_threshold,
            contradiction_threshold=self._contradiction_threshold,
        )
        return _finalize_record(
            mode="forward_verification",
            symbolic_ok=sym.ok,
            sym_issues=sym.issues,
            error_codes=sym.error_codes,
            nli=nli,
            decision=dec,
            fusion_diag=fusion_diag,
            verbalized=verbalized,
            normalized=normalize_forward_bundle(
                goal=goal,
                conclusion=conclusion,
                goal_achieved=goal_achieved,
                known_facts=known_facts,
                forward_result=forward_result,
                proof=proof,
            ),
            trace=trace,
            symbolic_checks={"issues": sym.issues, "codes": sym.error_codes},
        )

    def verify_answer(
        self,
        *,
        answer_text: str,
        conclusion: str,
        proof: dict[str, Any] | None = None,
        modality_expected: str = "",
        goal_action: str = "",
        action_token_in_answer: str | None = None,
    ) -> VerificationRecord:
        sym_extra, diag_sym = check_answer_vs_goal(
            modality_expected=modality_expected,
            action_token_in_answer=action_token_in_answer or answer_text,
            goal_action=goal_action,
        )
        sym_sa = symbolic_answer_checks(symbolic_ok=sym_extra, diag_from_validator=diag_sym)
        sym_ok = sym_sa.ok
        trace = ["symbolic_answer_done"]
        verbalized = {"premise": conclusion, "hypothesis": answer_text}
        nli: NLIResult | None = None
        if use_nli_for("answer_verification", nesy_nli_mock=self._nesy_nli_mock):
            nli = self._nli.verify(conclusion, answer_text)
            trace.append("nli_answer")
        dec, fusion_diag = fuse_ne_sy_v5(
            symbolic_ok=sym_ok,
            nli=nli,
            entailment_threshold=self._entailment_threshold,
            contradiction_threshold=self._contradiction_threshold,
        )
        issues = list(sym_sa.issues)
        return _finalize_record(
            mode="answer_verification",
            symbolic_ok=sym_ok,
            sym_issues=issues,
            error_codes=sym_sa.error_codes,
            nli=nli,
            decision=dec,
            fusion_diag=fusion_diag,
            verbalized=verbalized,
            normalized=normalize_answer_bundle(
                answer_text=answer_text,
                conclusion=conclusion,
                proof=proof,
                symbolic_ok=sym_ok,
            ),
            trace=trace,
            symbolic_checks={"issues": issues, "codes": sym_sa.error_codes, "check_answer_vs_goal": diag_sym},
        )


def nesy_engine_singleton() -> NeSyEngine:
    return NeSyEngine()
