"""Calibrate the NLI acceptance test (threshold tau, template rule) on the DEVELOPMENT split only.

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.calibrate_nli

Grid: tau x rule, run with the full system (nesy_diag) on the dev instances of the external F1-F4 set.
Selection criterion, fixed before looking at any result:
    dev score = mean(diagnosis accuracy on observable faults, 1 - false-alarm rate on CONTROL)
ties -> the higher (more conservative) tau, then pos_neg. Test instances are never run here.
The chosen values are written to experiments/diag_external/calibration.json; run the benchmark with
NLI_TAU / NLI_RULE set to them.
"""

from __future__ import annotations

import json
import sys

from . import nli as nli_mod
from .external_diag import OUT_DIR, build, load_domains, score
from .run_eval import CONFIGS, run_instance

TAUS = [0.40, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80]
RULES = ["pos_only"]  # the LLM measurement is scored on the positive template only


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    kbs, items, split = load_domains()
    insts, meta = build(kbs, items, split)
    dev = [i for i in insts if meta[i.iid]["split"] == "dev"]
    model = nli_mod.NLIModel()
    grid = []
    for rule in RULES:
        for tau in TAUS:
            nli_mod.ACCEPT_THRESHOLD, nli_mod.ACCEPT_RULE = tau, rule
            rows = [dict(run_instance(kbs[meta[i.iid]["domain"]], model, CONFIGS["nesy_diag"], i), **meta[i.iid])
                    for i in dev]
            b = score(rows, meta, True)["all"]
            s = (b["diagnosis_acc_observable"] + 1 - b["false_alarm_rate_control"]) / 2
            grid.append({"tau": tau, "rule": rule, "dev_score": round(s, 4),
                         "diag_acc_observable": round(b["diagnosis_acc_observable"], 4),
                         "false_alarm_control": round(b["false_alarm_rate_control"], 4),
                         "final_answer_acc": round(b["final_answer_acc"], 4), "n_dev": len(dev)})
            print(grid[-1], flush=True)
    best = max(grid, key=lambda g: (g["dev_score"], g["tau"], g["rule"] == "pos_neg"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"calibration_{nli_mod.BACKEND}.json").write_text(json.dumps({"chosen": best, "grid": grid}, indent=1), encoding="utf-8")
    print("chosen:", best)


if __name__ == "__main__":
    main()
