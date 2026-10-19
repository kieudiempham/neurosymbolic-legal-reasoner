"""Externally built diagnostic benchmark (data/dataset/diag_gpt_v1, built by GPT from the 300 QA).

Unlike inject.build_instances, faults here were chosen WITHOUT looking at the KB, so the benchmark is not
biased towards faults our KB happens to expose. Only F1-F4 and CONTROL are used: the F5 fixtures are not
mapped to real rules and F6 is a synthetic two-rule micro-KB (our KB-conflict instances are built from
real exception relations instead).

Every instance is tagged with
  - split: dev/test of its source question (dev questions were used to patch the KBs)
  - status: observable      the fault changes the reasoning outcome on our KB (the diagnosable subset)
            no_symptom      the fault leaves the outcome unchanged (redundant fact / alternative path);
                            MBD cannot see it by definition, only the final answer is scored
            source_not_covered / source_relabelled   excluded (KB or gold issue of the source question)

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.external_diag --configs rule_check,nesy_diag
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from .dataset import check_case, extend_kb_vocab, load_items, to_gold_cases
from .inject import Instance
from .kb import load_kb
from .reasoner import Fact, backward_trace_required, forward_reason, proof_support

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "dataset" / "diag_gpt_v1"
OUT_DIR = ROOT / "experiments" / "diag_external"

DOMAINS = {
    "bhxh": ("kb_bhxh_v1.yaml", ["bhxh_v1/bhxh_90.jsonl"]),
    "doanh_nghiep": ("kb_dn_v2.yaml", ["dn_v1/dn_dev.jsonl", "dn_v1/dn_test.jsonl"]),
    "thue": ("kb_thue_v2.yaml", ["thue_v1/thue_dev.jsonl", "thue_v1/thue_test.jsonl"]),
    "lao_dong": ("kb_ld_v2.yaml", ["ld_v1/ld_dev.jsonl", "ld_v1/ld_test.jsonl"]),
    "lien_nganh": ("kb_ln_v2.yaml", ["ln_v1/ln_dev.jsonl", "ln_v1/ln_test.jsonl"]),
}
MODE_CATEGORY = {"CONTROL": "Normal", "F1": "MissingCaseInformation", "F2": "ParserOmission",
                 "F3": "ParserMisinterpretation", "F4": "UnsupportedParserFact"}


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def load_domains():
    kbs, items, split = {}, {}, {}
    for dom, (kb_file, paths) in DOMAINS.items():
        full = [str(ROOT / "data" / "dataset" / p) for p in paths]
        kbs[dom] = extend_kb_vocab(load_kb(kb_file), load_items(full))
        for p in full:
            for it in load_items([p]):
                items[it["id"]] = it
                split[it["id"]] = "test" if p.endswith("_test.jsonl") else "dev"
    return kbs, items, split


def _facts(fs: list[dict], spans: dict[str, str]) -> dict[str, Fact]:
    return {f["pred"]: Fact(f["pred"], bool(f["value"]), "parser", spans.get(f["pred"], "")) for f in fs}


def build(kbs, items, split) -> tuple[list[Instance], dict[str, dict]]:
    """Return (instances, meta by iid). Excluded records are kept in meta with their status."""
    inputs = _jsonl(DATA / "diagnostic_model_inputs.jsonl")
    gold = {g["id"]: g for g in _jsonl(DATA / "diagnostic_gold_labels_DRAFT.jsonl")}
    insts, meta = [], {}
    for inp in inputs:
        g = gold[inp["id"]]
        mode = g["target_mode"]
        if mode not in MODE_CATEGORY:
            continue
        dom, sid, iid = inp["domain"], inp["source_question_id"], inp["id"]
        kb, src = kbs[dom], items[sid]
        m = {"mode": mode, "domain": dom, "source": sid, "split": split[sid]}
        meta[iid] = m
        gc, _ = to_gold_cases([src], kb)
        src_ok = bool(gc) and check_case(kb, gc[0])["verdict"] in ("ok", "ok_partial_missing")
        if (src["expected"] == "insufficient") != (g["source_answer_expected_DRAFT"] == "insufficient"):
            m["status"] = "source_relabelled"  # our reviewed label differs (label_revisions.json)
            continue
        if not src_ok:
            m["status"] = "source_not_covered"
            continue
        goal = inp["goal"]["pred"]
        spans = {f["pred"]: f["span"] for f in src["facts"]}
        gold_vals = {f["pred"]: bool(f["value"]) for f in src["facts"]}
        parsed = _facts(inp["parsed_facts"], spans)
        st = forward_reason(kb, goal, parsed)
        st0 = forward_reason(kb, goal, _facts(src["facts"], spans))
        tp = (g.get("target_proposition") or {}).get("pred")
        if mode == "CONTROL":
            visible = True
        elif mode in ("F1", "F2"):
            visible = st.status == "unknown" and tp in backward_trace_required(kb, st)
        elif mode == "F3":
            visible = st.status != st0.status and tp in proof_support(kb, st)
        else:  # F4: the hallucinated fact must carry the (wrong) conclusion
            visible = st.status in ("true", "false") and tp in proof_support(kb, st)
        m["status"] = "observable" if visible else "no_symptom"
        cat = MODE_CATEGORY[mode]
        insufficient = src["expected"] == "insufficient"
        insts.append(Instance(
            iid=iid, case_id=sid, category=cat, gold_fault=f"{cat}({tp})" if tp else "",
            origin="natural" if mode in ("F1", "CONTROL") else "injected",
            question=inp["original_question"], goal=goal, parsed=parsed,
            user_answers={} if mode == "F1" else gold_vals, question_facts=gold_vals,
            expected_answer="clarification_requested" if insufficient else src["expected"]))
    return insts, meta


def group_bootstrap(rows: list[dict], key: str, n_boot: int = 1000, seed: int = 0) -> tuple[float, float]:
    """95% interval resampling SOURCE QUESTIONS (several diagnostic cases share one source)."""
    if not rows:
        return (0.0, 0.0)
    groups = defaultdict(list)
    for r in rows:
        groups[r["case"]].append(float(r[key]))
    keys = list(groups)
    rng = random.Random(seed)
    means = []
    for _ in range(n_boot):
        vals = [v for _ in keys for v in groups[keys[rng.randrange(len(keys))]]]
        means.append(sum(vals) / len(vals))
    means.sort()
    return (means[int(0.025 * n_boot)], means[int(0.975 * n_boot) - 1])


def score(rows: list[dict], meta: dict[str, dict], diagnosis: bool) -> dict:
    if diagnosis:
        # a CONTROL case whose KB has encoded general/exception overlaps is correctly diagnosed as "only
        # resolvable overlaps" (true of the instance and benign), as in inject.build_instances
        for r in rows:
            if r["gold_category"] == "Normal" and r["first_diagnosis"] and r["first_status"] != "ambiguous":
                r["hit"] = all(f.startswith("ResolvableRuleOverlap(") for f in r["first_diagnosis"])
    def block(rs: list[dict]) -> dict:
        b = {"n": len(rs), "sources": len({r["case"] for r in rs})}
        if not rs:
            return b
        b["final_answer_acc"] = sum(r["answer_ok"] for r in rs) / len(rs)
        b["final_answer_acc_ci95"] = group_bootstrap(rs, "answer_ok")
        if diagnosis:
            obs = [r for r in rs if meta[r["iid"]]["status"] == "observable" and r["gold_category"] != "Normal"]
            ctl = [r for r in rs if r["gold_category"] == "Normal"]
            if obs:
                b["diagnosis_acc_observable"] = sum(r["hit"] for r in obs) / len(obs)
                b["diagnosis_acc_observable_ci95"] = group_bootstrap(obs, "hit")
                b["n_observable"] = len(obs)
            if ctl:
                b["false_alarm_rate_control"] = sum(not r["hit"] for r in ctl) / len(ctl)
            b["per_mode_diag_acc_observable"] = {
                md: round(sum(r["hit"] for r in obs if meta[r["iid"]]["mode"] == md)
                          / max(1, sum(meta[r["iid"]]["mode"] == md for r in obs)), 3)
                for md in ("F1", "F2", "F3", "F4")}
            b["confusion"] = {md: dict(Counter(r["pred_category"] for r in rs if meta[r["iid"]]["mode"] == md))
                              for md in MODE_CATEGORY}
        return b

    return {"all": block(rows), "dev": block([r for r in rows if meta[r["iid"]]["split"] == "dev"]),
            "test": block([r for r in rows if meta[r["iid"]]["split"] == "test"]),
            "no_symptom": block([r for r in rows if meta[r["iid"]]["status"] == "no_symptom"])}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    from .nli import NLIModel
    from .run_eval import CONFIGS, run_instance

    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default="rule_check,nesy_diag")
    ap.add_argument("--build-only", action="store_true", help="only report the instance set")
    args = ap.parse_args()
    kbs, items, split = load_domains()
    insts, meta = build(kbs, items, split)
    stats = {"by_mode_status": {md: dict(Counter(m["status"] for m in meta.values() if m["mode"] == md))
                                for md in MODE_CATEGORY},
             "used_by_split": dict(Counter(meta[i.iid]["split"] for i in insts)),
             "excluded": {k: m for k, m in meta.items() if m["status"] not in ("observable", "no_symptom")}}
    print(json.dumps({k: v for k, v in stats.items() if k != "excluded"}, ensure_ascii=False, indent=1))
    print("excluded:", {k: (m["source"], m["status"]) for k, m in stats["excluded"].items()})
    if args.build_only:
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    nli = NLIModel()
    for name in args.configs.split(","):
        cfg, t0, rows = CONFIGS[name], time.time(), []
        for n, inst in enumerate(insts, 1):
            if n % 25 == 0:
                print(f"  [{name}] {n}/{len(insts)} ({time.time() - t0:.0f}s)", flush=True)
            rows.append(dict(run_instance(kbs[meta[inst.iid]["domain"]], nli, cfg, inst), **meta[inst.iid]))
        nli.save()
        res = score(rows, meta, cfg.diagnosis)
        res["seconds"] = round(time.time() - t0, 1)
        out = {"config": name, "stats": stats, "results": res, "per_instance": rows}
        (OUT_DIR / f"results_{name}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{name}]", json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "confusion"}
                                       for k, v in res.items() if isinstance(v, dict)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
