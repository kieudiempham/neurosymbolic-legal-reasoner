"""Auto repair loops — re-parse / re-layer2 or answer generator until ACCEPT/REJECT or max attempts."""

from __future__ import annotations

from typing import Any, Callable

from retrieval.rule_repair import reload_rule_from_index
from retrieval.rulebase_loader import RulebaseIndex
from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.reasoning import ReasoningState
from schemas.rule import RuleRecord
from schemas.verification import VerificationRecord
from verification.engine import NeSyEngine
from verification.repair_handlers import default_answer_regenerate, repair_parse_bundle
from verification.repair_routing import repair_target_for_code

PARSE_HANDLER_MODULE = "question_parser_or_layer2_builder"
ANSWER_HANDLER_MODULE = "answer_generator"
RULE_HANDLER_MODULE = "legal_frame_extractor_or_rule_builder"
BACKWARD_HANDLER_MODULE = "backward_reasoner"
FORWARD_HANDLER_MODULE = "forward_reasoner"
RETRIEVAL_HANDLER_MODULE = "retrieval_or_retrieval_ranking"

PARSE_HANDLER_TARGETS = {"parser", PARSE_HANDLER_MODULE}
ANSWER_HANDLER_TARGETS = {"answer_generation", ANSWER_HANDLER_MODULE}
BACKWARD_HANDLER_TARGETS = {"selected_rule_ranking", "backward_requirement_extraction", BACKWARD_HANDLER_MODULE}
FORWARD_HANDLER_TARGETS = {"forward_reasoner", "forward_proof_construction", FORWARD_HANDLER_MODULE}
RETRIEVAL_HANDLER_TARGETS = {"retrieval", RETRIEVAL_HANDLER_MODULE}


def _repair_action_log(
    *,
    verifier_mode: str,
    verdict: str,
    issue_type: str,
    repair_target: str,
    repair_action: str,
    rerun_result: str,
) -> dict[str, Any]:
    return {
        "verifier_mode": verifier_mode,
        "verdict": verdict,
        "issue_type": issue_type,
        "repair_target": repair_target,
        "repair_action": repair_action,
        "rerun_result": rerun_result,
    }


def _with_repair_metadata(
    rec: VerificationRecord,
    *,
    repair_applied: bool,
    rerun_stage: str | None,
    repair_diagnostics: dict[str, Any],
) -> VerificationRecord:
    return rec.model_copy(
        update={
            "decision": rec.final_decision,
            "reasons": list(rec.diagnostics),
            "repair_hints": [rec.repair_hint] if rec.repair_hint else [],
            "repair_applied": repair_applied,
            "rerun_stage": rerun_stage,
            "repair_diagnostics": repair_diagnostics,
        }
    )


def _first_error_code(rec: VerificationRecord) -> str | None:
    return rec.diagnostic_errors[0] if rec.diagnostic_errors else None


def _enforce_material_gain(
    rec: VerificationRecord,
    *,
    initial_decision: str,
    repair_attempted: bool,
    material_gain: bool,
    reason: str,
) -> VerificationRecord:
    if not repair_attempted:
        return rec
    if initial_decision == "ACCEPT":
        return rec
    if material_gain:
        return rec
    if rec.final_decision not in ("ACCEPT", "REPAIR"):
        return rec
    return rec.model_copy(
        update={
            "final_decision": "REJECT",
            "decision": "REJECT",
            "diagnostics": list(rec.diagnostics) + [reason],
        }
    )


