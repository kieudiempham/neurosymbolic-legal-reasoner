"""Bridge from the GPT-generated dataset (docs/dataset_handoff/schema.json) to the diagnosis pipeline.

- load_items(paths)            -> raw dataset items
- extend_kb_vocab(kb, items)   -> KB whose vocabulary also contains the dataset's declared predicates
- to_gold_cases(items, kb)     -> GoldCase objects usable by inject.build_instances / run_eval
- check_kb(kb, cases, items)   -> does the KB, run on the gold facts, reproduce the gold conclusion?

    PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.dataset check "data/dataset/*.jsonl" [--kb kb_bhxh.yaml]
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter
from pathlib import Path

from .kb import KB, DATA_DIR, GoldCase, load_kb
from .reasoner import Fact, backward_trace_required, forward_reason

OUT_DIR = Path(__file__).resolve().parents[2] / "experiments" / "dataset_check"


def load_items(paths: list[str]) -> list[dict]:
    items = []
    for p in paths:
        for f in sorted(glob.glob(p)):
            for line in Path(f).read_text(encoding="utf-8").splitlines():
                if line.strip():
                    items.append(json.loads(line))
    return items


def extend_kb_vocab(kb: KB, items: list[dict]) -> KB:
    """Add predicates declared by the dataset (new_predicates) to the KB vocabulary, without overriding."""
    vocab = dict(kb.vocab)
    for it in items:
        for np in it.get("new_predicates") or []:
            p = np.get("pred")
            if p and p not in vocab:
                vocab[p] = {k: np.get(k, "") for k in ("kind", "template_pos", "template_neg", "ask")}
                vocab[p]["origin"] = f"dataset:{it.get('id')}"
    return KB(kb.rules, kb.exception_of, kb.priority_over, vocab)


def to_gold_cases(items: list[dict], kb: KB) -> tuple[list[GoldCase], list[dict]]:
    """Convert application questions; return (cases, skipped) where skipped explains each exclusion."""
    cases, skipped = [], []
    for it in items:
        iid = it.get("id", "?")
        if it.get("question_type") != "application":
            skipped.append({"id": iid, "reason": "lookup question (not diagnosable)"})
            continue
        goal = (it.get("goal") or {}).get("pred", "")
        if goal not in kb.vocab:
            skipped.append({"id": iid, "reason": f"goal predicate not in vocabulary: {goal}"})
            continue
        facts, bad = {}, []
        for f in it.get("facts") or []:
            p = f.get("pred", "")
            if f.get("span", "") not in it.get("question", ""):
                bad.append(f"span not in question for {p}")
            elif p not in kb.vocab:
                bad.append(f"unknown predicate {p}")
            elif kb.vocab[p].get("kind") != "input":
                bad.append(f"fact uses derived predicate {p}")
            else:
                facts[p] = (bool(f["value"]), f["span"])
        if bad:
            skipped.append({"id": iid, "reason": "; ".join(bad)})
            continue
        exp = it.get("expected")
        if exp == "insufficient":
            cases.append(GoldCase(iid, it.get("domain", ""), it["question"], goal, facts, "unknown",
                                  list(it.get("missing_facts") or [])))
        else:
            cases.append(GoldCase(iid, it.get("domain", ""), it["question"], goal, facts, str(exp)))
    return cases, skipped


def _resolved_value(kb: KB, state) -> bool | None:
    """If every competing pair on the goal has an encoded resolution, the winning conclusion's polarity."""
    pairs = [(a, b) for a, b, pred in state.competing_pairs if pred == state.goal]
    losers = set()
    for a, b in pairs:
        res = kb.resolution(a, b)
        if not res:
            return None
        losers.add(res[1])
    # a rule defeated in any pair is out (nested exceptions); the surviving rules must agree
    vals = {kb.rules[r].conclusion.value for a, b in pairs for r in (a, b) if r not in losers}
    return vals.pop() if len(vals) == 1 else None


def check_case(kb: KB, case: GoldCase) -> dict:
    facts = {p: Fact(p, v, "parser", s) for p, (v, s) in case.facts.items()}
    st = forward_reason(kb, case.goal, facts)
    required = backward_trace_required(kb, st)
    got = st.status
    if got == "conflict":
        v = _resolved_value(kb, st)
        got = "abstain" if v is None else ("true" if v else "false")
    if not kb.rules_concluding(case.goal):
        verdict = "kb_has_no_rule_for_goal"
    elif case.expected == "unknown":
        missing_ok = bool(required) and set(case.natural_missing) <= set(required)
        verdict = "ok" if got == "unknown" and missing_ok else (
            "ok_partial_missing" if got == "unknown" else "kb_concludes_despite_missing")
    elif got == case.expected:
        verdict = "ok"
    elif got == "unknown":
        verdict = "kb_cannot_derive"  # a rule or a link in the chain is missing
    elif got == "abstain":
        verdict = "unresolved_conflict"  # missing exception/priority relation
    else:
        verdict = "wrong_conclusion"
    goal_rules = [r.id for r in kb.rules_concluding(case.goal)]
    return {
        "id": case.id, "goal": case.goal, "expected": case.expected, "kb_result": got, "verdict": verdict,
        "required_unresolved": required, "gold_missing": case.natural_missing,
        "applied_rules": st.applied_rules, "goal_rules_in_kb": goal_rules,
        "competing": [list(x) for x in st.competing_pairs],
    }


def check_kb(kb: KB, cases: list[GoldCase]) -> dict:
    rows = [check_case(kb, c) for c in cases]
    verdicts = Counter(r["verdict"] for r in rows)
    ok = verdicts["ok"] + verdicts["ok_partial_missing"]
    no_rule = Counter(r["goal"] for r in rows if not r["goal_rules_in_kb"])
    return {
        "cases": len(rows), "coverage_ok": ok, "coverage_rate": ok / max(1, len(rows)),
        "verdicts": dict(verdicts), "goals_without_any_rule": dict(no_rule), "rows": rows,
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check"])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--kb", default="kb_bhxh.yaml", help=f"KB yaml under {DATA_DIR}")
    args = ap.parse_args()
    items = load_items(args.paths)
    kb = extend_kb_vocab(load_kb(args.kb), items)
    cases, skipped = to_gold_cases(items, kb)
    rep = check_kb(kb, cases)
    rep["items"] = len(items)
    rep["skipped"] = skipped
    rep["skipped_by_reason"] = dict(Counter(s["reason"].split(":")[0].split(";")[0] for s in skipped))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "kb_coverage.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if k not in ("rows", "skipped")}, ensure_ascii=False, indent=1))
    for r in rep["rows"]:
        if r["verdict"] not in ("ok", "ok_partial_missing"):
            print(f"  {r['verdict']:28s} {r['id']:12s} goal={r['goal']} expected={r['expected']} kb={r['kb_result']} "
                  f"unresolved={r['required_unresolved'][:4]}")
    print("wrote", OUT_DIR / "kb_coverage.json")


if __name__ == "__main__":
    main()
