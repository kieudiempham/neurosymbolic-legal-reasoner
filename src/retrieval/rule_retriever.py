"""Retrieve and rank rules: BM25 (lexical) + structured v5 hybrid — candidates only; backward decides."""

from __future__ import annotations

import json
import logging
from typing import Any

from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord
from retrieval.hybrid_rule_ranker import bm25_scores_for_documents, hybrid_combine, normalize_scores
from retrieval.retrieval_query import build_rule_retrieval_query
from retrieval.rulebase_loader import RulebaseIndex, get_rulebase_index
from utils.text import lower_fold

logger = logging.getLogger(__name__)


def _token_overlap(a: str, b: str) -> float:
    ta = set(lower_fold(a).replace("_", " ").split())
    tb = set(lower_fold(b).replace("_", " ").split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, len(ta | tb))


def rule_document_text(rule: RuleRecord) -> str:
    """Single searchable document for BM25 (rulebase JSON is read-only; we only compose text)."""
    parts: list[str] = [
        rule.rule_id,
        rule.logic_form,
        rule.head.predicate,
        json.dumps(rule.head.args, ensure_ascii=False),
        json.dumps(rule.body, ensure_ascii=False),
        json.dumps(rule.metadata, ensure_ascii=False),
    ]
    prov = rule.metadata.get("provenance") or {}
    if isinstance(prov, dict):
        parts.extend(str(prov.get(k) or "") for k in ("source_ref", "source_ref_full", "article", "clause"))
    for aux in rule.auxiliary_clauses or []:
        parts.append(json.dumps(aux, ensure_ascii=False))
    return "\n".join(p for p in parts if p)


def structured_score_rule(
    rule: RuleRecord,
    *,
    layer1: Layer1Parse,
    layer2: Layer2Parse,
    goal: dict[str, Any],
) -> tuple[float, dict[str, float], list[str]]:
    """Structured re-rank signals aligned with v5 parse."""
    matched: list[str] = []
    comp: dict[str, float] = {}
    score = 0.0

    gf = goal.get("predicate")
    if gf == rule.head.predicate:
        score += 10.0
        comp["head_predicate_match"] = 10.0
        matched.append("head_predicate")
    else:
        comp["head_predicate_match"] = 0.0

    if layer1.question_focus != "unknown" and layer1.question_focus == rule.logic_form:
        score += 5.0
        comp["logic_form_focus_match"] = 5.0
        matched.append("logic_form")
    else:
        comp["logic_form_focus_match"] = 0.0

    ga = [str(x) for x in (goal.get("args") or [])]
    ha = [str(x) for x in rule.head.args]
    arg_ov = 0.0
    for g in ga:
        for h in ha:
            arg_ov += _token_overlap(g, h)
    comp["goal_head_arg_overlap"] = 2.0 * arg_ov
    score += 2.0 * arg_ov
    if arg_ov > 0.01:
        matched.append("goal_head_args")

    qtext = f"{layer1.subject_text} {layer1.action_text} {layer1.modality_text}"
    act_ov = 0.0
    for atom in ha:
        act_ov += _token_overlap(qtext, atom)
    comp["action_modality_overlap"] = 1.5 * act_ov
    score += 1.5 * act_ov
    if act_ov > 0.01:
        matched.append("action_modality")

    blob = str(rule.head.args) + str(rule.body)
    cond_ov = 0.0
    for c in layer2.condition_atoms or []:
        cond_ov += 2.0 * _token_overlap(blob, c)
    comp["condition_atom_overlap"] = cond_ov
    score += cond_ov
    if cond_ov > 0.01:
        matched.append("condition_atoms")

    if layer2.subject_normalized and layer2.subject_normalized in blob:
        score += 1.0
        comp["subject_id_in_rule"] = 1.0
        matched.append("subject_normalized")
    else:
        comp["subject_id_in_rule"] = 0.0

    if layer2.subject_type_guess and layer2.subject_type_guess != "unknown":
        if layer2.subject_type_guess in lower_fold(blob):
            score += 0.8
            comp["subject_type_guess"] = 0.8
            matched.append("subject_type")
        else:
            comp["subject_type_guess"] = 0.0
    else:
        comp["subject_type_guess"] = 0.0

    td = (layer1.time_text or "") + " " + (layer1.deadline_text or "")
    if td.strip() and any(
        x in lower_fold(blob) for x in ("thời hạn", "thoi han", "ngày", "deadline", "han")
    ):
        to = _token_overlap(td, blob)
        score += 1.2 * to
        comp["time_deadline_relevance"] = 1.2 * to
        if to > 0.01:
            matched.append("time_deadline")
    else:
        comp["time_deadline_relevance"] = 0.0

    ex = layer1.exception_text or ""
    if ex.strip():
        to = _token_overlap(ex, blob)
        score += 1.2 * to
        comp["exception_relevance"] = 1.2 * to
        if to > 0.01:
            matched.append("exception")
    else:
        comp["exception_relevance"] = 0.0

    md = rule.metadata or {}
    dom = str(md.get("domain") or md.get("doc_domain") or "")
    if dom and dom in lower_fold(build_rule_retrieval_query(layer1, layer2)):
        score += 0.5
        comp["metadata_domain"] = 0.5
    else:
        comp["metadata_domain"] = 0.0

    comp["structured_total"] = score
    return score, comp, matched


