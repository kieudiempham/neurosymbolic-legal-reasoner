"""Experiment with a real LLM semantic parser: naturally occurring parser errors instead of injected ones.

For every distinct question of the benchmark (original questions, and questions whose fact span was deleted
for the Missing Case Information setting) the LLM parser output replaces the gold parse. Reports parse
quality, the natural parser errors it produces, and final-answer accuracy of Base NeSy vs NeSy + Diagnosis.
Writes experiments/diag/results_real_parser.json.
"""

from __future__ import annotations

import json
import time
from collections import Counter

from .controller import Diagnoser, RunConfig, category_of
from .inject import build_instances
from .kb import load_cases, load_kb
from .llm_parser import LLMParser
from .nli import NLIModel
from .run_eval import OUT_DIR


def main() -> None:
    kb = load_kb()
    insts = build_instances(kb, load_cases(kb=kb))
    seen, uniq = set(), []
    for i in insts:
        key = (i.question, tuple(i.kb_variant))
        if key not in seen:
            seen.add(key)
            uniq.append(i)
    parser = LLMParser(kb)
    nli = NLIModel()
    print(f"{len(uniq)} distinct (question, KB) instances; parser model {parser.model}")

    tp = fp = fn = 0
    err_types = Counter()
    rows = []
    t0 = time.time()
    for n, inst in enumerate(uniq, 1):
        parsed = parser.parse(inst.question)
        gold = inst.question_facts
        omitted = [p for p in gold if p not in parsed]
        wrong = [p for p in gold if p in parsed and parsed[p].value != gold[p]]
        spurious = [p for p in parsed if p not in gold]
        tp += sum(1 for p in gold if p in parsed and parsed[p].value == gold[p])
        fp += len(wrong) + len(spurious)
        fn += len(omitted) + len(wrong)
        err_types.update({"omitted": len(omitted), "wrong_value": len(wrong), "spurious": len(spurious)})

        kbv = kb.without_relations(inst.kb_variant) if inst.kb_variant else kb
        user = lambda c, i=inst: i.user_answers.get(c)  # noqa: E731
        base = Diagnoser(kbv, nli, RunConfig(diagnosis=False)).run(inst.question, inst.goal, parsed, user)
        diag = Diagnoser(kbv, nli, RunConfig(), reparse=parser.reparse).run(inst.question, inst.goal, parsed, user)
        rows.append({
            "iid": inst.iid, "gold_category": inst.category, "question": inst.question,
            "parse_errors": {"omitted": omitted, "wrong_value": wrong, "spurious": spurious},
            "parse_exact": not (omitted or wrong or spurious),
            "expected": inst.expected_answer,
            "base_answer": base.answer, "base_ok": base.answer == inst.expected_answer,
            "diag_answer": diag.answer, "diag_ok": diag.answer == inst.expected_answer,
            "diagnosis": diag.first_diagnosis, "diag_status": diag.first_status, "recovery": diag.recovery,
            "measurements": diag.nli_calls + diag.kb_checks,
        })
        if n % 10 == 0:
            print(f"  {n}/{len(uniq)} ({time.time() - t0:.0f}s)", flush=True)
    nli.save()
    parser.save()

    P = tp / (tp + fp) if tp + fp else 0.0
    R = tp / (tp + fn) if tp + fn else 0.0
    n = len(rows)
    affected = [r for r in rows if not r["parse_exact"]]
    summary = {
        "parser_model": parser.model,
        "instances": n,
        "parse_fact_precision": P,
        "parse_fact_recall": R,
        "parse_fact_f1": 2 * P * R / (P + R) if P + R else 0.0,
        "parse_exact_rate": sum(r["parse_exact"] for r in rows) / n,
        "parse_error_counts": dict(err_types),
        "base_nesy_acc": sum(r["base_ok"] for r in rows) / n,
        "nesy_diag_acc": sum(r["diag_ok"] for r in rows) / n,
        "instances_with_parse_error": len(affected),
        "base_nesy_acc_on_parse_errors": sum(r["base_ok"] for r in affected) / max(1, len(affected)),
        "nesy_diag_acc_on_parse_errors": sum(r["diag_ok"] for r in affected) / max(1, len(affected)),
        "parser_faults_diagnosed": dict(Counter(category_of(f) for r in rows for f in r["diagnosis"])),
        "measurements_per_query": sum(r["measurements"] for r in rows) / n,
        "by_gold_category": {
            c: {"n": sum(r["gold_category"] == c for r in rows),
                "base_acc": sum(r["base_ok"] for r in rows if r["gold_category"] == c) / max(1, sum(r["gold_category"] == c for r in rows)),
                "diag_acc": sum(r["diag_ok"] for r in rows if r["gold_category"] == c) / max(1, sum(r["gold_category"] == c for r in rows))}
            for c in sorted({r["gold_category"] for r in rows})
        },
    }
    (OUT_DIR / "results_real_parser.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
