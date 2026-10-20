"""Merge per-batch registry-vocabulary rule files into one input for registry_kb.

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.kbx.merge_batches OUT.json IN1.json IN2.json ...
"""

from __future__ import annotations

import json
import sys


def main() -> None:
    out, *ins = sys.argv[1:]
    merged = {"rules": [], "exception_of": [], "extra_predicates": [], "goals_decided": []}
    seen_pred = set()
    for f in ins:
        d = json.loads(open(f, encoding="utf-8").read())
        merged["rules"] += d.get("rules") or []
        merged["exception_of"] += d.get("exception_of") or []
        for p in d.get("extra_predicates") or []:
            if p["pred"] not in seen_pred:
                seen_pred.add(p["pred"])
                merged["extra_predicates"].append(p)
        merged["goals_decided"] = sorted(set(merged["goals_decided"]) | set(d.get("goals_decided") or []))
    ids = [r["id"] for r in merged["rules"]]
    assert len(ids) == len(set(ids)), "duplicate rule ids across batches"
    open(out, "w", encoding="utf-8").write(json.dumps(merged, ensure_ascii=False, indent=1))
    print(len(merged["rules"]), "rules,", len(merged["exception_of"]), "exception pairs,",
          len(merged["extra_predicates"]), "extra predicates, goals:", merged["goals_decided"])


if __name__ == "__main__":
    main()
