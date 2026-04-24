from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def _unique_keep_order(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _select_representative_cases(
    rows: list[dict[str, Any]],
    max_cases: int,
) -> list[str]:
    failed = [
        r for r in rows
        if str(r.get("error_stage_final") or "").strip() == "no_grounded_rule_found"
    ]
    by_domain: dict[str, list[dict[str, Any]]] = {}
    for r in failed:
        domain = str(r.get("domain_hint") or "unknown").strip() or "unknown"
        by_domain.setdefault(domain, []).append(r)

    # Round-robin by domain to keep cross-domain representativeness.
    selected: list[str] = []
    domain_keys = sorted(by_domain.keys())
    idx = 0
    while len(selected) < max_cases and domain_keys:
        exhausted = 0
        for domain in list(domain_keys):
            bucket = by_domain.get(domain, [])
            if idx < len(bucket):
                cid = str(bucket[idx].get("id") or "").strip()
                if cid:
                    selected.append(cid)
                    if len(selected) >= max_cases:
                        break
            else:
                exhausted += 1
        if exhausted == len(domain_keys):
            break
        idx += 1

    return _unique_keep_order(selected)[:max_cases]


def _build_rulebase_indexes(project_root: Path) -> dict[str, dict[str, Any]]:
    base = project_root / "data" / "processed" / "rulebase"
    out: dict[str, dict[str, Any]] = {}
    for domain in ("enterprise", "tax", "labor"):
        canonical_path = base / domain / "canonical_rules.jsonl"
        runtime_path = base / domain / "runtime" / "rulebase_reasoning_core.json"

        canonical_rows = _read_jsonl(canonical_path) if canonical_path.exists() else []
        canonical_rule_ids = {str(r.get("rule_id") or "") for r in canonical_rows if r.get("rule_id")}
        canonical_by_pred: dict[str, list[str]] = {}
        for r in canonical_rows:
            head = r.get("canonical_head")
            if not isinstance(head, dict):
                continue
            pred = str(head.get("predicate") or "").strip()
            rid = str(r.get("rule_id") or "").strip()
            if pred and rid:
                canonical_by_pred.setdefault(pred, []).append(rid)

        runtime_payload = _read_json(runtime_path) if runtime_path.exists() else {}
        core_rule_ids = {
            str(x) for x in (runtime_payload.get("core_rule_ids") or []) if isinstance(x, str) and x
        }
        runtime_rules = runtime_payload.get("rules_reasoning_core")
        runtime_by_pred: dict[str, list[str]] = {}
        if isinstance(runtime_rules, list):
            for r in runtime_rules:
                if not isinstance(r, dict):
                    continue
                rid = str(r.get("rule_id") or "").strip()
                head = r.get("head")
                pred = ""
                if isinstance(head, dict):
                    pred = str(head.get("predicate") or "").strip()
                if rid and pred:
                    runtime_by_pred.setdefault(pred, []).append(rid)

        out[domain] = {
            "canonical_path": str(canonical_path),
            "runtime_path": str(runtime_path),
            "canonical_rule_ids": canonical_rule_ids,
            "canonical_by_pred": canonical_by_pred,
            "runtime_rule_ids": core_rule_ids,
            "runtime_by_pred": runtime_by_pred,
        }
    return out


def _extract_case_trace(
    case_row: dict[str, Any],
    rerun_dir: Path,
    rulebase_indexes: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    cid = str(case_row.get("id") or "")
    raw_path = rerun_dir / "raw" / f"{cid}.json"
    raw = _read_json(raw_path)
    debug_trace = raw.get("debug_trace") if isinstance(raw, dict) else None
    if not isinstance(debug_trace, dict):
        debug_trace = {}

    domain = str(case_row.get("domain_hint") or "unknown").strip() or "unknown"
    idx = rulebase_indexes.get(domain, {})
    canonical_rule_ids = idx.get("canonical_rule_ids", set())
    runtime_rule_ids = idx.get("runtime_rule_ids", set())
    canonical_by_pred = idx.get("canonical_by_pred", {})
    runtime_by_pred = idx.get("runtime_by_pred", {})

    gate = debug_trace.get("rule_backward_gate_rerun") or debug_trace.get("rule_backward_gate") or []
    if not isinstance(gate, list):
        gate = []
    gate0 = gate[0] if gate and isinstance(gate[0], dict) else {}
    final_goal = gate0.get("goal") if isinstance(gate0.get("goal"), dict) else {}
    goal_pred = str(final_goal.get("predicate") or "").strip()

    top_retrieved_ids = gate0.get("top_retrieved_rule_ids")
    if not isinstance(top_retrieved_ids, list):
        top_retrieved_ids = []
    top_retrieved_ids = [str(x) for x in top_retrieved_ids if isinstance(x, str)]

    retrieved_by_domain = debug_trace.get("retrieved_rules_by_domain")
    retrieved_top_k: list[dict[str, Any]] = []
    if isinstance(retrieved_by_domain, dict):
        for dom, rows in retrieved_by_domain.items():
            if not isinstance(rows, list):
                continue
            for row in rows[:8]:
                if not isinstance(row, dict):
                    continue
                retrieved_top_k.append(
                    {
                        "domain": dom,
                        "rule_id": row.get("rule_id"),
                        "score": row.get("score"),
                        "source_doc": row.get("source_doc"),
                    }
                )

    reasoning_result = raw.get("reasoning_result") if isinstance(raw, dict) else {}
    admitted = []
    if isinstance(reasoning_result, dict):
        value = reasoning_result.get("candidate_rules_considered")
        if isinstance(value, list):
            admitted = value

    verify_diag = debug_trace.get("verification_diagnostics_after_repair") or debug_trace.get("verification_diagnostics") or []
    unify_failures: list[dict[str, Any]] = []
    if isinstance(verify_diag, list):
        for row in verify_diag:
            if not isinstance(row, dict):
                continue
            reasons = row.get("rejection_reason")
            if isinstance(reasons, list) and reasons:
                unify_failures.append(
                    {
                        "rule_id": row.get("rule_id"),
                        "verification_decision": row.get("verification_decision"),
                        "rejection_reason": reasons,
                        "repair_hints": row.get("repair_hints") or [],
                    }
                )

    lookup_rows = []
    for rid in top_retrieved_ids:
        lookup_rows.append(
            {
                "rule_id": rid,
                "canonical_exists": rid in canonical_rule_ids,
                "runtime_exists": rid in runtime_rule_ids,
            }
        )

    canonical_matches = canonical_by_pred.get(goal_pred, []) if goal_pred else []
    runtime_matches = runtime_by_pred.get(goal_pred, []) if goal_pred else []

    return {
        "qid": cid,
        "question": case_row.get("question"),
        "domain_hint": domain,
        "intent_hint": case_row.get("intent_hint"),
        "raw_result_path": str(case_row.get("raw_result_path") or raw_path),
        "final_goal": final_goal,
        "canonical_lookup": {
            "canonical_file": idx.get("canonical_path"),
            "goal_predicate": goal_pred,
            "goal_predicate_match_count": len(canonical_matches),
            "goal_predicate_match_sample": canonical_matches[:5],
            "top_retrieved_rule_presence": lookup_rows,
        },
        "runtime_lookup": {
            "runtime_file": idx.get("runtime_path"),
            "goal_predicate": goal_pred,
            "goal_predicate_match_count": len(runtime_matches),
            "goal_predicate_match_sample": runtime_matches[:5],
            "top_retrieved_rule_presence": lookup_rows,
        },
        "retrieved_top_k": retrieved_top_k[:12],
        "admitted_planner_candidates": admitted,
        "unify_failures": unify_failures,
        "backward_plan_failure": {
            "stage": gate0.get("stage"),
            "decision": gate0.get("decision"),
            "reason": gate0.get("reason"),
            "top_retrieved_rule_ids": top_retrieved_ids,
        },
    }


def _to_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Oracle Trace Summary (Phase-1)",
        "",
        "| qid | domain | goal_predicate | top_retrieved_count | admitted_candidates | unify_failures | backward_reason |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        goal = row.get("final_goal") if isinstance(row.get("final_goal"), dict) else {}
        goal_pred = str(goal.get("predicate") or "")
        retrieved_count = len(row.get("backward_plan_failure", {}).get("top_retrieved_rule_ids") or [])
        admitted_count = len(row.get("admitted_planner_candidates") or [])
        unify_count = len(row.get("unify_failures") or [])
        reason = str(row.get("backward_plan_failure", {}).get("reason") or "")
        lines.append(
            f"| {row.get('qid','')} | {row.get('domain_hint','')} | {goal_pred} | {retrieved_count} | {admitted_count} | {unify_count} | {reason} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract oracle trace chain for representative failed cases.")
    parser.add_argument(
        "--rerun-dir",
        type=Path,
        required=True,
        help="Path to rerun q_per_case_runtime directory.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Project root containing data/processed/rulebase.",
    )
    parser.add_argument(
        "--case-ids",
        nargs="*",
        default=None,
        help="Specific case IDs (e.g., n01 n11 n21). If omitted, auto-select representative failures.",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=5,
        help="Maximum number of cases to extract when auto-selecting.",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=None,
        help="Output JSON path. Default: <rerun-dir>/oracle_trace_phase1_5cases.json",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=None,
        help="Output markdown path. Default: <rerun-dir>/oracle_trace_phase1_5cases.md",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rerun_dir = args.rerun_dir
    results_path = rerun_dir / "30_case_audit_results.json"
    rows = _read_json(results_path)
    if not isinstance(rows, list):
        raise ValueError(f"Invalid results payload: {results_path}")

    if args.case_ids:
        selected_ids = _unique_keep_order([str(x).strip() for x in args.case_ids if str(x).strip()])
    else:
        selected_ids = _select_representative_cases(rows, max_cases=args.max_cases)

    selected_rows: list[dict[str, Any]] = []
    row_map = {str(r.get("id") or ""): r for r in rows if isinstance(r, dict)}
    for cid in selected_ids:
        if cid in row_map:
            selected_rows.append(row_map[cid])

    indexes = _build_rulebase_indexes(args.project_root)
    traces = [_extract_case_trace(r, rerun_dir, indexes) for r in selected_rows]

    out_json = args.out_json or (rerun_dir / "oracle_trace_phase1_5cases.json")
    out_md = args.out_md or (rerun_dir / "oracle_trace_phase1_5cases.md")

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "meta": {
            "rerun_dir": str(rerun_dir),
            "selected_case_ids": selected_ids,
            "selection_mode": "manual" if args.case_ids else "auto_representative_no_grounded_rule_found",
        },
        "cases": traces,
    }
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(_to_markdown(traces), encoding="utf-8")

    print(f"[oracle-trace] wrote JSON: {out_json}")
    print(f"[oracle-trace] wrote MD: {out_md}")
    print(f"[oracle-trace] cases: {', '.join(selected_ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
