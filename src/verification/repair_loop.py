"""Auto repair loops — re-parse / re-layer2 or answer generator until ACCEPT/REJECT or max attempts."""

from __future__ import annotations

from typing import Any, Callable

from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.verification import VerificationRecord
from verification.engine import NeSyEngine
from verification.repair_handlers import default_answer_regenerate, repair_parse_bundle
from verification.repair_routing import repair_target_for_code

PARSE_HANDLER_MODULE = "question_parser_or_layer2_builder"
ANSWER_HANDLER_MODULE = "answer_generator"


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
