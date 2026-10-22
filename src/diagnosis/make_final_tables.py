"""Final Section 5 numbers on the full scope: 300 QA, 1,950 single-fault instances (1,499 dev + 451 test),
453 two-fault instances (349 dev + 104 test). Computed only from saved per-instance logs; nothing is re-run here.

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.make_final_tables
      -> experiments/final_tables.json, experiments/final_tables.md

Sources
  single fault : experiments/diag_dataset/ensemble_gpt/*/results_all.json        (all 5 configs, 1,950 each)
  budget       : experiments/budget/budget_results_all.json                       (re-run 2026-10-22, 1,950;
                 its unlimited setting agrees with the logs above on 1,950/1,950 instances)
  two faults   : experiments/multi_fault/results.json                             (453 per config)
  end-to-end   : experiments/e2e/qa_results.json, irac_scores_v2_all.json         (300 questions)
"""

from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

from .strict_eval import asked, multi_gold, norm_set, single_gold

ROOT = Path(__file__).resolve().parents[2]
E = ROOT / "experiments"


def load_single(cfg: str) -> list[dict]:
    base = E / "diag_dataset" / "ensemble_gpt"
    rows = []
    for d in sorted(os.listdir(base)):
        rows += json.loads((base / d / "results_all.json").read_text(encoding="utf-8"))["per_instance"][cfg]
    return rows


def per_instance(r: dict, gold_of) -> tuple[int, int, int, int, int]:
    """(true positives, false positives, false negatives, clarification questions, unnecessary questions)"""
    g = gold_of(r)
    p = norm_set(r["first_diagnosis"])
    if not any(x.startswith(("ResolvableRuleOverlap", "UnresolvedKBConflict")) for x in g):
        p = {x for x in p if not x.startswith("ResolvableRuleOverlap")}
    good = {x.split("(", 1)[1][:-1] for x in g if x.startswith(("MissingCaseInformation", "ParserOmission"))}
    a = asked(r["recovery"])
    return len(p & g), len(p - g), len(g - p), len(a), sum(c not in good for c in a)


def f1(t) -> float:
    tp, fp, fn = sum(x[0] for x in t), sum(x[1] for x in t), sum(x[2] for x in t)
    P, R = tp / max(1, tp + fp), tp / max(1, tp + fn)
    return 2 * P * R / max(1e-9, P + R)