def run_parse_repair_loop(
    engine: NeSyEngine,
    *,
    layer1: Layer1Parse,
    layer2: Layer2Parse,
    question_text: str,
    user_facts: list[str],
    max_repair_attempts_parse: int,
    repair_parse_fn: Callable[..., tuple[Layer1Parse, Layer2Parse, dict[str, Any]]] | None = None,
) -> tuple[Layer1Parse, Layer2Parse, VerificationRecord, list[dict[str, Any]]]:
    """
    Re-verify parse after REPAIR. Updates Layer1 when slot-aware LLM repair succeeds.
    """

    def _default_rp(
        q: str,
        l1: Layer1Parse,
        l2: Layer2Parse,
        uf: list[str],
        pl: dict[str, Any],
        *,
        repair_hint: str,
    ) -> tuple[Layer1Parse, Layer2Parse, dict[str, Any]]:
        return repair_parse_bundle(q, l1, l2, uf, pl, repair_hint=repair_hint)

    rp = repair_parse_fn or _default_rp
    trace: list[dict[str, Any]] = []
    l1 = layer1
    current = layer2
    last_rec = engine.verify_parse(l1, current, question_text=question_text)
    trace.append(
        {
            "phase": "parse",
            "attempt": 0,
            "decision": last_rec.final_decision,
            "repair_target_module": last_rec.repair_target_module,
            "input_snapshot": {"goal": dict(current.goal or {}), "layer1_focus": l1.question_focus},
            "diagnostic_errors": list(last_rec.diagnostic_errors),
            "auto_repair_eligible": False,
            **_repair_action_log(
                verifier_mode="parse_verification",
                verdict=last_rec.final_decision,
                issue_type=str(_first_error_code(last_rec) or "none"),
                repair_target=str(last_rec.repair_target_module or "unspecified"),
                repair_action="initial_verify",
                rerun_result="not_rerun",
            ),
        }
    )

    attempt = 0
    while last_rec.final_decision == "REPAIR" and attempt < max_repair_attempts_parse:
        code = _first_error_code(last_rec)
        target = repair_target_for_code(code or "")
        eligible = bool(code) and target in PARSE_HANDLER_TARGETS
        trace[-1]["auto_repair_eligible"] = eligible
        if not eligible:
            trace[-1]["note"] = "no_auto_repair_handler_or_wrong_target"
            break

        attempt += 1
        before = {"goal": dict(current.goal or {}), "layer1": l1.model_dump(mode="json")}
        hint = last_rec.repair_hint or ""
        l1_new, current, rt = rp(
            question_text,
            l1,
            current,
            list(user_facts),
            last_rec.repair_payload or {},
            repair_hint=hint,
        )
        l1 = l1_new
        after = {"goal": dict(current.goal or {}), "layer1": l1.model_dump(mode="json")}
        last_rec = engine.verify_parse(l1, current, question_text=question_text)
        trace.append(
            {
                "phase": "parse",
                "attempt": attempt,
                "decision": last_rec.final_decision,
                "repair_target_module": last_rec.repair_target_module,
                "input_snapshot": before,
                "output_snapshot": after,
                "diagnostic_errors": list(last_rec.diagnostic_errors),
                "repair_hint": hint,
                "repair_trace": rt,
                **_repair_action_log(
                    verifier_mode="parse_verification",
                    verdict=last_rec.final_decision,
                    issue_type=str(code or "none"),
                    repair_target=str(target or "unspecified"),
                    repair_action="repair_parse_bundle",
                    rerun_result="rerun_done",
                ),
            }
        )
        if last_rec.final_decision in ("ACCEPT", "REJECT"):
            break

    fields_changed: list[str] = []
    if trace[0].get("input_snapshot", {}).get("goal") != dict(current.goal or {}):
        fields_changed.append("goal")
    if trace[0].get("input_snapshot", {}).get("layer1_focus") != l1.question_focus:
        fields_changed.append("layer1_focus")

    final_gain = {
        "parse_improved": trace[0].get("decision") != last_rec.final_decision,
        "final_status_before": trace[0].get("decision"),
        "final_status_after": last_rec.final_decision,
        "goal_changed": "goal" in fields_changed,
        "repair_attempted": attempt > 0,
        "material_gain": bool(fields_changed),
        "fields_changed": fields_changed,
    }
    material_gain = bool(fields_changed)
    last_rec = _enforce_material_gain(
        last_rec,
        initial_decision=str(trace[0].get("decision") or "REJECT"),
        repair_attempted=attempt > 0,
        material_gain=material_gain,
        reason="repair_without_material_parse_gain",
    )
    final_gain["final_status_after"] = last_rec.final_decision
    root_cause = str(_first_error_code(last_rec) or "unknown")
    trace.append(
        {
            "phase": "parse",
            "final_decision": last_rec.final_decision,
            "attempts_used": attempt,
            "post_repair_gain": final_gain,
            "repair_attempted": attempt > 0,
            "material_gain": material_gain,
            "fields_changed": fields_changed,
            "root_cause": root_cause,
            **_repair_action_log(
                verifier_mode="parse_verification",
                verdict=last_rec.final_decision,
                issue_type=root_cause,
                repair_target=str(last_rec.repair_target_module or "unspecified"),
                repair_action=("stop_after_controlled_repair" if last_rec.final_decision != "ACCEPT" else "finalize_after_repair"),
                rerun_result=("failed" if last_rec.final_decision != "ACCEPT" else "accepted"),
            ),
        }
    )
    last_rec = _with_repair_metadata(
        last_rec,
        repair_applied=attempt > 0,
        rerun_stage="parse_verification" if attempt > 0 else None,
        repair_diagnostics={
            "decision": last_rec.final_decision,
            "reasons": list(last_rec.diagnostics),
            "repair_target": last_rec.repair_target,
            "repair_hints": [last_rec.repair_hint] if last_rec.repair_hint else [],
            "repair_applied": attempt > 0,
            "rerun_stage": "parse_verification" if attempt > 0 else None,
            "root_cause": root_cause,
            "before_after": {
                "parse_before": trace[0].get("input_snapshot"),
                "parse_after": {"goal": dict(current.goal or {}), "layer1": l1.model_dump(mode="json")},
                "verification_before": trace[0].get("decision"),
                "verification_after": last_rec.final_decision,
            },
            "post_repair_gain": final_gain,
        },
    )
    return l1, current, last_rec, trace


