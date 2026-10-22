"""Strict, fault-level evaluation of the diagnosers (standard MBD-style metrics), from saved per-instance results.

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.strict_eval   -> experiments/strict_eval.json / .md

Same rules for every method:
- fault-level precision / recall / F1 (micro): a diagnosed fault is a true positive only if it is an injected
  fault; every other reported fault — including an unstated condition reported as missing — is a false
  positive. Encoded resolvable overlaps count as faults only where an overlap/conflict was injected.
- exact isolation: the set of reported faults equals the set of injected faults.
- clarification precision: share of clarification questions that ask about an injected missing/omitted
  proposition; unnecessary questions per query.
- questions per correct answer.
Evaluated on the held-out test sets: single fault (5 domains), two simultaneous faults.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAME = {"missing": "MissingCaseInformation", "omission": "ParserOmission", "misinterp": "ParserMisinterpretation",
        "unsupported": "UnsupportedParserFact"}


def split_fault(f: str) -> set[str]:
    """'MissingCaseInformation(a,b)' -> {'MissingCaseInformation(a)', 'MissingCaseInformation(b)'}; pairs stay whole."""
    cat, args = f.split("(", 1)
    args = args[:-1]
    if cat in ("ResolvableRuleOverlap", "UnresolvedKBConflict"):
        return {f"{cat}({args.replace(' ', '')})"}
    return {f"{cat}({a.strip()})" for a in args.split(",") if a.strip()}


def norm_set(faults: list[str]) -> set[str]:
    out = set()
    for f in faults:
        out |= split_fault(f)
    return out


def asked(recovery: list[str]) -> list[str]:
    out = []
    for x in recovery:
        m = re.match(r"(Clarify|MissingCaseInformation)\((.+)\)$", x)
        if m:
            out.append(m.group(2))
    return out


def evaluate(rows: list[dict], gold_of) -> dict:
    tp = fp = fn = exact = 0
    q_total = q_good = 0
    sizes = []
    correct_answers = sum(r["answer_ok"] for r in rows)
    for r in rows:
        gold = gold_of(r)
        pred = norm_set(r["first_diagnosis"])
        if not any(g.startswith(("ResolvableRuleOverlap", "UnresolvedKBConflict")) for g in gold):
            pred = {p for p in pred if not p.startswith("ResolvableRuleOverlap")}  # benign overlap, not a fault
        tp += len(pred & gold)
        fp += len(pred - gold)
        fn += len(gold - pred)
        exact += pred == gold
        if pred:
            sizes.append(len(pred))
        good_props = {g.split("(", 1)[1][:-1] for g in gold if g.startswith(("MissingCaseInformation", "ParserOmission"))}
        for c in asked(r["recovery"]):
            q_total += 1
            q_good += c in good_props
    P = tp / max(1, tp + fp)
    R = tp / max(1, tp + fn)
    n = len(rows)
    return {"n": n, "fault_precision": round(P, 4), "fault_recall": round(R, 4), "fault_f1": round(2 * P * R / max(1e-9, P + R), 4),
            "exact_isolation": round(exact / n, 4), "mean_diagnosis_size": round(sum(sizes) / max(1, len(sizes)), 2),
            "clarifications_per_query": round(q_total / n, 2), "clarification_precision": round(q_good / max(1, q_total), 4),
            "unnecessary_clarifications_per_query": round((q_total - q_good) / n, 2),
            "qa_acc": round(correct_answers / n, 4), "questions_per_correct_answer": round(q_total / max(1, correct_answers), 2)}


def single_gold(r: dict) -> set[str]:
    return set() if not r["gold_fault"] else split_fault(r["gold_fault"])


def multi_gold(r: dict) -> set[str]:
    parts = r["iid"].split("#", 1)[1].split("+")
    return {f"{NAME[p.split(':')[0]]}({p.split(':', 1)[1]})" for p in parts}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    out = {}
    base = ROOT / "experiments" / "diag_dataset" / "ensemble_gpt"
    for split in ("test", "dev"):
        for cfg in ("rule_check", "nesy_diag", "raw_nli", "no_mbd"):
            rows = []
            for d in sorted(os.listdir(base)):
                if d.endswith(split):
                    rows += json.loads((base / d / "results_all.json").read_text(encoding="utf-8"))["per_instance"][cfg]
            out[f"single|{split}|{cfg}"] = evaluate(rows, single_gold)
    mf = json.loads((ROOT / "experiments" / "multi_fault" / "results.json").read_text(encoding="utf-8"))["rows"]
    for split in ("test", "dev"):
        for cfg in ("rule_check", "nesy_diag", "no_mbd"):
            out[f"two_faults|{split}|{cfg}"] = evaluate(mf[f"{split}|{cfg}"], multi_gold)
    (ROOT / "experiments" / "strict_eval.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    keys = ["fault_precision", "fault_recall", "fault_f1", "exact_isolation", "mean_diagnosis_size", "clarifications_per_query",
            "clarification_precision", "unnecessary_clarifications_per_query", "qa_acc", "questions_per_correct_answer"]
    L = ["| Setting | Method | n | " + " | ".join(keys) + " |", "|---|---|---|" + "---|" * len(keys)]
    for k, v in out.items():
        bench, split, cfg = k.split("|")
        L.append(f"| {bench} {split} | { {'rule_check': 'Heuristic', 'nesy_diag': 'Ours', 'raw_nli': 'Ours - acceptance test', 'no_mbd': 'Ours - MBD'}[cfg] } | {v['n']} | " + " | ".join(str(v[x]) for x in keys) + " |")
    (ROOT / "experiments" / "strict_eval.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
