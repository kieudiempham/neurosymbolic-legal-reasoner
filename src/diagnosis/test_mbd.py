"""Behavioural tests of the MBD layer (run: PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.test_mbd).

Each test builds observations by hand and asks SWI-Prolog for the set-minimal diagnoses, so it checks the
diagnostic model itself, independently of NLI quality.
"""

from __future__ import annotations

import sys

from .mbd_engine import Observations, minimal_diagnoses


def show(ds) -> list[list[str]]:
    return sorted(sorted(str(f) for f in d) for d in ds)


def check(name: str, got, expected) -> bool:
    ok = got == expected
    print(f"[{'PASS' if ok else 'FAIL'}] {name}\n        got      {got}\n        expected {expected}")
    return ok


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    results = []

    # 1. all-normal is inconsistent for required(p) & not parsed; two set-minimal diagnoses before any NLI
    o = Observations(required={"b"})
    results.append(check("unknown(b) before NLI -> {miss(b)} and {omit(b)}", show(minimal_diagnoses(o)),
                         [["MissingCaseInformation(b)"], ["ParserOmission(b)"]]))
    # 2. NLI entail eliminates miss(b)
    o.q["b"] = "entail"
    results.append(check("after q(b)=entail -> only {omit(b)}", show(minimal_diagnoses(o)), [["ParserOmission(b)"]]))
    # 3. NLI neutral eliminates omit(b)
    o.q["b"] = "neutral"
    results.append(check("after q(b)=neutral -> only {miss(b)}", show(minimal_diagnoses(o)),
                         [["MissingCaseInformation(b)"]]))
    # 4. a parsed fact on the proof with no evidence: the empty diagnosis is consistent (no false alarm)
    o = Observations(checked={"a"}, parsed={"a": True})
    results.append(check("checked(a) parsed, unmeasured -> {} (normal)", show(minimal_diagnoses(o)), [[]]))
    # 5. contradiction -> misinterpretation; neutral -> unsupported fact
    o.q["a"] = "contra"
    results.append(check("q(a)=contra -> {misinterp(a)}", show(minimal_diagnoses(o)), [["ParserMisinterpretation(a)"]]))
    o.q["a"] = "neutral"
    results.append(check("q(a)=neutral -> {unsupported(a)}", show(minimal_diagnoses(o)), [["UnsupportedParserFact(a)"]]))
    # 6. competing applicable rules: overlap vs conflict before KB verification, then resolved by it
    o = Observations(competing={("R1", "R2")})
    results.append(check("competing(R1,R2) before KB check -> {overlap} and {kbconflict}", show(minimal_diagnoses(o)),
                         [["ResolvableRuleOverlap(R1, R2)"], ["UnresolvedKBConflict(R1, R2)"]]))
    o.resolution[("R1", "R2")] = "yes"
    results.append(check("resolution=yes -> {overlap}", show(minimal_diagnoses(o)), [["ResolvableRuleOverlap(R1, R2)"]]))
    o.resolution[("R1", "R2")] = "no"
    results.append(check("resolution=no -> {kbconflict}", show(minimal_diagnoses(o)), [["UnresolvedKBConflict(R1, R2)"]]))
    # 7. two independent anomalies -> diagnoses with two faults (cross product, all set-minimal)
    o = Observations(required={"b", "c"})
    results.append(check("required(b), required(c) -> 4 two-fault diagnoses", len(minimal_diagnoses(o)), 4))

    print(f"\n{sum(results)}/{len(results)} passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