def run_forward_repair_loop(
    engine: NeSyEngine,
    *,
    goal: dict[str, Any],
    conclusion: str,
    goal_achieved: bool,
    known_facts: dict[str, Any],
    forward_state: Any,
    proof_obj: Any,
    forward_retry_fn: Callable[[], tuple[str, bool, Any, Any]],
    max_attempts: int,
    requirement_artifact: dict[str, Any] | None = None,
    selected_rule_id: str | None = None,
) -> tuple[str, bool, Any, Any, VerificationRecord, list[dict[str, Any]]]:
    """
    Re-verify forward + proof after REPAIR. For incomplete proofs in fact_application mode.
    """
    trace: list[dict[str, Any]] = []
    conc = conclusion
    gok = goal_achieved
    fst = forward_state
    pobj = proof_obj
    last_rec = engine.verify_forward(
        goal=goal,
        conclusion=conc,
        goal_achieved=gok,
        known_facts=known_facts,
        forward_result=fst.forward_result.model_dump(mode="json") if fst and fst.forward_result else None,
        proof=pobj.model_dump(mode="json") if pobj else None,
        requirement_artifact=requirement_artifact,
        selected_rule_id=selected_rule_id,
    )
    trace.append(
        {
            "phase": "forward",
            "attempt": 0,
            "decision": last_rec.final_decision,
            "repair_target_module": last_rec.repair_target_module,
            "input_snapshot": {"conclusion": conc[:200], "goal_achieved": gok},
            "diagnostic_errors": list(last_rec.diagnostic_errors),
            "auto_repair_eligible": False,
        }
    )

    attempt = 0
    while last_rec.final_decision == "REPAIR" and attempt < max_attempts:
        code = _first_error_code(last_rec)
        target = repair_target_for_code(code or "")
        eligible = bool(code) and target in FORWARD_HANDLER_TARGETS  # Assume defined
        trace[-1]["auto_repair_eligible"] = eligible
        if not eligible:
            trace[-1]["note"] = "no_auto_repair_handler_or_wrong_target"
            break

        attempt += 1
        before = {"conclusion": conc, "goal_achieved": gok}
        # For forward, retry the forward computation
        conc, gok, fst, pobj = forward_retry_fn()
        last_rec = engine.verify_forward(
            goal=goal,
            conclusion=conc,
            goal_achieved=gok,
            known_facts=known_facts,
            forward_result=fst.forward_result.model_dump(mode="json") if fst and fst.forward_result else None,
            proof=pobj.model_dump(mode="json") if pobj else None,
            requirement_artifact=requirement_artifact,
            selected_rule_id=selected_rule_id,
        )
        trace.append(
            {
                "phase": "forward",
                "attempt": attempt,
                "decision": last_rec.final_decision,
                "repair_target_module": last_rec.repair_target_module,
                "input_snapshot": before,
                "output_snapshot": {"conclusion": conc[:200], "goal_achieved": gok},
                "diagnostic_errors": list(last_rec.diagnostic_errors),
            }
        )
        if last_rec.final_decision in ("ACCEPT", "REJECT"):
            break

    final_gain = {
        "forward_improved": last_rec.final_decision != trace[0].get("decision"),
        "final_status_before": trace[0].get("decision"),
        "final_status_after": last_rec.final_decision,
        "repair_attempted": attempt > 0,
    }
    root_cause = str(_first_error_code(last_rec) or "unknown")
    trace.append(
        {
            "phase": "forward",
            "final_decision": last_rec.final_decision,
            "attempts_used": attempt,
            "post_repair_gain": final_gain,
            "root_cause": root_cause,
        }
    )
    last_rec = _with_repair_metadata(
        last_rec,
        repair_applied=attempt > 0,
        rerun_stage="forward_verification" if attempt > 0 else None,
        repair_diagnostics={
            "decision": last_rec.final_decision,
            "reasons": list(last_rec.diagnostics),
            "repair_target": last_rec.repair_target,
            "repair_hints": [last_rec.repair_hint] if last_rec.repair_hint else [],
            "repair_applied": attempt > 0,
            "rerun_stage": "forward_verification" if attempt > 0 else None,
            "root_cause": root_cause,
            "before_after": {
                "forward_before": trace[0].get("input_snapshot"),
                "forward_after": {"conclusion": conc, "goal_achieved": gok},
                "verification_before": trace[0].get("decision"),
                "verification_after": last_rec.final_decision,
            },
            "post_repair_gain": final_gain,
        },
    )
    return conc, gok, fst, pobj, last_rec, trace