def diff_ci(H, O, stat, n=2000, seed=0):
    rng = random.Random(seed)
    N = len(H)
    ds = sorted(stat([O[i] for i in idx]) - stat([H[i] for i in idx])
                for idx in ([rng.randrange(N) for _ in range(N)] for _ in range(n)))
    return round(stat(O) - stat(H), 4), [round(ds[int(0.025 * n)], 4), round(ds[int(0.975 * n) - 1], 4)]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    out: dict = {"scope": {"qa_questions": 300, "single_fault_instances": None, "two_fault_instances": None}}
    single = {c: load_single(c) for c in ("nesy_diag", "rule_check", "raw_nli", "no_mbd", "base_nesy")}
    n1 = len(single["nesy_diag"])
    mf = json.loads((E / "multi_fault" / "results.json").read_text(encoding="utf-8"))["rows"]
    two = {c: mf[f"dev|{c}"] + mf[f"test|{c}"] for c in ("nesy_diag", "rule_check", "no_mbd")}
    n2 = len(two["nesy_diag"])
    out["scope"]["single_fault_instances"], out["scope"]["two_fault_instances"] = n1, n2

    # ---- single fault, fault level ----
    sf = {}
    for c, rows in single.items():
        faulty = [r for r in rows if r["gold_category"] != "Normal"]
        d = {"n": len(rows), "n_faulty": len(faulty), "qa_acc": sum(r["answer_ok"] for r in rows) / len(rows),
             "qa_acc_faulty": sum(r["answer_ok"] for r in faulty) / len(faulty),
             "clarifications_per_query": sum(len(asked(r["recovery"])) for r in rows) / len(rows)}
        if c != "base_nesy":
            t = [per_instance(r, single_gold) for r in rows]
            tp, fp, fn = sum(x[0] for x in t), sum(x[1] for x in t), sum(x[2] for x in t)
            d |= {"fault_precision": tp / max(1, tp + fp), "fault_recall": tp / max(1, tp + fn), "fault_f1": f1(t),
                  "extra_faults_per_query": fp / len(rows), "unnecessary_questions_per_query": sum(x[4] for x in t) / len(rows)}
        sf[c] = {k: round(v, 4) if isinstance(v, float) else v for k, v in d.items()}
    out["single_fault"] = sf
    H = [per_instance(r, single_gold) for r in single["rule_check"]]
    O = [per_instance(r, single_gold) for r in single["nesy_diag"]]
    out["single_fault_ci"] = {"fault_f1_diff": diff_ci(H, O, f1),
                              "unnecessary_questions_diff": diff_ci(H, O, lambda t: sum(x[4] for x in t) / len(t)),
                              "extra_faults_diff": diff_ci(H, O, lambda t: sum(x[1] for x in t) / len(t))}

    # ---- two faults ----
    tf = {}
    for c, rows in two.items():
        t = [per_instance(r, multi_gold) for r in rows]
        tp, fp, fn = sum(x[0] for x in t), sum(x[1] for x in t), sum(x[2] for x in t)
        tf[c] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in {
            "n": len(rows), "both_found": sum(r["both_found"] for r in rows) / len(rows),
            "any_found": sum(r["any_found"] for r in rows) / len(rows), "qa_acc": sum(r["answer_ok"] for r in rows) / len(rows),
            "fault_f1": f1(t), "fault_precision": tp / max(1, tp + fp), "fault_recall": tp / max(1, tp + fn),
            "clarifications_per_query": sum(r["asks"] for r in rows) / len(rows),
            "unnecessary_questions_per_query": sum(x[4] for x in t) / len(rows)}.items()}
    out["two_faults"] = tf
    H2 = [per_instance(r, multi_gold) for r in two["rule_check"]]
    O2 = [per_instance(r, multi_gold) for r in two["nesy_diag"]]
    out["two_faults_ci"] = {"fault_f1_diff": diff_ci(H2, O2, f1),
                            "unnecessary_questions_diff": diff_ci(H2, O2, lambda t: sum(x[4] for x in t) / len(t))}

    # ---- clarification budget (re-run on 1,950) ----
    b = json.loads((E / "budget" / "budget_results_all.json").read_text(encoding="utf-8"))["summary"]
    out["budget"] = {c: {k: b[f"{c}|{k}"]["qa_acc"] for k in ("0", "1", "2", "inf")} | {"n": b[f"{c}|0"]["n"]}
                     for c in ("nesy_diag", "rule_check", "no_mbd", "raw_nli")}
    out["budget"]["base_nesy"] = {k: sf["base_nesy"]["qa_acc"] for k in ("0", "1", "2", "inf")} | {"n": n1}

    # ---- end-to-end + IRAC (300) ----
    qa = json.loads((E / "e2e" / "qa_results.json").read_text(encoding="utf-8"))["summary"]
    ir = json.loads((E / "e2e" / "irac_scores_v2_all.json").read_text(encoding="utf-8"))["summary"]
    out["end_to_end"] = {m: {"qa_acc_300": qa["all"][m], "qa_acc_test_106": qa["test"][m], "qa_acc_dev_194": qa["dev"][m],
                             "irac_300": ir[m]["IRAC_0_100"]} for m in ("gpt4o", "symbolic", "heuristic", "ours")}
    (E / "final_tables.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

    p = lambda x: f"{100 * x:.1f}"  # noqa: E731
    e2e, s, t = out["end_to_end"], sf, tf
    L = [f"# Final Section 5 tables — 300 QA, {n1} single-fault and {n2} two-fault diagnostic instances", "",
         f"**Table 1. Main comparison.** E2E QA: all 300 questions, real GPT-4o parser. Faulty QA, Clarif./query: "
         f"{s['nesy_diag']['n_faulty']} faulty of the {n1} diagnostic instances / all {n1}. IRAC: 300 questions (1,200 answers).", "",
         "| Method | E2E QA Acc. ↑ | Faulty QA Acc. ↑ | Clarif. / query ↓ | IRAC ↑ |", "|---|---|---|---|---|",
         f"| GPT-4o (pure LLM) | {p(e2e['gpt4o']['qa_acc_300'])} | N/A | N/A | {e2e['gpt4o']['irac_300']} |",
         f"| Symbolic QA | {p(e2e['symbolic']['qa_acc_300'])} | {p(s['base_nesy']['qa_acc_faulty'])} | 0.00 | {e2e['symbolic']['irac_300']} |",
         f"| Heuristic diagnosis | {p(e2e['heuristic']['qa_acc_300'])} | {p(s['rule_check']['qa_acc_faulty'])} | {s['rule_check']['clarifications_per_query']:.2f} | {e2e['heuristic']['irac_300']} |",
         f"| **Ours (cross-layer MBD)** | {p(e2e['ours']['qa_acc_300'])} | {p(s['nesy_diag']['qa_acc_faulty'])} | {s['nesy_diag']['clarifications_per_query']:.2f} | {e2e['ours']['irac_300']} |",
         "", f"**Table 2. Diagnostic performance.** Single-fault: {n1} instances; two-fault: {n2} instances. "
         "A reported fault counts as correct only if it was injected.", "",
         "| Method | Fault F1-score (single-fault) ↑ | Fault F1-score (two-fault) ↑ | Extra faults / query ↓ | Unnecessary questions / query ↓ |",
         "|---|---|---|---|---|"]
    for c, name in (("no_mbd", "Direct symptom→cause mapping"), ("rule_check", "Heuristic diagnosis"),
                    ("nesy_diag", "**Ours (cross-layer MBD)**")):
        L.append(f"| {name} | {p(s[c]['fault_f1'])} | {p(t[c]['fault_f1'])} | {s[c]['extra_faults_per_query']:.2f} | "
                 f"{s[c]['unnecessary_questions_per_query']:.2f} |")
    ci, ci2 = out["single_fault_ci"], out["two_faults_ci"]
    L += ["", f"Ours − Heuristic (95% paired bootstrap): fault F1 single {100*ci['fault_f1_diff'][0]:+.1f} "
          f"[{100*ci['fault_f1_diff'][1][0]:.1f}, {100*ci['fault_f1_diff'][1][1]:.1f}], two-fault {100*ci2['fault_f1_diff'][0]:+.1f} "
          f"[{100*ci2['fault_f1_diff'][1][0]:.1f}, {100*ci2['fault_f1_diff'][1][1]:.1f}]; unnecessary questions/query "
          f"{ci['unnecessary_questions_diff'][0]:+.2f} [{ci['unnecessary_questions_diff'][1][0]:.2f}, {ci['unnecessary_questions_diff'][1][1]:.2f}].",
          "", f"**Two simultaneous faults (n = {n2}).**", "",
          "| Method | Both faults found | ≥ 1 found | QA acc. | Clarif. / query |", "|---|---|---|---|---|"]
    for c, name in (("no_mbd", "Direct mapping"), ("rule_check", "Heuristic"), ("nesy_diag", "Ours")):
        L.append(f"| {name} | {p(t[c]['both_found'])} | {p(t[c]['any_found'])} | {p(t[c]['qa_acc'])} | {t[c]['clarifications_per_query']:.2f} |")
    L += ["", f"**Figure 1 data — QA accuracy vs clarification budget (n = {n1}).**", "",
          "| Method | B = 0 | B = 1 | B = 2 | unlimited |", "|---|---|---|---|---|"]
    for c, name in (("no_mbd", "Direct mapping"), ("rule_check", "Heuristic"), ("nesy_diag", "Ours")):
        L.append(f"| {name} | " + " | ".join(p(out["budget"][c][k]) for k in ("0", "1", "2", "inf")) + " |")
    L += ["", f"**Figure 2 data — ablation (n = {n1}).**", "",
          "| Variant | QA acc. | Fault F1-score | Clarif. / query |", "|---|---|---|---|"]
    for c, name in (("nesy_diag", "Ours (full)"), ("raw_nli", "− acceptance test"), ("no_mbd", "− MBD"),
                    ("base_nesy", "− diagnosis & recovery")):
        L.append(f"| {name} | {p(s[c]['qa_acc'])} | {'–' if 'fault_f1' not in s[c] else p(s[c]['fault_f1'])} | "
                 f"{s[c]['clarifications_per_query']:.2f} |")
    (E / "final_tables.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
