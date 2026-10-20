"""Move the NLI cache computation to a GPU machine (Kaggle / Colab) and back.

    # 1. here: write every (question, template) pair any benchmark run may measure, minus cached ones
    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.nli_gpu export
    # 2. on the GPU box: python nli_kaggle.py pairs.jsonl nli_scores.jsonl   (kaggle/nli_kaggle.py)
    # 3. here: merge the scores into experiments/diag/nli_cache.json
    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.nli_gpu import nli_scores.jsonl

Pairs are exhaustive over the goal's dependency closure: for every question a run can see (dataset
instances incl. edited "missing" questions, and the external F1-F4 set) and every predicate reachable
backwards from the goal, both templates. That covers measurements in later recovery rounds too, so
the benchmark never has to call the model on CPU.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .dataset import check_case
from .external_diag import DOMAINS, ROOT, build, load_domains
from .inject import build_instances
from .kb import GoldCase
from .nli import ACCEPT_RULE, BACKEND, CACHE_FILE, MODEL_NAME

OUT = ROOT / "experiments" / "nli_gpu"
SEP = "␞"


def closure(kb, goal: str) -> set[str]:
    seen, stack = set(), [goal]
    while stack:
        g = stack.pop()
        if g in seen:
            continue
        seen.add(g)
        for r in kb.rules_concluding(g):
            stack += [lit.pred for lit in r.premises]
    return seen


def collect() -> list[tuple[str, str]]:
    from .dataset import to_gold_cases

    kbs, items, split = load_domains()
    pairs: dict[tuple[str, str], None] = {}

    def add(kb, question: str, goal: str, extra: set[str]) -> None:
        for p in closure(kb, goal) | extra:
            v = kb.vocab.get(p)
            if v:
                pairs[(question, v["template_pos"])] = None
                if ACCEPT_RULE != "pos_only":
                    pairs[(question, v["template_neg"])] = None

    for dom in DOMAINS:
        kb = kbs[dom]
        its = [it for it in items.values() if it["domain"] == dom]
        cases, _ = to_gold_cases(its, kb)
        for c in cases:  # every original question (real-parser / LLM runs see all of them)
            add(kb, c.question, c.goal, set(c.facts))
        covered: list[GoldCase] = [c for c in cases if check_case(kb, c)["verdict"] in ("ok", "ok_partial_missing")]
        for inst in build_instances(kb, covered):  # injected instances, incl. edited questions
            add(kb, inst.question, inst.goal, set(inst.parsed))
    insts, meta = build(kbs, items, split)
    for inst in insts:
        add(kbs[meta[inst.iid]["domain"]], inst.question, inst.goal, set(inst.parsed))
    return list(pairs)


def dev_labelled_pairs() -> list[dict]:
    """(question, positive template, gold label) for the input propositions in the goal closure of every
    DEVELOPMENT instance of the external F1-F4 set; gold = what the source question states (annotated
    facts), neutral otherwise. Used only to choose among measurement prompts/models."""
    kbs, items, split = load_domains()
    insts, meta = build(kbs, items, split)
    out, seen = [], set()
    for i in insts:
        if meta[i.iid]["split"] != "dev":
            continue
        kb = kbs[meta[i.iid]["domain"]]
        for p in sorted(closure(kb, i.goal)):
            v = kb.vocab.get(p)
            if not v or v["kind"] != "input" or (i.question, v["template_pos"]) in seen:
                continue
            seen.add((i.question, v["template_pos"]))
            gold = ("entail" if i.question_facts[p] else "contra") if p in i.question_facts else "neutral"
            out.append({"premise": i.question, "hypothesis": v["template_pos"], "pred": p, "gold": gold})
    return out


def nli_metrics(rows: list[tuple[str, str]]) -> dict:
    labs = ["entail", "neutral", "contra"]
    f1s, per = [], {}
    for lab in labs:
        tp = sum(g == lab and p == lab for g, p in rows)
        fp = sum(g != lab and p == lab for g, p in rows)
        fn = sum(g == lab and p != lab for g, p in rows)
        pr, rc = tp / max(1, tp + fp), tp / max(1, tp + fn)
        f1s.append(2 * pr * rc / max(1e-9, pr + rc))
        per[lab] = {"recall": round(rc, 3), "precision": round(pr, 3), "n": tp + fn}
    return {"n": len(rows), "accuracy": round(sum(g == p for g, p in rows) / max(1, len(rows)), 4),
            "macro_f1": round(sum(f1s) / 3, 4), "per_label": per}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["export", "import", "dev-pairs", "eval-dev"])
    ap.add_argument("scores", nargs="?", help="nli_scores.jsonl produced on the GPU (import)")
    args = ap.parse_args()
    cache = json.loads(CACHE_FILE.read_text(encoding="utf-8")) if CACHE_FILE.exists() else {}

    if args.cmd == "dev-pairs":
        rows = dev_labelled_pairs()
        OUT.mkdir(parents=True, exist_ok=True)
        with (OUT / "pairs_qwen_dev.jsonl").open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps({"premise": r["premise"], "hypothesis": r["hypothesis"]}, ensure_ascii=False) + "\n")
        (OUT / "dev_gold.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        print(f"{len(rows)} dev pairs ->", OUT / "pairs_qwen_dev.jsonl")
        return
    if args.cmd == "eval-dev":
        gold = {(r["premise"], r["hypothesis"]): r["gold"] for r in json.loads((OUT / "dev_gold.json").read_text(encoding="utf-8"))}
        diag = CACHE_FILE.parent
        systems = {}
        for name, fn in (("mdeberta", "nli_cache.json"), ("qwen_v1", "nli_cache_qwen2.5-7b_v1.json")):
            if (diag / fn).exists():
                c = json.loads((diag / fn).read_text(encoding="utf-8"))
                systems[name] = {k: c[k[0] + SEP + k[1]] for k in gold if k[0] + SEP + k[1] in c}
        if args.scores:
            for line in Path(args.scores).read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    systems.setdefault("qwen_" + r.get("prompt", "?"), {})[(r["premise"], r["hypothesis"])] = r["scores"]
        report = {}
        for name, sc in systems.items():
            rows = [(gold[k], max(v, key=v.get)) for k, v in sc.items() if k in gold]
            report[name] = nli_metrics(rows)
            print(name, json.dumps(report[name], ensure_ascii=False))
        (OUT / "dev_prompt_selection.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
        return

    if args.cmd == "export":
        pairs = collect()
        todo = [p for p in pairs if p[0] + SEP + p[1] not in cache]
        OUT.mkdir(parents=True, exist_ok=True)
        with (OUT / f"pairs_{BACKEND}.jsonl").open("w", encoding="utf-8") as f:
            for prem, hyp in todo:
                f.write(json.dumps({"premise": prem, "hypothesis": hyp}, ensure_ascii=False) + "\n")
        (OUT / f"meta_{BACKEND}.json").write_text(json.dumps({"model": MODEL_NAME, "pairs_total": len(pairs), "pairs_todo": len(todo),
                                                   "questions": len({p for p, _ in pairs})}, indent=1), encoding="utf-8")
        print(f"{len(pairs)} pairs over {len({p for p, _ in pairs})} questions; {len(todo)} not cached -> {OUT / 'pairs.jsonl'}")
        return

    n_new = n_bad = 0
    raw = Path(args.scores).read_bytes()
    if args.scores.endswith(".gz"):
        import gzip

        raw = gzip.decompress(raw)
    elif args.scores.endswith(".zip"):
        import io
        import zipfile

        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            raw = z.read(next(n for n in z.namelist() if n.endswith(".jsonl")))
    for line in raw.decode("utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        s = r["scores"]
        if set(s) != {"entail", "neutral", "contra"} or abs(sum(s.values()) - 1) > 1e-3:
            n_bad += 1
            continue
        key = r["premise"] + SEP + r["hypothesis"]
        n_new += key not in cache
        cache[key] = s
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    print(f"merged: {n_new} new, {n_bad} malformed skipped; cache now {len(cache)} pairs")


if __name__ == "__main__":
    main()
