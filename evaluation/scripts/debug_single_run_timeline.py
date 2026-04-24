#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Run exactly one QA pipeline execution and save a structured debug timeline report."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.config import settings
from retrieval.evidence_retriever import configure_evidence_path
from retrieval.rulebase_loader import configure_rulebase_path
from runtime.nli_bootstrap import resolve_nli_stack_bundle
from runtime.pipeline_tracing import TraceCollector, new_trace_id
from runtime.qa_orchestrator import run_ask
from runtime.qa_runtime import configure_qa_orchestrator
from session.session_service import SessionService
from verification.engine import NeSyEngine

QUESTION = "Nếu nộp tiền thuế trễ hạn thì doanh nghiệp có thể bị áp dụng những hậu quả pháp lý gì?"
OUTPUT_PATH = REPO_ROOT / "artifacts" / "debug_reports" / "single_run_tax_delay_debug_report.json"


def _safe_get(d: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default


def _extract_verification_status(resp: Any) -> dict[str, Any]:
    logs = list(getattr(resp, "verification_trace", []) or [])
    if not logs:
        return {"present": False, "latest_decision": None, "by_mode": {}}

    by_mode: dict[str, str] = {}
    for rec in logs:
        mode = str(getattr(rec, "mode", "") or "unknown")
        decision = str(getattr(rec, "final_decision", "") or "unknown")
        by_mode[mode] = decision
    latest = logs[-1]
    return {
        "present": True,
        "latest_decision": str(getattr(latest, "final_decision", "") or "unknown"),
        "by_mode": by_mode,
    }


def _requirement_set_summary(reasoning: Any) -> dict[str, Any]:
    if not reasoning:
        return {
            "present": False,
            "count": 0,
            "sample": [],
            "artifact": None,
        }
    reqs = list(getattr(reasoning, "requirement_set", []) or [])
    sample = []
    for r in reqs[:5]:
        sample.append(
            {
                "key": str(getattr(r, "key", "") or ""),
                "predicate": getattr(r, "predicate", None),
                "description": str(getattr(r, "description", "") or "")[:160],
            }
        )
    artifact = getattr(reasoning, "requirement_artifact", None)
    artifact_dump = artifact.model_dump(mode="json") if artifact is not None else None
    return {
        "present": True,
        "count": len(reqs),
        "sample": sample,
        "artifact": artifact_dump,
    }


def _to_checkpoint(
    stage_name: str,
    *,
    reached: bool,
    resp: Any,
    debug_trace: dict[str, Any],
    span_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    selected_rule = getattr(resp, "selected_rule", None)
    if isinstance(selected_rule, dict):
        selected_rule_id = selected_rule.get("rule_id")
    else:
        selected_rule_id = None

    clarification_questions = list(getattr(resp, "clarification_questions", []) or [])
    clarification_targets = []
    for q in clarification_questions[:10]:
        try:
            clarification_targets.append(
                {
                    "fact_key": q.fact_key,
                    "target_kind": q.target_kind,
                    "blocking_reason": q.blocking_reason,
                    "reason_hint": q.reason_hint,
                }
            )
        except Exception:
            pass

    reasoning = getattr(resp, "reasoning", None)
    missing_facts = list(getattr(reasoning, "missing_facts", []) or [])

    retrieved_rules = list(getattr(resp, "retrieved_rules", []) or [])
    retrieved_count = len(retrieved_rules)

    proof_obj = getattr(resp, "proof", None)
    proof_present = bool(proof_obj is not None and list(getattr(proof_obj, "proof_steps", []) or []))

    answer_obj = getattr(resp, "answer", None)
    final_answer_present = bool(answer_obj is not None and str(getattr(answer_obj, "answer_text", "") or "").strip())

    gen_span = span_index.get("generate_answer") or {}
    gen_out = gen_span.get("output_summary") if isinstance(gen_span, dict) else {}
    candidate_answer_present = bool(_safe_get(gen_out, "answer_text_len", default=0) > 0)

    eval_log = getattr(resp, "evaluation_log", None)
    final_status = str(getattr(eval_log, "final_status", "") or "") if eval_log is not None else ""
    error_stage = str(getattr(eval_log, "error_stage_final", "") or "") if eval_log is not None else ""

    checkpoint = {
        "stage": stage_name,
        "reached": reached,
        "needs_clarification": bool(getattr(resp, "needs_clarification", False)),
        "clarification_targets": clarification_targets,
        "missing_facts": missing_facts,
        "selected_rule": {
            "present": bool(selected_rule_id),
            "rule_id": selected_rule_id,
        },
        "retrieved_rules": {
            "count": retrieved_count,
            "top_rule_ids": [r.get("rule_id") for r in retrieved_rules[:5] if isinstance(r, dict)],
        },
        "requirement_set_summary": _requirement_set_summary(reasoning),
        "proof_present": proof_present,
        "verification_status": _extract_verification_status(resp),
        "candidate_answer_present": candidate_answer_present,
        "final_answer_present": final_answer_present,
        "final_status": final_status,
        "error_stage": error_stage,
        "span_output": span_index.get(stage_name, {}),
    }
    return checkpoint


def _stage_reachability(span_index: dict[str, dict[str, Any]]) -> dict[str, bool]:
    # Map required checkpoints to the nearest run_ask spans.
    return {
        "after_parse": bool(span_index.get("parse_repair") or span_index.get("parse_layer2")),
        "after_clarification": bool(span_index.get("clarification")) or bool(span_index.get("parse_ambiguity_policy")),
        "after_rule_retrieval": bool(span_index.get("retrieve_rules")),
        "after_rule_selection": bool(span_index.get("rule_backward_gate")),
        "after_backward_reasoning": bool(span_index.get("rule_backward_gate")),
        "after_forward_reasoning": bool(span_index.get("forward_gate")),
        "after_answer_generation": bool(span_index.get("generate_answer")),
        "after_final_decision": True,
        "after_response_build": True,
    }


def _suppress_paths_for_run(resp: Any, debug_trace: dict[str, Any], span_index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    eval_log = getattr(resp, "evaluation_log", None)
    final_status = str(getattr(eval_log, "final_status", "") or "") if eval_log is not None else ""
    error_stage = str(getattr(eval_log, "error_stage_final", "") or "") if eval_log is not None else ""

    selected_rule = getattr(resp, "selected_rule", None)
    selected_rule_present = bool(selected_rule)
    proof_present = bool(getattr(resp, "proof", None))
    answer_present = bool(getattr(resp, "answer", None) and str(getattr(resp.answer, "answer_text", "") or "").strip())
    needs_clarification = bool(getattr(resp, "needs_clarification", False))

    parse_blocking = bool(debug_trace.get("parse_ambiguity_blocking_no_usable_primary_batch"))

    conditions = [
        {
            "path": "parse_unavailable",
            "condition": "parse_unavailable_meta is not None",
            "matched_this_run": str(error_stage).lower() == "parse_unavailable" or str(debug_trace.get("error", "")).lower() == "parse_unavailable",
            "suppresses_answer": True,
        },
        {
            "path": "parse_ambiguity_blocking_interactive",
            "condition": "blocking parse ambiguity and clarification_enabled=True",
            "matched_this_run": needs_clarification and bool(span_index.get("parse_ambiguity_policy")),
            "suppresses_answer": True,
        },
        {
            "path": "parse_ambiguity_blocking_no_usable_primary_batch",
            "condition": "blocking parse ambiguity + clarification disabled + unusable primary parse",
            "matched_this_run": parse_blocking,
            "suppresses_answer": False,
            "returns_degraded_answer": True,
        },
        {
            "path": "parse_rejected",
            "condition": "v_parse.final_decision == REJECT",
            "matched_this_run": str(debug_trace.get("error", "")).lower() == "parse_rejected",
            "suppresses_answer": True,
        },
        {
            "path": "backward_disabled_by_run_config",
            "condition": "enable_backward_chaining=False",
            "matched_this_run": str(debug_trace.get("error", "")).lower() == "backward_disabled_by_run_config",
            "suppresses_answer": True,
        },
        {
            "path": "rule_backward_gate_failed_without_fallback_answer",
            "condition": "not rg.ok and fallback answer not generated",
            "matched_this_run": (not selected_rule_present) and (not proof_present) and (not answer_present) and str(error_stage).lower().startswith("rule"),
            "suppresses_answer": True,
        },
        {
            "path": "clarification_required_from_backward",
            "condition": "rg.clarification_needed and enable_clarification=True",
            "matched_this_run": needs_clarification and bool(span_index.get("rule_backward_gate")) and bool(span_index.get("clarification")),
            "suppresses_answer": True,
        },
        {
            "path": "clarification_disabled_by_run_config",
            "condition": "rg.clarification_needed and enable_clarification=False and no conditional answer branch",
            "matched_this_run": str(debug_trace.get("error", "")).lower() == "clarification_disabled_by_run_config",
            "suppresses_answer": True,
        },
        {
            "path": "forward_gate_failed_without_partial_answer",
            "condition": "not fg.ok and partial fallback branch not taken",
            "matched_this_run": str(debug_trace.get("error", "")).lower().startswith("forward") and not answer_present,
            "suppresses_answer": True,
        },
        {
            "path": "answer_verification_reject_no_fallback",
            "condition": "v_ans.final_decision == REJECT and fallback disallowed",
            "matched_this_run": str(_safe_get(debug_trace, "answer_verification", "final_decision", default="")).upper() == "REJECT"
            and str(_safe_get(debug_trace, "answer_verification", "note", default="")).lower() == "no_fallback_per_policy",
            "suppresses_answer": not answer_present,
        },
    ]

    return conditions


def _first_answer_drop_and_origin(checkpoints: list[dict[str, Any]], resp: Any) -> tuple[str | None, str, str]:
    candidate_stage = None
    for cp in checkpoints:
        if cp.get("reached") and cp.get("candidate_answer_present"):
            candidate_stage = cp["stage"]
            break

    first_drop = None
    if candidate_stage is None:
        # Never generated candidate answer; find earliest reached checkpoint with final_answer absent.
        for cp in checkpoints:
            if cp.get("reached") and not cp.get("final_answer_present"):
                first_drop = cp["stage"]
                break
        if first_drop is None:
            first_drop = "after_parse"
        origin = "answer_never_generated"
    else:
        origin = "answer_generated_then_overwritten"
        for cp in checkpoints:
            if cp.get("reached") and not cp.get("final_answer_present"):
                first_drop = cp["stage"]
                break
        if first_drop is None:
            first_drop = "after_response_build"
            origin = "answer_preserved"

    eval_log = getattr(resp, "evaluation_log", None)
    final_status = str(getattr(eval_log, "final_status", "") or "") if eval_log is not None else ""
    error_stage = str(getattr(eval_log, "error_stage_final", "") or "") if eval_log is not None else ""

    degraded_origin = "unknown"
    fs = final_status.lower()
    es = error_stage.lower()
    if fs == "needs_clarification":
        degraded_origin = "clarification"
    elif "rule" in es:
        degraded_origin = "rule_selection_or_backward"
    elif "forward" in es:
        degraded_origin = "forward"
    elif "answer" in es:
        degraded_origin = "answer_generation"
    elif "parse" in es:
        degraded_origin = "clarification"
    elif fs in {"failed", "open"}:
        degraded_origin = "final_decision"

    return first_drop, origin, degraded_origin


def _probable_blocker_module(resp: Any, checkpoints: list[dict[str, Any]]) -> tuple[str, str]:
    eval_log = getattr(resp, "evaluation_log", None)
    final_status = str(getattr(eval_log, "final_status", "") or "") if eval_log is not None else ""
    error_stage = str(getattr(eval_log, "error_stage_final", "") or "") if eval_log is not None else ""

    if final_status.lower() == "needs_clarification":
        return (
            "parse/clarification_gate",
            "Pipeline exits to clarification before answer generation (needs_clarification=True).",
        )
    if "rule" in error_stage.lower() or "backward" in error_stage.lower():
        return (
            "rule_selection_or_backward_reasoning",
            f"error_stage_final={error_stage}",
        )
    if "forward" in error_stage.lower():
        return (
            "forward_reasoning",
            f"error_stage_final={error_stage}",
        )
    if "answer" in error_stage.lower():
        return (
            "answer_generation_or_answer_verification",
            f"error_stage_final={error_stage}",
        )

    # Fallback from stage reachability
    reached_answer_gen = any(cp["stage"] == "after_answer_generation" and cp.get("reached") for cp in checkpoints)
    if not reached_answer_gen:
        return (
            "upstream_before_answer_generation",
            "generate_answer stage not reached.",
        )
    return (
        "final_decision_or_response_build",
        "answer generation reached but final artifact still missing.",
    )


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    configure_rulebase_path(REPO_ROOT / "data" / "processed" / "rulebase" / "doanhnghiep" / "rulebase_reasoning_core.json")
    configure_evidence_path(REPO_ROOT / "data" / "corpus" / "evidence_chunks.json")

    nli_verifier, nli_meta, nli_degraded = resolve_nli_stack_bundle(settings)
    configure_qa_orchestrator(
        rulebase_core_path=settings.resolved_rulebase_core(),
        evidence_chunks_path=settings.resolved_evidence_chunks(),
        rule_retrieval_top_k=settings.rule_retrieval_top_k,
        nesy_nli_mock=settings.nesy_nli_mock,
        nli_verifier=nli_verifier,
        nli_degraded=nli_degraded,
        nli_meta=nli_meta,
        entailment_threshold=settings.nli_entailment_threshold,
        contradiction_threshold=settings.nli_contradiction_threshold,
        answer_reject_allow_fallback=settings.answer_reject_allow_fallback,
        settings=settings,
    )

    svc = SessionService()
    engine = NeSyEngine(nesy_nli_mock=True)
    trace_collector = TraceCollector(
        trace_id=new_trace_id(),
        question_text=QUESTION,
        session_id=None,
        turn="ask",
    )

    response = run_ask(
        question=QUESTION,
        session_id="debug_single_run_tax_delay_001",
        user_facts=[],
        session_svc=svc,
        nesy=engine,
        trace_collector=trace_collector,
    )

    debug_trace = dict(getattr(response, "debug_trace", {}) or {})
    pipeline_trace = trace_collector.to_dict()

    span_index: dict[str, dict[str, Any]] = {}
    for s in pipeline_trace.get("steps", []):
        if not isinstance(s, dict):
            continue
        name = str(s.get("step_name") or "")
        if name:
            span_index[name] = {
                "status": s.get("status"),
                "decision": s.get("decision"),
                "output_summary": s.get("output_summary") or {},
                "errors": s.get("errors") or [],
            }

    reachability = _stage_reachability(span_index)

    checkpoint_order = [
        "after_parse",
        "after_clarification",
        "after_rule_retrieval",
        "after_rule_selection",
        "after_backward_reasoning",
        "after_forward_reasoning",
        "after_answer_generation",
        "after_final_decision",
        "after_response_build",
    ]

    checkpoints = [
        _to_checkpoint(
            stage,
            reached=reachability.get(stage, False),
            resp=response,
            debug_trace=debug_trace,
            span_index=span_index,
        )
        for stage in checkpoint_order
    ]

    first_drop_stage, answer_origin, degraded_origin = _first_answer_drop_and_origin(checkpoints, response)
    suppress_paths = _suppress_paths_for_run(response, debug_trace, span_index)
    blocker_module, blocker_reason = _probable_blocker_module(response, checkpoints)

    eval_log = getattr(response, "evaluation_log", None)
    final_status = str(getattr(eval_log, "final_status", "") or "") if eval_log is not None else ""
    error_stage = str(getattr(eval_log, "error_stage_final", "") or "") if eval_log is not None else ""

    exact_condition = {
        "error_stage_final": error_stage,
        "needs_clarification": bool(getattr(response, "needs_clarification", False)),
        "clarification_questions_count": len(list(getattr(response, "clarification_questions", []) or [])),
        "debug_error": debug_trace.get("error"),
        "matched_suppress_paths": [p for p in suppress_paths if p.get("matched_this_run")],
        "blocker_reason": blocker_reason,
    }

    recommendation = {
        "module_to_patch_first": blocker_module,
        "why": blocker_reason,
        "suggested_focus": "Address the earliest matched suppress path before touching downstream answer generation.",
        "do_not_patch_now": True,
    }

    report = {
        "meta": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "question": QUESTION,
            "session_id": response.session_id,
            "single_run": True,
            "report_version": "1.0",
        },
        "run_summary": {
            "needs_clarification": bool(getattr(response, "needs_clarification", False)),
            "final_status": final_status,
            "answer_quality": getattr(response, "answer_quality", None),
            "answer_quality_reason": getattr(response, "answer_quality_reason", None),
            "final_answer_present": bool(getattr(response, "answer", None) and str(getattr(response.answer, "answer_text", "") or "").strip()),
            "error_stage_final": error_stage,
        },
        "timeline": checkpoints,
        "first_answer_drop_stage": first_drop_stage,
        "answer_drop_origin": answer_origin,
        "degraded_origin": degraded_origin,
        "suppress_answer_paths": suppress_paths,
        "probable_blocker_module": blocker_module,
        "exact_condition_causing_no_answer_or_degraded": exact_condition,
        "recommendation": recommendation,
        "pipeline_trace_steps": pipeline_trace.get("steps", []),
    }

    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Debug report saved to: {OUTPUT_PATH}")
    print(f"Final status: {final_status}")
    print(f"Needs clarification: {getattr(response, 'needs_clarification', False)}")
    print(f"First answer drop stage: {first_drop_stage}")
    print(f"Probable blocker module: {blocker_module}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
