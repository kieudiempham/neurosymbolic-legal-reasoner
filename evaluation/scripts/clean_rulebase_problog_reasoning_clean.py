"""Clean `rulebase.problog` into a reasoning-stable ProbLog program.

Implements the 5 requested fixes:
1) Dedup exact clauses (same head + same body; comment differences ignored)
2) Drop clauses containing truncated atoms (by known suffixes)
3) Drop partial/unsafe clauses (normalization_status=partial AND reasoning_safe_partial != true)
4) Atomize dossier(...) into dossier_item/2 (and rewrite dossier atoms in bodies)
5) Drop clauses with unsafe anchor/action heuristics (too long or known bad prefixes)

Outputs:
- rulebase_reasoning_clean.problog
- excluded_clauses.json
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from pipelines._paths import legal_qa_nesy_root


BAD_TRUNC_SUFFIXES: tuple[str, ...] = (
    "_mot_t",
    "_co_l",
    "_kiem_toa",
    "_cua_con",
    "_cong_ngh",
)

# Heuristic prefix that is known to produce unstable/unify-hostile anchors.
BAD_ANCHOR_SUBSTRINGS: tuple[str, ...] = (
    "nguong_dieu_kien_dinh_luong_",
)

MAX_ACTION_LEN = 60
MAX_ANCHOR_LEN = 80
MAX_METRIC_LEN = 80
MAX_COND_LEN = 120


_ATOM_TOKEN_RE = re.compile(r"\b[a-z][a-z0-9_]*\b")


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", "", s)


def _safe_strip_outer_quotes(s: str) -> str:
    s2 = s.strip()
    if len(s2) >= 2 and s2[0] == "'" and s2[-1] == "'":
        return s2[1:-1]
    return s2


def _extract_doc_atoms_from_dossier_list_literal(list_arg: str) -> list[str] | None:
    # list_arg comes as a single-quoted atom string in the current problog export,
    # e.g. '[\'so_thue\', \'bao_hiem\']'
    if not list_arg:
        return None
    content = _safe_strip_outer_quotes(list_arg)
    # Extract lower snake_case-ish atoms inside the literal.
    docs = _ATOM_TOKEN_RE.findall(content)
    # Preserve order + uniqueness.
    out: list[str] = []
    seen: set[str] = set()
    for d in docs:
        if d in seen:
            continue
        seen.add(d)
        out.append(d)
    return out if out else None


def _split_args(args_str: str) -> list[str] | None:
    """Split arguments in a Prolog term: a,b,'c,d', [x,y] (no nesting beyond quotes/brackets)."""
    s = args_str.strip()
    if not s:
        return []
    out: list[str] = []
    cur: list[str] = []
    in_sq = False
    escape = False
    bracket_depth = 0
    for ch in s:
        if in_sq:
            cur.append(ch)
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == "'":
                in_sq = False
            continue
        if ch == "'":
            in_sq = True
            cur.append(ch)
            continue
        if ch == "[":
            bracket_depth += 1
            cur.append(ch)
            continue
        if ch == "]":
            bracket_depth = max(0, bracket_depth - 1)
            cur.append(ch)
            continue
        if ch == "," and bracket_depth == 0:
            part = "".join(cur).strip()
            out.append(part)
            cur = []
            continue
        cur.append(ch)
    part = "".join(cur).strip()
    if part:
        out.append(part)
    return out


def _parse_predicate_term(term_str: str) -> tuple[str, list[str]] | None:
    t = term_str.strip().rstrip(".")
    if not t:
        return None
    # Find the first "(" at top-level (there shouldn't be other parentheses before it).
    i = t.find("(")
    if i <= 0 or not t.endswith(")"):
        return None
    pred = t[:i].strip()
    args_str = t[i + 1 : -1]
    if not pred or not _ATOM_TOKEN_RE.match(pred):
        # predicate must be atom-safe
        return None
    args = _split_args(args_str)
    if args is None:
        return None
    return pred, args


def _extract_dossier_atom_from_body_fragment(body_str: str, start_idx: int) -> tuple[str, int] | None:
    """Given body_str and index at 'dossier(', return (atom_text, end_idx)."""
    if not body_str.startswith("dossier(", start_idx):
        return None
    i = start_idx
    in_sq = False
    escape = False
    depth = 0
    while i < len(body_str):
        ch = body_str[i]
        if in_sq:
            if escape:
                escape = False
            else:
                if ch == "\\":
                    escape = True
                elif ch == "'":
                    in_sq = False
            i += 1
            continue
        if ch == "'":
            in_sq = True
            i += 1
            continue
        if ch == "(":
            depth += 1
            i += 1
            continue
        if ch == ")":
            depth -= 1
            i += 1
            if depth == 0:
                return body_str[start_idx:i].strip(), i - 1
            continue
        i += 1
    return None


def _rewrite_body_dossier_atoms(body_str: str) -> tuple[str | None, str | None]:
    """Replace dossier(Action, ListLiteral) inside a body with dossier_item(Action, Doc1), ..."""
    if not body_str:
        return body_str, None
    out = body_str
    while True:
        idx = out.find("dossier(", 0)
        if idx == -1:
            return out, None
        parsed = _extract_dossier_atom_from_body_fragment(out, idx)
        if not parsed:
            return None, "non_atomized_dossier"
        atom_text, end_idx = parsed
        # Parse: dossier(action, '...[...]...')
        pt = _parse_predicate_term(atom_text)
        if not pt:
            return None, "non_atomized_dossier"
        pred, args = pt
        if pred != "dossier" or len(args) != 2:
            return None, "non_atomized_dossier"
        action_atom = args[0].strip()
        if not _ATOM_TOKEN_RE.match(action_atom):
            return None, "non_atomized_dossier"
        docs = _extract_doc_atoms_from_dossier_list_literal(args[1])
        if not docs:
            return None, "non_atomized_dossier"
        repl_atoms = ", ".join([f"dossier_item({action_atom}, {d})."[:-1] for d in docs])
        # Convert the produced string to atoms (without trailing dots).
        repl_atoms = ", ".join([f"dossier_item({action_atom}, {d})" for d in docs])
        out = out[:idx] + repl_atoms + out[end_idx + 1 :]


def _rewrite_clause_if_needed(clause_text: str) -> tuple[list[str], str | None]:
    """Return (emitted_clause_texts_without_trailing_comments, error_reason).

    Handles dossier in HEAD by converting to dossier_item(...).
    Handles dossier atoms in BODY by rewriting to dossier_item conjunction.
    """
    clause_core = clause_text.strip()
    if not clause_core.endswith("."):
        return [], "invalid_clause_ending"
    clause_core = clause_core[:-1].rstrip()

    if ":-" in clause_core:
        head_part, body_part = clause_core.split(":-", 1)
        head_part = head_part.strip()
        body_part = body_part.strip()
    else:
        head_part = clause_core.strip()
        body_part = ""

    # HEAD dossier(...) => dossier_item(...) facts/rules.
    head_pt = _parse_predicate_term(head_part)
    if not head_pt:
        return [], "unparseable_head"
    head_pred, head_args = head_pt

    if head_pred == "dossier":
        if len(head_args) != 2:
            return [], "non_atomized_dossier"
        action_atom = head_args[0].strip()
        if not _ATOM_TOKEN_RE.match(action_atom):
            return [], "non_atomized_dossier"
        docs = _extract_doc_atoms_from_dossier_list_literal(head_args[1])
        if not docs:
            return [], "non_atomized_dossier"
        emitted: list[str] = []
        for d in docs:
            if body_part:
                emitted.append(f"dossier_item({action_atom}, {d}) :- {body_part}.")
            else:
                emitted.append(f"dossier_item({action_atom}, {d}).")
        return emitted, None

    # Non-dossier head: rewrite dossier atoms in body.
    if body_part:
        new_body, err = _rewrite_body_dossier_atoms(body_part)
        if err:
            return [], err
        body_part = new_body.strip()
        if body_part:
            return [f"{head_part} :- {body_part}."], None
    return [f"{head_part}."], None


def _extract_rule_meta_from_comments(comments: list[str]) -> tuple[str | None, str | None]:
    rid: str | None = None
    norm: str | None = None
    for c in comments:
        m = re.match(r"^%\s*rule_id:\s*(.*)\s*$", c)
        if m:
            rid = m.group(1).strip()
        m2 = re.match(r"^%\s*normalization_status:\s*(.*)\s*$", c)
        if m2:
            norm = m2.group(1).strip()
    return rid, norm


def _atoms_in_clause(clause_without_comments: str) -> list[str]:
    return _ATOM_TOKEN_RE.findall(clause_without_comments)


def _has_truncated_atom(clause_without_comments: str) -> bool:
    atoms = _atoms_in_clause(clause_without_comments)
    for a in atoms:
        la = a.lower()
        if any(la.endswith(suf) for suf in BAD_TRUNC_SUFFIXES):
            return True
    return False


def _has_unsafe_anchor_action(clause_without_comments: str, head_pred: str | None, head_args: list[str] | None) -> bool:
    # Fast path: known bad anchor substring appears anywhere.
    low = clause_without_comments.lower()
    if any(b in low for b in BAD_ANCHOR_SUBSTRINGS):
        return True

    if not head_pred or not head_args:
        return False

    # Head-based checks.
    try:
        if head_pred in ("obligation", "permission", "prohibition"):
            # (Subject, Action, Object)
            action = head_args[1] if len(head_args) >= 2 else ""
            if action and len(action) > MAX_ACTION_LEN:
                return True
        if head_pred == "authority_action":
            action = head_args[1] if len(head_args) >= 2 else ""
            if action and len(action) > MAX_ACTION_LEN:
                return True
        if head_pred == "exception":
            action = head_args[0] if len(head_args) >= 1 else ""
            if action and len(action) > MAX_ACTION_LEN:
                return True
        if head_pred == "applicability_condition":
            action = head_args[0] if len(head_args) >= 1 else ""
            cond = head_args[1] if len(head_args) >= 2 else ""
            if action and len(action) > MAX_ACTION_LEN:
                return True
            if cond and len(cond) > MAX_COND_LEN:
                return True
        if head_pred == "deadline":
            action = head_args[0] if len(head_args) >= 1 else ""
            anchor = head_args[3] if len(head_args) >= 4 else ""
            if action and len(action) > MAX_ACTION_LEN:
                return True
            if anchor and len(anchor) > MAX_ANCHOR_LEN:
                return True
        if head_pred == "threshold":
            metric = head_args[0] if len(head_args) >= 1 else ""
            if metric and len(metric) > MAX_METRIC_LEN:
                return True
        if head_pred == "dossier_item":
            action = head_args[0] if len(head_args) >= 1 else ""
            if action and len(action) > MAX_ACTION_LEN:
                return True
    except Exception:
        # Conservative: if parsing failed, don't treat as unsafe here.
        return False

    return False


@dataclass
class ClauseBlock:
    comments: list[str]
    clause_text: str  # without trailing whitespace/newlines
    rule_id: str | None
    normalization_status: str | None


def _parse_problog_clauses(lines: Iterable[str]) -> tuple[list[str], list[ClauseBlock]]:
    header_comments: list[str] = []
    blocks: list[ClauseBlock] = []

    comment_buf: list[str] = []
    clause_buf: list[str] = []
    reading_clause = False

    def flush_clause() -> None:
        nonlocal comment_buf, clause_buf, blocks
        if not clause_buf:
            return
        clause_text = "\n".join(clause_buf).strip()
        rid, norm = _extract_rule_meta_from_comments(comment_buf)
        blocks.append(
            ClauseBlock(
                comments=comment_buf,
                clause_text=clause_text,
                rule_id=rid,
                normalization_status=norm,
            )
        )
        comment_buf = []
        clause_buf = []

    for line in lines:
        if line.startswith("%"):
            if not reading_clause and not clause_buf and not blocks:
                # Still in header (before first clause)
                header_comments.append(line.rstrip("\n"))
                continue
            comment_buf.append(line.rstrip("\n"))
            continue

        stripped = line.strip()
        if not stripped:
            if reading_clause:
                # keep blank lines within clause? currently not expected
                continue
            # blank line between blocks; finalize nothing here.
            continue

        # Non-comment line.
        reading_clause = True
        clause_buf.append(line.rstrip("\n"))
        # Clause ends when a non-comment line ends with '.'
        if stripped.endswith("."):
            flush_clause()
            reading_clause = False

    # EOF flush
    flush_clause()
    return header_comments, blocks


def main() -> None:
    root = legal_qa_nesy_root()
    in_problog = root / "data" / "processed" / "rulebase" / "rulebase.problog"
    core_json = root / "data" / "processed" / "rulebase" / "rulebase_reasoning_core.json"

    out_problog = root / "data" / "processed" / "rulebase" / "rulebase_reasoning_clean.problog"
    out_excluded = root / "data" / "processed" / "rulebase" / "excluded_clauses.json"

    core_payload = json.loads(core_json.read_text(encoding="utf-8"))
    core_rules = core_payload.get("rules_reasoning_core") or []
    core_by_id: dict[str, dict[str, Any]] = {}
    for r in core_rules:
        rid = r.get("rule_id")
        if not isinstance(rid, str):
            continue
        meta = r.get("metadata") or {}
        core_by_id[rid] = meta if isinstance(meta, dict) else {}

    # Parse input problog.
    header_comments, blocks = _parse_problog_clauses(in_problog.read_text(encoding="utf-8").splitlines())

    excluded: list[dict[str, Any]] = []
    by_reason: dict[str, int] = {
        "duplicate_exact": 0,
        "truncated_atom": 0,
        "partial_not_safe": 0,
        "non_atomized_dossier": 0,
        "unsafe_anchor_or_action": 0,
    }

    seen_signatures: set[str] = set()
    emitted_lines: list[str] = []
    if header_comments:
        emitted_lines.extend([c for c in header_comments if c.strip()])
        emitted_lines.append(
            "% --- reasoning-clean produced by scripts/clean_rulebase_problog_reasoning_clean.py ---"
        )
        emitted_lines.append("")

    def add_excluded(rule_id: str | None, clause_sig: str, reason: str, extra: dict[str, Any] | None = None) -> None:
        entry: dict[str, Any] = {"rule_id": rule_id, "clause_signature": clause_sig, "reason": reason}
        if extra:
            entry.update(extra)
        excluded.append(entry)
        by_reason[reason] = by_reason.get(reason, 0) + 1

    def add_emitted(clause_out: str, comments: list[str]) -> None:
        # clause_out must already end with '.'
        sig = _norm_ws(clause_out.rstrip("."))
        if sig in seen_signatures:
            add_excluded(None, sig, "duplicate_exact")
            return
        seen_signatures.add(sig)
        # Keep provenance comments.
        if comments:
            emitted_lines.extend([c for c in comments])
        emitted_lines.append(clause_out.strip())
        emitted_lines.append("")  # blank line between clauses

    kept_clause_count = 0
    input_clause_count = len(blocks)

    out_has_dossier_item_fact: set[str] = set()

    for b in blocks:
        rid = b.rule_id
        norm_status = (b.normalization_status or "").strip().lower()

        # Partial unsafe filter (#3) applies to the source rule clause.
        if norm_status == "partial":
            if not rid:
                add_excluded(rid, _norm_ws(b.clause_text.rstrip(".")), "partial_not_safe")
                continue
            meta = core_by_id.get(rid)
            safe_partial = bool((meta or {}).get("reasoning_safe_partial") is True)
            if not safe_partial:
                add_excluded(rid, _norm_ws(b.clause_text.rstrip(".")), "partial_not_safe")
                continue

        # Rewrite clause to atomized dossier_item form.
        emitted_variants, err = _rewrite_clause_if_needed(b.clause_text)
        if err == "non_atomized_dossier":
            add_excluded(rid, _norm_ws(b.clause_text.rstrip(".")), "non_atomized_dossier")
            continue
        if err:
            # Other parse/rewrite errors: be conservative.
            add_excluded(rid, _norm_ws(b.clause_text.rstrip(".")), "non_atomized_dossier", {"rewrite_error": err})
            continue

        # For non-dossier clauses, dossier atoms in body were rewritten already.
        # Now validate each emitted clause variant with filters (#2, #5, dedup).
        for clause_out in emitted_variants:
            # Truncated atoms (#2)
            if _has_truncated_atom(clause_out):
                add_excluded(rid, _norm_ws(clause_out.rstrip(".")), "truncated_atom")
                continue

            # Unsafe anchor/action (#5)
            head_pred_args = _parse_predicate_term(clause_out.rstrip("."))
            head_pred = head_pred_args[0] if head_pred_args else None
            head_args = head_pred_args[1] if head_pred_args else None
            if _has_unsafe_anchor_action(clause_out, head_pred, head_args):
                add_excluded(rid, _norm_ws(clause_out.rstrip(".")), "unsafe_anchor_or_action")
                continue

            # Duplicate exact (#1) handled by add_emitted via signature.
            # Emit.
            add_emitted(clause_out, b.comments)
            kept_clause_count += 1
            # Track dossier_item facts for later validation if needed.
            if head_pred == "dossier_item" and len(head_args) == 2:
                out_has_dossier_item_fact.add(f"{head_args[0]}::{head_args[1]}")

    # Ensure there is no dossier(...) term in the final output (except comments).
    out_text = "\n".join(emitted_lines).rstrip() + "\n"
    if "dossier(" in out_text:
        # If this happens, we missed a rewrite; fail fast.
        raise RuntimeError("Output still contains dossier( predicate calls; dossier atomization is incomplete.")

    out_problog.write_text(out_text, encoding="utf-8")

    report = {
        "export_summary": {
            "clauses_initial": input_clause_count,
            "clauses_kept": kept_clause_count,
            "clauses_excluded": len(excluded),
            "clauses_excluded_by_reason": by_reason,
        },
    }

    excluded_obj = {
        "excluded_clauses": excluded,
        "report": report,
    }
    out_excluded.write_text(json.dumps(excluded_obj, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote reasoning-clean ProbLog: {out_problog}")
    print(f"Wrote exclusions: {out_excluded}")
    print("Report:", report["export_summary"])


if __name__ == "__main__":
    main()

