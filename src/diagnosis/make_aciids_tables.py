"""All result tables for the ACIIDS paper, from the saved benchmark results (no re-running).

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.make_aciids_tables  -> experiments/tables_aciids.md

Main measurement = mDeBERTa + GPT-4o-mini (ensemble_gpt), chosen on the development split.
All headline numbers are on held-out TEST data.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXT = ROOT / "experiments" / "diag_external"
DOM = ROOT / "experiments" / "diag_dataset" / "ensemble_gpt"
OUT = ROOT / "experiments" / "tables_aciids.md"
MAIN = "ensemble_gpt"
METHODS = [("base_nesy", "Symbolic QA (no diagnosis)"), ("no_mbd", "Direct symptom→cause (no MBD)"),
           ("rule_check", "Heuristic IF–THEN diagnosis"), ("nesy_diag", "**Ours: Cross-Layer MBD**")]
MODES = {"F1": "MissingCaseInformation", "F2": "ParserOmission", "F3": "ParserMisinterpretation",
         "F4": "UnsupportedParserFact"}
DOMAINS = [("bhxh", "Social insurance"), ("dn", "Enterprise"), ("thue", "Tax"), ("ld", "Labour"), ("ln", "Cross-domain")]


def pct(x) -> str:
    return "–" if x is None else f"{100 * x:.1f}"


def ci(c) -> str:
    return "" if not c else f" [{100 * c[0]:.0f}, {100 * c[1]:.0f}]"


def ext(tool: str, cfg: str) -> dict | None:
    f = EXT / tool / f"results_{cfg}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def asks(rows) -> float:
    return sum(sum(x.startswith(("Clarify", "MissingCase")) for x in r["recovery"]) for r in rows) / max(1, len(rows))


def macro_f1(rows) -> float:
    """Macro-F1 over the four fault types + Normal, on observable faults and CONTROL."""
    labs = ["Normal", *MODES.values()]
    f1s = []
    for lab in labs:
        tp = sum(r["gold_category"] == lab and r["pred_category"] == lab for r in rows)
        fp = sum(r["gold_category"] != lab and r["pred_category"] == lab for r in rows)
        fn = sum(r["gold_category"] == lab and r["pred_category"] != lab for r in rows)
        p, rc = tp / max(1, tp + fp), tp / max(1, tp + fn)
        f1s.append(2 * p * rc / max(1e-9, p + rc))
    return sum(f1s) / len(f1s)


def domain_runs() -> dict:
    out = {}
    for d in sorted(DOM.iterdir()):
        fs = list(d.glob("results_*.json"))
        if fs:
            out[d.name] = json.loads(fs[0].read_text(encoding="utf-8"))
    return out


def pooled(runs: dict, split: str, cfg: str) -> dict:
    rows = [r for name, d in runs.items() if name.endswith(split) for r in d["per_instance"].get(cfg, [])]
    faulty = [r for r in rows if r["gold_category"] != "Normal"]
    from .run_eval import correct_action

    out = {"n": len(rows), "ans": sum(r["answer_ok"] for r in rows) / max(1, len(rows)),
           "ans_faulty": sum(r["answer_ok"] for r in faulty) / max(1, len(faulty)), "asks": asks(rows)}
    if rows and rows[0]["hit"] is not None:
        out["diag"] = sum(r["hit"] for r in rows) / len(rows)
        out["act"] = sum(correct_action(r) for r in rows) / len(rows)
        out["f1"] = macro_f1(rows)
        out["nli"] = sum(r["nli_calls"] for r in rows) / len(rows)
    return out


def main() -> None:
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    L = ["# ACIIDS result tables", "",
         "Measurement (NLI) for all diagnosing methods: mDeBERTa + GPT-4o-mini (mean of label distributions, "
         "prompt v4, τ = 0.50, positive template), all chosen on the **development split only**. "
         "Numbers are on **held-out test** data unless marked dev.", ""]

    # ---- Table 1: overall (per-domain injected-fault benchmark, test pooled) ----
    runs = domain_runs()
    base = pooled(runs, "test", "base_nesy")
    L += ["## Table 1 — Overall performance (controlled fault injection, 5 domains, test pooled)", "",
          f"n = {base['n']} test instances (each a question with one injected or natural fault, or none).", "",
          "| Method | QA accuracy | QA acc. on faulty inputs | Diagnosis acc. | Diagnostic macro-F1 | Correct action | Recovery gain (pp) | Clarifications / query |",
          "|---|---|---|---|---|---|---|---|"]
    for cfg, name in METHODS:
        p = pooled(runs, "test", cfg)
        gain = None if cfg == "base_nesy" else 100 * (p["ans_faulty"] - base["ans_faulty"])
        L.append(f"| {name} | {pct(p['ans'])} | {pct(p['ans_faulty'])} | {pct(p.get('diag'))} | {pct(p.get('f1'))} | "
                 f"{pct(p.get('act'))} | {'–' if gain is None else f'+{gain:.1f}'} | {p['asks']:.2f} |")
    L += ["", "GPT-4o (pure LLM) and IRAC score: not run yet.", ""]

    # ---- Table 2: per fault type, external F1-F4 (KB-independent faults), test ----
    L += ["## Table 2 — Diagnosis by fault type (external F1–F4 set, faults chosen without the KB, test)", "",
          "| Fault type | Heuristic | Ours | n |", "|---|---|---|---|"]
    rc, us = ext(MAIN, "rule_check"), ext(MAIN, "nesy_diag")
    for m, cat in MODES.items():
        def acc(d):
            rows = [r for r in d["per_instance"] if r["split"] == "test" and r["mode"] == m and r["status"] == "observable"]
            return sum(bool(r.get("correct_action", r["hit"])) for r in rows) / max(1, len(rows)), len(rows)
        a, n = acc(rc)
        b, _ = acc(us)
        L.append(f"| {m} — {cat} | {pct(a)} | {pct(b)} | {n} |")
    for name, d in (("Heuristic", rc), ("Ours", us)):
        t = d["results"]["test"]
        rows = [r for r in d["per_instance"] if r["split"] == "test"]
        L.append(f"| *{name}: all observable* | | | |")
        L.append(f"|  diagnosis acc. {pct(t['diagnosis_acc_observable'])}{ci(t.get('diagnosis_acc_observable_ci95'))}, "
                 f"correct action {pct(t.get('correct_action_observable'))}, QA acc. {pct(t['final_answer_acc'])}, "
                 f"false alarms on CONTROL {pct(t.get('false_alarm_rate_control'))}, clarifications/query {asks(rows):.2f} | | | |")
    L += ["", "Correct action = diagnosis correct, or the only open choice is missing-vs-omitted on the true "
          "proposition and the system asks the user about exactly it. 95% CI: bootstrap over source questions.", ""]

    # ---- Table 3: measurement tools ----
    L += ["## Table 3 — Effect of the measurement (NLI) model on Ours (external F1–F4, test)", "",
          "| Measurement | NLI macro-F1 (dev pairs) | Diagnosis acc. | Correct action | QA acc. | False alarms | Clarifications / query |",
          "|---|---|---|---|---|---|---|"]
    sel = {}
    f = ROOT / "experiments" / "nli_gpu" / "nli_dev_metrics.json"
    if f.exists():
        sel = json.loads(f.read_text(encoding="utf-8"))
    tools = [("mdeberta", "mDeBERTa-v3 (XNLI classifier)", "mdeberta"), ("qwen", "Qwen2.5-7B-Instruct (open LLM)", "qwen"),
             ("gpt4omini", "GPT-4o-mini", "gpt4omini"), ("ensemble", "mDeBERTa + Qwen2.5-7B", "ensemble"),
             ("ensemble_gpt", "**mDeBERTa + GPT-4o-mini**", "ensemble_gpt")]
    for tool, name, key in tools:
        d = ext(tool, "nesy_diag")
        if not d:
            continue
        t = d["results"]["test"]
        rows = [r for r in d["per_instance"] if r["split"] == "test"]
        mf = sel.get(key, {}).get("macro_f1") if key else None
        L.append(f"| {name} | {'–' if mf is None else f'{mf:.2f}'} | {pct(t['diagnosis_acc_observable'])} | "
                 f"{pct(t.get('correct_action_observable'))} | {pct(t['final_answer_acc'])} | "
                 f"{pct(t.get('false_alarm_rate_control'))} | {asks(rows):.2f} |")
    o = ext("mdeberta", "oracle_nli")
    if o:
        t = o["results"]["test"]
        L.append(f"| Perfect measurement (oracle, upper bound) | 1.00 | {pct(t['diagnosis_acc_observable'])} | "
                 f"{pct(t.get('correct_action_observable'))} | {pct(t['final_answer_acc'])} | {pct(t.get('false_alarm_rate_control'))} | – |")
    L += ["", "NLI macro-F1: argmax label vs. annotated question content on 1,306 labelled development pairs.", ""]

    # ---- Table 4: per domain ----
    L += ["## Table 4 — Per domain (controlled fault injection, Ours vs Heuristic)", "",
          "| Domain | Split | n | QA acc. Ours | QA acc. Heur. | Diag. Ours | Diag. Heur. | Clarif./q Ours | Clarif./q Heur. |",
          "|---|---|---|---|---|---|---|---|---|"]
    for key, name in DOMAINS:
        for split in ("dev", "test"):
            d = runs.get(f"{key}_{split}")
            if not d:
                continue
            o_, h_ = d["per_instance"]["nesy_diag"], d["per_instance"]["rule_check"]
            L.append(f"| {name} | {split} | {len(o_)} | {pct(sum(r['answer_ok'] for r in o_) / len(o_))} | "
                     f"{pct(sum(r['answer_ok'] for r in h_) / len(h_))} | {pct(sum(r['hit'] for r in o_) / len(o_))} | "
                     f"{pct(sum(r['hit'] for r in h_) / len(h_))} | {asks(o_):.2f} | {asks(h_):.2f} |")
    L += ["", "Social insurance has no test split (all 90 questions were used to develop the KB).", ""]

    # ---- Table 5: ablation ----
    L += ["## Table 5 — Ablation (controlled fault injection, test pooled)", "",
          "| Variant | QA acc. | Diagnosis acc. | Clarifications / query |", "|---|---|---|---|"]
    for cfg, name in [("nesy_diag", "Ours (full)"), ("raw_nli", "− acceptance test (raw NLI labels)"),
                      ("no_mbd", "− MBD (symptom→cause mapping)"), ("base_nesy", "− diagnosis & recovery")]:
        p = pooled(runs, "test", cfg)
        if p["n"]:
            L.append(f"| {name} | {pct(p['ans'])} | {pct(p.get('diag'))} | {p['asks']:.2f} |")
    # ---- Table 6: equal clarification budget + measurement cost ----
    bf = ROOT / "experiments" / "budget" / "budget_results.json"
    if bf.exists():
        br = json.loads(bf.read_text(encoding="utf-8"))
        L += ["## Table 6 — QA accuracy under an equal clarification budget (injected faults, test, n = 451)", "",
              "The simulated user answers at most B clarification questions per query (budgets fixed in advance).", "",
              "| Method | B = 0 | B = 1 | B = 2 | unlimited | NLI measurements / query | KB checks / query |",
              "|---|---|---|---|---|---|---|"]
        for cfg, name in [("no_mbd", "Direct symptom→cause (no MBD)"), ("rule_check", "Heuristic IF–THEN"),
                          ("nesy_diag", "**Ours: Cross-Layer MBD**")]:
            cells = [pct(br[f"{cfg}|{b}"]["qa_acc"]) for b in ("0", "1", "2", "inf")]
            L.append(f"| {name} | {' | '.join(cells)} | {br[f'{cfg}|inf']['nli_per_query']:.2f} | "
                     f"{br[f'{cfg}|inf']['kb_checks_per_query']:.2f} |")
        L.append("")
    # ---- Table 8: end-to-end QA (real GPT-4o parser) + IRAC ----
    qf, jf = ROOT / "experiments" / "e2e" / "qa_results.json", ROOT / "experiments" / "e2e" / "irac_scores.json"
    if qf.exists():
        q = json.loads(qf.read_text(encoding="utf-8"))["summary"]
        ir = json.loads(jf.read_text(encoding="utf-8"))["summary"] if jf.exists() else {}
        L += ["## Table 8 — End-to-end QA on the 300 questions (real GPT-4o parser, oracle goal, no simulated user) and IRAC", "",
              f"Parser vs gold facts: precision {pct(q['parser']['precision'])}, recall {pct(q['parser']['recall'])}. "
              "IRAC: 40 stratified questions, blind, judge GPT-4.1, rubric 100·(0.10 I + 0.35 R + 0.40 A + 0.15 C).", "",
              "| Method | QA test (n=106) | QA dev (n=194) | QA all (n=300) | yes / no / insufficient (all) | IRAC | I | R | A | C |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for m, name in [("gpt4o", "GPT-4o (pure LLM)"), ("symbolic", "Symbolic QA"), ("heuristic", "Heuristic IF–THEN"),
                        ("ours", "**Ours: Cross-Layer MBD**")]:
            g = q["by_gold_label_all"]
            i = ir.get(m, {})
            L.append(f"| {name} | {pct(q['test'][m])} | {pct(q['dev'][m])} | {pct(q['all'][m])} | "
                     f"{pct(g['true'][m])} / {pct(g['false'][m])} / {pct(g['insufficient'][m])} | "
                     f"{i.get('IRAC_0_100', '–')} | {i.get('I', '–')} | {i.get('R', '–')} | {i.get('A', '–')} | {i.get('C', '–')} |")
        L += ["", "Test QA by domain (social insurance: dev): " + "; ".join(
            f"{d}: " + ", ".join(f"{m} {pct(v[m])}" for m in ("gpt4o", "heuristic", "ours")) + f" (n={v['n']})"
            for d, v in q["by_domain_test_or_all"].items()), ""]

    # ---- Table 7: two simultaneous faults ----
    mf = ROOT / "experiments" / "multi_fault" / "results.json"
    if mf.exists():
        ms = json.loads(mf.read_text(encoding="utf-8"))["summary"]
        L += ["## Table 7 — Two simultaneous faults on different propositions (test; dev in parentheses)", "",
              "| Method | Both faults found | ≥ 1 found | QA acc. | Clarifications / query | n |", "|---|---|---|---|---|---|"]
        for cfg, name in [("no_mbd", "Direct symptom→cause (no MBD)"), ("rule_check", "Heuristic IF–THEN"),
                          ("nesy_diag", "**Ours: Cross-Layer MBD**")]:
            t, d = ms[f"test|{cfg}"], ms[f"dev|{cfg}"]
            L.append(f"| {name} | {pct(t['both_found'])} ({pct(d['both_found'])}) | {pct(t['any_found'])} "
                     f"({pct(d['any_found'])}) | {pct(t['answer_ok'])} ({pct(d['answer_ok'])}) | "
                     f"{t['asks_per_query']:.2f} ({d['asks_per_query']:.2f}) | {t['n']} ({d['n']}) |")
        L.append("")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
