"""End-to-end single-question runner: wraps ``run_ask`` / ``run_clarify`` with ``QAResponse`` + trace export."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from runtime.pipeline_tracing import (
    TraceCollector,
    new_trace_id,
    save_pipeline_trace_json,
    trace_summary_compact,
)
from runtime.qa_orchestrator import run_ask, run_clarify
from schemas.http_response import AskResponse, ClarifyResponse
from schemas.pipeline_trace import PipelineTrace
from schemas.qa_response import FinalAnswerSummary, QAResponse, QARunRecord
from schemas.verification import VerificationRecord
from retrieval.evidence_retriever import EvidenceRetriever
from retrieval.rulebase_loader import RulebaseIndex
from session.session_service import SessionService
from verification.engine import NeSyEngine
from verification.nli_verifier import NLIVerifier

from runtime.nli_bootstrap import resolve_pipeline_nesy_engine

logger = logging.getLogger(__name__)


def _final_answer_summary(ans: Any) -> FinalAnswerSummary | None:
    if ans is None:
        return None
    cites = [c.model_dump(mode="json") for c in (getattr(ans, "legal_citations", None) or [])]
    return FinalAnswerSummary(
        answer_text=getattr(ans, "answer_text", "") or "",
        generation_mode=getattr(ans, "generation_mode", "") or "",
        legal_citations=cites,
        proof_summary=getattr(ans, "proof_summary", "") or "",
        verification_summary=getattr(ans, "verification_summary", "") or "",
    )


def _verification_decisions(logs: list[VerificationRecord]) -> dict[str, str]:
    return {r.mode: r.final_decision for r in logs}


def _ask_status(ask: AskResponse) -> tuple[str, str | None, str | None]:
    """Returns (qa_status, reason, failure_code)."""
    dt = ask.debug_trace or {}
    if ask.needs_clarification:
        return "needs_clarification", "clarification_required", None
    if dt.get("error") == "parse_rejected":
        return "failed", "parse_verification_rejected", "parse_rejected"
    if dt.get("note") == "no_unifying_rule":
        return "failed", "no_unifying_rule", "no_unifying_rule"
    if ask.answer and (ask.answer.answer_text or "").strip():
        return "answered", None, None
    if ask.answer:
        return "answered", None, None
    return "failed", "no_answer_produced", "no_answer"


def ask_response_to_qa(
    ask: AskResponse,
    *,
    question_text: str,
    trace_id: str | None,
    pipeline_trace: PipelineTrace | None,
    trace_file: str | None = None,
) -> QAResponse:
    status, reason, fcode = _ask_status(ask)
    ts: dict[str, Any] = {}
    if pipeline_trace and pipeline_trace.steps:
        ts = trace_summary_compact(pipeline_trace.steps)
    goal = ask.layer2.goal if ask.layer2 else None
    missing: list[str] = []
    if ask.reasoning and getattr(ask.reasoning, "missing_facts", None):
        missing = list(ask.reasoning.missing_facts or [])

    return QAResponse(
        status=status,  # type: ignore[arg-type]
        question_text=question_text,
        session_id=ask.session_id,
        trace_id=trace_id,
        final_answer=_final_answer_summary(ask.answer),
        clarification_prompts=list(ask.clarification_questions),
        reason=reason,
        failure_code=fcode,
        current_trace_summary={"goal": goal, "missing_facts": missing},
        trace_summary=ts,
        pipeline_trace=pipeline_trace,
        meta={"trace_file": trace_file, "debug_trace_keys": list((ask.debug_trace or {}).keys())},
    )


def clarify_response_to_qa(
    resp: ClarifyResponse,
    *,
    question_text: str,
    trace_id: str | None,
    pipeline_trace: PipelineTrace | None,
    trace_file: str | None = None,
) -> QAResponse:
    dt = resp.debug_trace or {}
    if resp.needs_clarification:
        status = "needs_clarification"
        reason = "clarification_required"
        fcode = None
    elif dt.get("error") == "parse_rejected":
        status = "failed"
        reason = "parse_verification_rejected"
        fcode = "parse_rejected"
    elif resp.answer and (resp.answer.answer_text or "").strip():
        status = "answered"
        reason = None
        fcode = None
    elif resp.answer:
        status = "answered"
        reason = None
        fcode = None
    else:
        status = "failed"
        reason = dt.get("error") or "clarify_no_answer"
        fcode = "no_answer"

    ts: dict[str, Any] = {}
    if pipeline_trace and pipeline_trace.steps:
        ts = trace_summary_compact(pipeline_trace.steps)

    goal = resp.layer2.goal if resp.layer2 else None
    missing = list(resp.reasoning.missing_facts or []) if resp.reasoning else []

    return QAResponse(
        status=status,  # type: ignore[arg-type]
        question_text=question_text,
        session_id=resp.session_id,
        trace_id=trace_id,
        final_answer=_final_answer_summary(resp.answer),
        clarification_prompts=list(resp.clarification_questions),
        reason=reason,
        failure_code=fcode,
        current_trace_summary={"goal": goal, "missing_facts": missing},
        trace_summary=ts,
        pipeline_trace=pipeline_trace,
        meta={"trace_file": trace_file, "debug_trace_keys": list(dt.keys()), "turn": "clarify"},
    )


def to_run_record(qa: QAResponse, *, qid: str | None = None) -> QARunRecord:
    """Flatten for batch dataset rows."""
    sr = []
    if qa.meta and qa.meta.get("selected_rule_ids"):
        sr = qa.meta["selected_rule_ids"]
    fa = qa.final_answer
    return QARunRecord(
        qid=qid,
        status=qa.status,
        session_id=qa.session_id,
        trace_id=qa.trace_id,
        answer_text=fa.answer_text if fa else None,
        selected_rule_ids=sr,
        goal=qa.current_trace_summary.get("goal") if qa.current_trace_summary else None,
        missing_facts=list(qa.current_trace_summary.get("missing_facts") or []) if qa.current_trace_summary else [],
        verification_decisions=qa.meta.get("verification_decisions") or {},
        trace_file=qa.meta.get("trace_file") if isinstance(qa.meta, dict) else None,
        failure_reason=qa.reason,
    )


def run_qa_pipeline(
    question_text: str,
    *,
    session_id: str | None = None,
    user_facts: list[str] | None = None,
    debug: bool = True,
    save_trace: bool = False,
    qid: str | None = None,
    trace_dir: Path | None = None,
    session_svc: SessionService | None = None,
    nesy: NeSyEngine | None = None,
    nli_verifier: NLIVerifier | None = None,
    settings: Any | None = None,
    rule_index: RulebaseIndex | None = None,
    evidence_retriever: EvidenceRetriever | None = None,
    top_k: int | None = None,
    max_repair_attempts_parse: int | None = None,
    max_repair_attempts_answer: int | None = None,
    max_repair_attempts_rule: int | None = None,
    max_repair_attempts_backward: int | None = None,
    max_repair_attempts_forward: int | None = None,
    answer_reject_allow_fallback: bool | None = None,
) -> QAResponse:
    """
    Single entrypoint: full ``run_ask`` with structured tracing.

    * ``debug``: build ``PipelineTrace`` (step timings + summaries).
    * ``save_trace``: write JSON under ``artifacts/traces/`` (or ``trace_dir``).

    When ``nesy`` is not passed, resolves ``NeSyEngine`` via ``runtime.nli_bootstrap`` using the same
    ``app.config.Settings`` / ``resolve_nli_stack_bundle`` path as FastAPI (``.env`` / ``LEGAL_QA_*``).
    Pass ``nesy`` or ``nli_verifier`` to override without bootstrap.
    """
    cfg = settings
    if cfg is None:
        try:
            from runtime.nli_bootstrap import load_app_settings

            cfg = load_app_settings()
        except Exception as e:
            logger.warning("Could not load app settings (%s); using NeSyEngine mock fallback.", e)
            cfg = None

    resolved_nesy = nesy
    nli_runtime: dict[str, Any]
    if resolved_nesy is None:
        try:
            resolved_nesy, nli_runtime = resolve_pipeline_nesy_engine(
                nesy=None,
                nli_verifier=nli_verifier,
                settings=cfg,
            )
        except Exception as e:
            logger.warning("NLI bootstrap failed (%s); using NeSyEngine(nli_degraded=True) — symbolic-only mode.", e)
            resolved_nesy = NeSyEngine(nli_degraded=True, nli_meta={"nli_status": "degraded_symbolic_only_bootstrap_error"})
            nli_runtime = {
                "verifier_class": "NeSyEngine",
                "source": "degraded_symbolic_only",
                "bootstrap_error": str(e),
                "nli_degraded": True,
            }
    else:
        if nli_verifier is not None:
            logger.warning("Both ``nesy`` and ``nli_verifier`` set; using ``nesy`` only.")
        try:
            from runtime.nli_bootstrap import load_app_settings, nli_runtime_descriptor

            s = cfg or load_app_settings()
            nli_runtime = nli_runtime_descriptor(resolved_nesy, s)
        except Exception:
            nli_runtime = {"verifier_class": type(getattr(resolved_nesy, "_nli", object())).__name__, "source": "caller_nesy"}

    top_k_r = top_k if top_k is not None else (cfg.rule_retrieval_top_k if cfg is not None else 8)
    m_parse = max_repair_attempts_parse if max_repair_attempts_parse is not None else 2
    m_ans = max_repair_attempts_answer if max_repair_attempts_answer is not None else 2
    m_rule = max_repair_attempts_rule if max_repair_attempts_rule is not None else 2
    m_bwd = max_repair_attempts_backward if max_repair_attempts_backward is not None else 1
    m_fwd = max_repair_attempts_forward if max_repair_attempts_forward is not None else 1
    ans_fb = (
        answer_reject_allow_fallback
        if answer_reject_allow_fallback is not None
        else (cfg.answer_reject_allow_fallback if cfg is not None else False)
    )

    want_trace = debug or save_trace
    tid = new_trace_id() if want_trace else None
    tc: TraceCollector | None = (
        TraceCollector(tid or new_trace_id(), question_text=question_text, session_id=session_id)
        if want_trace
        else None
    )

    ask = run_ask(
        question=question_text,
        session_id=session_id,
        user_facts=user_facts or [],
        session_svc=session_svc,
        nesy=resolved_nesy,
        rule_index=rule_index,
        evidence_retriever=evidence_retriever,
        top_k=top_k_r,
        max_repair_attempts_parse=m_parse,
        max_repair_attempts_answer=m_ans,
        max_repair_attempts_rule=m_rule,
        max_repair_attempts_backward=m_bwd,
        max_repair_attempts_forward=m_fwd,
        answer_reject_allow_fallback=ans_fb,
        trace_collector=tc,
    )

    pt: PipelineTrace | None = tc.to_pipeline_trace() if tc and not tc._noop else None

    trace_path: str | None = None
    if save_trace and pt:
        p = save_pipeline_trace_json(pt, directory=trace_dir)
        trace_path = str(p.resolve())

    qa = ask_response_to_qa(
        ask,
        question_text=question_text,
        trace_id=tid,
        pipeline_trace=pt,
        trace_file=trace_path,
    )
    vmap = _verification_decisions(ask.verification_trace or [])
    meta = dict(qa.meta or {})
    meta["verification_decisions"] = vmap
    meta["qid"] = qid
    meta["nli_runtime"] = nli_runtime
    if ask.selected_rule:
        meta["selected_rule_ids"] = [ask.selected_rule.get("rule_id", "")]
    qa = qa.model_copy(update={"meta": meta})
    return qa


def run_clarification_pipeline(
    session_id: str,
    answers: list[dict[str, Any]],
    *,
    debug: bool = True,
    save_trace: bool = False,
    qid: str | None = None,
    trace_dir: Path | None = None,
    session_svc: SessionService | None = None,
    nesy: NeSyEngine | None = None,
    nli_verifier: NLIVerifier | None = None,
    settings: Any | None = None,
    rule_index: RulebaseIndex | None = None,
    evidence_retriever: EvidenceRetriever | None = None,
    top_k: int | None = None,
    max_repair_attempts_parse: int | None = None,
    max_repair_attempts_answer: int | None = None,
    max_repair_attempts_rule: int | None = None,
    max_repair_attempts_backward: int | None = None,
    max_repair_attempts_forward: int | None = None,
    answer_reject_allow_fallback: bool | None = None,
) -> QAResponse:
    """Resume session after clarification; same tracing contract as ``run_qa_pipeline``."""
    cfg = settings
    if cfg is None:
        try:
            from runtime.nli_bootstrap import load_app_settings

            cfg = load_app_settings()
        except Exception as e:
            logger.warning("Could not load app settings (%s); using NeSyEngine mock fallback.", e)
            cfg = None

    resolved_nesy = nesy
    nli_runtime: dict[str, Any]
    if resolved_nesy is None:
        try:
            resolved_nesy, nli_runtime = resolve_pipeline_nesy_engine(
                nesy=None,
                nli_verifier=nli_verifier,
                settings=cfg,
            )
        except Exception as e:
            logger.warning("NLI bootstrap failed (%s); using NeSyEngine(nli_degraded=True) — symbolic-only mode.", e)
            resolved_nesy = NeSyEngine(nli_degraded=True, nli_meta={"nli_status": "degraded_symbolic_only_bootstrap_error"})
            nli_runtime = {
                "verifier_class": "NeSyEngine",
                "source": "degraded_symbolic_only",
                "bootstrap_error": str(e),
                "nli_degraded": True,
            }
    else:
        if nli_verifier is not None:
            logger.warning("Both ``nesy`` and ``nli_verifier`` set; using ``nesy`` only.")
        try:
            from runtime.nli_bootstrap import load_app_settings, nli_runtime_descriptor

            s = cfg or load_app_settings()
            nli_runtime = nli_runtime_descriptor(resolved_nesy, s)
        except Exception:
            nli_runtime = {"verifier_class": type(getattr(resolved_nesy, "_nli", object())).__name__, "source": "caller_nesy"}

    top_k_r = top_k if top_k is not None else (cfg.rule_retrieval_top_k if cfg is not None else 8)
    m_parse = max_repair_attempts_parse if max_repair_attempts_parse is not None else 2
    m_ans = max_repair_attempts_answer if max_repair_attempts_answer is not None else 2
    m_rule = max_repair_attempts_rule if max_repair_attempts_rule is not None else 2
    m_bwd = max_repair_attempts_backward if max_repair_attempts_backward is not None else 1
    m_fwd = max_repair_attempts_forward if max_repair_attempts_forward is not None else 1
    ans_fb = (
        answer_reject_allow_fallback
        if answer_reject_allow_fallback is not None
        else (cfg.answer_reject_allow_fallback if cfg is not None else False)
    )

    want_trace = debug or save_trace
    tid = new_trace_id() if want_trace else None
    tc: TraceCollector | None = (
        TraceCollector(
            tid or new_trace_id(),
            question_text="",
            session_id=session_id,
            turn="clarify",
        )
        if want_trace
        else None
    )

    resp = run_clarify(
        session_id=session_id,
        answers=answers,
        session_svc=session_svc,
        nesy=resolved_nesy,
        rule_index=rule_index,
        evidence_retriever=evidence_retriever,
        top_k=top_k_r,
        max_repair_attempts_parse=m_parse,
        max_repair_attempts_answer=m_ans,
        max_repair_attempts_rule=m_rule,
        max_repair_attempts_backward=m_bwd,
        max_repair_attempts_forward=m_fwd,
        answer_reject_allow_fallback=ans_fb,
        trace_collector=tc,
    )

    qtext = ""
    if session_svc and (st := session_svc.get(session_id)):
        qtext = st.original_question or ""

    pt: PipelineTrace | None = tc.to_pipeline_trace() if tc and not tc._noop else None
    if tc and not tc._noop and qtext:
        tc.question_text = qtext

    trace_path: str | None = None
    if save_trace and pt:
        p = save_pipeline_trace_json(pt, directory=trace_dir)
        trace_path = str(p.resolve())

    qa = clarify_response_to_qa(
        resp,
        question_text=qtext,
        trace_id=tid,
        pipeline_trace=pt,
        trace_file=trace_path,
    )
    vmap = _verification_decisions(resp.verification_trace or [])
    meta = dict(qa.meta or {})
    meta["verification_decisions"] = vmap
    meta["qid"] = qid
    meta["nli_runtime"] = nli_runtime
    if resp.selected_rule:
        meta["selected_rule_ids"] = [resp.selected_rule.get("rule_id", "")]
    qa = qa.model_copy(update={"meta": meta})
    return qa


run_single_question_pipeline = run_qa_pipeline
