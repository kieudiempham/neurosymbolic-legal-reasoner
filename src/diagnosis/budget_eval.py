"""Accuracy under an equal clarification budget (analysis; budgets fixed in advance: 0, 1, 2, unlimited).

    PYTHONPATH=src NLI_BACKEND=ensemble_gpt NLI_TAU=0.5 NLI_RULE=pos_only .venv_diag/Scripts/python -m diagnosis.budget_eval

Same injected-fault test instances, same measurements; the simulated user answers at most B clarification
questions per query (later questions get no answer). Writes experiments/budget/budget_results.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .dataset import check_case, extend_kb_vocab, load_items, to_gold_cases
from .inject import build_instances
from .kb import load_kb
from .nli import NLIModel
from .run_eval import CONFIGS, run_instance

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "budget"
TEST = {"dn": ("dn_v1/dn_test.jsonl", "kb_dn_v2.yaml"), "thue": ("thue_v1/thue_test.jsonl", "kb_thue_v2.yaml"),
        "ld": ("ld_v1/ld_test.jsonl", "kb_ld_v2.yaml"), "ln": ("ln_v1/ln_test.jsonl", "kb_ln_v2.yaml")}
DEV = {"bhxh": ("bhxh_v1/bhxh_90.jsonl", "kb_bhxh_v1.yaml"), "dn": ("dn_v1/dn_dev.jsonl", "kb_dn_v2.yaml"),
       "thue": ("thue_v1/thue_dev.jsonl", "kb_thue_v2.yaml"), "ld": ("ld_v1/ld_dev.jsonl", "kb_ld_v2.yaml"),
       "ln": ("ln_v1/ln_dev.jsonl", "kb_ln_v2.yaml")}
BUDGETS = [0, 1, 2, None]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    nli = NLIModel()
    split = sys.argv[sys.argv.index("--split") + 1] if "--split" in sys.argv else "test"
    sets = [("test", TEST), ("dev", DEV)] if split == "all" else [(split, TEST if split == "test" else DEV)]
    runs = []
    for sp, table in sets:
      for dom, (ds, kbf) in table.items():
        items = load_items([str(ROOT / "data" / "dataset" / ds)])
        kb = extend_kb_vocab(load_kb(kbf), items)
        cases, _ = to_gold_cases(items, kb)
        cases = [c for c in cases if check_case(kb, c)["verdict"] in ("ok", "ok_partial_missing")]
        runs += [(f"{dom}_{sp}", kb, i) for i in build_instances(kb, cases)]
    print(split, len(runs), "instances", flush=True)
    per_instance = {}
    res = {}
    for cfg in ("nesy_diag", "rule_check", "no_mbd", "raw_nli"):
        for b in BUDGETS:
            rows = [dict(run_instance(kb, nli, CONFIGS[cfg], i, budget=b), set=name) for name, kb, i in runs]
            faulty = [r for r in rows if r["gold_category"] != "Normal"]
            key = f"{cfg}|{'inf' if b is None else b}"
            res[key] = {"n": len(rows), "qa_acc": round(sum(r["answer_ok"] for r in rows) / len(rows), 4),
                        "qa_acc_faulty": round(sum(r["answer_ok"] for r in faulty) / len(faulty), 4),
                        "diag_acc": round(sum(r["hit"] for r in rows) / len(rows), 4),
                        "nli_per_query": round(sum(r["nli_calls"] for r in rows) / len(rows), 2),
                        "kb_checks_per_query": round(sum(r["kb_checks"] for r in rows) / len(rows), 2)}
            print(key, res[key], flush=True)
            per_instance[key] = [{"set": r["set"], "iid": r["iid"], "answer_ok": r["answer_ok"],
                                  "asks": sum(x.startswith(("Clarify", "MissingCase")) for x in r["recovery"])} for r in rows]
    OUT.mkdir(parents=True, exist_ok=True)
    name = "budget_results.json" if split == "test" else f"budget_results_{split}.json"
    (OUT / name).write_text(json.dumps({"split": split, "summary": res, "per_instance": per_instance} if split != "test" else res,
                                       indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
