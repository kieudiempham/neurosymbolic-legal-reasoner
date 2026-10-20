"""Turn rules re-expressed in a dataset's predicate registry into a loadable KB.

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.kbx.registry_kb \
        data/diag/kb_full_draft/review_kb_dn_v1/dn_rules_registry_vocab.json \
        data/diag/kb_full_draft/review_kb_dn_v1/dn_predicate_registry.json --name kb_dn_v2

Writes data/diag/<name>.yaml and <name>_vocabulary.yaml. An optional data/diag/<name>_patches.yaml
(same format as for build_kb: add_rules / remove_rules / add_exception_of) is applied; patches must
only come from development-split failures.
"""

from __future__ import annotations

import argparse
import json
import sys

import yaml

from .corpus import ROOT

DIAG = ROOT / "data" / "diag"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("rules_json")
    ap.add_argument("registry_json")
    ap.add_argument("--name", required=True)
    args = ap.parse_args()

    data = json.loads(open(args.rules_json, encoding="utf-8").read())
    registry = json.loads(open(args.registry_json, encoding="utf-8").read())
    patches_f = DIAG / f"{args.name}_patches.yaml"
    patches = (yaml.safe_load(patches_f.read_text(encoding="utf-8")) or {}) if patches_f.exists() else {}

    removed = {r["id"] for r in patches.get("remove_rules") or []}
    rules = [r for r in data["rules"] if r["id"] not in removed]
    for r in patches.get("add_rules") or []:
        rules.append(dict(r, note=r.get("reason", ""), from_rules=[], basis="patch"))

    vocab = {}
    for p in registry:
        vocab[p["pred"]] = {"kind": p.get("kind") or "input", "template_pos": p.get("template_pos", ""),
                            "template_neg": p.get("template_neg", ""), "ask": ""}
    for p in data.get("extra_predicates") or []:
        vocab.setdefault(p["pred"], {k: p.get(k, "") for k in ("kind", "template_pos", "template_neg", "ask")})
    concluded = {r["conclusion"].lstrip("~") for r in rules}
    missing = []
    for r in rules:
        for lit in [*r["premises"], r["conclusion"]]:
            p = lit.lstrip("~")
            if p not in vocab:
                missing.append(p)
                vocab[p] = {"kind": "derived" if p in concluded else "input", "template_pos": p.replace("_", " "),
                            "template_neg": "không " + p.replace("_", " "), "ask": "", "origin": "auto_placeholder"}
            elif p in concluded and vocab[p]["kind"] != "derived":
                vocab[p]["kind"] = "derived"
    for p, v in vocab.items():
        if v["kind"] == "input" and not v.get("ask"):
            v["ask"] = f"Xin cho biết: {v['template_pos']}"

    ids = {r["id"] for r in rules}
    exc = [list(x) for x in (data.get("exception_of") or []) + (patches.get("add_exception_of") or [])
           if x[0] in ids and x[1] in ids]
    # "general rule G is defeated by every rule concluding the opposite" (enumerated exemption lists)
    by_id = {r["id"]: r for r in rules}
    for g in patches.get("defeated_by_all") or []:
        if g not in by_id:
            continue
        c = by_id[g]["conclusion"]
        opposite = c[1:] if c.startswith("~") else "~" + c
        exc += [[r["id"], g] for r in rules if r["conclusion"] == opposite and [r["id"], g] not in exc]
    kb = {"rules": [{"id": r["id"], "premises": r["premises"], "conclusion": r["conclusion"], "source": r["source"],
                     "basis": r.get("basis", "llm_reexpressed")} for r in rules],
          "exception_of": exc, "priority_over": []}
    (DIAG / f"{args.name}.yaml").write_text(yaml.safe_dump(kb, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (DIAG / f"{args.name}_vocabulary.yaml").write_text(
        yaml.safe_dump({"predicates": vocab}, allow_unicode=True, sort_keys=True), encoding="utf-8")
    print(json.dumps({"rules": len(rules), "exception_of": len(exc), "predicates": len(vocab),
                      "placeholder_predicates": sorted(set(missing)),
                      "not_derivable": data.get("not_derivable") or []}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
