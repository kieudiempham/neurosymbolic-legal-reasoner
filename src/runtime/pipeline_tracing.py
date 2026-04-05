"""Collect per-step timing and summaries for the QA pipeline (debug + batch export)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from schemas.answer import FinalAnswer
from schemas.evidence import EvidenceSnippet
from schemas.pipeline_trace import PipelineStepTrace, PipelineTrace
from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord
from schemas.verification import VerificationRecord


def new_trace_id() -> str:
    return f"trace_{uuid.uuid4().hex[:16]}"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def summarize_layer1_trace(layer1: Layer1Parse) -> dict[str, Any]:
    meta = layer1.parse_metadata or {}
    return {
        "parser_backend": meta.get("parser_backend"),
        "parser_model": meta.get("parser_model"),
        "fallback_used": meta.get("fallback_used"),
        "fallback_reason": meta.get("fallback_reason"),
        "question_focus": layer1.question_focus,
        "modality_text": layer1.modality_text,
        "utterance_type": layer1.utterance_type,
        "assertion_status": layer1.assertion_status,
        "action_text_excerpt": (layer1.action_text or "")[:200],
    }


def summarize_layer2_trace(layer2: Layer2Parse) -> dict[str, Any]:
    ambs = (layer2.diagnostics or {}).get("ambiguities") or []
    return {
        "subject_normalized": layer2.subject_normalized,
        "subject_type_guess": layer2.subject_type_guess,
        "condition_atoms": layer2.condition_atoms[:12],
        "facts": layer2.facts[:12],
        "goal": layer2.goal,
        "query_rule_candidate": (layer2.query_rule_candidate or "")[:400],
        "ambiguity_count": len(ambs),
        "blocking_ambiguity": any(a.get("blocking") for a in ambs),
    }


def summarize_verification_trace(rec: VerificationRecord) -> dict[str, Any]:
    return {
        "mode": rec.mode,
        "final_decision": rec.final_decision,
        "symbolic_ok": rec.symbolic_ok,
        "repair_target_module": rec.repair_target_module,
        "diagnostic_errors": rec.diagnostic_errors[:8],
        "semantic_scores": dict(list(rec.semantic_scores.items())[:8]) if rec.semantic_scores else {},
    }


def summarize_evidence_trace(evidence: list[EvidenceSnippet]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for e in evidence[:8]:
        bd = e.score_breakdown or {}
        rows.append(
            {
                "chunk_id": e.chunk_id,
                "score": round(e.score, 5),
                "article_clause": e.article_clause,
                "bm25_variant_used": bd.get("bm25_variant_used"),
                "structured_total": bd.get("structured_total"),
            }
        )
    return {"top_k": len(evidence), "passages": rows}


def summarize_answer_trace(ans: FinalAnswer) -> dict[str, Any]:
    return {
        "generation_mode": ans.generation_mode,
        "answer_text_len": len(ans.answer_text or ""),
        "citations_count": len(ans.legal_citations),
        "has_proof_summary": bool((ans.proof_summary or "").strip()),
        "evidence_snippets_count": len(ans.evidence_snippets),
    }


class TraceCollector:
    """Context-manager based step timing + summaries for one pipeline run."""

    def __init__(
        self,
        trace_id: str,
        *,
        question_text: str,
        session_id: str | None,
        turn: str = "ask",
        noop: bool = False,
    ) -> None:
        self.trace_id = trace_id
        self.question_text = question_text
        self.session_id = session_id
        self.turn = turn
        self._noop = noop
        self._steps: list[PipelineStepTrace] = []

    @classmethod
    def noop(cls) -> TraceCollector:
        """Single code path in orchestrator: spans record nothing."""
        return cls(new_trace_id(), question_text="", session_id=None, noop=True)

    def span(self, step_name: str):
        return _Span(self, step_name)

    def add_step(self, step: PipelineStepTrace) -> None:
        self._steps.append(step)

    def to_pipeline_trace(self) -> PipelineTrace:
        return PipelineTrace(
            trace_id=self.trace_id,
            question_text=self.question_text,
            session_id=self.session_id,
            turn=self.turn,  # type: ignore[arg-type]
            steps=list(self._steps),
        )

    def to_dict(self) -> dict[str, Any]:
        return self.to_pipeline_trace().model_dump(mode="json")


class _Span:
    __slots__ = ("_collector", "_name", "_t0", "_started_iso", "output_summary", "input_summary", "warnings", "decision")

    def __init__(self, collector: TraceCollector, name: str) -> None:
        self._collector = collector
        self._name = name
        self._t0 = 0.0
        self._started_iso = ""
        self.output_summary: dict[str, Any] = {}
        self.input_summary: dict[str, Any] = {}
        self.warnings: list[str] = []
        self.decision: str | None = None

    def __enter__(self) -> _Span:
        self._t0 = perf_counter()
        self._started_iso = _utc_iso()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._collector._noop:
            return None
        t1 = perf_counter()
        ended_iso = _utc_iso()
        status = "failed" if exc_type else "success"
        err: list[str] = []
        if exc_type and exc:
            err.append(f"{exc_type.__name__}: {exc}")
        step = PipelineStepTrace(
            step_name=self._name,
            status=status,  # type: ignore[arg-type]
            started_at=self._started_iso,
            ended_at=ended_iso,
            duration_ms=(t1 - self._t0) * 1000.0,
            input_summary=self.input_summary,
            output_summary=self.output_summary,
            decision=self.decision,
            errors=err,
            warnings=list(self.warnings),
        )
        self._collector.add_step(step)


def default_trace_directory() -> Path:
    """`artifacts/traces` under repo root (parent of `src`)."""
    here = Path(__file__).resolve()
    repo_root = here.parent.parent.parent
    return repo_root / "artifacts" / "traces"


def save_pipeline_trace_json(
    trace: PipelineTrace | dict[str, Any],
    *,
    directory: Path | None = None,
    filename: str | None = None,
) -> Path:
    """Write trace JSON; creates directory if needed."""
    d = directory or default_trace_directory()
    d.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sid = ""
    if isinstance(trace, PipelineTrace):
        sid = (trace.session_id or "")[:12]
        payload = trace.model_dump(mode="json")
    else:
        payload = trace
        sid = str(payload.get("session_id") or "")[:12]
    name = filename or f"trace_{ts}_{sid or 'nosess'}.json"
    path = d / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def trace_summary_compact(steps: list[PipelineStepTrace]) -> dict[str, Any]:
    """Short map step_name -> duration_ms + status for API trace_summary."""
    return {
        s.step_name: {"status": s.status, "duration_ms": round(s.duration_ms, 2), "decision": s.decision}
        for s in steps
    }