def run_answer_repair_loop(
    engine: NeSyEngine,
    *,
    answer_text: str,
    conclusion: str,
    proof: dict[str, Any] | None,
    modality_expected: str,
    goal_action: str,
    action_token_in_answer: str | None,
    max_repair_attempts_answer: int,
    evidence_bundle: dict[str, Any] | None = None,
    regenerate_fn: Callable[[int, str, dict[str, Any]], str] | None = None,
    question_mode: str = "hybrid",
    missing_facts: list[str] | None = None,
) -> tuple[str, VerificationRecord, list[dict[str, Any]]]:
    trace: list[dict[str, Any]] = []
    text = answer_text
    last_rec = engine.verify_answer(
        answer_text=text,
        conclusion=conclusion,
        proof=proof,
        evidence_bundle=evidence_bundle,
        modality_expected=modality_expected,
        goal_action=goal_action,
        action_token_in_answer=action_token_in_answer or text,
        question_mode=question_mode,
        missing_facts=missing_facts,
    )
    regen = regenerate_fn or (lambda a, h, p: default_answer_regenerate(conclusion, a, h, p))

    trace.append(
        {
            "phase": "answer",
            "attempt": 0,
            "decision": last_rec.final_decision,
            "repair_target_module": last_rec.repair_target_module,
            "input_snapshot": {"answer_excerpt": text[:200]},
            "diagnostic_errors": list(last_rec.diagnostic_errors),
            "auto_repair_eligible": False,
            **_repair_action_log(
                verifier_mode="answer_verification",
                verdict=last_rec.final_decision,
                issue_type=str(_first_error_code(last_rec) or "none"),
                repair_target=str(last_rec.repair_target_module or "unspecified"),
                repair_action="initial_verify",
                rerun_result="not_rerun",
            ),
        }
    )

    attempt = 0
    while last_rec.final_decision == "REPAIR" and attempt < max_repair_attempts_answer:
        code = _first_error_code(last_rec)
        target = repair_target_for_code(code or "")
        eligible = bool(code) and target in ANSWER_HANDLER_TARGETS
        trace[-1]["auto_repair_eligible"] = eligible
        if not eligible:
            trace[-1]["note"] = "no_auto_repair_handler_or_wrong_target"
            break

        attempt += 1
        before = text
        hint = last_rec.repair_hint or ""
        payload = last_rec.repair_payload or {}
        text = regen(attempt, hint, payload)
        last_rec = engine.verify_answer(
            answer_text=text,
            conclusion=conclusion,
            proof=proof,
            evidence_bundle=evidence_bundle,
            modality_expected=modality_expected,
            goal_action=goal_action,
            action_token_in_answer=text,
            question_mode=question_mode,
            missing_facts=missing_facts,
        )
        trace.append(
            {
                "phase": "answer",
                "attempt": attempt,
                "decision": last_rec.final_decision,
                "repair_target_module": last_rec.repair_target_module,
                "input_snapshot": {"answer_excerpt": before[:200]},
                "output_snapshot": {"answer_excerpt": text[:200]},
                "diagnostic_errors": list(last_rec.diagnostic_errors),
                "repair_hint": hint,
                **_repair_action_log(
                    verifier_mode="answer_verification",
                    verdict=last_rec.final_decision,
                    issue_type=str(code or "none"),
                    repair_target=str(target or "unspecified"),
                    repair_action="regenerate_answer",
                    rerun_result="rerun_done",
                ),
            }
        )
        if last_rec.final_decision in ("ACCEPT", "REJECT"):
            break

    final_gain = {
        "answer_nonempty_before": bool(answer_text),
        "answer_nonempty_after": bool(text),
        "answer_improved": text != answer_text,
        "final_status_before": trace[0].get("decision"),
        "final_status_after": last_rec.final_decision,
    }
    root_cause = str(_first_error_code(last_rec) or "unknown")
    trace.append(
        {
            "phase": "answer",
            "final_decision": last_rec.final_decision,
            "attempts_used": attempt,
            "post_repair_gain": final_gain,
            "root_cause": root_cause,
            **_repair_action_log(
                verifier_mode="answer_verification",
                verdict=last_rec.final_decision,
                issue_type=root_cause,
                repair_target=str(last_rec.repair_target_module or "unspecified"),
                repair_action=("stop_after_controlled_repair" if last_rec.final_decision != "ACCEPT" else "finalize_after_repair"),
                rerun_result=("failed" if last_rec.final_decision != "ACCEPT" else "accepted"),
            ),
        }
    )
    last_rec = _with_repair_metadata(
        last_rec,
        repair_applied=attempt > 0,
        rerun_stage="answer_verification" if attempt > 0 else None,
        repair_diagnostics={
            "decision": last_rec.final_decision,
            "reasons": list(last_rec.diagnostics),
            "repair_target": last_rec.repair_target,
            "repair_hints": [last_rec.repair_hint] if last_rec.repair_hint else [],
            "repair_applied": attempt > 0,
            "rerun_stage": "answer_verification" if attempt > 0 else None,
            "root_cause": root_cause,
            "before_after": {
                "answer_before": answer_text,
                "answer_after": text,
                "verification_before": trace[0].get("decision"),
                "verification_after": last_rec.final_decision,
            },
            "post_repair_gain": final_gain,
        },
    )
    return text, last_rec, trace


