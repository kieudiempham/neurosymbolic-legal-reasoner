"""Retrieve and rank rules: BM25 (lexical) + structured v5 hybrid — candidates only; backward decides."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord
from retrieval.hybrid_rule_ranker import bm25_scores_for_documents, normalize_scores
from retrieval.retrieval_query import build_rule_retrieval_query
from retrieval.rulebase_loader import RulebaseIndex, get_rulebase_index
from utils.semantic_families import normalize_predicate_family
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

_REGISTRATION_CHANGE_ATOM = "dang_ky_thay_doi_noi_dung_dang_ky_doanh_nghiep"
_REGISTRATION_ACTION_HINTS = {
    "gui_thong_bao",
    "thong_bao_thay_doi_noi_dung_dang_ky_doanh_nghiep",
    "thong_bao_thay_doi",
}
_ENTERPRISE_REGISTRATION_ANCHORS = (
    "thay doi noi dung dang ky doanh nghiep",
    "thong bao thay doi noi dung dang ky doanh nghiep",
    "dang ky doanh nghiep",
    "enterprise_registration",
    "deadline",
)
_TAX_ATTRACTOR_TERMS = (
    "thuc_hien_nop_thay_so_tien_thue_bi_cuong_che",
    "cuong che thue",
    "nop thay tien thue",
    "nguoi nop thue bi cuong che",
    "thue bi cuong che",
    "nop_thay",
    "cuong_che",
)

_CONTEXT_SIGNAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "inheritance": (
        "thua ke",
        "thua_ke",
        "di san",
        "di_san",
        "nguoi thua ke",
        "nguoi_thua_ke",
        "thua ke co phan",
    ),
    "ownership_transfer": (
        "chuyen nhuong",
        "chuyen_nhuong",
        "chuyen quyen so huu",
        "chuyen_quyen_so_huu",
        "mua ban co phan",
        "sang ten",
    ),
    "merger": (
        "sap nhap",
        "sap_nhap",
        "hop nhat",
        "hop_nhat",
        "chia tach",
        "chia_tach",
        "tai cau truc",
        "tai_cau_truc",
    ),
    "bankruptcy": (
        "pha san",
        "pha_san",
        "mat kha nang thanh toan",
        "mat_kha_nang_thanh_toan",
        "giai the",
        "giai_the",
    ),
    "tax_enforcement": (
        "cuong che thue",
        "cuong_che",
        "nop thay tien thue",
        "nop_thay",
        "bien phap cuong che",
        "thu hoi no thue",
        "thu_hoi_no_thue",
    ),
}


def _norm_predicate_token(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "", lower_fold((value or "").strip()))


def _extract_atom_predicate(atom: Any) -> str:
    if isinstance(atom, dict):
        return _norm_predicate_token(str(atom.get("predicate") or ""))
    s = lower_fold(str(atom or "").strip())
    if not s:
        return ""
    pred = s.split("(", 1)[0].strip() if "(" in s else s.split()[0].strip()
    return _norm_predicate_token(pred)


def _layer2_condition_predicates(layer2: Layer2Parse) -> set[str]:
    out: set[str] = set()
    for atom in layer2.condition_atoms or []:
        pred = _extract_atom_predicate(atom)
        if pred and pred not in _GENERIC_BODY_PREDICATES:
            out.add(pred)
    return out


def _rule_condition_predicates(rule: RuleRecord) -> set[str]:
    out: set[str] = set()
    for atom in rule.body or []:
        pred = _extract_atom_predicate(atom)
        if pred:
            out.add(pred)
    hp = _norm_predicate_token(str(rule.head.predicate or ""))
    if hp:
        out.add(hp)
    return out


def _layer2_event_type(layer2: Layer2Parse) -> str:
    diagnostics = dict(getattr(layer2, "diagnostics", None) or {})
    cond_norm = dict(diagnostics.get("condition_normalization") or {})
    frame = dict(cond_norm.get("frame") or {})
    return _norm_predicate_token(str(frame.get("event_type") or ""))


def _rule_event_type(rule: RuleRecord) -> str:
    md = rule.metadata or {}
    for raw in (
        md.get("event_type"),
        md.get("canonical_predicate"),
        md.get("condition_predicate"),
        md.get("motif"),
    ):
        candidate = _norm_predicate_token(str(raw or ""))
        if candidate and candidate != "unknown":
            return candidate
    cond_preds = _rule_condition_predicates(rule)
    if cond_preds:
        return sorted(cond_preds)[0]
    return ""


def _layer2_action_object(layer2: Layer2Parse, goal: dict[str, Any]) -> tuple[str, str]:
    diagnostics = dict(getattr(layer2, "diagnostics", None) or {})
    goal_can = dict(diagnostics.get("goal_canonicalization") or {})
    action = _norm_predicate_token(str(goal_can.get("action_canonical") or ""))
    obj = _norm_predicate_token(str(goal_can.get("object_canonical") or ""))
    args = [str(x or "") for x in (goal.get("args") or [])]
    if not action and len(args) >= 2:
        action = _norm_predicate_token(args[1])
    if not obj and len(args) >= 3:
        obj = _norm_predicate_token(args[2])
    return action, obj


def map_action_group(action: str) -> str:
    if not action:
        return "other"
    a = action.lower()
    if "thong_bao" in a or "gui" in a:
        return "notification"
    if "dang_ky" in a or "cap_nhat" in a:
        return "registration"
    if "nop" in a or "bo_sung" in a or "ho_so" in a:
        return "submission"
    if "thue" in a or "le_phi" in a or "tien" in a:
        return "payment"
    if "cuong_che" in a or "xu_phat" in a:
        return "enforcement"
    return "other"


def _is_action_group_conflict(query_group: str, rule_group: str) -> bool:
    if not query_group or not rule_group:
        return False
    if query_group == rule_group:
        return False
    return (query_group, rule_group) in {
        ("notification", "payment"),
        ("notification", "enforcement"),
        ("notification", "submission"),
        ("registration", "payment"),
        ("registration", "enforcement"),
        ("registration", "submission"),
        ("payment", "notification"),
        ("payment", "registration"),
        ("payment", "submission"),
        ("enforcement", "notification"),
        ("enforcement", "registration"),
        ("enforcement", "submission"),
        ("submission", "notification"),
        ("submission", "registration"),
        ("submission", "payment"),
    }


def _infer_rule_action_token(rule: RuleRecord) -> str:
    head = _norm_predicate_token(str(rule.head.predicate or ""))
    if head:
        return head
    for atom in rule.body or []:
        pred = _extract_atom_predicate(atom)
        if pred:
            return pred
    return ""


def _is_strong_action_group_conflict(query_group: str, rule_group: str) -> bool:
    if not query_group or not rule_group:
        return False
    pair = (query_group, rule_group)
    return pair in {
        ("notification", "payment"),
        ("notification", "enforcement"),
        ("registration", "payment"),
        ("registration", "enforcement"),
        ("payment", "notification"),
        ("enforcement", "notification"),
        ("payment", "registration"),
        ("enforcement", "registration"),
    }


def _rule_action_object_blob(rule: RuleRecord) -> str:
    parts: list[str] = [
        str(rule.head.predicate or ""),
        " ".join(str(x or "") for x in (rule.head.args or [])),
        " ".join(str((x or {}).get("predicate") or "") for x in (rule.body or [])),
    ]
    return lower_fold(" ".join(parts))


def _rule_semantic_blob(rule: RuleRecord) -> str:
    md = rule.metadata or {}
    prov = md.get("provenance") or {}
    parts: list[str] = [
        str(rule.logic_form or ""),
        str(rule.head.predicate or ""),
        " ".join(str(x or "") for x in (rule.head.args or [])),
        " ".join(str((b or {}).get("predicate") or "") for b in (rule.body or [])),
        json.dumps(rule.body or [], ensure_ascii=False),
        str(md.get("domain") or ""),
        str(md.get("layer") or ""),
        str(md.get("source_doc") or ""),
        str(md.get("source_article") or ""),
        str(prov.get("source_ref_full") or ""),
        str(prov.get("source_ref") or ""),
        str(prov.get("surface_text") or ""),
    ]
    return lower_fold(" ".join(p for p in parts if p))


def _rule_context_blob(rule: RuleRecord) -> str:
    md = rule.metadata or {}
    prov = md.get("provenance") or {}
    parts: list[str] = [
        json.dumps(rule.body or [], ensure_ascii=False),
        str(md.get("source_doc") or ""),
        str(md.get("source_article") or ""),
        str(prov.get("source_ref_full") or ""),
        str(prov.get("source_ref") or ""),
        str(prov.get("surface_text") or ""),
    ]
    return lower_fold(" ".join(p for p in parts if p))


def _query_context_blob(layer1: Layer1Parse, layer2: Layer2Parse, goal: dict[str, Any]) -> str:
    diagnostics = dict(getattr(layer2, "diagnostics", None) or {})
    cond_norm = dict(diagnostics.get("condition_normalization") or {})
    frame = dict(cond_norm.get("frame") or {})
    goal_can = dict(diagnostics.get("goal_canonicalization") or {})
    goal_args = " ".join(str(x or "") for x in (goal.get("args") or []))
    parts: list[str] = [
        str(layer1.subject_text or ""),
        str(layer1.condition_text or ""),
        str(layer1.action_text or ""),
        str(layer1.time_text or ""),
        str(layer1.deadline_text or ""),
        str(layer1.exception_text or ""),
        " ".join(str(x or "") for x in (layer2.condition_atoms or [])),
        str(goal.get("predicate") or ""),
        goal_args,
        str(frame.get("event_type") or ""),
        str(goal_can.get("action_canonical") or ""),
        str(goal_can.get("object_canonical") or ""),
    ]
    return lower_fold(" ".join(p for p in parts if p))


def _detect_context_signals(blob: str) -> set[str]:
    hits: set[str] = set()
    for label, keywords in _CONTEXT_SIGNAL_KEYWORDS.items():
        if any(k in blob for k in keywords):
            hits.add(label)
    return hits


def _is_enterprise_registration_deadline_query(
    *,
    layer1: Layer1Parse,
    layer2: Layer2Parse,
    goal: dict[str, Any],
) -> bool:
    goal_pred = str(goal.get("predicate") or "").strip().lower()

    diagnostics = dict(getattr(layer2, "diagnostics", None) or {})
    cond_norm = dict(diagnostics.get("condition_normalization") or {})
    cond_domain = str(cond_norm.get("domain") or "").strip().lower()
    has_enterprise_domain = cond_domain == "enterprise_registration"

    cond_atoms = [str(a or "").strip().lower() for a in (layer2.condition_atoms or []) if str(a or "").strip()]
    has_registration_atom = any(_REGISTRATION_CHANGE_ATOM in a for a in cond_atoms)

    parse_text_blob = lower_fold(
        " ".join(
            [
                str(layer1.subject_text or ""),
                str(layer1.condition_text or ""),
                str(layer1.action_text or ""),
                str(layer1.time_text or ""),
                str(layer1.deadline_text or ""),
            ]
        )
    )
    has_registration_text = (
        "thay doi noi dung dang ky doanh nghiep" in parse_text_blob
        or "dang ky doanh nghiep" in parse_text_blob
        or "thong bao thay doi noi dung dang ky doanh nghiep" in parse_text_blob
    )

    action_blob = lower_fold(
        " ".join(
            [
                str(layer1.action_text or ""),
                " ".join(str(x or "") for x in (goal.get("args") or [])),
            ]
        )
    )
    has_notification_action = any(h in action_blob for h in _REGISTRATION_ACTION_HINTS) or (
        "gui thong bao" in action_blob
    )

    has_deadline_signal = (
        goal_pred == "deadline"
        or str(layer1.question_focus or "").strip().lower() == "deadline"
        or any(x in parse_text_blob for x in ("thoi han", "may ngay", "ngay", "deadline"))
    )

    has_registration_signal = has_registration_atom or has_registration_text

    if has_enterprise_domain and has_registration_atom and has_notification_action and has_deadline_signal:
        return True

    return has_registration_signal and has_notification_action and has_deadline_signal


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
        return normalize_predicate_family(gp)
    qf = str(layer1.question_focus or "").strip().lower()
    if qf and qf != "unknown":
        return normalize_predicate_family(qf)
    return ""


def _rule_semantic_family(rule: RuleRecord) -> str:
    hp = str(rule.head.predicate or "").strip().lower()
    if hp and hp != "unknown":
        return normalize_predicate_family(hp)
    lf = str(rule.logic_form or "").strip().lower()
    if lf and lf != "unknown":
        return normalize_predicate_family(lf)
    motif = str((rule.metadata or {}).get("motif") or "").strip().lower()
    if motif:
        return normalize_predicate_family(motif)
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
    q_action, q_object = _layer2_action_object(layer2, goal)
    rule_action_token = _infer_rule_action_token(rule)
    rule_action_blob = _rule_action_object_blob(rule)

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
        "procedure",
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
    semantic_blob = _rule_semantic_blob(rule)
    layer2_event = _layer2_event_type(layer2)
    rule_event = _rule_event_type(rule)
    query_cond_preds = _layer2_condition_predicates(layer2)
    rule_cond_preds = _rule_condition_predicates(rule)

    event_type_match = 0.0
    if layer2_event and (layer2_event == rule_event or layer2_event in rule_cond_preds):
        event_type_match = 7.0
        score += event_type_match
        matched.append("event_type")
    comp["event_type_match"] = event_type_match

    cond_ov = 0.0
    if query_cond_preds and rule_cond_preds:
        inter = query_cond_preds & rule_cond_preds
        union = query_cond_preds | rule_cond_preds
        if inter:
            cond_ov = 6.0 * (len(inter) / max(1, len(union)))
            if query_cond_preds.issubset(rule_cond_preds):
                cond_ov += 2.0
            elif len(inter) >= 2:
                cond_ov += 1.0
            score += cond_ov
    comp["condition_atom_overlap"] = cond_ov
    if cond_ov > 0.01:
        matched.append("condition_atoms")

    if event_type_match > 0.0 and cond_ov > 0.01:
        score += 2.5
        comp["event_atom_alignment_bonus"] = 2.5
        matched.append("event_atom_alignment")
    else:
        comp["event_atom_alignment_bonus"] = 0.0

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
    goal_family_score = 0.0
    if goal_family and rule_family:
        if goal_family == rule_family:
            goal_family_score = 3.5
            if goal_family == "deadline":
                deadline_action_overlap = _token_overlap(q_action.replace("_", " "), rule_action_token) if q_action and rule_action_token else 0.0
                deadline_object_overlap = _token_overlap(q_object.replace("_", " "), rule_action_blob) if q_object else 0.0
                deadline_anchor = max(deadline_action_overlap, deadline_object_overlap)
                comp["deadline_action_overlap"] = deadline_action_overlap
                comp["deadline_object_overlap"] = deadline_object_overlap
                if deadline_anchor < 0.35:
                    goal_family_score -= 2.5
                    comp["deadline_event_action_mismatch"] = -2.5
                    comp["deadline_event_action_reason"] = "deadline_family_but_event_action_mismatch"
                    matched.append("deadline_event_action_mismatch")
                else:
                    comp["deadline_event_action_mismatch"] = 0.0
                    comp["deadline_event_action_reason"] = "deadline_family_and_event_anchor"
            else:
                comp["deadline_action_overlap"] = 0.0
                comp["deadline_object_overlap"] = 0.0
                comp["deadline_event_action_mismatch"] = 0.0
            score += goal_family_score
            matched.append("semantic_family")
        else:
            mismatch_penalty = 3.5
            if _is_shared_rule(rule):
                mismatch_penalty += 2.0
            if goal_family in {"permission", "obligation", "prohibition", "applicability", "legal_effect"} and rule_family in {
                "deadline",
                "threshold",
                "dossier",
                "procedure",
            }:
                mismatch_penalty += 2.5
            score -= mismatch_penalty
            goal_family_score = -mismatch_penalty
    else:
        goal_family_score = 0.0
    comp["goal_family_match"] = goal_family_score
    # Keep legacy key for downstream diagnostics compatibility.
    comp["semantic_compatibility"] = goal_family_score

    action_obj_score = 0.0
    if q_action:
        action_obj_score += 2.2 * _token_overlap(q_action.replace("_", " "), rule_action_blob)
    if q_object:
        action_obj_score += 1.8 * _token_overlap(q_object.replace("_", " "), rule_action_blob)
    if action_obj_score > 0.0:
        score += action_obj_score
        matched.append("action_object")
    comp["action_object_similarity"] = action_obj_score
    comp["action_object_match"] = action_obj_score

    action_group_score = 0.0
    query_action_group = map_action_group(q_action)
    rule_action_group = map_action_group(rule_action_token)
    if query_action_group == rule_action_group and query_action_group != "other":
        action_group_score = 2.0
    elif _is_action_group_conflict(query_action_group, rule_action_group):
        action_group_score = -3.5
    comp["action_group_score"] = action_group_score

    query_context_blob = _query_context_blob(layer1, layer2, goal)
    rule_context_blob = _rule_context_blob(rule)
    query_context_signals = _detect_context_signals(query_context_blob)
    rule_context_signals = _detect_context_signals(rule_context_blob)
    missing_context_signals = rule_context_signals - query_context_signals

    context_mismatch_penalty = 0.0
    if missing_context_signals:
        context_mismatch_penalty += 2.2 * len(missing_context_signals)
        if "tax_enforcement" in missing_context_signals:
            context_mismatch_penalty += 1.8
        score -= context_mismatch_penalty
        matched.append("context_mismatch")
    comp["context_mismatch_penalty"] = -context_mismatch_penalty
    comp["context_rule_signal_count"] = float(len(rule_context_signals))
    comp["context_query_signal_count"] = float(len(query_context_signals))
    comp["context_missing_signal_count"] = float(len(missing_context_signals))

    query_is_enterprise_registration_deadline = _is_enterprise_registration_deadline_query(
        layer1=layer1,
        layer2=layer2,
        goal=goal,
    )

    if query_is_enterprise_registration_deadline:
        positive_boost = 0.0
        if any(anchor in semantic_blob for anchor in _ENTERPRISE_REGISTRATION_ANCHORS):
            positive_boost += 4.0
        rule_domain = str(md.get("domain") or "").strip().lower()
        if rule_domain in {"enterprise", "enterprise_registration", "shared"}:
            positive_boost += 1.5
        if str(rule.head.predicate or "").strip().lower() in {
            "deadline",
            "regulatory_deadline",
            "regulatory_deadline_requirement",
        }:
            positive_boost += 1.5
        if positive_boost > 0.0:
            score += positive_boost
            matched.append("enterprise_registration_positive")
        comp["enterprise_registration_positive_boost"] = positive_boost

        tax_attractor_penalty = 0.0
        if any(term in semantic_blob for term in _TAX_ATTRACTOR_TERMS):
            tax_attractor_penalty = 22.0
            score -= tax_attractor_penalty
            matched.append("tax_attractor_penalized")
        comp["tax_attractor_penalty"] = -tax_attractor_penalty

        semantic_family_mismatch_penalty = 0.0
        if any(
            term in semantic_blob
            for term in (
                "thuc_hien_nop_thay_so_tien_thue_bi_cuong_che",
                "cuong che thue",
                "nop thay tien thue",
                "nguoi nop thue bi cuong che",
                "ben thu ba",
            )
        ):
            semantic_family_mismatch_penalty = 10.0
            score -= semantic_family_mismatch_penalty
        comp["semantic_family_mismatch_penalty"] = -semantic_family_mismatch_penalty
    else:
        comp["enterprise_registration_positive_boost"] = 0.0
        comp["tax_attractor_penalty"] = 0.0
        comp["semantic_family_mismatch_penalty"] = 0.0

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
            score -= 3.5
            comp["shared_generic_anchor_penalty"] = -3.5
        else:
            comp["shared_generic_anchor_penalty"] = 0.0
    else:
        comp["shared_generic_anchor_penalty"] = 0.0

    anchor_strength = (
        max(0.0, comp.get("head_predicate_match", 0.0))
        + max(0.0, comp.get("event_type_match", 0.0))
        + max(0.0, comp.get("goal_family_match", 0.0))
        + max(0.0, comp.get("goal_head_arg_overlap", 0.0))
        + max(0.0, comp.get("condition_atom_overlap", 0.0))
        + max(0.0, comp.get("action_modality_overlap", 0.0))
        + max(0.0, comp.get("action_object_similarity", 0.0))
    )
    query_blob = f"{layer1.subject_text} {layer1.action_text} {layer1.modality_text}".strip()
    query_terms = [t for t in lower_fold(query_blob).split() if t]
    lexical_shortcut = len(query_terms) <= 3

    if _is_generic_attractor_rule(rule):
        attractor_penalty = 0.0
        if anchor_strength < 2.0:
            attractor_penalty += 1.8
        if anchor_strength < 4.0:
            attractor_penalty += 0.8
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
    w_lexical: float = 0.25,
    w_structured: float = 0.75,
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

    ranked: list[tuple[RuleRecord, float, dict[str, Any]]] = []
    semantic_rows: list[dict[str, Any]] = []
    query_action_canonical, _ = _layer2_action_object(layer2, goal)
    query_action_group = map_action_group(query_action_canonical)
    for i, rule in enumerate(pool):
        br, sr = bm25_raw[i], struct_raw[i]
        comp, mf = struct_diags[i]
        rule_family = _rule_semantic_family(rule)

        domain_match = 1.0 if comp.get("metadata_domain", 0.0) > 0.0 else 0.0
        event_type_match = 1.0 if comp.get("event_type_match", 0.0) > 0.0 else 0.0
        condition_atom_signal = min(1.0, max(0.0, float(comp.get("condition_atom_overlap", 0.0))) / 6.0)
        goal_family_match = 1.0 if comp.get("goal_family_match", 0.0) > 0.0 else 0.0
        action_object_match = min(1.0, max(0.0, float(comp.get("action_object_match", 0.0))) / 2.0)
        context_penalty_signal = max(0.0, -float(comp.get("context_mismatch_penalty", 0.0)))

        rule_action_token = _infer_rule_action_token(rule)
        rule_action_group = map_action_group(rule_action_token)
        action_group_score = 0.0
        if query_action_group == rule_action_group and query_action_group != "other":
            action_group_score = 2.0
        elif _is_strong_action_group_conflict(query_action_group, rule_action_group):
            action_group_score = -3.5

        semantic_total = (
            0.75 * domain_match
            + 2.75 * event_type_match
            + 2.25 * condition_atom_signal
            + 2.0 * goal_family_match
            + 1.75 * action_object_match
            - 2.25 * context_penalty_signal
            + action_group_score
        )

        lexical_tie_bonus = 0.05 * bm25_norm[i]
        if goal_family and rule_family and goal_family != rule_family:
            lexical_tie_bonus *= 0.2
        if comp.get("deadline_event_action_mismatch", 0.0) < 0.0:
            lexical_tie_bonus *= 0.4
        total = semantic_total + lexical_tie_bonus

        semantic_rows.append(
            {
                "index": i,
                "semantic_total": semantic_total,
                "event_type_match": event_type_match,
                "condition_atom_signal": condition_atom_signal,
                "bm25_norm": bm25_norm[i],
                "action_group_score": action_group_score,
            }
        )

        diag: dict[str, Any] = {
            "final_score": total,
            "score_total": total,
            "score_total_base": semantic_total,
            "tie_break_adjustment": lexical_tie_bonus,
            "bm25_raw": br,
            "bm25_norm": bm25_norm[i],
            "structured_raw": sr,
            "structured_norm": struct_norm[i],
            "hybrid_weights": {"lexical": w_lexical, "structured": w_structured},
            "semantic_formula_signals": {
                "domain_match": domain_match,
                "event_type_match": event_type_match,
                "condition_atom_overlap": condition_atom_signal,
                "goal_family_match": goal_family_match,
                "action_object_match": action_object_match,
                "context_mismatch_penalty": context_penalty_signal,
                "action_group_score": action_group_score,
                "deadline_event_action_mismatch": float(comp.get("deadline_event_action_mismatch", 0.0) or 0.0),
                "deadline_event_action_overlap": float(comp.get("deadline_event_action_overlap", 0.0) or 0.0),
            },
            "action_group_query": query_action_group,
            "action_group_rule": rule_action_group,
            "action_group_score": action_group_score,
            "score_components": comp,
            "matched_features": mf,
            "retrieval_query_preview": query[:500],
        }
        ranked.append((rule, total, diag))

    # Semantic-first constraint:
    # If strong event+atom candidates exist, they must be preferred over lexical-only candidates.
    has_strong_semantic = any(
        row["event_type_match"] >= 1.0 and row["condition_atom_signal"] >= 0.35 for row in semantic_rows
    )
    rebuilt: list[tuple[RuleRecord, float, dict[str, Any]]] = []
    for rule, total, diag in ranked:
        sig = dict(diag.get("semantic_formula_signals") or {})
        strong_sem = sig.get("event_type_match", 0.0) >= 1.0 and sig.get("condition_atom_overlap", 0.0) >= 0.35
        weak_sem = sig.get("event_type_match", 0.0) <= 0.0 and sig.get("condition_atom_overlap", 0.0) < 0.2
        if has_strong_semantic:
            semantic_priority = 2 if strong_sem else (0 if weak_sem else 1)
        else:
            semantic_priority = 1
        diag["semantic_selection_constraint"] = {
            "strong_event_atom": strong_sem,
            "weak_event_atom": weak_sem,
            "active": has_strong_semantic,
            "semantic_priority": semantic_priority,
        }
        rebuilt.append((rule, total, diag))
    ranked = rebuilt

    ranked.sort(
        key=lambda x: (
            -int((x[2].get("semantic_selection_constraint") or {}).get("semantic_priority", 1)),
            -x[1],
            -float(x[2].get("bm25_norm") or 0.0),
        )
    )

    top_candidates = ranked[:top_k]
    if top_candidates:
        top1_group = str((top_candidates[0][2] or {}).get("action_group_rule") or "other")
        if top1_group != query_action_group:
            matching = [
                item
                for item in top_candidates
                if str((item[2] or {}).get("action_group_rule") or "other") == query_action_group
            ]
            if matching:
                preferred = max(matching, key=lambda x: x[1])
                reordered = [preferred] + [item for item in top_candidates if item is not preferred]
                top_candidates = reordered
                pref_diag = dict(top_candidates[0][2] or {})
                pref_diag["action_group_selection_override"] = {
                    "active": True,
                    "query_group": query_action_group,
                    "original_top1_group": top1_group,
                }
                top_candidates[0] = (top_candidates[0][0], top_candidates[0][1], pref_diag)

    return top_candidates


class RuleRetriever:
    """Legacy stub — use retrieve_rules() for the QA pipeline."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def retrieve(self, layer2: Any, top_k: int) -> list[Any]:
        raise NotImplementedError
