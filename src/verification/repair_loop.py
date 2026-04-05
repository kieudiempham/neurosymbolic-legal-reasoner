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


def _first_error_code(rec: VerificationRecord) -> str | None:
    return rec.diagnostic_errors[0] if rec.diagnostic_errors else None


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
        }
    )

    attempt = 0
    while (
        last_rec.final_decision == "REPAIR"
        and attempt < max_repair_attempts_parse
    ):
        code = _first_error_code(last_rec)
        target = repair_target_for_code(code or "")
        eligible = bool(code) and target == PARSE_HANDLER_MODULE
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
            }
        )
        if last_rec.final_decision in ("ACCEPT", "REJECT"):
            break

    trace.append({"phase": "parse", "final_decision": last_rec.final_decision, "attempts_used": attempt})
    return l1, current, last_rec, trace


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
    regenerate_fn: Callable[[int, str, dict[str, Any]], str] | None = None,
) -> tuple[str, VerificationRecord, list[dict[str, Any]]]:
    trace: list[dict[str, Any]] = []
    text = answer_text
    last_rec = engine.verify_answer(
        answer_text=text,
        conclusion=conclusion,
        proof=proof,
        modality_expected=modality_expected,
        goal_action=goal_action,
        action_token_in_answer=action_token_in_answer or text,
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
        }
    )

    attempt = 0
    while last_rec.final_decision == "REPAIR" and attempt < max_repair_attempts_answer:
        code = _first_error_code(last_rec)
        target = repair_target_for_code(code or "")
        eligible = bool(code) and target == ANSWER_HANDLER_MODULE
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
            modality_expected=modality_expected,
            goal_action=goal_action,
            action_token_in_answer=text,
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
            }
        )
        if last_rec.final_decision in ("ACCEPT", "REJECT"):
            break

    trace.append({"phase": "answer", "final_decision": last_rec.final_decision, "attempts_used": attempt})
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
            }
        )
        if last.final_decision in ("ACCEPT", "REJECT"):
            break

    trace.append(
        {
            "phase": "rule",
            "final_decision": last.final_decision,
            "attempts_used": attempt,
            "final_rule_id": rule.rule_id,
        }
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
        }
    )
    attempt = 0
    excluded: set[str] = set()
    while last.final_decision == "REPAIR" and attempt < max_attempts:
        code = _first_error_code(last)
        if not code or repair_target_for_code(code) != BACKWARD_HANDLER_MODULE:
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
            }
        )
        if last.final_decision in ("ACCEPT", "REJECT"):
            break

    trace.append(
        {
            "phase": "backward",
            "final_decision": last.final_decision,
            "attempts_used": attempt,
            "final_rule_id": sel.rule_id if sel else None,
        }
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
    )
    trace.append(
        {
            "phase": "forward",
            "attempt": 0,
            "decision": last.final_decision,
            "repair_target_module": last.repair_target_module,
            "diagnostic_errors": list(last.diagnostic_errors),
            "action_taken": "initial_verify_forward",
        }
    )
    attempt = 0
    while last.final_decision == "REPAIR" and attempt < max_attempts:
        code = _first_error_code(last)
        if not code or repair_target_for_code(code) != FORWARD_HANDLER_MODULE:
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
        )
        trace.append(
            {
                "phase": "forward",
                "attempt": attempt,
                "decision": last.final_decision,
                "action_taken": "forward_retry_fn_rerun",
                "diagnostic_errors": list(last.diagnostic_errors),
            }
        )
        if last.final_decision in ("ACCEPT", "REJECT"):
            break

    trace.append({"phase": "forward", "final_decision": last.final_decision, "attempts_used": attempt})
    return conc, gok, fst, pobj, last, trace
