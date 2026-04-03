"""
High-precision subset selection from rulebase_logic IR for ProbLog / chaining.

Does not modify the full rulebase_logic.json; use extract script to emit a sidecar JSON.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Align with rulebase_logic_ir.GENERIC_PREDICATE_SLUGS + common vague roots
_GENERIC_ACTION_SLUGS: frozenset[str] = frozenset(
    {
        "dang_ky",
        "thong_bao",
        "xem_xet",
        "cap_nhat",
        "nop_ho_so",
        "chuan_bi_ho_so",
        "thuc_hien",
    }
)

_CORE_LOGIC_FORMS: frozenset[str] = frozenset(
    {
        "obligation",
        "permission",
        "prohibition",
        "deadline",
        "threshold",
        "exception",
        "applicability_condition",
        "authority_action",
        "legal_effect",
        "dossier",
    }
)

# Forms excluded from core by default (too procedural / IR shape varies).
_EXCLUDED_LOGIC_FORMS: frozenset[str] = frozenset({"procedure_step"})

_CLEANUP_RISKY_SUBSTRINGS: tuple[str, ...] = (
    "truncat",
    "shortened",
    "capped",
    "placeholder",
    "dossier_predicate_fallback",
    "incomplete",
)

_MAX_ATOM_LEN = 96
_LONG_EFFECT_LEN = 100


def _walk_atoms(x: Any, out: list[str]) -> None:
    if x is None:
        return
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return
    if isinstance(x, str):
        t = x.strip()
        if t:
            out.append(t)
        return
    if isinstance(x, dict):
        for v in x.values():
            _walk_atoms(v, out)
        return
    if isinstance(x, list):
        for v in x:
            _walk_atoms(v, out)


def _all_string_atoms(rule: dict[str, Any]) -> list[str]:
    atoms: list[str] = []
    _walk_atoms(rule.get("head"), atoms)
    _walk_atoms(rule.get("body"), atoms)
    _walk_atoms(rule.get("auxiliary_clauses"), atoms)
    return atoms


# Known tail fragments from slug truncation (IR / Excel width), not normal short words.
_BAD_TRUNC_SUFFIXES: tuple[str, ...] = (
    "_mot_t",
    "_mot_th",
    "_mot_tho",
    "_co_l",
    "_dieu_l",
    "_cong_ngh",
    "_cua_con",
    "_thu_t",
    "_phap_l",
)


def _has_known_truncation_suffix(s: str) -> bool:
    if len(s) < 24:
        return False
    sl = s.lower()
    return any(sl.endswith(x) for x in _BAD_TRUNC_SUFFIXES)


def _has_unresolved_or_placeholder_atoms(atoms: list[str]) -> bool:
    for a in atoms:
        sl = a.lower()
        if "unresolved_" in sl:
            return True
        if sl.endswith("_") and len(sl) > 1:
            return True
        if "placeholder" in sl:
            return True
    return False


def _normalization_gate(
    meta: dict[str, Any], lr: dict[str, Any]
) -> tuple[bool, list[str]]:
    """
    full → OK.
    partial → OK if reasoning_safe_partial, OR reasoning_ready with no risky cleanup notes.
    """
    ns = meta.get("normalization_status")
    notes = " ".join(
        (lr.get("head_cleanup_notes") or [])
        + (lr.get("body_cleanup_notes") or [])
        + (meta.get("normalization_notes") or [])
    ).lower()

    risky = any(r in notes for r in _CLEANUP_RISKY_SUBSTRINGS)

    if ns == "full":
        return True, []
    if ns == "partial":
        if meta.get("reasoning_safe_partial"):
            return True, []
        if lr.get("logic_readiness") == "reasoning_ready" and not risky:
            return True, []
        return False, ["partial_not_reasoning_safe"]
    return False, ["normalization_not_full_or_safe_partial"]


def _structural_gate(lr: dict[str, Any]) -> tuple[bool, list[str]]:
    meta = lr.get("metadata") or {}
    reasons: list[str] = []

    if not lr.get("selected_for_reasoning"):
        reasons.append("not_selected_for_reasoning")
    if lr.get("reasoning_partition") != "exportable_clean":
        reasons.append("not_exportable_clean")
    if not meta.get("problog_exportable"):
        reasons.append("problog_not_exportable")
    if lr.get("logic_readiness") != "reasoning_ready":
        reasons.append("logic_readiness_not_ready")
    if lr.get("fallback_kind") is not None:
        reasons.append("fallback_kind_set")
    if meta.get("export_blockers"):
        reasons.append("export_blockers_non_empty")

    dup = meta.get("duplicate_role")
    if dup not in ("primary_variant", "unique_variant"):
        if dup == "redundant_variant":
            reasons.append("redundant_variant")
        else:
            reasons.append("duplicate_role_not_primary_or_unique")

    return (len(reasons) == 0), reasons


def _semantic_core_filters(lr: dict[str, Any]) -> tuple[list[str], list[str]]:
    """
    Returns (exclusion_reasons, inclusion_tags) when structural+norm gates already pass.
    """
    meta = lr.get("metadata") or {}
    ex: list[str] = []
    tags: list[str] = []

    lf = lr.get("logic_form") or ""
    if lf in _EXCLUDED_LOGIC_FORMS:
        ex.append("logic_form_out_of_core_scope")
        return ex, tags

    if lf not in _CORE_LOGIC_FORMS:
        ex.append("logic_form_unknown")
        return ex, tags

    if meta.get("canonical_status") == "fallback_family_level":
        ex.append("fallback_family_level_predicate")

    atoms = _all_string_atoms(lr)
    if _has_unresolved_or_placeholder_atoms(atoms):
        ex.append("unresolved_semantic_role")

    for a in atoms:
        if len(a) > _MAX_ATOM_LEN:
            ex.append("unsafe_for_unification")
            break

    for a in atoms:
        if _has_known_truncation_suffix(a):
            ex.append("truncated_head_or_body_atom")
            break

    notes_l = (
        " ".join((lr.get("head_cleanup_notes") or []) + (lr.get("body_cleanup_notes") or []))
    ).lower()
    if any(s in notes_l for s in ("truncated", "shortened", "capped")):
        if "truncated_head_or_body_atom" not in ex:
            ex.append("truncated_head_or_body_atom")

    # Generic obligation/permission/prohibition action (2nd head arg is usually action slug)
    head = lr.get("head") or {}
    pred = head.get("predicate")
    args = head.get("args") if isinstance(head.get("args"), list) else []
    if pred in ("obligation", "permission", "prohibition") and len(args) >= 2:
        act = args[1]
        if isinstance(act, str) and act in _GENERIC_ACTION_SLUGS:
            ex.append("generic_predicate_not_canonical")

    # legal_effect: default conservative exclusion unless compact
    if lf == "legal_effect":
        oc = meta.get("object_canonical") or ""
        ec = meta.get("effect_canonical") or ""
        if isinstance(oc, str) and len(oc) > _LONG_EFFECT_LEN:
            ex.append("unsafe_effect_or_object")
        if isinstance(ec, str) and len(ec) > _LONG_EFFECT_LEN:
            ex.append("unsafe_effect_or_object")
        if "truncated_long_effect" in notes_l or "capped_long_effect" in notes_l:
            ex.append("unsafe_effect_or_object")

    # authority_action: need non-unknown authority when present
    if lf == "authority_action":
        auth = meta.get("authority_canonical")
        if auth in (None, "", "unknown"):
            ex.append("unsafe_authority_action_incomplete")

    # dossier: placeholder / fallback in head cleanup
    if lf == "dossier":
        if "dossier_predicate_fallback" in notes_l or "placeholder" in notes_l:
            ex.append("unsafe_dossier_placeholder")

    aux = lr.get("auxiliary_clauses") or []
    for a in aux:
        if not isinstance(a, dict):
            continue
        h = a.get("head") or {}
        al = h.get("args") if isinstance(h.get("args"), list) else []
        for item in al:
            if item == "unresolved_dossier_item_atom" or (
                isinstance(item, list) and "unresolved_dossier_item_atom" in item
            ):
                ex.append("unsafe_dossier_placeholder")
                break

    # Weak applicability / exception anchors
    if lf in ("exception", "applicability_condition"):
        if len(args) >= 2:
            anchor = args[1]
            if isinstance(anchor, str):
                al = anchor.lower()
                if anchor == "truong_hop" or (
                    al.startswith("truong_hop_") and len(anchor) < 18
                ):
                    ex.append("unsafe_generic_condition_anchor")
                if al == "tru_truong_hop" and len(args) == 2:
                    ex.append("unsafe_generic_condition_anchor")

    # Deadline: very long anchor (4th arg) is unstable
    if lf == "deadline" and len(args) >= 4:
        anc = args[3]
        if isinstance(anc, str) and len(anc) > 88:
            ex.append("unsafe_deadline_anchor")

    # Dedup ex
    ex = list(dict.fromkeys(ex))

    # Inclusion tags (for documentation)
    if not ex:
        tags.append("stable_for_unification")
        ns = meta.get("normalization_status")
        if ns == "full":
            tags.append("full_normalization")
        dup = meta.get("duplicate_role")
        if dup == "primary_variant":
            tags.append("primary_variant")
        elif dup == "unique_variant":
            tags.append("unique_variant")
        if lf == "deadline":
            tags.append("clean_deadline_rule")
        elif lf == "threshold":
            tags.append("clean_threshold_rule")
        elif lf == "exception":
            tags.append("clean_exception_rule")
        elif lf == "applicability_condition":
            tags.append("clean_applicability_rule")
        elif lf in ("obligation", "permission", "prohibition"):
            tags.append("clean_normative_rule")

    return ex, tags


def select_reasoning_core_records(
    rules: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """
    Returns (core_records, excluded_entries, report_dict).
    Each core record is a copy of the rule with core_selection_decision / core_selection_reason.
    """
    core: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []

    exportable_clean = 0
    for lr in rules:
        meta = lr.get("metadata") or {}
        if (
            lr.get("selected_for_reasoning")
            and lr.get("reasoning_partition") == "exportable_clean"
        ):
            exportable_clean += 1

    for lr in rules:
        rid = lr.get("rule_id", "")
        ok_struct, rs = _structural_gate(lr)
        meta = lr.get("metadata") or {}

        if not ok_struct:
            excluded.append({"rule_id": rid, "reason": rs})
            continue

        ok_norm, rn = _normalization_gate(meta, lr)
        if not ok_norm:
            excluded.append({"rule_id": rid, "reason": rn})
            continue

        ex_sem, tags = _semantic_core_filters(lr)
        if ex_sem:
            excluded.append({"rule_id": rid, "reason": ex_sem})
            continue

        row = dict(lr)
        row["core_selection_decision"] = "included"
        row["core_selection_reason"] = tags
        core.append(row)

    by_form: dict[str, int] = {}
    for r in core:
        lf = r.get("logic_form") or "unknown"
        by_form[lf] = by_form.get(lf, 0) + 1

    reason_hist = Counter()
    for e in excluded:
        for r in e.get("reason") or []:
            reason_hist[r] += 1

    report = {
        "total_rules": len(rules),
        "exportable_clean_count": exportable_clean,
        "core_rule_count": len(core),
        "excluded_exportable_clean_count": max(0, exportable_clean - len(core)),
        "core_by_logic_form": dict(sorted(by_form.items(), key=lambda x: x[0])),
        "exclusion_reason_histogram": dict(reason_hist.most_common()),
        "core_quality_summary": {
            "total_rules": len(rules),
            "exportable_clean_rules": exportable_clean,
            "rules_in_reasoning_core": len(core),
            "exportable_clean_excluded_from_core": max(0, exportable_clean - len(core)),
        },
        "conclusion": (
            "Core set is a high-precision slice: use for first-phase ProbLog export and chaining; "
            "keep full rulebase_logic.json for traceability. Prefer avoiding legal_effect, "
            "long applicability anchors, dossier placeholders, and generic normative roots in early reasoning."
        ),
    }
    return core, excluded, report


def build_reasoning_core_package(
    *,
    logic_payload: dict[str, Any],
    source_path: str | Path,
    core_version: int = 1,
    selection_policy: str = "high_precision_reasoning_core_v1",
) -> dict[str, Any]:
    rules = logic_payload.get("rules") or []
    core, excluded, report = select_reasoning_core_records(rules)

    pkg: dict[str, Any] = {
        "core_version": core_version,
        "selection_policy": selection_policy,
        "source_file": str(source_path).replace("\\", "/"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "core_rule_count": len(core),
        "core_rule_ids": [r.get("rule_id") for r in core if r.get("rule_id")],
        "rules_reasoning_core": core,
        "excluded_from_core": excluded,
        "report": report,
    }
    return pkg


def load_logic_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_reasoning_core_json(pkg: dict[str, Any], out_path: Path) -> None:
    out_path.write_text(json.dumps(pkg, ensure_ascii=False, indent=2), encoding="utf-8")


__all__ = [
    "build_reasoning_core_package",
    "select_reasoning_core_records",
    "load_logic_json",
    "write_reasoning_core_json",
]
