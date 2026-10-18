"""Fill the NLI cache once, in batches, for every (question, proposition) a benchmark run may measure.

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.precompute_nli --dataset data/dataset/bhxh_v1/bhxh_90.jsonl \
        --kb kb_bhxh_v1.yaml --subset 150

Uses the same instances as run_eval (same dataset, KB and stratified subset). Propositions covered: the
required and proof-supporting propositions of the initial reasoning state (both templates each).
Measurements needed only after a recovery round are computed on demand during the run.
"""

from __future__ import annotations

import argparse
import sys
import time

from .dataset import check_case, extend_kb_vocab, load_items, to_gold_cases
from .inject import build_instances
from .kb import load_cases, load_kb
from .nli import NLIModel
from .reasoner import backward_trace_required, forward_reason, proof_support
from .run_eval import stratified_subset


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", nargs="*")
    ap.add_argument("--kb", default="kb_bhxh.yaml")
    ap.add_argument("--subset", type=int, default=0)
    ap.add_argument("--chunk", type=int, default=64, help="pairs per save")
    args = ap.parse_args()

    kb = load_kb(args.kb)
    if args.dataset:
        items = load_items(args.dataset)
        kb = extend_kb_vocab(kb, items)
        cases, _ = to_gold_cases(items, kb)
        cases = [c for c in cases if check_case(kb, c)["verdict"] in ("ok", "ok_partial_missing")]
    else:
        cases = load_cases(kb=kb)
    insts = build_instances(kb, cases)
    if args.subset:
        insts = stratified_subset(insts, args.subset)

    pairs = []
    for inst in insts:
        kbv = kb.without_relations(inst.kb_variant) if inst.kb_variant else kb
        st = forward_reason(kbv, inst.goal, inst.parsed)
        for c in set(backward_trace_required(kbv, st)) | set(proof_support(kbv, st)):
            v = kb.vocab[c]
            pairs += [(inst.question, v["template_pos"]), (inst.question, v["template_neg"])]
    pairs = list(dict.fromkeys(pairs))
    nli = NLIModel()
    todo = [p for p in pairs if p[0] + "␞" + p[1] not in nli._cache]
    print(f"{len(insts)} instances, {len(pairs)} pairs, {len(todo)} not cached", flush=True)
    t0 = time.time()
    for i in range(0, len(todo), args.chunk):
        nli.predict_many(todo[i : i + args.chunk])
        nli.save()
        done = min(i + args.chunk, len(todo))
        rate = (time.time() - t0) / done
        print(f"  {done}/{len(todo)}  {rate:.2f}s/pair  eta {rate * (len(todo) - done) / 60:.0f} min", flush=True)
    print("done in", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
