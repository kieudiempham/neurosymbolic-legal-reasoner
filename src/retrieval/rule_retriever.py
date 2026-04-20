"""Retrieve and rank rules: BM25 (lexical) + structured v5 hybrid — candidates only; backward decides."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord
from retrieval.hybrid_rule_ranker import bm25_scores_for_documents, hybrid_combine, normalize_scores
from retrieval.retrieval_query import build_rule_retrieval_query
from retrieval.rulebase_loader import RulebaseIndex, get_rulebase_index
from utils.text import lower_fold

logger = logging.getLogger(__name__)

_SYMBOLIC_TOKEN = re.compile(r"^[A-Z_][A-Z0-9_]{0,4}$")
_GENERIC_BODY_PREDICATES = {
    "applies_if",
    "condition",
    "eligible",
    "subject",
    "fact",
    "context",
}

_GOAL_FAMILY_BY_PREDICATE: dict[str, str] = {
    "obligation": "obligation",
    "permission": "permission",
    "prohibition": "prohibition",
    "deadline": "deadline",
    "regulatory_deadline": "deadline",
    "regulatory_deadline_requirement": "deadline",
    "threshold": "threshold",
    "applicability": "applicability",
    "legal_effect": "legal_effect",
}


def _is_shared_rule(rule: RuleRecord) -> bool:
    md = rule.metadata or {}
    return (
        str(md.get("domain") or "") == "shared"
        or str(md.get("layer") or "") == "shared"
        or str(rule.rule_id).startswith("shared_motif_")
    )


def _goal_semantic_family(layer1: Layer1Parse, goal: dict[str, Any]) -> str:
    gp = str(goal.get("predicate") or "").strip().lower()
    if gp and gp != "unknown":
        return _GOAL_FAMILY_BY_PREDICATE.get(gp, gp)
    qf = str(layer1.question_focus or "").strip().lower()
    if qf and qf != "unknown":
        return _GOAL_FAMILY_BY_PREDICATE.get(qf, qf)
    return ""


def _rule_semantic_family(rule: RuleRecord) -> str:
    hp = str(rule.head.predicate or "").strip().lower()
    if hp and hp != "unknown":
        return _GOAL_FAMILY_BY_PREDICATE.get(hp, hp)
    lf = str(rule.logic_form or "").strip().lower()
    if lf and lf != "unknown":
        return _GOAL_FAMILY_BY_PREDICATE.get(lf, lf)
    motif = str((rule.metadata or {}).get("motif") or "").strip().lower()
    if motif:
        return _GOAL_FAMILY_BY_PREDICATE.get(motif, motif)
    return ""


def _head_matches_goal_family(rule: RuleRecord, goal_family: str) -> bool:
    if not goal_family:
        return False
    return _rule_semantic_family(rule) == goal_family


def _is_symbolic_placeholder(value: str) -> bool:
    s = value.strip()
    if not s:
        return True
    if _SYMBOLIC_TOKEN.fullmatch(s):
        return True
    sl = lower_fold(s)
    return sl.startswith("unresolved_") or sl.endswith("_atom")


def _is_generic_condition_atom(value: str) -> bool:
    v = lower_fold(str(value or "").strip())
    return v.startswith("stated_condition(")


def _token_overlap(a: str, b: str) -> float:
    ta = set(lower_fold(a).replace("_", " ").split())
    tb = set(lower_fold(b).replace("_", " ").split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, len(ta | tb))


def _is_generic_head_arg(arg: str) -> bool:
    s = str(arg or "").strip()
    if not s:
        return True
    if _is_symbolic_placeholder(s):
        return True
    return bool(re.fullmatch(r"[a-z]", s.lower()))


def _is_generic_attractor_rule(rule: RuleRecord) -> bool:
    body_preds = [str((x or {}).get("predicate") or "").strip().lower() for x in (rule.body or [])]
    generic_body = not body_preds or all(p in _GENERIC_BODY_PREDICATES for p in body_preds)
    head_args = [str(x) for x in (rule.head.args or [])]
    if not head_args:
        return generic_body
    generic_arg_ratio = sum(1 for a in head_args if _is_generic_head_arg(a)) / max(1, len(head_args))
    return generic_body and generic_arg_ratio >= 0.67


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

    # Prevent dossier/procedure forms from dominating permission-style questions.
    if layer1.question_focus == "permission" and rule.logic_form in {
        "dossier",
        "procedure_step",
        "deadline",
        "threshold",
    }:
        score -= 3.0
        comp["focus_logic_penalty"] = -3.0
    elif layer1.question_focus == "permission" and rule.logic_form in {"obligation", "legal_effect"}:
        score += 1.0
        comp["focus_logic_penalty"] = 1.0
    else:
        comp["focus_logic_penalty"] = 0.0

    ga = [str(x) for x in (goal.get("args") or [])]
    ha = [str(x) for x in rule.head.args]
    arg_ov = 0.0
    for g in ga:
        if _is_symbolic_placeholder(g):
            continue
        for h in ha:
            if _is_symbolic_placeholder(h):
                continue
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
        if _is_generic_condition_atom(str(c)):
            continue
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

    goal_family = _goal_semantic_family(layer1, goal)
    rule_family = _rule_semantic_family(rule)
    if goal_family and rule_family:
        if goal_family == rule_family:
            score += 2.0
            comp["semantic_compatibility"] = 2.0
            matched.append("semantic_family")
        else:
            mismatch_penalty = 1.5
            if _is_shared_rule(rule):
                mismatch_penalty += 1.5
            if goal_family in {"permission", "obligation", "prohibition", "applicability", "legal_effect"} and rule_family in {
                "deadline",
                "threshold",
                "dossier",
                "procedure",
            }:
                mismatch_penalty += 1.5
            score -= mismatch_penalty
            comp["semantic_compatibility"] = -mismatch_penalty
    else:
        comp["semantic_compatibility"] = 0.0

    if _is_shared_rule(rule):
        has_anchor = any(
            (
                comp.get("head_predicate_match", 0.0) > 0.0,
                comp.get("goal_head_arg_overlap", 0.0) > 0.01,
                comp.get("condition_atom_overlap", 0.0) > 0.01,
                comp.get("action_modality_overlap", 0.0) > 0.01,
            )
        )
        if not has_anchor:
            score -= 1.5
            comp["shared_generic_anchor_penalty"] = -1.5
        else:
            comp["shared_generic_anchor_penalty"] = 0.0
    else:
        comp["shared_generic_anchor_penalty"] = 0.0

    anchor_strength = (
        max(0.0, comp.get("head_predicate_match", 0.0))
        + max(0.0, comp.get("goal_head_arg_overlap", 0.0))
        + max(0.0, comp.get("condition_atom_overlap", 0.0))
        + max(0.0, comp.get("action_modality_overlap", 0.0))
    )
    query_blob = f"{layer1.subject_text} {layer1.action_text} {layer1.modality_text}".strip()
    query_terms = [t for t in lower_fold(query_blob).split() if t]
    lexical_shortcut = len(query_terms) <= 3

    if _is_generic_attractor_rule(rule):
        attractor_penalty = 0.0
        if anchor_strength < 2.0:
            attractor_penalty += 1.8
        if lexical_shortcut:
            attractor_penalty += 0.7
        if comp.get("semantic_compatibility", 0.0) < 0:
            attractor_penalty += 1.3
        dom = str((rule.metadata or {}).get("domain") or "").lower()
        if dom in {"labor", "lao_dong"} and anchor_strength < 3.0:
            attractor_penalty += 0.8
        if attractor_penalty > 0:
            score -= attractor_penalty
            comp["attractor_penalty"] = -attractor_penalty
        else:
            comp["attractor_penalty"] = 0.0
    else:
        comp["attractor_penalty"] = 0.0

    comp["semantic_anchor_strength"] = anchor_strength

    if score < 0.0:
        comp["structured_floor_applied"] = -score
        score = 0.0
    else:
        comp["structured_floor_applied"] = 0.0

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
    goal_family = _goal_semantic_family(layer1, goal)
    if isinstance(gp, str) and gp and gp != "unknown":
        filtered = [r for r in pool if r.head.predicate == gp]
        if not filtered and goal_family:
            filtered = [r for r in pool if _head_matches_goal_family(r, goal_family)]
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
        base_total = hybrid[i]
        br, sr = bm25_raw[i], struct_raw[i]
        comp, mf = struct_diags[i]
        tie_adjust = 0.0
        if sr > 0.0:
            tie_adjust += min(0.05, sr * 0.01)
        if sr <= 0.0 and _is_shared_rule(rule):
            tie_adjust -= 0.03
        if br <= 0.0 and sr <= 0.0 and _is_shared_rule(rule):
            tie_adjust -= 0.04
        total = base_total + tie_adjust
        diag: dict[str, Any] = {
            "final_score": total,
            "score_total": total,
            "score_total_base": base_total,
            "tie_break_adjustment": tie_adjust,
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
