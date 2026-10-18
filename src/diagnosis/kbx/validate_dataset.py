"""Validate a GPT-generated dataset against docs/dataset_handoff/schema.json and the predicate rules.

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.kbx.validate_dataset path/to/*.jsonl

Writes <first input dir>/validation_report.json and new_predicates.yaml (the vocabulary the dataset declares).
"""

from __future__ import annotations

import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

from .corpus import ROOT

HANDOFF = ROOT / "docs" / "dataset_handoff"
REQUIRED = ["id", "domain", "question_type", "question", "goal", "facts", "expected", "reasoning_chain",
            "legal_basis", "answer"]
DOMAINS = {"bhxh", "doanh_nghiep", "thue", "lao_dong", "lien_nganh"}
NAME_OK = re.compile(r"^[a-z][a-z0-9_]*$")


def known_predicates() -> set[str]:
    curated = yaml.safe_load((ROOT / "data" / "diag" / "vocabulary.yaml").read_text(encoding="utf-8"))["predicates"]
    suggested = set(re.findall(r"\| `([a-z0-9_]+)` \|", (HANDOFF / "predicates.md").read_text(encoding="utf-8")))
    return set(curated) | suggested


def main(paths: list[str]) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    files = [f for p in paths for f in sorted(glob.glob(p))]
    items, errors, warnings = [], [], []
    for f in files:
        for n, line in enumerate(Path(f).read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                items.append((f"{Path(f).name}:{n}", json.loads(line)))
            except json.JSONDecodeError as e:
                errors.append(f"{Path(f).name}:{n} invalid JSON ({e.msg})")

    known = known_predicates()
    declared: dict[str, dict] = {}
    ids = Counter(it.get("id") for _, it in items)
    pred_uses = Counter()
    for loc, it in items:
        where = f"{loc} [{it.get('id')}]"
        for k in REQUIRED:
            if k not in it:
                errors.append(f"{where} missing field '{k}'")
        if it.get("domain") not in DOMAINS:
            errors.append(f"{where} bad domain {it.get('domain')!r}")
        if it.get("expected") not in ("true", "false", "insufficient"):
            errors.append(f"{where} bad expected {it.get('expected')!r}")
        if it.get("expected") == "insufficient" and not it.get("missing_facts"):
            errors.append(f"{where} expected=insufficient but no missing_facts")
        for np in it.get("new_predicates") or []:
            p = np.get("pred", "")
            if not NAME_OK.match(p):
                errors.append(f"{where} bad predicate name {p!r}")
            if p in declared and declared[p].get("template_pos") != np.get("template_pos"):
                warnings.append(f"{where} predicate {p} re-declared with a different meaning")
            declared.setdefault(p, dict(np, first_declared_in=it.get("id")))
        q = it.get("question", "")
        preds = [(it.get("goal") or {}).get("pred", "")]
        for fct in it.get("facts") or []:
            preds.append(fct.get("pred", ""))
            if fct.get("span", "") not in q:
                errors.append(f"{where} span not in question: {fct.get('span')!r}")
            if not isinstance(fct.get("value"), bool):
                errors.append(f"{where} fact {fct.get('pred')} value is not boolean")
            if str(fct.get("pred", "")).startswith("not_"):
                warnings.append(f"{where} predicate {fct.get('pred')} starts with not_ (use value=false)")
        preds += list(it.get("missing_facts") or [])
        for p in preds:
            pred_uses[p] += 1
    all_known = known | set(declared)
    undeclared = sorted(p for p in pred_uses if p and p not in all_known)
    for p in undeclared:
        errors.append(f"undeclared predicate {p!r} (used {pred_uses[p]}x)")
    for i, c in ids.items():
        if c > 1:
            errors.append(f"duplicate id {i!r} ({c}x)")

    its = [it for _, it in items]
    report = {
        "files": files, "items": len(its), "errors": len(errors), "warnings": len(warnings),
        "by_domain": dict(Counter(it.get("domain") for it in its)),
        "by_question_type": dict(Counter(it.get("question_type") for it in its)),
        "by_expected": dict(Counter(it.get("expected") for it in its)),
        "by_info_level": dict(Counter(it.get("info_level") for it in its)),
        "multi_hop": sum(bool(it.get("multi_hop")) or len(it.get("reasoning_chain") or []) >= 2 for it in its),
        "predicates_used": len(pred_uses), "predicates_from_handoff": len([p for p in pred_uses if p in known]),
        "predicates_declared_new": len(declared), "undeclared_predicates": undeclared,
        "error_list": errors[:300], "warning_list": warnings[:300],
    }
    out_dir = Path(files[0]).parent if files else Path(".")
    (out_dir / "validation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "new_predicates.yaml").write_text(yaml.safe_dump({"predicates": declared}, allow_unicode=True,
                                                                sort_keys=True), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("error_list", "warning_list")},
                     ensure_ascii=False, indent=1))
    for e in errors[:20]:
        print("ERROR", e)
    for w in warnings[:10]:
        print("WARN ", w)


if __name__ == "__main__":
    main(sys.argv[1:] or [str(HANDOFF / "examples.jsonl")])
