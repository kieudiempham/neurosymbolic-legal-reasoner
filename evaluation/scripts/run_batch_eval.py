"""
Batch evaluation runner for qa_290 experiment (gold_mode).

Reads:  evaluation/qa_290_exp_cases_gold_mode.jsonl   (290 cases, one per line)
Writes: evaluation/results/qa_290_nesy_fulltrace_v1.jsonl  (one result JSON per line)

Usage:
    python evaluation/scripts/run_batch_eval.py
    python evaluation/scripts/run_batch_eval.py --limit 10          # first N cases
    python evaluation/scripts/run_batch_eval.py --resume            # skip already-done ids
    python evaluation/scripts/run_batch_eval.py --output results/custom.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
CASES_FILE = ROOT / "evaluation" / "qa_290_exp_cases_gold_mode.jsonl"
DEFAULT_OUT = ROOT / "evaluation" / "results" / "qa_290_nesy_fulltrace_v1.jsonl"
API_URL = "http://127.0.0.1:8001/ask"
TIMEOUT = 60  # seconds per request


# ---------------------------------------------------------------------------
# Response extraction helpers
# ---------------------------------------------------------------------------

def _get(obj: Any, *keys: str, default: Any = None) -> Any:
    cur = obj
    for k in keys:
        if isinstance(cur, dict):
            cur = cur.get(k)
        else:
            return default
        if cur is None:
            return default
    return cur


def _extract_verification(resp: dict) -> dict[str, str]:
    """Map verification_trace entries → parse/rule/forward/answer PASS/FAIL."""
    trace: list[dict] = resp.get("verification_trace") or []
    result = {"parse": "N/A", "rule": "N/A", "forward": "N/A", "answer": "N/A"}
    mode_map = {
        "parse_verification": "parse",
        "rule_verification":  "rule",
        "forward_verification": "forward",
        "answer_verification": "answer",
    }
    for entry in trace:
        mode = entry.get("mode", "")
        key = mode_map.get(mode)
        if key is None:
            continue
        ok = entry.get("symbolic_ok")
        decision = entry.get("final_decision", "")
        if ok is True or decision in ("OK", "PASS"):
            result[key] = "PASS"
        elif ok is False or decision in ("FAIL", "BLOCK"):
            result[key] = "FAIL"
        else:
            result[key] = decision or "N/A"
    return result


def _extract_final_status(resp: dict) -> str:
    """Derive a coarse final_status from the response."""
    answer = resp.get("answer") or {}
    gen_mode = answer.get("generation_mode", "")
    if resp.get("needs_clarification"):
        return "needs_clarification"
    if "fallback" in gen_mode.lower():
        return "fallback"
    proof = resp.get("proof") or {}
    conclusion = (proof.get("conclusion") or "").lower()
    if "blocked" in conclusion or "fail" in conclusion:
        return "partial"
    if answer.get("answer_text"):
        return "success"
    return "unknown"


def _extract_legal_citations(resp: dict) -> list[str]:
    citations = _get(resp, "answer", "legal_citations") or []
    out: list[str] = []
    for c in citations:
        label = c.get("display_label") or c.get("label") or c.get("source_ref") or ""
        if label:
            out.append(label)
    return out


def _extract_missing_facts(resp: dict) -> list[str]:
    """Extract missing / clarification facts from the response."""
    questions: list[dict] = resp.get("clarification_questions") or []
    facts: list[str] = []
    for q in questions:
        fact = q.get("missing_fact") or q.get("question_text") or ""
        if fact:
            facts.append(fact)
    # also try clarification_artifact
    artifact = resp.get("clarification_artifact") or {}
    missing = artifact.get("missing_facts") or []
    for m in missing:
        if isinstance(m, str) and m not in facts:
            facts.append(m)
        elif isinstance(m, dict):
            f = m.get("fact_key") or m.get("fact") or ""
            if f and f not in facts:
                facts.append(f)
    return facts


def _proof_present(resp: dict) -> bool:
    proof = resp.get("proof") or {}
    return bool(proof.get("proof_id") and proof.get("used_rules"))


def build_result_record(case: dict, resp: dict) -> dict:
    selected_rule = resp.get("selected_rule") or {}
    reasoning_result = resp.get("reasoning_result") or {}
    domains_used: list[str] = reasoning_result.get("active_domains_used") or []

    return {
        "id": case["id"],
        "question": case["question"],

        # --- system output ---
        "predicted_domains": domains_used,
        "selected_rule_id": selected_rule.get("rule_id"),

        "final_answer": _get(resp, "answer", "answer_text"),
        "final_status": _extract_final_status(resp),

        "proof_present": _proof_present(resp),
        "legal_citations": _extract_legal_citations(resp),

        "missing_facts": _extract_missing_facts(resp),

        "verification": _extract_verification(resp),

        # --- gold reference (for eval script) ---
        "gold_answer_mode": case.get("gold_answer_mode"),
        "gold_missing_facts": case.get("gold_missing_facts") or [],
        "gold_response_requirements": case.get("gold_response_requirements") or {},

        # --- metadata ---
        "domain": case.get("domain"),
        "question_group": case.get("question_group"),

        # irac filled by compute_eval_tables.py, placeholder here
        "irac": None,

        "latency_ms": None,   # filled below
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_done_ids(out_path: Path) -> set[str]:
    done: set[str] = set()
    if not out_path.exists():
        return done
    with out_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                done.add(rec["id"])
            except Exception:
                pass
    return done


def run(args: argparse.Namespace) -> int:
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    done_ids: set[str] = set()
    if args.resume:
        done_ids = load_done_ids(out_path)
        print(f"[resume] {len(done_ids)} cases already done, skipping.")

    cases: list[dict] = []
    with CASES_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))

    if args.limit:
        cases = cases[: args.limit]

    total = len(cases)
    skipped = 0
    success = 0
    errors = 0

    write_mode = "a" if args.resume else "w"
    with out_path.open(write_mode, encoding="utf-8") as out_f:
        for i, case in enumerate(cases, 1):
            cid = case["id"]
            if cid in done_ids:
                skipped += 1
                continue

            payload = {
                "question": case["question"],
                "domain": case.get("domain"),
            }

            t0 = time.perf_counter()
            try:
                r = requests.post(API_URL, json=payload, timeout=TIMEOUT)
                r.raise_for_status()
                resp = r.json()
                latency_ms = round((time.perf_counter() - t0) * 1000)
            except Exception as exc:
                latency_ms = round((time.perf_counter() - t0) * 1000)
                print(f"  [{i}/{total}] ERROR {cid}: {exc}", file=sys.stderr)
                record = {
                    "id": cid,
                    "question": case["question"],
                    "domain": case.get("domain"),
                    "question_group": case.get("question_group"),
                    "gold_answer_mode": case.get("gold_answer_mode"),
                    "gold_missing_facts": case.get("gold_missing_facts") or [],
                    "gold_response_requirements": case.get("gold_response_requirements") or {},
                    "final_status": "error",
                    "error": str(exc),
                    "latency_ms": latency_ms,
                }
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                out_f.flush()
                errors += 1
                continue

            record = build_result_record(case, resp)
            record["latency_ms"] = latency_ms

            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            out_f.flush()
            success += 1

            status_flag = "OK" if record["final_status"] == "success" else record["final_status"].upper()
            print(f"  [{i}/{total}] {cid} | {status_flag} | {latency_ms}ms")

    print(f"\nDone. success={success}, errors={errors}, skipped={skipped}")
    print(f"Output: {out_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch eval runner for qa_290")
    parser.add_argument("--limit", type=int, default=0, help="Run only first N cases (0=all)")
    parser.add_argument("--resume", action="store_true", help="Skip cases already in output file")
    parser.add_argument("--output", default=str(DEFAULT_OUT), help="Output jsonl path")
    return run(parser.parse_args())


if __name__ == "__main__":
    sys.exit(main())
