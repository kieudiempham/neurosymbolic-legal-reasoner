"""NeSy Verify Engine v5 — multi-mode: NLI + symbolic + fusion + diagnostics + repair routing."""

from __future__ import annotations

from typing import Any

from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord
from schemas.verification import FusionDecision, NLIResult, VerificationMode, VerificationRecord
from verification.controlled_verbalizer import (
    verbalization_guardrails,
    verbalize_answer_mode,
    verbalize_backward_mode,
    verbalize_forward_mode,
    verbalize_goal,
    verbalize_layer1_subject,
    verbalize_parse_mode,
    verbalize_rule_mode,
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
from verification.symbolic_check_types import SymbolicCheckResult
from verification.symbolic_modes import (
    symbolic_answer_checks,
    symbolic_backward,
    symbolic_forward,
    symbolic_parse,
    symbolic_rule,
)
from verification.symbolic_validator import check_answer_vs_goal


def _first_code(codes: list[str]) -> str | None:
    return codes[0] if codes else None


def _sym_dict(sym: SymbolicCheckResult) -> dict[str, Any]:
    return {"ok": sym.ok, "issues": sym.issues, "codes": sym.error_codes, "checks": sym.checks}


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
    verbalization_meta: dict[str, Any] | None = None,
    record_extra: dict[str, Any] | None = None,
    nli_trace: dict[str, Any] | None = None,
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
    extra = dict(record_extra or {})
    if verbalization_meta:
        extra["verbalization_meta"] = verbalization_meta
    if nli_trace:
        extra["nli_trace"] = nli_trace
    return VerificationRecord(
        mode=mode,
        symbolic_result="ok" if symbolic_ok else "failed",
        symbolic_ok=symbolic_ok,
        nli_result=nli,
        final_decision=decision,
        decision=decision,
        diagnostics=diag,
        reasons=list(diag),
        repair_target=repair_legacy,
        diagnostic_errors=list(error_codes),
        repair_target_module=rt_mod,
        repair_hint=hint,
        repair_hints=[hint] if hint else [],
        repair_payload=payload,
        repair_applied=False,
        rerun_stage=None,
        repair_diagnostics={
            "decision": decision,
            "reasons": list(diag),
            "repair_target": repair_legacy,
            "repair_target_module": rt_mod,
            "repair_hints": [hint] if hint else [],
            "repair_applied": False,
            "rerun_stage": None,
        },
        semantic_scores=semantic_scores or nli_scores,
        symbolic_checks=symbolic_checks,
        normalized_inputs=normalized,
        verbalized_texts=verbalized,
        trace=trace,
        extra=extra,
    )


class NeSyEngine:
    """Multi-mode NeSy verification — single source of truth for runtime."""

    def __init__(
        self,
        nli: NLIVerifier | None = None,
        *,
        nesy_nli_mock: bool = False,
        nli_degraded: bool = False,
        nli_meta: dict[str, Any] | None = None,
        entailment_threshold: float = 0.70,
        contradiction_threshold: float = 0.70,
    ) -> None:
        self._nli = nli if nli is not None else MockNLIVerifier()
        self._nesy_nli_mock = nesy_nli_mock
        self._nli_degraded = nli_degraded
        self._nli_meta = dict(nli_meta or {})
        self._entailment_threshold = entailment_threshold
        self._contradiction_threshold = contradiction_threshold

    def _nli_trace_bundle(self, mode: VerificationMode, nli: NLIResult | None) -> dict[str, Any]:
        will_run = use_nli_for(mode, nesy_nli_mock=self._nesy_nli_mock, nli_degraded=self._nli_degraded)
        meta = dict(self._nli_meta)
        status = "ok"
        if self._nli_degraded:
            status = "degraded_symbolic_only"
        elif not will_run and self._nesy_nli_mock:
            status = "skipped_by_policy"
        elif not will_run:
            status = "skipped"
        if will_run and nli is not None:
            status = "ok"
        out: dict[str, Any] = {
            "mode": mode,
            "nli_enabled": will_run,
            "nli_status": status,
            "nli_provider": meta.get("nli_provider", "unknown"),
            "nli_model_name": meta.get("nli_model_name"),
        }
        if nli and nli.scores:
            out["entailment"] = float(nli.scores.get("entailment", 0.0))
            out["contradiction"] = float(nli.scores.get("contradiction", 0.0))
            out["neutral"] = float(nli.scores.get("neutral", 0.0))
        elif nli:
            out["nli_label"] = nli.label
            out["nli_score"] = float(nli.score)
        return out

    def verify_parse(
        self,
        layer1: Layer1Parse,
        layer2: Layer2Parse,
        *,
        question_text: str = "",
    ) -> VerificationRecord:
        sym = symbolic_parse(question_text, layer1, layer2)
        trace = ["symbolic_parse_done"]
        prem, hyp, tmpl = verbalize_parse_mode(question_text, layer1, layer2)
        verbalized: dict[str, str] = {
            "premise": prem,
            "hypothesis": hyp,
            "premise_alignment": prem,
            "hypothesis_goal": hyp,
            "layer1_subject": verbalize_layer1_subject(layer1.subject_text or "chủ_thể"),
        }
        gr = verbalization_guardrails(
            mode="parse_verification",
            layer1=layer1,
            layer2=layer2,
            premise=prem,
            hypothesis=hyp,
        )
        meta = {"template": tmpl, "guardrails": gr, "premise": prem, "hypothesis": hyp}
        nli: NLIResult | None = None
        if use_nli_for("parse_verification", nesy_nli_mock=self._nesy_nli_mock, nli_degraded=self._nli_degraded):
            nli = self._nli.verify(prem, hyp)
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
            symbolic_checks=_sym_dict(sym),
            verbalization_meta=meta,
            nli_trace=self._nli_trace_bundle("parse_verification", nli),
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
        prem, hyp, tmpl = verbalize_rule_mode(law_span, legal_frame, rule_candidate)
        verbalized: dict[str, str] = {
            "premise": prem,
            "hypothesis": hyp,
            "premise_law": prem,
            "hypothesis_rule": hyp,
        }
        gr = verbalization_guardrails(
            mode="rule_verification",
            goal=layer2_goal,
            premise=prem,
            hypothesis=hyp,
        )
        meta = {"template": tmpl, "guardrails": gr, "premise": prem, "hypothesis": hyp}
        nli: NLIResult | None = None
        if use_nli_for("rule_verification", nesy_nli_mock=self._nesy_nli_mock, nli_degraded=self._nli_degraded):
            nli = self._nli.verify(prem, hyp)
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
            symbolic_checks=_sym_dict(sym),
            verbalization_meta=meta,
            nli_trace=self._nli_trace_bundle("rule_verification", nli),
        )

    def verify_backward(
        self,
        *,
        goal: dict[str, Any],
        selected_rule_id: str | None,
        requirements_ok: bool,
        backward_plan: dict[str, Any] | None = None,
        missing_facts: list[str] | None = None,
        requirement_keys: list[str] | None = None,
        requirement_artifact: dict[str, Any] | None = None,
    ) -> VerificationRecord:
        sym = symbolic_backward(
            goal,
            selected_rule_id,
            backward_plan,
            requirements_ok=requirements_ok,
            missing_facts=missing_facts,
            requirement_keys=requirement_keys,
            requirement_artifact=requirement_artifact,
        )
        trace = ["symbolic_backward_done"]
        prem, hyp, tmpl = verbalize_backward_mode(goal, selected_rule_id, backward_plan, missing_facts)
        verbalized = {"premise": prem, "hypothesis": hyp}
        gr = verbalization_guardrails(mode="backward_verification", goal=goal, premise=prem, hypothesis=hyp)
        meta = {"template": tmpl, "guardrails": gr, "premise": prem, "hypothesis": hyp}
        nli: NLIResult | None = None
        if use_nli_for("backward_verification", nesy_nli_mock=self._nesy_nli_mock, nli_degraded=self._nli_degraded):
            nli = self._nli.verify(prem, hyp)
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
                requirement_artifact=requirement_artifact,
            ),
            trace=trace,
            symbolic_checks=_sym_dict(sym),
            verbalization_meta=meta,
            nli_trace=self._nli_trace_bundle("backward_verification", nli),
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
        requirement_artifact: dict[str, Any] | None = None,
        selected_rule_id: str | None = None,
    ) -> VerificationRecord:
        sym = symbolic_forward(
            goal_achieved=goal_achieved,
            forward_result=forward_result,
            proof=proof,
            conclusion=conclusion,
            goal=goal,
            requirement_artifact=requirement_artifact,
            selected_rule_id=selected_rule_id,
        )
        trace = ["symbolic_forward_done"]
        prem, hyp, tmpl = verbalize_forward_mode(goal, known_facts, proof, forward_result, conclusion)
        verbalized = {
            "premise": prem,
            "hypothesis": hyp,
            "premise_goal": verbalize_goal(goal),
            "hypothesis_conclusion": conclusion,
        }
        gr = verbalization_guardrails(mode="forward_verification", goal=goal, premise=prem, hypothesis=hyp)
        meta = {"template": tmpl, "guardrails": gr, "premise": prem, "hypothesis": hyp}
        nli: NLIResult | None = None
        if use_nli_for("forward_verification", nesy_nli_mock=self._nesy_nli_mock, nli_degraded=self._nli_degraded):
            nli = self._nli.verify(prem, hyp)
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
                requirement_artifact=requirement_artifact,
                selected_rule_id=selected_rule_id,
            ),
            trace=trace,
            symbolic_checks=_sym_dict(sym),
            verbalization_meta=meta,
            nli_trace=self._nli_trace_bundle("forward_verification", nli),
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
        sym_sa = symbolic_answer_checks(
            symbolic_ok=sym_extra,
            diag_from_validator=diag_sym,
            answer_text=answer_text,
            conclusion=conclusion,
            proof=proof,
        )
        sym_ok = sym_sa.ok
        trace = ["symbolic_answer_done"]
        prem, hyp, tmpl = verbalize_answer_mode(answer_text, conclusion, proof)
        verbalized = {"premise": prem, "hypothesis": hyp}
        gr = verbalization_guardrails(
            mode="answer_verification",
            premise=prem,
            hypothesis=hyp,
            conclusion=conclusion,
        )
        meta = {"template": tmpl, "guardrails": gr, "premise": prem, "hypothesis": hyp}
        nli: NLIResult | None = None
        if use_nli_for("answer_verification", nesy_nli_mock=self._nesy_nli_mock, nli_degraded=self._nli_degraded):
            nli = self._nli.verify(prem, hyp)
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
            symbolic_checks={**_sym_dict(sym_sa), "check_answer_vs_goal": diag_sym},
            verbalization_meta=meta,
            nli_trace=self._nli_trace_bundle("answer_verification", nli),
        )


def nesy_engine_singleton() -> NeSyEngine:
    return NeSyEngine(nesy_nli_mock=True)
