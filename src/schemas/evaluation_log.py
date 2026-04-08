"""Stable QA backend evaluation log contract and normalization helpers."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel


QA_EVAL_LOG_FIELDS: list[str] = [
    "sample_id",
    "query_text",
    "parsed_layer1",
    "parsed_layer2",
    "predicted_domains",
    "activated_domains",
    "bridge_rules_used",
    "cross_domain_jumps_attempted",
    "cross_domain_jumps_success",
    "cross_domain_jumps_blocked",
    "retrieved_topk",
    "selected_rule",
    "requirement_set",
    "missing_facts",
    "clarification_question",
    "clarification_answer",
    "proof",
    "proof_domains",
    "final_statute_grounding",
    "verification_reports",
    "repair_actions",
    "evidence_snippets",
    "legal_citations",
    "final_answer",
    "final_status",
    "error_stage_first",
    "error_stage_final",
    "backend_modes",
]


class QAEvaluationLogArtifact(BaseModel):
    sample_id: str | None = None
    query_text: str | None = None
    parsed_layer1: dict[str, Any] | None = None
    parsed_layer2: dict[str, Any] | None = None
    predicted_domains: list[str] | None = None
    activated_domains: list[str] | None = None
    bridge_rules_used: list[str] | None = None
    cross_domain_jumps_attempted: int | None = None
    cross_domain_jumps_success: int | None = None
    cross_domain_jumps_blocked: int | None = None
    retrieved_topk: list[dict[str, Any]] | None = None
    selected_rule: dict[str, Any] | None = None
    requirement_set: list[dict[str, Any]] | None = None
    missing_facts: list[str] | None = None
    clarification_question: list[dict[str, Any]] | None = None
    clarification_answer: list[dict[str, Any]] | None = None
    proof: dict[str, Any] | None = None
    proof_domains: list[str] | None = None
    final_statute_grounding: str | None = None
    verification_reports: list[dict[str, Any]] | None = None
    repair_actions: list[dict[str, Any]] | None = None
    evidence_snippets: list[dict[str, Any]] | None = None
    legal_citations: list[dict[str, Any]] | None = None
    final_answer: str | None = None
    final_status: str | None = None
    error_stage_first: str | None = None
    error_stage_final: str | None = None
    backend_modes: dict[str, Any] | None = None


def _list_of_dict(items: list[Any] | None) -> list[dict[str, Any]] | None:
    if items is None:
        return None
    out: list[dict[str, Any]] = []
    for item in items:
        if item is None:
            continue
        if hasattr(item, "model_dump"):
            out.append(item.model_dump(mode="json"))
        elif isinstance(item, dict):
            out.append(dict(item))
    return out


def _collect_repair_actions(debug_trace: dict[str, Any] | None) -> list[dict[str, Any]] | None:
    if not isinstance(debug_trace, dict):
        return None
    found: list[dict[str, Any]] = []

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            keys = {str(k).lower() for k in node.keys()}
            if any("repair" in k for k in keys):
                found.append(dict(node))
            for v in node.values():
                _walk(v)
            return
        if isinstance(node, list):
            for x in node:
                _walk(x)

    _walk(debug_trace)
    cg = debug_trace.get("clarification_gain")
    if isinstance(cg, dict):
        found.append({"phase": "clarification", **cg})
    return found or None


def _error_stages(debug_trace: dict[str, Any] | None) -> tuple[str | None, str | None]:
    if not isinstance(debug_trace, dict):
        return None, None

    first: str | None = None
    spans = (((debug_trace.get("pipeline_trace") or {}).get("spans")) or [])
    if isinstance(spans, list):
        for sp in spans:
            if not isinstance(sp, dict):
                continue
            name = str(sp.get("name") or "")
            out = sp.get("output_summary") or {}
            if isinstance(out, dict):
                reason = str(out.get("error") or out.get("reason") or "").strip().lower()
                if reason and any(t in reason for t in ("error", "reject", "fail", "blocked")):
                    first = name or reason
                    break

    final = None
    for key in ("stage", "error", "warning"):
        v = debug_trace.get(key)
        if isinstance(v, str) and v.strip():
            final = v.strip()
            break
    if final is None and first is not None:
        final = first
    return first, final


def _extract_cross_domain_metrics(
    debug_trace: dict[str, Any] | None,
    proof_payload: dict[str, Any] | None,
    answer_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    activated_domains: list[str] = []
    bridge_rules_used: list[str] = []
    proof_domains: list[str] = []
    cross_domain_jumps_attempted: int | None = None
    cross_domain_jumps_success: int | None = None
    cross_domain_jumps_blocked: int | None = None
    final_statute_grounding: str | None = None

    if isinstance(debug_trace, dict):
        ctx = debug_trace.get("reasoning_context") or {}
        if isinstance(ctx, dict):
            for x in (ctx.get("primary_domains") or []):
                sx = str(x).strip()
                if sx and sx not in activated_domains:
                    activated_domains.append(sx)
            for x in (ctx.get("secondary_domains") or []):
                sx = str(x).strip()
                if sx and sx not in activated_domains:
                    activated_domains.append(sx)

    if isinstance(proof_payload, dict):
        for st in (proof_payload.get("proof_steps") or []):
            if not isinstance(st, dict):
                continue
            dom = str(st.get("domain") or "").strip()
            if dom and dom not in proof_domains:
                proof_domains.append(dom)
            for br in (st.get("bridge_fact_ids_used") or []):
                sbr = str(br).strip()
                if sbr and sbr not in bridge_rules_used:
                    bridge_rules_used.append(sbr)
            art = str(st.get("source_article") or "").strip()
            if art:
                # Keep the latest step statute as final grounding fallback.
                final_statute_grounding = art

        prov = proof_payload.get("provenance") or {}
        if isinstance(prov, dict):
            trace = prov.get("cross_domain_trace") or {}
            if isinstance(trace, dict):
                ad = trace.get("activated_domains") or {}
                if isinstance(ad, dict):
                    active = ad.get("active_domains") or {}
                    if isinstance(active, dict):
                        for dom in active.keys():
                            sdom = str(dom).strip()
                            if sdom and sdom not in activated_domains:
                                activated_domains.append(sdom)

                transitions = trace.get("domain_transitions") or []
                if isinstance(transitions, list):
                    cross_domain_jumps_success = len(transitions)
                    for t in transitions:
                        if isinstance(t, dict):
                            bid = str(t.get("bridge_rule_id") or "").strip()
                            if bid and bid not in bridge_rules_used:
                                bridge_rules_used.append(bid)
            if not final_statute_grounding:
                fs = str(prov.get("final_statute") or "").strip()
                if fs:
                    final_statute_grounding = fs
            for bid in (prov.get("bridges_triggered") or []):
                sbid = str(bid).strip()
                if sbid and sbid not in bridge_rules_used:
                    bridge_rules_used.append(sbid)

    if isinstance(debug_trace, dict):
        metrics = debug_trace.get("cross_domain_metrics") or {}
        if isinstance(metrics, dict):
            if metrics.get("cross_domain_jumps_success") is not None:
                try:
                    cross_domain_jumps_success = int(metrics.get("cross_domain_jumps_success"))
                except (TypeError, ValueError):
                    pass
            if metrics.get("cross_domain_jumps_attempted") is not None:
                try:
                    cross_domain_jumps_attempted = int(metrics.get("cross_domain_jumps_attempted"))
                except (TypeError, ValueError):
                    pass
            if metrics.get("cross_domain_jumps_blocked") is not None:
                try:
                    cross_domain_jumps_blocked = int(metrics.get("cross_domain_jumps_blocked"))
                except (TypeError, ValueError):
                    pass
        blocked = debug_trace.get("cross_domain_jumps_blocked")
        if isinstance(blocked, list) and cross_domain_jumps_blocked is None:
            cross_domain_jumps_blocked = len(blocked)

    if cross_domain_jumps_success is None:
        cross_domain_jumps_success = 0
    if cross_domain_jumps_blocked is None:
        cross_domain_jumps_blocked = 0
    if cross_domain_jumps_attempted is None:
        cross_domain_jumps_attempted = cross_domain_jumps_success + cross_domain_jumps_blocked

    if not final_statute_grounding and isinstance(answer_payload, dict):
        cites = answer_payload.get("legal_citations") or []
        if isinstance(cites, list) and cites:
            first = cites[0] if isinstance(cites[0], dict) else {}
            if isinstance(first, dict):
                final_statute_grounding = (
                    str(first.get("statute") or first.get("source_doc") or "").strip() or None
                )

    return {
        "activated_domains": activated_domains or None,
        "bridge_rules_used": bridge_rules_used or None,
        "cross_domain_jumps_attempted": cross_domain_jumps_attempted,
        "cross_domain_jumps_success": cross_domain_jumps_success,
        "cross_domain_jumps_blocked": cross_domain_jumps_blocked,
        "proof_domains": proof_domains or None,
        "final_statute_grounding": final_statute_grounding,
    }


def build_evaluation_log_artifact(
    *,
    session_id: str,
    query_text: str | None,
    layer1: Any | None,
    layer2: Any | None,
    retrieved_rules: list[dict[str, Any]] | None,
    selected_rule: dict[str, Any] | None,
    reasoning: Any | None,
    proof: Any | None,
    answer: Any | None,
    needs_clarification: bool,
    clarification_questions: list[Any] | None,
    verification_trace: list[Any] | None,
    debug_trace: dict[str, Any] | None,
) -> QAEvaluationLogArtifact:
    l1 = layer1.model_dump(mode="json") if hasattr(layer1, "model_dump") else (dict(layer1) if isinstance(layer1, dict) else None)
    l2 = layer2.model_dump(mode="json") if hasattr(layer2, "model_dump") else (dict(layer2) if isinstance(layer2, dict) else None)
    rs = reasoning.model_dump(mode="json") if hasattr(reasoning, "model_dump") else (dict(reasoning) if isinstance(reasoning, dict) else None)
    pf = proof.model_dump(mode="json") if hasattr(proof, "model_dump") else (dict(proof) if isinstance(proof, dict) else None)
    ans = answer.model_dump(mode="json") if hasattr(answer, "model_dump") else (dict(answer) if isinstance(answer, dict) else None)

    routing = (debug_trace or {}).get("domain_routing") or {}
    predicted_domains = None
    if isinstance(routing, dict):
        primary = routing.get("primary_domains") or []
        secondary = routing.get("secondary_domains") or []
        predicted_domains = [str(x) for x in [*primary, *secondary] if str(x).strip()]
        if not predicted_domains:
            predicted_domains = None

    cross_metrics = _extract_cross_domain_metrics(debug_trace, pf, ans)
    activated_domains = cross_metrics.get("activated_domains")
    bridge_rules_used = cross_metrics.get("bridge_rules_used")
    cross_domain_jumps_attempted = cross_metrics.get("cross_domain_jumps_attempted")
    cross_domain_jumps_success = cross_metrics.get("cross_domain_jumps_success")
    cross_domain_jumps_blocked = cross_metrics.get("cross_domain_jumps_blocked")
    proof_domains = cross_metrics.get("proof_domains")
    final_statute_grounding = cross_metrics.get("final_statute_grounding")

    retrieved_topk = list(retrieved_rules or [])[:8] or None

    requirement_set = None
    missing_facts = None
    if isinstance(rs, dict):
        requirement_set = list(rs.get("requirement_set") or []) or None
        missing_facts = [str(x) for x in (rs.get("missing_facts") or []) if str(x).strip()] or None

    clarification_q = _list_of_dict(list(clarification_questions or []))
    clarification_a = None
    if isinstance(debug_trace, dict):
        ca = debug_trace.get("clarification_answers")
        if isinstance(ca, list):
            clarification_a = _list_of_dict(ca)

    verification_reports = _list_of_dict(list(verification_trace or []))
    repair_actions = _collect_repair_actions(debug_trace)

    evidence_snippets = None
    legal_citations = None
    final_answer = None
    if isinstance(ans, dict):
        evidence_snippets = list(ans.get("evidence_snippets") or []) or None
        legal_citations = list(ans.get("legal_citations") or []) or None
        final_answer = str(ans.get("answer_text") or "").strip() or None
        extra = ans.get("extra") or {}
        if isinstance(extra, dict) and extra.get("evidence_linkage"):
            linkage_rows = []
            for subgoal, ids in (extra.get("evidence_linkage") or {}).items():
                linkage_rows.append({"subgoal": str(subgoal), "evidence_ids": list(ids or [])})
            if linkage_rows:
                repair_actions = list(repair_actions or []) + [{"phase": "evidence_linkage", "rows": linkage_rows}]

    first_error, final_error = _error_stages(debug_trace)

    final_status: str
    if final_answer:
        final_status = "answered"
    elif needs_clarification:
        final_status = "needs_clarification"
    elif final_error:
        final_status = "failed"
    elif pf is not None:
        final_status = "partial"
    else:
        final_status = "open"

    backend_modes = None
    if isinstance(debug_trace, dict) and isinstance(debug_trace.get("backend_modes"), dict):
        backend_modes = dict(debug_trace.get("backend_modes") or {})
    if backend_modes is None:
        parse_meta = (l1 or {}).get("parse_metadata") if isinstance(l1, dict) else {}
        parse_meta = parse_meta if isinstance(parse_meta, dict) else {}
        parse_mode = "fallback" if bool(parse_meta.get("fallback_used")) or str(parse_meta.get("parser_backend") or "") == "heuristic" else "real"
        answer_mode_raw = str((ans or {}).get("generation_mode") or "") if isinstance(ans, dict) else ""
        answer_mode = "real" if answer_mode_raw == "llm_grounded" else ("fallback" if answer_mode_raw else "none")
        verifier_mode = "none"
        if verification_reports:
            traces = [((r or {}).get("extra") or {}).get("nli_trace") for r in verification_reports if isinstance(r, dict)]
            statuses = [str(t.get("nli_status") or "") for t in traces if isinstance(t, dict)]
            if any("degraded" in s for s in statuses):
                verifier_mode = "degraded"
            elif any("mock" in s or "skipped_by_policy" in s for s in statuses):
                verifier_mode = "mock"
            elif any(s == "ok" for s in statuses):
                verifier_mode = "real"
        retrieval_mode = "none"
        backend_name = ""
        if isinstance(debug_trace, dict):
            backend_name = str(((debug_trace.get("rule_retrieval") or {}).get("backend") or "")).strip()
        if backend_name:
            low = backend_name.lower()
            retrieval_mode = "fallback" if "fallback" in low else ("degraded" if "degraded" in low else ("mock" if "mock" in low else "real"))
        backend_modes = {
            "parse_backend": {
                "provider": parse_meta.get("parser_backend"),
                "model": parse_meta.get("parser_model"),
                "mode": parse_mode,
            },
            "answer_backend": {
                "provider": "llm" if answer_mode_raw == "llm_grounded" else ("template" if answer_mode_raw else None),
                "model": answer_mode_raw or None,
                "mode": answer_mode,
            },
            "verifier_backend": {
                "provider": "nesy_engine",
                "model": None,
                "mode": verifier_mode,
            },
            "retrieval_backend": {
                "provider": "internal",
                "model": backend_name or None,
                "mode": retrieval_mode,
            },
        }

    return QAEvaluationLogArtifact(
        sample_id=session_id,
        query_text=query_text,
        parsed_layer1=l1,
        parsed_layer2=l2,
        predicted_domains=predicted_domains,
        activated_domains=activated_domains,
        bridge_rules_used=bridge_rules_used,
        cross_domain_jumps_attempted=cross_domain_jumps_attempted,
        cross_domain_jumps_success=cross_domain_jumps_success,
        cross_domain_jumps_blocked=cross_domain_jumps_blocked,
        retrieved_topk=retrieved_topk,
        selected_rule=selected_rule,
        requirement_set=requirement_set,
        missing_facts=missing_facts,
        clarification_question=clarification_q,
        clarification_answer=clarification_a,
        proof=pf,
        proof_domains=proof_domains,
        final_statute_grounding=final_statute_grounding,
        verification_reports=verification_reports,
        repair_actions=repair_actions,
        evidence_snippets=evidence_snippets,
        legal_citations=legal_citations,
        final_answer=final_answer,
        final_status=final_status,
        error_stage_first=first_error,
        error_stage_final=final_error,
        backend_modes=backend_modes,
    )


def flatten_evaluation_log_for_csv(log: QAEvaluationLogArtifact) -> dict[str, Any]:
    row: dict[str, Any] = {}
    data = log.model_dump(mode="json")
    for key in QA_EVAL_LOG_FIELDS:
        val = data.get(key)
        if isinstance(val, (dict, list)):
            row[key] = json.dumps(val, ensure_ascii=False)
        else:
            row[key] = val
    return row
