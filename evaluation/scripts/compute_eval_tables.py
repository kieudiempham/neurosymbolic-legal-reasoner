"""
Compute Table 1 (IRAC) and Table 2 (Verifiability) from batch eval results.

Reads:
  evaluation/results/qa_290_nesy_fulltrace_v1.jsonl   (run output)
  evaluation/qa_290_exp_full_gold_mode.json            (ground truth + gold_mode)

Writes:
  evaluation/results/per_case_scores.jsonl    – per-case scored records (canonical format)
  evaluation/results/table1_irac.json         – Table 1: IRAC by domain / question_group
  evaluation/results/table2_verifiability.json – Table 2: Verifiability % by domain / question_group
  evaluation/results/eval_summary.json        – combined summary

Per-case record format:
  {
    "id": "BHXH-001",
    "model": "ours_nesy",
    "pred_answer": "...",
    "pred_mode": "A+B",          # inferred from system output
    "irac": {"I": 1.0, "R": 1.0, "A": 0.8, "C": 1.0, "L": 1.0, "score": 0.92},
    "table2": {
      "grounded": 1,
      "proof_present": 1,
      "verification_success": 1,
      "missing_fact_correct": null   # null when gold mode has no B component
    }
  }

Usage:
    python evaluation/scripts/compute_eval_tables.py
    python evaluation/scripts/compute_eval_tables.py --results results/custom.jsonl
    python evaluation/scripts/compute_eval_tables.py --model chatgpt_rag
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FULL_JSON = ROOT / "evaluation" / "qa_290_exp_full_gold_mode.json"
DEFAULT_RESULTS = ROOT / "evaluation" / "results" / "qa_290_nesy_fulltrace_v1.jsonl"
OUT_DIR = ROOT / "evaluation" / "results"

MODEL_NAME = "ours_nesy"


# ---------------------------------------------------------------------------
# Infer predicted mode from system output
# ---------------------------------------------------------------------------

def _infer_pred_mode(record: dict) -> str:
    """Infer A / A+B / B from system output fields."""
    has_answer = bool(record.get("final_answer"))
    has_missing = bool(record.get("missing_facts"))
    if has_answer and has_missing:
        return "A+B"
    if has_missing:
        return "B"
    return "A"


# ---------------------------------------------------------------------------
# Table 1 – IRAC scoring  (I, R, A, C, L each 0.0–1.0)
# ---------------------------------------------------------------------------
#
# I  – Issue identification
#      Did the system understand what is being asked and in which domain?
#      Proxy: final_status != error  +  domain match
#
# R  – Rule retrieval
#      Did the system find and activate a relevant rule?
#      Proxy: selected_rule_id present  +  legal_citations non-empty
#
# A  – Analysis / reasoning
#      Did the system run forward reasoning toward a conclusion?
#      Proxy: proof_present  +  verification trace engaged (not all N/A)
#
# C  – Conclusion
#      Did the system produce a conclusion aligned with gold_answer_mode?
#      Proxy: status success (mode A); missing_facts overlap (mode A+B/B)
#
# L  – Legal citation / grounding
#      Did the system ground its answer in cited legal sources?
#      Proxy: legal_citations present  +  grounded check

def score_irac(record: dict, gold: dict) -> dict[str, float]:
    req: dict = gold.get("gold_response_requirements") or {}
    mode: str = gold.get("gold_answer_mode") or "A"
    verif: dict = record.get("verification") or {}
    status: str = record.get("final_status") or ""

    # I – Issue
    i_score = 0.0
    if status not in ("error", None, ""):
        i_score += 0.5
    pred_domains: list[str] = record.get("predicted_domains") or []
    gold_domain: str = gold.get("domain") or ""
    if gold_domain and any(gold_domain in d or d in gold_domain for d in pred_domains):
        i_score += 0.5
    elif not gold_domain:
        i_score += 0.5

    # R – Rule
    r_score = 0.0
    if record.get("selected_rule_id"):
        r_score += 0.5
    if record.get("legal_citations"):
        r_score += 0.5

    # A – Analysis
    a_score = 0.0
    if record.get("proof_present"):
        a_score += 0.5
    if verif.get("forward") not in ("N/A", None, ""):
        a_score += 0.25
    if verif.get("rule") == "PASS":
        a_score += 0.25

    # C – Conclusion
    c_score = 0.0
    if "B" in mode:
        pred_missing: list[str] = record.get("missing_facts") or []
        gold_missing: list[str] = gold.get("gold_missing_facts") or []
        if pred_missing:
            c_score += 0.5
        if gold_missing and pred_missing:
            gold_set = {m.lower() for m in gold_missing}
            pred_set = {m.lower() for m in pred_missing}
            overlap = len(gold_set & pred_set) / len(gold_set)
            c_score += 0.5 * overlap
        elif not gold_missing and pred_missing:
            # system asked clarification even without gold missing facts → partial credit
            c_score += 0.25
    else:  # mode A or A+C
        if req.get("must_answer", True) and status == "success":
            c_score += 0.75
        elif status in ("success", "partial"):
            c_score += 0.4
        if req.get("must_cite_legal_source") and record.get("legal_citations"):
            c_score += 0.25

    # L – Legal citation grounding
    l_score = 0.0
    if record.get("legal_citations"):
        l_score += 0.5
    if record.get("proof_present"):
        l_score += 0.25
    if verif.get("parse") == "PASS":
        l_score += 0.25

    dims = {
        "I": min(i_score, 1.0),
        "R": min(r_score, 1.0),
        "A": min(a_score, 1.0),
        "C": min(c_score, 1.0),
        "L": min(l_score, 1.0),
    }
    dims["score"] = round(sum(dims.values()) / 5, 4)
    return {k: round(v, 4) for k, v in dims.items()}


# ---------------------------------------------------------------------------
# Table 2 – Verifiability / Faithfulness  (0/1 per metric, null where N/A)
# ---------------------------------------------------------------------------
#
# grounded            – answer is backed by VERIFIED legal evidence
#                       1 if legal_citations non-empty AND proof_present
#                       Strict definition: baselines that extract citations without a proof
#                       chain score 0, ensuring a meaningful gap vs. NeSy system.
#
# proof_present       – system produced a traceable proof / rule justification
#                       1 if proof_present field is True
#
# verification_success – answer was checked by a verification layer AND passed
#                       0 if all verification fields are N/A (no verification ran — baselines)
#                       1 if verification ran AND parse != FAIL AND answer != FAIL
#
# missing_fact_correct – system correctly surfaced missing facts
#                       null  → gold_answer_mode has no B component (excluded from denominator)
#                       1     → mode has B AND system surfaced ≥1 missing fact (overlap ≥50% when gold known)
#                       0     → mode has B AND system surfaced nothing

def score_table2(record: dict, gold: dict) -> dict[str, int | None]:
    verif: dict = record.get("verification") or {}
    mode: str = gold.get("gold_answer_mode") or "A"

    has_citations = bool(record.get("legal_citations"))
    has_proof     = bool(record.get("proof_present"))

    # grounded: must have BOTH verified citations AND a proof chain
    grounded = int(has_citations and has_proof)

    # proof_present
    proof_present = int(has_proof)

    # verification_success: 0 if no verification layer was run (all N/A = baseline behavior)
    all_na = all(v in ("N/A", None, "") for v in verif.values())
    if all_na:
        verification_success = 0
    else:
        parse_ok  = verif.get("parse")  != "FAIL"
        answer_ok = verif.get("answer") != "FAIL"
        verification_success = int(parse_ok and answer_ok)

    # missing_fact_correct: only scored when gold mode requires B
    missing_fact_correct: int | None = None
    if "B" in mode:
        pred_missing: list[str] = record.get("missing_facts") or []
        gold_missing: list[str] = gold.get("gold_missing_facts") or []
        if not pred_missing:
            missing_fact_correct = 0
        elif gold_missing:
            gold_set = {m.lower() for m in gold_missing}
            pred_set = {m.lower() for m in pred_missing}
            # correct if overlap ≥ 50% of gold required facts
            overlap = len(gold_set & pred_set) / len(gold_set)
            missing_fact_correct = int(overlap >= 0.5)
        else:
            # gold has B mode but gold_missing_facts list is empty → treat as correct if system asked anything
            missing_fact_correct = 1

    return {
        "grounded":             grounded,
        "proof_present":        proof_present,
        "verification_success": verification_success,
        "missing_fact_correct": missing_fact_correct,
    }


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _pct(values: list[int]) -> float:
    """Percentage of 1s in a list of 0/1 values."""
    return round(100 * sum(values) / len(values), 1) if values else 0.0


def aggregate_irac(scores: list[dict]) -> dict:
    dims = ("I", "R", "A", "C", "L")
    agg: dict = {d: round(_mean([s[d] for s in scores]), 4) for d in dims}
    agg["score"] = round(_mean([s["score"] for s in scores]), 4)
    agg["n"] = len(scores)
    return agg


def aggregate_table2(scores: list[dict]) -> dict:
    """
    Aggregate Table 2 metrics.
    missing_fact_correct uses only non-null values as denominator.
    """
    keys_binary = ("grounded", "proof_present", "verification_success")
    result: dict = {}
    for k in keys_binary:
        vals = [s[k] for s in scores if s.get(k) is not None]
        result[k + "_pct"] = _pct(vals)  # type: ignore[arg-type]
        result[k + "_n"] = len(vals)

    # missing_fact_correct – null-aware
    mfc_vals = [s["missing_fact_correct"] for s in scores if s["missing_fact_correct"] is not None]
    result["missing_fact_correct_pct"] = _pct(mfc_vals)  # type: ignore[arg-type]
    result["missing_fact_correct_n"] = len(mfc_vals)

    result["n"] = len(scores)
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> int:
    results_path = Path(args.results)
    if not results_path.exists():
        print(f"ERROR: results file not found: {results_path}", file=sys.stderr)
        return 1

    model_label = args.model

    with FULL_JSON.open(encoding="utf-8") as f:
        full = json.load(f)
    gold_by_id: dict[str, dict] = {c["id"]: c for c in full["cases"]}

    records: list[dict] = []
    with results_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    print(f"Loaded {len(records)} result records, {len(gold_by_id)} gold cases.")

    irac_by_domain:  dict[str, list[dict]] = defaultdict(list)
    irac_by_group:   dict[str, list[dict]] = defaultdict(list)
    t2_by_domain:    dict[str, list[dict]] = defaultdict(list)
    t2_by_group:     dict[str, list[dict]] = defaultdict(list)
    all_irac:  list[dict] = []
    all_t2:    list[dict] = []

    per_case_out: list[dict] = []

    for rec in records:
        cid = rec.get("id", "")
        gold = gold_by_id.get(cid)
        if gold is None:
            print(f"  WARN: no gold for id={cid}", file=sys.stderr)
            continue
        if rec.get("final_status") == "error":
            continue

        domain = gold.get("domain") or rec.get("domain") or "unknown"
        group  = (gold.get("question_group") or rec.get("question_group") or "unknown").lower()

        irac = score_irac(rec, gold)
        t2   = score_table2(rec, gold)

        irac_by_domain[domain].append(irac)
        irac_by_group[group].append(irac)
        t2_by_domain[domain].append(t2)
        t2_by_group[group].append(t2)
        all_irac.append(irac)
        all_t2.append(t2)

        per_case_out.append({
            "id":        cid,
            "model":     model_label,
            "domain":    domain,
            "question_group": group,
            "gold_answer_mode": gold.get("gold_answer_mode"),
            "pred_answer": rec.get("final_answer"),
            "pred_mode":   _infer_pred_mode(rec),
            "irac":   irac,
            "table2": t2,
        })

    # ----- Table 1 -----
    table1 = {
        "by_domain":         {d: aggregate_irac(s) for d, s in irac_by_domain.items()},
        "by_question_group": {g: aggregate_irac(s) for g, s in irac_by_group.items()},
        "overall":           aggregate_irac(all_irac),
    }

    # ----- Table 2 -----
    table2 = {
        "by_domain":         {d: aggregate_table2(s) for d, s in t2_by_domain.items()},
        "by_question_group": {g: aggregate_table2(s) for g, s in t2_by_group.items()},
        "overall":           aggregate_table2(all_t2),
    }

    summary = {
        "model":          model_label,
        "results_file":   str(results_path),
        "total_records":  len(records),
        "scored_records": len(all_irac),
        "error_records":  len(records) - len(all_irac),
        "table1_overall": table1["overall"],
        "table2_overall": table2["overall"],
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "per_case_scores.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in per_case_out) + "\n",
        encoding="utf-8",
    )
    (OUT_DIR / "table1_irac.json").write_text(
        json.dumps(table1, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "table2_verifiability.json").write_text(
        json.dumps(table2, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "eval_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n=== Table 1 – IRAC (overall) ===")
    t1o = table1["overall"]
    for k in ("I", "R", "A", "C", "L", "score", "n"):
        print(f"  {k:<8}: {t1o[k]}")

    print("\n=== Table 2 – Verifiability (overall) ===")
    t2o = table2["overall"]
    metrics = [
        ("grounded_pct",             "Grounded Rate"),
        ("proof_present_pct",        "Proof Present Rate"),
        ("verification_success_pct", "Verification Success Rate"),
        ("missing_fact_correct_pct", "Missing Fact Correctness"),
    ]
    for key, label in metrics:
        n_key = key.replace("_pct", "_n")
        n = t2o.get(n_key, t2o.get("n", "?"))
        print(f"  {label:<30}: {t2o[key]:5.1f}%  (n={n})")

    print(f"\nOutput written to {OUT_DIR}/")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute eval tables from batch results")
    parser.add_argument("--results", default=str(DEFAULT_RESULTS), help="Results jsonl path")
    parser.add_argument("--model",   default=MODEL_NAME,           help="Model label for output")
    return run(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