def run_rule_repair_loop(
    engine: NeSyEngine,
    *,
    layer2_goal: dict[str, Any],
    rule_candidate: RuleRecord,
    law_span: str,
    legal_frame: str,
    rule_index: RulebaseIndex,
    max_attempts: int,
) -> tuple[RuleRecord, VerificationRecord, list[dict[str, Any]]]:
    """
    Reload canonical ``RuleRecord`` from the rulebase index (true rule-builder path for JSON rules).
    Re-verify until ACCEPT/REJECT or retries exhausted.
    """
    trace: list[dict[str, Any]] = []
    rule = rule_candidate
    last = engine.verify_rule(
        layer2_goal=layer2_goal,
        rule_candidate=rule,
        law_span=law_span or None,
        legal_frame=legal_frame,
    )
    trace.append(
        {
            "phase": "rule",
            "attempt": 0,
            "decision": last.final_decision,
            "rule_id": rule.rule_id,
            "repair_target_module": last.repair_target_module,
            "diagnostic_errors": list(last.diagnostic_errors),
            "action_taken": "initial_verify_rule",
            **_repair_action_log(
                verifier_mode="rule_verification",
                verdict=last.final_decision,
                issue_type=str(_first_error_code(last) or "none"),
                repair_target=str(last.repair_target_module or "unspecified"),
                repair_action="initial_verify",
                rerun_result="not_rerun",
            ),
        }
    )
    attempt = 0
    while last.final_decision == "REPAIR" and attempt < max_attempts:
        code = _first_error_code(last)
        if not code or repair_target_for_code(code) != RULE_HANDLER_MODULE:
            trace[-1]["note"] = "no_auto_repair_or_wrong_target"
            break
        attempt += 1
        reloaded = reload_rule_from_index(rule_index, rule.rule_id)
        if reloaded is None:
            trace.append({"phase": "rule", "attempt": attempt, "error": "rule_reload_failed", "rule_id": rule.rule_id})
            break
        rule = reloaded
        last = engine.verify_rule(
            layer2_goal=layer2_goal,
            rule_candidate=rule,
            law_span=(rule.source_ref_full or rule.source_ref) or law_span or None,
            legal_frame=legal_frame,
        )
        trace.append(
            {
                "phase": "rule",
                "attempt": attempt,
                "decision": last.final_decision,
                "rule_id": rule.rule_id,
                "action_taken": "reload_rule_from_rulebase_index",
                "diagnostic_errors": list(last.diagnostic_errors),
                **_repair_action_log(
                    verifier_mode="rule_verification",
                    verdict=last.final_decision,
                    issue_type=str(code or "none"),
                    repair_target=RULE_HANDLER_MODULE,
                    repair_action="reload_rule_from_index",
                    rerun_result="rerun_done",
                ),
            }
        )
        if last.final_decision in ("ACCEPT", "REJECT"):
            break

    fields_changed: list[str] = []
    if rule_candidate.rule_id != rule.rule_id:
        fields_changed.append("selected_rule")

    final_gain = {
        "selected_rule_before": rule_candidate.rule_id,
        "selected_rule_after": rule.rule_id,
        "selected_rule_improved": rule_candidate.rule_id != rule.rule_id,
        "final_status_before": trace[0].get("decision"),
        "final_status_after": last.final_decision,
        "repair_attempted": attempt > 0,
        "material_gain": bool(fields_changed),
        "fields_changed": fields_changed,
    }
    material_gain = bool(fields_changed)
    last = _enforce_material_gain(
        last,
        initial_decision=str(trace[0].get("decision") or "REJECT"),
        repair_attempted=attempt > 0,
        material_gain=material_gain,
        reason="repair_without_material_rule_gain",
    )
    trace.append(
        {
            "phase": "rule",
            "final_decision": last.final_decision,
            "attempts_used": attempt,
            "final_rule_id": rule.rule_id,
            "post_repair_gain": final_gain,
            "repair_attempted": attempt > 0,
            "material_gain": material_gain,
            "fields_changed": fields_changed,
            **_repair_action_log(
                verifier_mode="rule_verification",
                verdict=last.final_decision,
                issue_type=str(_first_error_code(last) or "none"),
                repair_target=str(last.repair_target_module or "unspecified"),
                repair_action=("stop_after_controlled_repair" if last.final_decision != "ACCEPT" else "finalize_after_repair"),
                rerun_result=("failed" if last.final_decision != "ACCEPT" else "accepted"),
            ),
        }
    )
    root_cause = str(_first_error_code(last) or "unknown")
    last = _with_repair_metadata(
        last,
        repair_applied=attempt > 0,
        rerun_stage="rule_verification" if attempt > 0 else None,
        repair_diagnostics={
            "decision": last.final_decision,
            "reasons": list(last.diagnostics),
            "repair_target": last.repair_target,
            "repair_hints": [last.repair_hint] if last.repair_hint else [],
            "repair_applied": attempt > 0,
            "rerun_stage": "rule_verification" if attempt > 0 else None,
            "root_cause": root_cause,
            "before_after": {
                "selected_rule_before": rule_candidate.rule_id,
                "selected_rule_after": rule.rule_id,
                "verification_before": trace[0].get("decision"),
                "verification_after": last.final_decision,
            },
            "post_repair_gain": final_gain,
        },
    )
    return rule, last, trace


