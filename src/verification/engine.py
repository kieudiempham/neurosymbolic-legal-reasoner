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


def _nli_scores(nli: NLIResult | None) -> tuple[float, float, float]:
    if nli is None:
        return 0.0, 0.0, 0.0
    if nli.scores:
        return (
            float(nli.scores.get("entailment", 0.0)),
            float(nli.scores.get("neutral", 0.0)),
            float(nli.scores.get("contradiction", 0.0)),
        )
    if nli.label == "entailment":
        return float(nli.score), 0.0, 0.0
    if nli.label == "contradiction":
        return 0.0, 0.0, float(nli.score)
    return 0.0, float(nli.score), 0.0


def _fuse_with_policy(
    *,
    mode: VerificationMode,
    symbolic_ok: bool,
    error_codes: list[str],
    nli: NLIResult | None,
    entailment_threshold: float,
    contradiction_threshold: float,
    parse_focus: str | None = None,
    parse_action: str | None = None,
    parse_action_hint: str | None = None,
    parse_goal_action: str | None = None,
    application_status: str = "final",
) -> tuple[FusionDecision, list[str]]:
    decision, fusion_diag = fuse_ne_sy_v5(
        symbolic_ok=symbolic_ok,
        nli=nli,
        entailment_threshold=entailment_threshold,
        contradiction_threshold=contradiction_threshold,
    )
    diag = list(fusion_diag)
    e, neu, c = _nli_scores(nli)

    if decision == "ACCEPT" and not symbolic_ok:
        decision = "REPAIR"
        diag.append("fusion_policy_no_accept_when_symbolic_failed")

    contradiction_flag = bool(
        (nli is not None and c >= contradiction_threshold)
        or (nli is not None and nli.label == "contradiction" and max(float(nli.score), c) >= 0.35)
    )
    parse_soft_guard = mode == "parse_verification" and symbolic_ok and parse_focus in {"deadline", "obligation"}

    legal_focus = (parse_focus or "").strip().lower() in {"legal_consequence", "legal_effect"}
    legal_tokens = {
        "hau_qua_phap_ly",
        "che_tai_ap_dung",
        "gia_tri_phap_ly",
        "bi_xu_ly",
        "xu_phat",
        "vo_hieu",
    }
    action_blob = f"{(parse_action or '').strip().lower()} {(parse_action_hint or '').strip().lower()}"
    legal_action_usable = any(tok in action_blob for tok in legal_tokens)
    goal_action = (parse_goal_action or "").strip().lower()
    legal_goal_action_known = bool(goal_action and goal_action not in {"unknown", "hanh_vi"})

    # Parse stage is an availability gate; avoid hard reject for contradiction-only conflicts
    # when symbolic parse is structurally valid for common deadline/obligation questions.
    if contradiction_flag and parse_soft_guard and decision == "REJECT":
        decision = "REPAIR"
        diag.append("fusion_policy_parse_contradiction_high_guarded_repair")

    if (
        contradiction_flag
        and decision == "REJECT"
        and mode == "parse_verification"
        and symbolic_ok
        and legal_focus
        and legal_action_usable
        and legal_goal_action_known
    ):
        decision = "REPAIR"
        diag.append("fusion_policy_parse_legal_effect_bounded_soft_repair")

    if contradiction_flag and decision != "REJECT":
        # Parse stage is used as an availability gate; keep symbolic-pass samples alive.
        if mode == "parse_verification" and symbolic_ok:
            decision = "REPAIR"
            diag.append("fusion_policy_parse_contradiction_soft_repair")
        else:
            decision = "REJECT"
            diag.append("fusion_policy_contradiction_hard_reject")

    if mode in {"parse_verification", "backward_verification", "forward_verification"} and decision == "ACCEPT":
        if nli is not None and neu >= max(e, c, 0.45):
            decision = "REPAIR"
            diag.append("fusion_policy_neutral_requires_repair")

    if mode == "backward_verification" and (
        "backward_semantic_family_mismatch" in error_codes or "backward_weak_grounding" in error_codes
    ):
        if decision != "REJECT":
            diag.append("fusion_policy_backward_semantic_guard_reject")
        decision = "REJECT"

    if mode == "forward_verification" and "forward_proof_error" in error_codes:
        # Conditional answers legitimately have incomplete proofs (missing facts not yet resolved).
        if application_status == "conditional":
            if decision == "ACCEPT":
                decision = "REPAIR"
            diag.append("fusion_policy_forward_proof_conditional_soft_repair")
        else:
            if decision != "REJECT":
                diag.append("fusion_policy_forward_proof_guard_reject")
            decision = "REJECT"

    # Grounded conditional (A+B) and rule-reading (A) answers are valid end states.
    # Only reject them for true NLI contradiction or hallucination — not for missing-fact failures.
    # answer_semantic_drift is NOT a missing-fact code: it means the conclusion is absent from the
    # answer text entirely, which is a genuine content problem even for conditional answers.
    _missing_fact_codes = {
        "answer_subject_action_mismatch",
        "answer_time_quantity_mismatch",
    }
    _has_non_missing_fact_error = bool(
        set(error_codes) - _missing_fact_codes
    ) if error_codes else False
    if (
        mode == "answer_verification"
        and decision == "REJECT"
        and application_status in {"conditional", "none"}
        and not contradiction_flag
        and not _has_non_missing_fact_error
        and (symbolic_ok or (not error_codes or set(error_codes) <= _missing_fact_codes))
    ):
        decision = "ACCEPT"
        diag.append("fusion_policy_conditional_answer_grounded_accept")

    return decision, diag


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

    def _nli_trace_bundle(
        self,
        mode: VerificationMode,
        nli: NLIResult | None,
        *,
        premise: str | None = None,
        hypothesis: str | None = None,
    ) -> dict[str, Any]:
        """
        Comprehensive NLI trace: backend info, entailment/neutral/contradiction scores, input texts, and decision status.

        Covers all five verification modes with explicit status:
        - "ok": NLI ran, nli.label present
        - "degraded_symbolic_only": NLI disabled due to nli_degraded flag
        - "skipped_by_policy": NLI policy (mock mode) disables this mode
        - "skipped": NLI policy allows this mode but None verifier  (symmetric case)
        """
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
        if premise is not None:
            out["premise"] = premise
        if hypothesis is not None:
            out["hypothesis"] = hypothesis
        if nli and nli.scores:
            out["nli_decision"] = nli.label
            out["entailment"] = float(nli.scores.get("entailment", 0.0))
            out["contradiction"] = float(nli.scores.get("contradiction", 0.0))
            out["neutral"] = float(nli.scores.get("neutral", 0.0))
        elif nli:
            out["nli_decision"] = nli.label
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
        goal_args = list((layer2.goal or {}).get("args") or [])
        goal_action = str(goal_args[1]) if len(goal_args) >= 2 else ""
        l1_meta = dict(layer1.parse_metadata or {})
        dec, fusion_diag = _fuse_with_policy(
            mode="parse_verification",
            symbolic_ok=sym.ok,
            error_codes=sym.error_codes,
            nli=nli,
            entailment_threshold=self._entailment_threshold,
            contradiction_threshold=self._contradiction_threshold,
            parse_focus=layer1.question_focus,
            parse_action=layer1.action_text,
            parse_action_hint=str(l1_meta.get("action_canonical_hint") or l1_meta.get("used_fallback_label") or ""),
            parse_goal_action=goal_action,
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
            nli_trace=self._nli_trace_bundle("parse_verification", nli, premise=prem, hypothesis=hyp),
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
        dec, fusion_diag = _fuse_with_policy(
            mode="rule_verification",
            symbolic_ok=sym.ok,
            error_codes=sym.error_codes,
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
            nli_trace=self._nli_trace_bundle("rule_verification", nli, premise=prem, hypothesis=hyp),
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
        dec, fusion_diag = _fuse_with_policy(
            mode="backward_verification",
            symbolic_ok=sym.ok,
            error_codes=sym.error_codes,
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
            nli_trace=self._nli_trace_bundle("backward_verification", nli, premise=prem, hypothesis=hyp),
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
        dec, fusion_diag = _fuse_with_policy(
            mode="forward_verification",
            symbolic_ok=sym.ok,
            error_codes=sym.error_codes,
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
            nli_trace=self._nli_trace_bundle("forward_verification", nli, premise=prem, hypothesis=hyp),
        )

    def verify_answer(
        self,
        *,
        answer_text: str,
        conclusion: str,
        proof: dict[str, Any] | None = None,
        evidence_bundle: dict[str, Any] | None = None,
        modality_expected: str = "",
        goal_action: str = "",
        action_token_in_answer: str | None = None,
        question_mode: str = "hybrid",
        missing_facts: list[str] | None = None,
    ) -> VerificationRecord:
        # Derive application_status from question_mode and missing_facts so downstream
        # fusion policy can distinguish A / A+B / A+C without schema changes.
        if question_mode == "rule_reading":
            application_status = "none"
        elif missing_facts:
            application_status = "conditional"
        else:
            application_status = "final"

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
            application_status=application_status,
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
        dec, fusion_diag = _fuse_with_policy(
            mode="answer_verification",
            symbolic_ok=sym_ok,
            error_codes=sym_sa.error_codes,
            nli=nli,
            entailment_threshold=self._entailment_threshold,
            contradiction_threshold=self._contradiction_threshold,
            application_status=application_status,
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
                evidence_bundle=evidence_bundle,
                symbolic_ok=sym_ok,
            ),
            trace=trace,
            symbolic_checks={**_sym_dict(sym_sa), "check_answer_vs_goal": diag_sym},
            verbalization_meta=meta,
            nli_trace=self._nli_trace_bundle("answer_verification", nli, premise=prem, hypothesis=hyp),
        )


def nesy_engine_singleton() -> NeSyEngine:
    return NeSyEngine(nesy_nli_mock=True)
