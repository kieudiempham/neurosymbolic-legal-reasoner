"""Two simultaneous faults on different propositions (design fixed before any result was seen).

    PYTHONPATH=src NLI_BACKEND=ensemble_gpt NLI_TAU=0.5 NLI_RULE=pos_only .venv_diag/Scripts/python -m diagnosis.multi_fault

Instances: from every question whose gold conclusion the KB reproduces (yes/no questions), two faults on two
different propositions, each of which is individually observable (as in inject.build_instances), in four
cross-layer combinations:
  missing + misinterp, omission + misinterp, missing + unsupported, misinterp + unsupported
(at most one instance per combination and question; the first admissible pair in name order).
Metrics: both faults found (acted on in any recovery round, or asked about by a clarification for
missing/omission), at least one found, first diagnosis exactly the two faults (benign overlaps ignored),
QA accuracy after recovery, clarification requests per query. Writes experiments/multi_fault/results.json.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from .dataset import check_case, extend_kb_vocab, load_items, to_gold_cases
from .inject import Instance, _delete_span, _parse, _reachable_inputs
from .kb import load_kb
from .nli import NLIModel
from .reasoner import Fact, backward_trace_required, forward_reason, proof_support
from .run_eval import CONFIGS, run_instance

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "multi_fault"
SETS = {"dev": {"bhxh": ("bhxh_v1/bhxh_90.jsonl", "kb_bhxh_v1.yaml"), "dn": ("dn_v1/dn_dev.jsonl", "kb_dn_v2.yaml"),
                "thue": ("thue_v1/thue_dev.jsonl", "kb_thue_v2.yaml"), "ld": ("ld_v1/ld_dev.jsonl", "kb_ld_v2.yaml"),
                "ln": ("ln_v1/ln_dev.jsonl", "kb_ln_v2.yaml")},
        "test": {"dn": ("dn_v1/dn_test.jsonl", "kb_dn_v2.yaml"), "thue": ("thue_v1/thue_test.jsonl", "kb_thue_v2.yaml"),
                 "ld": ("ld_v1/ld_test.jsonl", "kb_ld_v2.yaml"), "ln": ("ln_v1/ln_test.jsonl", "kb_ln_v2.yaml")}}
COMBOS = [("missing", "misinterp"), ("omission", "misinterp"), ("missing", "unsupported"), ("misinterp", "unsupported")]
NAME = {"missing": "MissingCaseInformation", "omission": "ParserOmission", "misinterp": "ParserMisinterpretation",
        "unsupported": "UnsupportedParserFact"}


def single_candidates(kb, case) -> dict[str, list]:
    """Individually observable single faults of a determinate case: kind -> [(prop, value or None)]."""
    base = _parse(case.facts)
    st0 = forward_reason(kb, case.goal, base)
    out = {k: [] for k in NAME}
    for c, (val, _span) in sorted(case.facts.items()):
        dropped = {p: f for p, f in base.items() if p != c}
        if c in backward_trace_required(kb, forward_reason(kb, case.goal, dropped)):
            out["missing"].append((c, None))
            out["omission"].append((c, None))
        flipped = dict(base)
        flipped[c] = Fact(c, not val, "parser", "")
        st = forward_reason(kb, case.goal, flipped)
        if c in proof_support(kb, st) and st.status != st0.status:
            out["misinterp"].append((c, None))
    for x in sorted(_reachable_inputs(kb, case.goal)):
        if x in case.facts:
            continue
        for v in (True, False):
            added = dict(base)
            added[x] = Fact(x, v, "parser", "")
            st = forward_reason(kb, case.goal, added)
            if x in proof_support(kb, st) and st.status != st0.status:
                out["unsupported"].append((x, v))
                break
    return out


def build(kb, cases) -> list[tuple[Instance, list[tuple[str, str]]]]:
    out = []
    for case in cases:
        if case.expected not in ("true", "false"):
            continue
        cand = single_candidates(kb, case)
        gold_vals = {p: v for p, (v, _) in case.facts.items()}
        for k1, k2 in COMBOS:
            pair = next(((a, b) for a in cand[k1] for b in cand[k2] if a[0] != b[0]), None)
            if not pair:
                continue
            (c1, _), (c2, v2) = pair
            question, parsed, qf = case.question, _parse(case.facts), dict(gold_vals)
            for kind, c, v in ((k1, c1, None), (k2, c2, v2)):
                if kind == "missing":
                    question = _delete_span(question, case.facts[c][1])
                    parsed.pop(c, None)
                    qf.pop(c, None)
                elif kind == "omission":
                    parsed.pop(c, None)
                elif kind == "misinterp":
                    parsed[c] = Fact(c, not gold_vals[c], "parser", case.facts[c][1])
                else:
                    parsed[c] = Fact(c, v, "parser", "")
            gold = [(k1, c1), (k2, c2)]
            iid = f"{case.id}#{k1}:{c1}+{k2}:{c2}"
            inst = Instance(iid, case.id, "MultiFault", " + ".join(f"{NAME[k]}({c})" for k, c in gold), "injected",
                            question, case.goal, parsed, gold_vals, qf, case.expected)
            out.append((inst, gold))
    return out


def found(kind: str, c: str, row: dict) -> bool:
    acted = set(row["recovery"])
    if f"{NAME[kind]}({c})" in acted:
        return True
    return kind in ("missing", "omission") and f"Clarify({c})" in acted


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    nli = NLIModel()
    report, rows_all = {}, {}
    for split, sets in SETS.items():
        insts = []
        for dom, (ds, kbf) in sets.items():
            items = load_items([str(ROOT / "data" / "dataset" / ds)])
            kb = extend_kb_vocab(load_kb(kbf), items)
            cases, _ = to_gold_cases(items, kb)
            cases = [c for c in cases if check_case(kb, c)["verdict"] in ("ok", "ok_partial_missing")]
            insts += [(dom, kb, i, g) for i, g in build(kb, cases)]
        print(split, len(insts), "instances", dict(Counter("+".join(k for k, _ in g) for *_, g in insts)), flush=True)
        for cfg in ("nesy_diag", "rule_check", "no_mbd"):
            rows = []
            for dom, kb, inst, gold in insts:
                r = run_instance(kb, nli, CONFIGS[cfg], inst)
                f = [found(k, c, r) for k, c in gold]
                core = {d for d in r["first_diagnosis"] if not d.startswith("ResolvableRuleOverlap(")}
                rows.append({"iid": inst.iid, "domain": dom, "combo": "+".join(k for k, _ in gold),
                             "both_found": all(f), "any_found": any(f),
                             "first_exact": core == {f"{NAME[k]}({c})" for k, c in gold},
                             "answer_ok": r["answer_ok"], "answer": r["answer"], "expected": r["expected"],
                             "asks": sum(x.startswith(("Clarify", "MissingCase")) for x in r["recovery"]),
                             "first_diagnosis": r["first_diagnosis"], "recovery": r["recovery"], "nli_calls": r["nli_calls"]})
            n = len(rows)
            s = {"n": n, **{k: round(sum(x[k] for x in rows) / n, 4) for k in ("both_found", "any_found", "first_exact", "answer_ok")},
                 "asks_per_query": round(sum(x["asks"] for x in rows) / n, 2),
                 "nli_per_query": round(sum(x["nli_calls"] for x in rows) / n, 2),
                 "by_combo": {c: {k: round(sum(x[k] for x in rows if x["combo"] == c) / max(1, sum(x["combo"] == c for x in rows)), 3)
                                  for k in ("both_found", "answer_ok")} | {"n": sum(x["combo"] == c for x in rows)}
                              for c in sorted({x["combo"] for x in rows})}}
            report[f"{split}|{cfg}"] = s
            rows_all[f"{split}|{cfg}"] = rows
            print(split, cfg, {k: v for k, v in s.items() if k != "by_combo"}, flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps({"summary": report, "rows": rows_all}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