def run_backward_repair_loop(
    engine: NeSyEngine,
    *,
    goal: dict[str, Any],
    selected_rule: RuleRecord,
    bstate: ReasoningState,
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    known_facts: dict[str, Any],
    max_attempts: int,
    run_backward_fn: Callable[..., tuple[RuleRecord | None, ReasoningState]] | None = None,
) -> tuple[RuleRecord | None, ReasoningState, VerificationRecord, list[dict[str, Any]]]:
    """Re-run backward with excluded ids when verification requests REPAIR."""
    from reasoning.backward_reasoner import run_backward as _rb

    rb = run_backward_fn or _rb
    trace: list[dict[str, Any]] = []
    sel = selected_rule
    st = bstate
    last = engine.verify_backward(
        goal=goal,
        selected_rule_id=sel.rule_id if sel else None,
        requirements_ok=st.can_continue_forward,
        backward_plan=st.backward_plan,
        missing_facts=st.missing_facts,
        requirement_keys=[r.key for r in st.requirement_set],
        requirement_artifact=(st.requirement_artifact.model_dump(mode="json") if st.requirement_artifact else None),
    )
    trace.append(
        {
            "phase": "backward",
            "attempt": 0,
            "decision": last.final_decision,
            "rule_id": sel.rule_id if sel else None,
            "repair_target_module": last.repair_target_module,
            "diagnostic_errors": list(last.diagnostic_errors),
            "action_taken": "initial_verify_backward",
            **_repair_action_log(
                verifier_mode="backward_verification",
                verdict=last.final_decision,
                issue_type=str(_first_error_code(last) or "none"),
                repair_target=str(last.repair_target_module or "unspecified"),
                repair_action="initial_verify",
                rerun_result="not_rerun",
            ),
        }
    )
    attempt = 0
    excluded: set[str] = set()
    while last.final_decision == "REPAIR" and attempt < max_attempts:
        code = _first_error_code(last)
        if not code or repair_target_for_code(code) not in BACKWARD_HANDLER_TARGETS:
            trace[-1]["note"] = "no_auto_repair_or_wrong_target"
            break
        attempt += 1
        excluded.add(sel.rule_id)
        sel2, st2 = rb(
            goal=goal,
            candidates=ranked,
            known_facts=known_facts,
            excluded_rule_ids=frozenset(excluded),
        )
        if not sel2:
            trace.append({"phase": "backward", "attempt": attempt, "error": "no_alternate_backward_rule"})
            break
        sel, st = sel2, st2
        last = engine.verify_backward(
            goal=goal,
            selected_rule_id=sel.rule_id,
            requirements_ok=st.can_continue_forward,
            backward_plan=st.backward_plan,
            missing_facts=st.missing_facts,
            requirement_keys=[r.key for r in st.requirement_set],
            requirement_artifact=(st.requirement_artifact.model_dump(mode="json") if st.requirement_artifact else None),
        )
        trace.append(
            {
                "phase": "backward",
                "attempt": attempt,
                "decision": last.final_decision,
                "rule_id": sel.rule_id,
                "action_taken": "run_backward_excluding_failed_ids",
                "excluded_rule_ids": list(excluded),
                "diagnostic_errors": list(last.diagnostic_errors),
                **_repair_action_log(
                    verifier_mode="backward_verification",
                    verdict=last.final_decision,
                    issue_type=str(code or "none"),
                    repair_target=str(repair_target_for_code(code)),
                    repair_action="rerank_selected_rule_and_rebuild_requirements",
                    rerun_result="rerun_done",
                ),
            }
        )
        if last.final_decision in ("ACCEPT", "REJECT"):
            break

    fields_changed: list[str] = []
    if (selected_rule.rule_id if selected_rule else None) != (sel.rule_id if sel else None):
        fields_changed.append("selected_rule")
    if bool((bstate.backward_plan or {}).get("candidates")) != bool((st.backward_plan or {}).get("candidates")):
        fields_changed.append("backward_plan_candidates")
    if list(bstate.missing_facts or []) != list(st.missing_facts or []):
        fields_changed.append("missing_facts")

    final_gain = {
        "selected_rule_before": selected_rule.rule_id if selected_rule else None,
        "selected_rule_after": sel.rule_id if sel else None,
        "selected_rule_improved": (selected_rule.rule_id if selected_rule else None) != (sel.rule_id if sel else None),
        "proof_nonempty_before": bool((bstate.backward_plan or {}).get("candidates")),
        "proof_nonempty_after": bool((st.backward_plan or {}).get("candidates")),
        "final_status_before": trace[0].get("decision"),
        "final_status_after": last.final_decision,
        "repair_attempted": attempt > 0,
        "material_gain": bool(fields_changed),
        "fields_changed": fields_changed,
    }
    material_gain = bool(fields_changed)
    last = _enforce_material_gain(
        last,
        initial_decision=str(trace[0].get("decision") or "REJECT"),
        repair_attempted=attempt > 0,
        material_gain=material_gain,
        reason="repair_without_material_backward_gain",
    )
    final_gain["final_status_after"] = last.final_decision
    trace.append(
        {
            "phase": "backward",
            "final_decision": last.final_decision,
            "attempts_used": attempt,
            "final_rule_id": sel.rule_id if sel else None,
            "post_repair_gain": final_gain,
            "repair_attempted": attempt > 0,
            "material_gain": material_gain,
            "fields_changed": fields_changed,
            **_repair_action_log(
                verifier_mode="backward_verification",
                verdict=last.final_decision,
                issue_type=str(_first_error_code(last) or "none"),
                repair_target=str(last.repair_target_module or "unspecified"),
                repair_action=("stop_after_controlled_repair" if last.final_decision != "ACCEPT" else "finalize_after_repair"),
                rerun_result=("failed" if last.final_decision != "ACCEPT" else "accepted"),
            ),
        }
    )
    root_cause = str(_first_error_code(last) or "unknown")
    last = _with_repair_metadata(
        last,
        repair_applied=attempt > 0,
        rerun_stage="backward_verification" if attempt > 0 else None,
        repair_diagnostics={
            "decision": last.final_decision,
            "reasons": list(last.diagnostics),
            "repair_target": last.repair_target,
            "repair_hints": [last.repair_hint] if last.repair_hint else [],
            "repair_applied": attempt > 0,
            "rerun_stage": "backward_verification" if attempt > 0 else None,
            "root_cause": root_cause,
            "before_after": {
                "selected_rule_before": selected_rule.rule_id if selected_rule else None,
                "selected_rule_after": sel.rule_id if sel else None,
                "proof_before": bstate.backward_plan,
                "proof_after": st.backward_plan,
                "verification_before": trace[0].get("decision"),
                "verification_after": last.final_decision,
            },
            "post_repair_gain": final_gain,
        },
    )
    return sel, st, last, trace


