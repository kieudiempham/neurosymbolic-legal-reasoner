"""
Export rules_reasoning_core JSON to ProbLog-safe .pl files + mapping JSON.

Reads only `rules_reasoning_core` from the package produced by rulebase_reasoning_core extraction.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from law_side.controlled_vocabulary_builder import strip_vi_accents, to_snake_id

_PROBLOG_ATOM = re.compile(r"^[a-z][a-z0-9_]*$")

_THRESHOLD_OP_MAP: dict[str, str] = {
    "==": "eq",
    "eq": "eq",
    ">=": "ge",
    "ge": "ge",
    "<=": "le",
    "le": "le",
    ">": "gt",
    "gt": "gt",
    "<": "lt",
    "lt": "lt",
}


def _ascii_comment(s: str | None) -> str:
    if not s:
        return ""
    t = strip_vi_accents(str(s))
    return t.encode("ascii", "replace").decode("ascii")


def sanitize_atom(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    sid = to_snake_id(s)
    if not sid:
        return None
    if sid[0].isdigit():
        sid = "x_" + sid
    if not _PROBLOG_ATOM.match(sid):
        sid = to_snake_id("x_" + sid) or "x_unknown"
        if sid[0].isdigit():
            sid = "x_" + sid
    if not _PROBLOG_ATOM.match(sid):
        return None
    return sid


def format_number(v: float | int) -> str:
    if isinstance(v, bool):
        raise ValueError("bool")
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return repr(v)
    raise ValueError(type(v))


def format_arg(v: Any) -> tuple[str | None, str | None]:
    """
    Returns (pl_fragment, error_code).
    ProbLog-safe: numbers or lowercase atoms.
    """
    if v is None:
        return None, "null_arg"
    if isinstance(v, bool):
        return None, "bool_arg"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return format_number(v), None
    if isinstance(v, str):
        a = sanitize_atom(v)
        if not a:
            return None, "invalid_atom_after_sanitize"
        return a, None
    return None, "unsafe_nested_args"


def normalize_threshold_op(op: str | float | int | None) -> str | None:
    if op is None:
        return None
    s = str(op).strip()
    return _THRESHOLD_OP_MAP.get(s, sanitize_atom(s) if s else None)


def body_clauses_to_pl(body: Any) -> tuple[list[str] | None, str | None]:
    """Returns (list of 'pred(a,b)' strings, error_reason)."""
    if not body:
        return [], None
    if not isinstance(body, list):
        return None, "invalid_body_clause"
    out: list[str] = []
    for b in body:
        if not isinstance(b, dict):
            return None, "invalid_body_clause"
        if b.get("type") == "raw_text":
            return None, "invalid_body_clause"
        pred = b.get("predicate")
        if not pred:
            return None, "invalid_body_clause"
        pred_s = sanitize_atom(str(pred)) if not _PROBLOG_ATOM.match(str(pred)) else str(pred)
        if not pred_s or not _PROBLOG_ATOM.match(pred_s):
            pred_s = sanitize_atom(str(pred))
        if not pred_s:
            return None, "invalid_body_clause"
        args = b.get("args", [])
        if not isinstance(args, list):
            return None, "unsafe_nested_args"
        parts: list[str] = []
        for a in args:
            if isinstance(a, (dict, list)):
                return None, "unsafe_nested_args"
            frag, err = format_arg(a)
            if err:
                return None, err
            assert frag is not None
            parts.append(frag)
        out.append(f"{pred_s}({', '.join(parts)})")
    return out, None


def _head_terms_for_form(
    logic_form: str, head: dict[str, Any]
) -> tuple[str, list[str]] | tuple[None, str]:
    pred = head.get("predicate")
    args = head.get("args")
    if not isinstance(pred, str) or not isinstance(args, list):
        return None, "unsupported_head_arity"

    if logic_form == "obligation":
        if pred != "obligation" or len(args) != 3:
            return None, "unsupported_head_arity"
    elif logic_form == "permission":
        if pred != "permission" or len(args) != 3:
            return None, "unsupported_head_arity"
    elif logic_form == "prohibition":
        if pred != "prohibition" or len(args) != 3:
            return None, "unsupported_head_arity"
    elif logic_form == "deadline":
        if pred != "deadline" or len(args) != 4:
            return None, "unsupported_head_arity"
    elif logic_form == "threshold":
        if pred != "threshold" or len(args) != 4:
            return None, "unsupported_head_arity"
    elif logic_form == "exception":
        if pred != "exception" or len(args) != 2:
            return None, "unsupported_head_arity"
    elif logic_form == "applicability_condition":
        if pred != "applicability_condition" or len(args) != 2:
            return None, "unsupported_head_arity"
    elif logic_form == "authority_action":
        if pred != "authority_action" or len(args) != 3:
            return None, "unsupported_head_arity"
    elif logic_form == "legal_effect":
        if pred != "legal_effect" or len(args) != 2:
            return None, "unsupported_head_arity"
    elif logic_form == "dossier":
        if pred != "dossier" or len(args) != 2:
            return None, "unsupported_head_arity"
    else:
        return None, "unknown_logic_form"

    pl_parts: list[str] = []
    for i, a in enumerate(args):
        if logic_form == "threshold" and i == 1:
            op = normalize_threshold_op(a)
            if not op or not _PROBLOG_ATOM.match(op):
                return None, "invalid_threshold_op"
            pl_parts.append(op)
            continue
        frag, err = format_arg(a)
        if err:
            return None, err
        assert frag is not None
        pl_parts.append(frag)

    return pred, pl_parts


def _expand_dossier_items(raw_items: Any) -> tuple[list[str] | None, str | None]:
    if isinstance(raw_items, str):
        raw_items = [raw_items]
    if not isinstance(raw_items, list):
        return None, "dossier_list_unusable"
    out: list[str] = []
    for it in raw_items:
        if isinstance(it, list):
            return None, "dossier_list_unusable"
        frag, err = format_arg(it)
        if err:
            return None, err
        assert frag is not None
        out.append(frag)
    if not out:
        return None, "dossier_list_unusable"
    return out, None


@dataclass
class ExportState:
    clause_seq: int = 0
    seen_main: set[str] = field(default_factory=set)
    seen_facts: set[str] = field(default_factory=set)
    has_dossier_actions: set[str] = field(default_factory=set)

    def next_clause_id(self) -> str:
        self.clause_seq += 1
        return f"cl_{self.clause_seq:06d}"


HELPERS_BLOCK = """% --- minimal helper predicates (reasoning sugar) ---
applies(X) :- applicability_condition(X, _).
has_exception(X) :- exception(X, _).
has_deadline(X) :- deadline(X, _, _, _).
"""


def export_reasoning_core_problog(
    core_package: dict[str, Any],
    *,
    facts_filename: str = "rulebase_reasoning_core_facts.pl",
) -> dict[str, Any]:
    """
    Build strings for main .pl, facts .pl, and mapping + report.
    Only reads core_package['rules_reasoning_core'].
    """
    rules = core_package.get("rules_reasoning_core")
    if not isinstance(rules, list):
        raise ValueError("rules_reasoning_core must be a list")

    st = ExportState()
    main_lines: list[str] = []
    fact_lines: list[str] = []

    mapping_entries: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    by_form_ok: dict[str, int] = {}
    by_form_skip: dict[str, int] = {}

    n_clauses = 0
    n_facts = 0
    n_dossier_items = 0
    n_rules_ok = 0
    n_main_unit = 0

    header_main = (
        "% ProbLog / Prolog core rules (reasoning subset)\n"
        "% Generated from rules_reasoning_core only — not the full rulebase.\n"
        f"% facts_file: {facts_filename}\n"
        "% Load facts before consulting this file, e.g. SWI-Prolog:\n"
        f"%   ?- consult('{facts_filename}').\n"
        "%   ?- consult('rulebase_reasoning_core.pl').\n\n"
    )
    header_facts = (
        "% Supporting facts: dossier_item/2, has_dossier/1, auxiliary deadline/threshold notes.\n"
        "% Generated from rules_reasoning_core auxiliary expansions.\n\n"
    )

    def add_mapping(
        rule: dict[str, Any],
        clause_id: str,
        pred: str,
        exported_head: list[Any],
        clause_text: str,
        *,
        file_role: str,
    ) -> None:
        prov = (rule.get("metadata") or {}).get("provenance") or {}
        mapping_entries.append(
            {
                "rule_id": rule.get("rule_id"),
                "clause_id": clause_id,
                "logic_form": rule.get("logic_form"),
                "exported_predicate": pred,
                "exported_head": exported_head,
                "source_ref_full": prov.get("source_ref_full"),
                "source_ref": prov.get("source_ref"),
                "selected_for_reasoning": rule.get("selected_for_reasoning"),
                "file_role": file_role,
                "clause_text": clause_text.strip(),
            }
        )

    def emit_auxiliary(rule: dict[str, Any]) -> None:
        nonlocal n_facts, n_clauses, n_dossier_items
        for aux in rule.get("auxiliary_clauses") or []:
            if not isinstance(aux, dict):
                continue
            kind = aux.get("kind", "")
            h = aux.get("head")
            if not isinstance(h, dict):
                continue
            pred = h.get("predicate")
            args = h.get("args", [])
            if pred == "dossier" and isinstance(args, list) and len(args) == 2:
                act, err = format_arg(args[0])
                items, err2 = _expand_dossier_items(args[1])
                if err or err2 or not act or not items:
                    continue
                for doc in items:
                    fact = f"dossier_item({act}, {doc})."
                    if fact in st.seen_facts:
                        continue
                    st.seen_facts.add(fact)
                    cid = st.next_clause_id()
                    com = _rule_comments(rule, cid)
                    block = com + fact + "\n"
                    fact_lines.append(block)
                    n_facts += 1
                    n_clauses += 1
                    n_dossier_items += 1
                    add_mapping(
                        rule,
                        cid,
                        "dossier_item",
                        [act, doc],
                        fact,
                        file_role="facts",
                    )
                continue

            if pred in ("deadline",) and kind.endswith("_fact"):
                ht = _head_terms_for_form("deadline", h)
                if isinstance(ht, tuple) and ht[0] is None:
                    continue
                assert isinstance(ht, tuple) and len(ht) == 2
                p, parts = ht
                fact = f"{p}({', '.join(parts)})."
                if fact in st.seen_facts:
                    continue
                st.seen_facts.add(fact)
                cid = st.next_clause_id()
                com = _rule_comments(rule, cid)
                fact_lines.append(com + fact + "\n")
                n_facts += 1
                n_clauses += 1
                add_mapping(rule, cid, p, parts, fact, file_role="facts")
                continue

            if pred == "threshold_note" and kind.endswith("_fact"):
                if len(args) != 4:
                    continue
                m, op, val, u = args
                opn = normalize_threshold_op(op)
                fv, e1 = format_arg(m)
                fv2, e2 = format_arg(val)
                fv3, e3 = format_arg(u)
                if not opn or e1 or e2 or e3:
                    continue
                fact = f"threshold_note({fv}, {opn}, {fv2}, {fv3})."
                if fact in st.seen_facts:
                    continue
                st.seen_facts.add(fact)
                cid = st.next_clause_id()
                com = _rule_comments(rule, cid)
                fact_lines.append(com + fact + "\n")
                n_facts += 1
                n_clauses += 1
                add_mapping(rule, cid, "threshold_note", [fv, opn, fv2, fv3], fact, file_role="facts")

    def _rule_comments(rule: dict[str, Any], clause_id: str) -> str:
        rid = rule.get("rule_id", "")
        lf = rule.get("logic_form", "")
        prov = (rule.get("metadata") or {}).get("provenance") or {}
        sref = _ascii_comment(prov.get("source_ref_full") or "")
        sr = _ascii_comment(prov.get("source_ref") or "")
        return (
            f"% clause_id: {clause_id}\n"
            f"% rule_id: {rid}\n"
            f"% logic_form: {lf}\n"
            f"% source_ref_full: {sref}\n"
            f"% source_ref: {sr}\n"
        )

    for rule in rules:
        lf = rule.get("logic_form")
        if not isinstance(lf, str):
            skipped.append({"rule_id": rule.get("rule_id"), "reason": ["unknown_logic_form"]})
            continue

        head = rule.get("head")
        if not isinstance(head, dict):
            skipped.append({"rule_id": rule.get("rule_id"), "reason": ["unsupported_head_arity"]})
            continue

        body_raw = rule.get("body")
        body_pl, berr = body_clauses_to_pl(body_raw)
        if berr:
            skipped.append({"rule_id": rule.get("rule_id"), "reason": [berr]})
            by_form_skip[lf] = by_form_skip.get(lf, 0) + 1
            continue

        # Dossier: expand to dossier_item (+ optional rule with body)
        if lf == "dossier":
            args = head.get("args", [])
            if len(args) != 2:
                skipped.append({"rule_id": rule.get("rule_id"), "reason": ["unsupported_head_arity"]})
                continue
            act, e1 = format_arg(args[0])
            items, e2 = _expand_dossier_items(args[1])
            if e1 or e2 or not act or not items:
                skipped.append(
                    {
                        "rule_id": rule.get("rule_id"),
                        "reason": [e1 or e2 or "dossier_list_unusable"],
                    }
                )
                continue
            for doc in items:
                unit = f"dossier_item({act}, {doc})"
                if body_pl:
                    line = unit + " :-\n    " + ",\n    ".join(body_pl) + ".\n"
                else:
                    line = unit + ".\n"
                if line in st.seen_facts:
                    continue
                st.seen_facts.add(line)
                cid = st.next_clause_id()
                com = _rule_comments(rule, cid)
                fact_lines.append(com + line)
                n_clauses += 1
                n_facts += 1
                n_dossier_items += 1
                add_mapping(
                    rule,
                    cid,
                    "dossier_item",
                    [act, doc],
                    line.strip(),
                    file_role="facts",
                )

            if act not in st.has_dossier_actions:
                st.has_dossier_actions.add(act)
                hf = f"has_dossier({act})."
                if hf not in st.seen_facts:
                    st.seen_facts.add(hf)
                    cid = st.next_clause_id()
                    com = _rule_comments(rule, cid)
                    fact_lines.append(com + hf + "\n")
                    n_facts += 1
                    n_clauses += 1
                    add_mapping(rule, cid, "has_dossier", [act], hf, file_role="facts")

            emit_auxiliary(rule)
            by_form_ok[lf] = by_form_ok.get(lf, 0) + 1
            n_rules_ok += 1
            continue

        ht = _head_terms_for_form(lf, head)
        if not isinstance(ht, tuple) or len(ht) != 2:
            skipped.append({"rule_id": rule.get("rule_id"), "reason": ["unsupported_head_arity"]})
            by_form_skip[lf] = by_form_skip.get(lf, 0) + 1
            continue
        if ht[0] is None:
            skipped.append({"rule_id": rule.get("rule_id"), "reason": [str(ht[1])]})
            by_form_skip[lf] = by_form_skip.get(lf, 0) + 1
            continue

        pred, parts = ht
        head_txt = f"{pred}({', '.join(parts)})"
        if body_pl:
            clause = head_txt + " :-\n    " + ",\n    ".join(body_pl) + ".\n"
        else:
            clause = head_txt + ".\n"

        if clause in st.seen_main:
            emit_auxiliary(rule)
            n_rules_ok += 1
            by_form_ok[lf] = by_form_ok.get(lf, 0) + 1
            continue
        st.seen_main.add(clause)

        cid = st.next_clause_id()
        com = _rule_comments(rule, cid)
        main_lines.append(com + clause)
        n_clauses += 1
        if not body_pl:
            n_main_unit += 1
        exported_head: list[Any] = []
        for x in head.get("args", []):
            if isinstance(x, (int, float)) and not isinstance(x, bool):
                exported_head.append(int(x) if isinstance(x, float) and x == int(x) else x)
            else:
                exported_head.append(x)

        add_mapping(rule, cid, pred, exported_head, clause, file_role="main")
        emit_auxiliary(rule)
        by_form_ok[lf] = by_form_ok.get(lf, 0) + 1
        n_rules_ok += 1

    main_out = header_main + "\n".join(main_lines) + "\n" + HELPERS_BLOCK + "\n"
    facts_out = header_facts
    if not fact_lines:
        facts_out += "% (empty) No auxiliary or dossier_item facts in this export.\n"
    else:
        facts_out += "\n".join(fact_lines) + "\n"

    report = {
        "export_summary": {
            "rules_in_core_input": len(rules),
            "rules_exported_ok": n_rules_ok,
            "rules_skipped": len(skipped),
            "clauses_emitted": n_clauses,
            "facts_file_lines_emitted": n_facts,
            "main_file_unit_facts": n_main_unit,
            "dossier_item_facts": n_dossier_items,
        },
        "breakdown_exported_by_logic_form": dict(sorted(by_form_ok.items(), key=lambda x: x[0])),
        "breakdown_skipped_by_logic_form": dict(sorted(by_form_skip.items(), key=lambda x: x[0])),
        "skipped_rules": skipped,
        "helpers_added": ["applies/1", "has_exception/1", "has_deadline/1"],
        "conclusion": (
            "Files are syntactically valid Prolog/ProbLog-style programs if your engine accepts "
            "this dialect. Load facts first, then the main file. Re-check clauses that use very "
            "long atoms. Smoke-test with query/1 or interactive consultation on sample predicates."
        ),
        "smoke_queries_suggested": [
            "deadline(dang_ky_chuyen_doi_cong_ty_voi_co_quan_dang_ky_kinh_doanh, 10, ngay, nguong_dieu_kien_dinh_luong_thoi_han_dang_ky_chuyen_doi_eq_10_ngay).",
            "threshold(ty_le_so_huu_co_phan_pho_thong, ge, 20, phan_tram).",
            "applicability_condition(dang_ky_mua_it_nhat_20_tong_so_co_phan_pho_thong_duoc_quyen_chao_ban, khi_dang_ky_thanh_lap_doanh_nghiep).",
        ],
    }

    return {
        "main_pl": main_out,
        "facts_pl": facts_out,
        "mapping_entries": mapping_entries,
        "report": report,
    }


def _relative_display_path(path: Path, root: Path | None) -> str:
    if root is None:
        return path.as_posix()
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def write_reasoning_core_problog_artifacts(
    core_json_path: Path,
    out_main: Path,
    out_facts: Path,
    out_mapping: Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    payload = json.loads(core_json_path.read_text(encoding="utf-8"))
    facts_name = out_facts.name
    result = export_reasoning_core_problog(payload, facts_filename=facts_name)

    out_main.parent.mkdir(parents=True, exist_ok=True)
    out_main.write_text(result["main_pl"], encoding="utf-8")
    out_facts.write_text(result["facts_pl"], encoding="utf-8")

    mapping_pkg = {
        "mapping_version": 1,
        "source_core_json": _relative_display_path(core_json_path, repo_root),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entries": result["mapping_entries"],
        "export_report": result["report"],
    }
    out_mapping.write_text(json.dumps(mapping_pkg, ensure_ascii=False, indent=2), encoding="utf-8")
    return result["report"]


__all__ = [
    "export_reasoning_core_problog",
    "write_reasoning_core_problog_artifacts",
    "sanitize_atom",
]