def score_rule(
    rule: RuleRecord,
    *,
    layer1: Layer1Parse,
    layer2: Layer2Parse,
    goal: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    """Backward-compatible aggregate structured score."""
    s, comp, mf = structured_score_rule(rule, layer1=layer1, layer2=layer2, goal=goal)
    diag: dict[str, Any] = {"final_score": s, "score_components": comp, "matched_features": mf}
    return s, diag


def retrieve_rules(
    *,
    layer1: Layer1Parse,
    layer2: Layer2Parse,
    top_k: int = 8,
    index: RulebaseIndex | None = None,
    w_lexical: float = 0.35,
    w_structured: float = 0.65,
) -> list[tuple[RuleRecord, float, dict[str, Any]]]:
    """
    Return top-k candidate rules for backward chaining.

    Each tuple is ``(rule, score_total, diagnostics)`` where diagnostics includes
    BM25 + structured breakdown; backward chaining remains authoritative for unification.
    """
    idx = index or get_rulebase_index()
    goal = layer2.goal
    gp = goal.get("predicate")
    pool = idx.all()
    if isinstance(gp, str) and gp and gp != "unknown":
        filtered = [r for r in pool if r.head.predicate == gp]
        if filtered:
            pool = filtered

    if not pool:
        return []

    documents = [rule_document_text(r) for r in pool]
    query = build_rule_retrieval_query(layer1, layer2, goal=goal)
    try:
        bm25_raw = bm25_scores_for_documents(documents, query)
    except Exception as e:  # pragma: no cover
        logger.warning("bm25 fallback zeros: %s", e)
        bm25_raw = [0.0] * len(pool)

    struct_raw: list[float] = []
    struct_diags: list[tuple[dict[str, float], list[str]]] = []
    for r in pool:
        s, comp, mf = structured_score_rule(r, layer1=layer1, layer2=layer2, goal=goal)
        struct_raw.append(s)
        struct_diags.append((comp, mf))

    bm25_norm = normalize_scores(bm25_raw)
    struct_norm = normalize_scores(struct_raw)
    hybrid = hybrid_combine(bm25_norm, struct_norm, w_lex=w_lexical, w_struct=w_structured)

    ranked: list[tuple[RuleRecord, float, dict[str, Any]]] = []
    for i, rule in enumerate(pool):
        total = hybrid[i]
        br, sr = bm25_raw[i], struct_raw[i]
        comp, mf = struct_diags[i]
        diag: dict[str, Any] = {
            "final_score": total,
            "score_total": total,
            "bm25_raw": br,
            "bm25_norm": bm25_norm[i],
            "structured_raw": sr,
            "structured_norm": struct_norm[i],
            "hybrid_weights": {"lexical": w_lexical, "structured": w_structured},
            "score_components": comp,
            "matched_features": mf,
            "retrieval_query_preview": query[:500],
        }
        ranked.append((rule, total, diag))

    ranked.sort(key=lambda x: -x[1])
    return ranked[:top_k]


class RuleRetriever:
    """Legacy stub — use retrieve_rules() for the QA pipeline."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def retrieve(self, layer2: Any, top_k: int) -> list[Any]:
        raise NotImplementedError