def run_forward_repair_loop(
    engine: NeSyEngine,
    *,
    goal: dict[str, Any],
    conclusion: str,
    goal_achieved: bool,
    known_facts: dict[str, Any],
    forward_state: Any,
    proof_obj: Any,
    forward_retry_fn: Callable[[], tuple[str, bool, Any, Any]],
    max_attempts: int,
    requirement_artifact: dict[str, Any] | None = None,
    selected_rule_id: str | None = None,
) -> tuple[str, bool, Any, Any, VerificationRecord, list[dict[str, Any]]]:
    """
    Re-run forward + proof construction when ``verify_forward`` returns REPAIR.
    ``forward_retry_fn`` must return ``(conclusion, goal_ok, forward_state, proof_object)``.
    """
    trace: list[dict[str, Any]] = []
    conc = conclusion
    gok = goal_achieved
    fst = forward_state
    pobj = proof_obj
    fr = fst.forward_result if fst is not None else None
    proof_dict = pobj.model_dump(mode="json") if hasattr(pobj, "model_dump") else pobj
    last = engine.verify_forward(
        goal=goal,
        conclusion=conc,
        goal_achieved=gok,
        known_facts=known_facts,
        forward_result=fr,
        proof=proof_dict if isinstance(proof_dict, dict) else None,
        requirement_artifact=requirement_artifact,
        selected_rule_id=selected_rule_id,
    )
    trace.append(
        {
            "phase": "forward",
            "attempt": 0,
            "decision": last.final_decision,
            "repair_target_module": last.repair_target_module,
            "diagnostic_errors": list(last.diagnostic_errors),
            "action_taken": "initial_verify_forward",
            **_repair_action_log(
                verifier_mode="forward_verification",
                verdict=last.final_decision,
                issue_type=str(_first_error_code(last) or "none"),
                repair_target=str(last.repair_target_module or "unspecified"),
                repair_action="initial_verify",
                rerun_result="not_rerun",
            ),
        }
    )
    attempt = 0
    while last.final_decision == "REPAIR" and attempt < max_attempts:
        code = _first_error_code(last)
        if not code or repair_target_for_code(code) not in FORWARD_HANDLER_TARGETS:
            trace[-1]["note"] = "no_auto_repair_or_wrong_target"
            break
        attempt += 1
        conc, gok, fst, pobj = forward_retry_fn()
        fr = fst.forward_result if fst is not None else None
        proof_dict = pobj.model_dump(mode="json") if hasattr(pobj, "model_dump") else pobj
        last = engine.verify_forward(
            goal=goal,
            conclusion=conc,
            goal_achieved=gok,
            known_facts=known_facts,
            forward_result=fr,
            proof=proof_dict if isinstance(proof_dict, dict) else None,
            requirement_artifact=requirement_artifact,
            selected_rule_id=selected_rule_id,
        )
        trace.append(
            {
                "phase": "forward",
                "attempt": attempt,
                "decision": last.final_decision,
                "action_taken": "forward_retry_fn_rerun",
                "diagnostic_errors": list(last.diagnostic_errors),
                **_repair_action_log(
                    verifier_mode="forward_verification",
                    verdict=last.final_decision,
                    issue_type=str(code or "none"),
                    repair_target=str(repair_target_for_code(code)),
                    repair_action="rerun_forward_and_rebuild_proof",
                    rerun_result="rerun_done",
                ),
            }
        )
        if last.final_decision in ("ACCEPT", "REJECT"):
            break

    fields_changed: list[str] = []
    if conc != conclusion:
        fields_changed.append("conclusion")
    if bool(proof_obj) != bool(pobj):
        fields_changed.append("proof_presence")
    if bool(getattr(forward_state, "forward_result", None)) != bool(getattr(fst, "forward_result", None)):
        fields_changed.append("forward_result")

    final_gain = {
        "proof_nonempty_before": bool(proof_obj),
        "proof_nonempty_after": bool(pobj),
        "conclusion_improved": conc != conclusion,
        "final_status_before": trace[0].get("decision"),
        "final_status_after": last.final_decision,
        "repair_attempted": attempt > 0,
        "material_gain": bool(fields_changed),
        "fields_changed": fields_changed,
    }
    material_gain = bool(fields_changed)
    last = _enforce_material_gain(
        last,
        initial_decision=str(trace[0].get("decision") or "REJECT"),
        repair_attempted=attempt > 0,
        material_gain=material_gain,
        reason="repair_without_material_forward_gain",
    )
    final_gain["final_status_after"] = last.final_decision
    root_cause = str(_first_error_code(last) or "unknown")
    trace.append(
        {
            "phase": "forward",
            "final_decision": last.final_decision,
            "attempts_used": attempt,
            "post_repair_gain": final_gain,
            "repair_attempted": attempt > 0,
            "material_gain": material_gain,
            "fields_changed": fields_changed,
            "root_cause": root_cause,
            **_repair_action_log(
                verifier_mode="forward_verification",
                verdict=last.final_decision,
                issue_type=root_cause,
                repair_target=str(last.repair_target_module or "unspecified"),
                repair_action=("stop_after_controlled_repair" if last.final_decision != "ACCEPT" else "finalize_after_repair"),
                rerun_result=("failed" if last.final_decision != "ACCEPT" else "accepted"),
            ),
        }
    )
    last = _with_repair_metadata(
        last,
        repair_applied=attempt > 0,
        rerun_stage="forward_verification" if attempt > 0 else None,
        repair_diagnostics={
            "decision": last.final_decision,
            "reasons": list(last.diagnostics),
            "repair_target": last.repair_target,
            "repair_hints": [last.repair_hint] if last.repair_hint else [],
            "repair_applied": attempt > 0,
            "rerun_stage": "forward_verification" if attempt > 0 else None,
            "root_cause": root_cause,
            "before_after": {
                "proof_before": proof_obj.model_dump(mode="json") if hasattr(proof_obj, "model_dump") else proof_obj,
                "proof_after": pobj.model_dump(mode="json") if hasattr(pobj, "model_dump") else pobj,
                "verification_before": trace[0].get("decision"),
                "verification_after": last.final_decision,
            },
            "post_repair_gain": final_gain,
        },
    )
    return conc, gok, fst, pobj, last, trace


