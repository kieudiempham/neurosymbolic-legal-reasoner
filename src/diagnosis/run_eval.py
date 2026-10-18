"""Run the diagnostic benchmark and write result tables.

Usage (from repo root):
    .venv_diag/Scripts/python -m diagnosis.run_eval            (with PYTHONPATH=src)
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from .controller import ALL_CATEGORIES, Diagnoser, RunConfig, category_of
from .inject import Instance, build_instances
from .kb import load_cases, load_kb
from .nli import NLIModel

OUT_DIR = Path(__file__).resolve().parents[2] / "experiments" / "diag"

CONFIGS = {
    "base_nesy": RunConfig(diagnosis=False),
    "nesy_diag": RunConfig(),
    "no_mbd": RunConfig(use_mbd=False),
    "exhaustive_evidence": RunConfig(directed=False),
}


def predicted_category(first_diag: list[str], status: str) -> str:
    if status == "ambiguous":
        return "Ambiguous"
    cats = [category_of(f) for f in first_diag]
    primary = [c for c in cats if c != "ResolvableRuleOverlap"]
    if primary:
        return primary[0]
    return cats[0] if cats else "Normal"


def gold_hit(inst: Instance, first_diag: list[str], status: str) -> bool:
    if status == "ambiguous":
        return False
    if inst.category == "Normal":
        return not first_diag
    if inst.category == "MissingCaseInformation" and inst.origin == "natural":
        return bool(first_diag) and all(category_of(f) == "MissingCaseInformation" for f in first_diag)
    if inst.gold_fault in first_diag:
        # Extra faults are tolerated only if they are true of the instance: a benign overlap, or a
        # proposition the (edited) question genuinely never states.
        def true_extra(f: str) -> bool:
            cat = category_of(f)
            if cat == "ResolvableRuleOverlap":
                return True
            prop = f[len(cat) + 1 : -1]
            return cat == "MissingCaseInformation" and prop not in inst.question_facts

        return all(f == inst.gold_fault or true_extra(f) for f in first_diag)
    return False


def nli_gold(inst: Instance, prop: str) -> str:
    if prop in inst.question_facts:
        return "entail" if inst.question_facts[prop] else "contra"
    return "neutral"


def prf(gold: list[str], pred: list[str], labels: list[str]) -> dict:
    out = {}
    for lab in labels:
        tp = sum(g == lab and p == lab for g, p in zip(gold, pred))
        fp = sum(g != lab and p == lab for g, p in zip(gold, pred))
        fn = sum(g == lab and p != lab for g, p in zip(gold, pred))
        P = tp / (tp + fp) if tp + fp else 0.0
        R = tp / (tp + fn) if tp + fn else 0.0
        F = 2 * P * R / (P + R) if P + R else 0.0
        out[lab] = {"precision": P, "recall": R, "f1": F, "support": sum(g == lab for g in gold)}
    return out


def stratified_subset(insts: list[Instance], target: int, seed: int = 42) -> list[Instance]:
    """Keep every rare/natural instance; sample injected parser/user faults evenly per category."""
    import random

    keep = [i for i in insts if i.origin == "natural" or i.category in ("UnresolvedKBConflict", "ResolvableRuleOverlap")]
    rest = [i for i in insts if i not in keep]
    cats = sorted({i.category for i in rest})
    per = max(1, (target - len(keep)) // max(1, len(cats)))
    rng = random.Random(seed)
    for c in cats:
        pool = [i for i in rest if i.category == c]
        keep += rng.sample(pool, min(per, len(pool)))
    order = {i.iid: k for k, i in enumerate(insts)}
    return sorted(keep, key=lambda i: order[i.iid])


def run(configs: list[str], subset: int = 0) -> dict:
    kb = load_kb()
    cases = load_cases(kb=kb)
    insts = build_instances(kb, cases)
    if subset:
        insts = stratified_subset(insts, subset)
    nli = NLIModel()
    print(f"{len(kb.rules)} rules, {len(cases)} gold cases, {len(insts)} instances")
    print("instances by category:", dict(Counter(i.category for i in insts)))

    results: dict[str, dict] = {}
    per_instance: dict[str, list[dict]] = {}
    for name in configs:
        cfg = CONFIGS[name]
        rows = []
        t0 = time.time()
        for n_done, inst in enumerate(insts, 1):
            if n_done % 25 == 0:
                print(f"  [{name}] {n_done}/{len(insts)} ({time.time() - t0:.0f}s)", flush=True)
            kbv = kb.without_relations(inst.kb_variant) if inst.kb_variant else kb
            dg = Diagnoser(kbv, nli, cfg)
            r = dg.run(inst.question, inst.goal, inst.parsed, lambda c, i=inst: i.user_answers.get(c))
            pred_cat = predicted_category(r.first_diagnosis, r.first_status) if cfg.diagnosis else "-"
            rows.append({
                "iid": inst.iid, "case": inst.case_id, "origin": inst.origin, "gold_category": inst.category,
                "gold_fault": inst.gold_fault, "pred_category": pred_cat, "first_diagnosis": r.first_diagnosis,
                "first_status": r.first_status, "candidates_first": r.candidates_first,
                "hit": gold_hit(inst, r.first_diagnosis, r.first_status) if cfg.diagnosis else None,
                "answer": r.answer, "expected": inst.expected_answer, "answer_ok": r.answer == inst.expected_answer,
                "nli_calls": r.nli_calls, "kb_checks": r.kb_checks, "rounds": r.rounds, "recovery": r.recovery,
                "nli_log": [dict(x, gold=nli_gold(inst, x["prop"])) for x in r.nli_log],
            })
        nli.save()
        per_instance[name] = rows
        results[name] = summarize(rows, cfg.diagnosis)
        results[name]["seconds"] = round(time.time() - t0, 1)
        print(f"[{name}] done in {results[name]['seconds']}s:",
              {k: v for k, v in results[name].items() if not isinstance(v, dict)})
    return {"results": results, "per_instance": per_instance, "n_instances": len(insts),
            "by_category": dict(Counter(i.category for i in insts)),
            "by_origin": dict(Counter(f"{i.category}/{i.origin}" for i in insts)),
            "kb_stats": kb_stats(kb, cases)}


def summarize(rows: list[dict], diagnosis: bool) -> dict:
    n = len(rows)
    s = {
        "final_answer_acc": sum(r["answer_ok"] for r in rows) / n,
        "nli_calls_per_query": sum(r["nli_calls"] for r in rows) / n,
        "kb_checks_per_query": sum(r["kb_checks"] for r in rows) / n,
        "measurements_per_query": sum(r["nli_calls"] + r["kb_checks"] for r in rows) / n,
    }
    faulty = [r for r in rows if r["gold_category"] != "Normal"]
    s["final_answer_acc_faulty"] = sum(r["answer_ok"] for r in faulty) / max(1, len(faulty))
    if diagnosis:
        s["diagnosis_acc"] = sum(r["hit"] for r in rows) / n
        s["ambiguous_rate"] = sum(r["first_status"] == "ambiguous" for r in rows) / n
        rec = [r for r in faulty if r["first_status"] == "unique" and r["hit"]]
        s["recovery_success_rate"] = sum(r["answer_ok"] for r in faulty if r["hit"]) / max(1, len(faulty))
        s["recovery_success_given_correct_diag"] = sum(r["answer_ok"] for r in rec) / max(1, len(rec))
        labels = ["Normal", *ALL_CATEGORIES]
        s["per_category"] = prf([r["gold_category"] for r in rows], [r["pred_category"] for r in rows], labels)
        s["per_category_acc"] = {
            c: (sum(r["hit"] for r in rows if r["gold_category"] == c) / max(1, sum(r["gold_category"] == c for r in rows)))
            for c in labels
        }
        cm = defaultdict(Counter)
        for r in rows:
            cm[r["gold_category"]][r["pred_category"]] += 1
        s["confusion"] = {g: dict(v) for g, v in cm.items()}
        nl = [x for r in rows for x in r["nli_log"]]
        if nl:
            labs = ["entail", "neutral", "contra"]
            p = prf([x["gold"] for x in nl], [x["label"] for x in nl], labs)
            s["nli"] = {
                "n": len(nl),
                "accuracy": sum(x["gold"] == x["label"] for x in nl) / len(nl),
                "macro_f1": sum(p[l]["f1"] for l in labs) / 3,
                "per_label": p,
                "confusion": {g: dict(Counter(x["label"] for x in nl if x["gold"] == g)) for g in labs},
            }
    return s


def kb_stats(kb, cases) -> dict:
    rules = list(kb.rules.values())
    depth: dict[str, int] = {}

    def d(pred: str, stack=()) -> int:
        if pred in depth:
            return depth[pred]
        if kb.vocab[pred]["kind"] == "input" or pred in stack:
            return 0
        best = 0
        for r in kb.rules_concluding(pred):
            best = max(best, 1 + max(d(l.pred, stack + (pred,)) for l in r.premises))
        depth[pred] = best
        return best

    return {
        "predicates": len(kb.vocab),
        "input_predicates": len(kb.input_preds()),
        "derived_predicates": len(kb.vocab) - len(kb.input_preds()),
        "rules": len(rules),
        "rules_multi_premise": sum(len(r.premises) >= 2 for r in rules),
        "rules_explicit": sum(r.basis == "explicit" for r in rules),
        "rules_a_contrario": sum(r.basis == "a_contrario" for r in rules),
        "exception_of": len(kb.exception_of),
        "priority_over": len(kb.priority_over),
        "max_chain_depth": max(d(p) for p in kb.vocab),
        "source_documents": len({r.source.split(",")[0] for r in rules}),
        "gold_cases": len(cases),
        "gold_cases_real": sum(c.source != "synthetic" for c in cases),
        "gold_cases_synthetic": sum(c.source == "synthetic" for c in cases),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default=",".join(CONFIGS))
    ap.add_argument("--subset", type=int, default=0, help="stratified subset size (0 = all instances)")
    ap.add_argument("--merge", action="store_true", help="merge results_<config>.json into results.json")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.merge:
        merged = None
        for name in CONFIGS:
            f = OUT_DIR / f"results_{name}.json"
            if not f.exists():
                continue
            part = json.loads(f.read_text(encoding="utf-8"))
            if merged is None:
                merged = part
            else:
                merged["results"].update(part["results"])
                merged["per_instance"].update(part["per_instance"])
        (OUT_DIR / "results.json").write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
        print("merged ->", OUT_DIR / "results.json", list(merged["results"]))
        return
    configs = args.configs.split(",")
    out = run(configs, args.subset)
    name = configs[0] if len(configs) == 1 else "all"
    (OUT_DIR / f"results_{name}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", OUT_DIR / f"results_{name}.json")


if __name__ == "__main__":
    main()