def run_retrieval_repair_loop(
    *,
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]],
    top_k_before: int,
    repair_reason: str,
    retrieve_retry_fn: Callable[[int], list[tuple[RuleRecord, float, dict[str, Any]]]],
    max_attempts: int = 1,
) -> tuple[list[tuple[RuleRecord, float, dict[str, Any]]], list[dict[str, Any]], dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    current = list(ranked)
    trace.append(
        {
            "phase": "retrieval_ranking",
            "attempt": 0,
            "decision": "ACCEPT" if current else "REPAIR",
            "reasons": [repair_reason] if repair_reason else [],
            "repair_target": "retrieval_ranking",
            "repair_hints": ["widen_top_k_and_retry_candidate_selection"],
            "repair_applied": False,
            "rerun_stage": None,
            "before_after": {
                "retrieved_count_before": len(current),
                "top_rule_ids_before": [r.rule_id for r, _, _ in current[:8]],
            },
            **_repair_action_log(
                verifier_mode="retrieval_verification",
                verdict="ACCEPT" if current else "REPAIR",
                issue_type="retrieval_ranking_error" if not current else "none",
                repair_target="retrieval",
                repair_action="initial_retrieval_check",
                rerun_result="not_rerun",
            ),
        }
    )
    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        retried = retrieve_retry_fn(attempt)
        improved = len(retried) > len(current)
        trace.append(
            {
                "phase": "retrieval_ranking",
                "attempt": attempt,
                "decision": "ACCEPT" if retried else "REJECT",
                "reasons": [repair_reason] if repair_reason else [],
                "repair_target": "retrieval_ranking",
                "repair_hints": ["widen_top_k_and_retry_candidate_selection"],
                "repair_applied": True,
                "rerun_stage": "retrieve_rules",
                "action_taken": f"retry_retrieval_with_top_k={top_k_before * (attempt + 1)}",
                "before_after": {
                    "retrieved_count_before": len(current),
                    "retrieved_count_after": len(retried),
                    "top_rule_ids_before": [r.rule_id for r, _, _ in current[:8]],
                    "top_rule_ids_after": [r.rule_id for r, _, _ in retried[:8]],
                },
                "post_repair_gain": {
                    "retrieval_improved": improved,
                    "final_status_before": trace[0].get("decision"),
                    "final_status_after": "ACCEPT" if retried else "REJECT",
                },
                **_repair_action_log(
                    verifier_mode="retrieval_verification",
                    verdict="ACCEPT" if retried else "REJECT",
                    issue_type="retrieval_ranking_error",
                    repair_target="retrieval",
                    repair_action="widen_topk_and_rerank",
                    rerun_result="rerun_done",
                ),
            }
        )
        current = retried
        if current:
            break

    summary = {
        "decision": "ACCEPT" if current else "REJECT",
        "reasons": [repair_reason] if repair_reason else [],
        "repair_target": "retrieval_ranking",
        "repair_hints": ["widen_top_k_and_retry_candidate_selection"],
        "repair_applied": attempt > 0,
        "rerun_stage": "retrieve_rules" if attempt > 0 else None,
        "post_repair_gain": trace[-1].get("post_repair_gain", {}) if trace else {},
        **_repair_action_log(
            verifier_mode="retrieval_verification",
            verdict="ACCEPT" if current else "REJECT",
            issue_type="retrieval_ranking_error" if not current else "none",
            repair_target="retrieval",
            repair_action=("stop_after_controlled_repair" if not current else "finalize_after_repair"),
            rerun_result=("failed" if not current else "accepted"),
        ),
    }
    return current, trace, summary
