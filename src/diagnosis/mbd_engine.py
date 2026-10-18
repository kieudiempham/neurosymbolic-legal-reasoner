"""Python side of the MBD layer: builds observations, enumerates candidates, asks SWI-Prolog for consistency."""

from __future__ import annotations

import itertools
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MBD_PL = Path(__file__).with_name("mbd.pl")
SWIPL = os.environ.get("SWIPL", str(ROOT / ".tools" / "swipl" / "bin" / "swipl.exe"))

FAULT_LAYER = {
    "missing": "user",
    "omission": "parser",
    "misinterp": "parser",
    "unsupported": "parser",
    "overlap": "kb",
    "kbconflict": "kb",
}
CATEGORY_NAME = {
    "missing": "MissingCaseInformation",
    "omission": "ParserOmission",
    "misinterp": "ParserMisinterpretation",
    "unsupported": "UnsupportedParserFact",
    "overlap": "ResolvableRuleOverlap",
    "kbconflict": "UnresolvedKBConflict",
}


@dataclass(frozen=True)
class Fault:
    kind: str
    args: tuple[str, ...]

    def to_prolog(self) -> str:
        return f"{self.kind}({', '.join(_atom(a) for a in self.args)})"

    def __str__(self) -> str:
        return f"{CATEGORY_NAME[self.kind]}({', '.join(self.args)})"


Diagnosis = frozenset  # frozenset[Fault]


@dataclass
class Observations:
    required: set[str] = field(default_factory=set)
    checked: set[str] = field(default_factory=set)
    parsed: dict[str, bool] = field(default_factory=dict)
    q: dict[str, str] = field(default_factory=dict)  # prop -> entail | neutral | contra
    competing: set[tuple[str, str]] = field(default_factory=set)
    resolution: dict[tuple[str, str], str] = field(default_factory=dict)  # pair -> yes | no

    def to_prolog(self) -> str:
        lines = [f"required({_atom(c)})." for c in sorted(self.required)]
        lines += [f"checked({_atom(c)})." for c in sorted(self.checked)]
        lines += [f"parsed({_atom(c)}, {'pos' if v else 'neg'})." for c, v in sorted(self.parsed.items())]
        lines += [f"q({_atom(c)}, {lab})." for c, lab in sorted(self.q.items())]
        lines += [f"competing({_atom(a)}, {_atom(b)})." for a, b in sorted(self.competing)]
        lines += [f"resolution({_atom(a)}, {_atom(b)}, {o})." for (a, b), o in sorted(self.resolution.items())]
        return "\n".join(lines)


def _atom(x: str) -> str:
    return "'" + str(x).replace("'", "\\'") + "'"


def fault_atoms(obs: Observations) -> list[Fault]:
    atoms = []
    for c in sorted(obs.required):
        atoms += [Fault("missing", (c,)), Fault("omission", (c,))]
    for c in sorted(obs.checked - obs.required):
        lab, val = obs.q.get(c), obs.parsed.get(c)
        if (lab == "entail" and val is True) or (lab == "contra" and val is False):
            continue  # evidence already confirms the parser on c; no fault mode can be minimal
        atoms += [Fault("misinterp", (c,)), Fault("unsupported", (c,))]
    for a, b in sorted(obs.competing):
        atoms += [Fault("overlap", (a, b)), Fault("kbconflict", (a, b))]
    return atoms


class PrologError(RuntimeError):
    pass


def prolog_consistent(obs: Observations, candidates: list[Diagnosis]) -> list[bool]:
    """One SWI-Prolog call checks every candidate against the model and current observations."""
    if not Path(SWIPL).exists():
        raise PrologError(f"SWI-Prolog not found at {SWIPL} (set SWIPL env var)")
    cand_terms = ["[" + ", ".join(f.to_prolog() for f in sorted(c, key=str)) + "]" for c in candidates]
    program = "\n".join(
        [
            f":- consult({_atom(MBD_PL.as_posix())}).",
            obs.to_prolog(),
            "cands([" + ",\n  ".join(cand_terms) + "]).",
            "main :- cands(Cs), forall(member(C, Cs), (consistent(C) -> writeln(1) ; writeln(0))).",
        ]
    )
    with tempfile.NamedTemporaryFile("w", suffix=".pl", delete=False, encoding="utf-8") as fh:
        fh.write(program)
        path = fh.name
    try:
        proc = subprocess.run(
            [SWIPL, "-q", "-f", "none", "-g", "main", "-t", "halt", path],
            capture_output=True,
            text=True,
            timeout=60,
        )
    finally:
        os.unlink(path)
    out = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip() in ("0", "1")]
    if proc.returncode != 0 or len(out) != len(candidates):
        raise PrologError(f"swipl failed (rc={proc.returncode}): {proc.stderr[-800:]}")
    return [x == "1" for x in out]


def minimal_diagnoses(obs: Observations, max_size: int = 3) -> list[Diagnosis]:
    """Set-minimal consistent diagnoses (Reiter-style), searched by increasing cardinality.

    The whole search runs in one SWI-Prolog call (mbd.pl: minimal_diagnoses/3)."""
    atoms = fault_atoms(obs)
    by_term = {_norm(f.to_prolog()): f for f in atoms}
    program = "\n".join(
        [
            f":- consult({_atom(MBD_PL.as_posix())}).",
            obs.to_prolog(),
            "atoms([" + ", ".join(f.to_prolog() for f in atoms) + "]).",
            f"main :- atoms(A), minimal_diagnoses(A, {min(max_size, len(atoms))}, Ds),"
            " forall(member(D, Ds), (write_canonical(D), nl)).",
        ]
    )
    lines = _run_swipl(program)
    out = []
    for ln in lines:
        inner = ln.strip()[1:-1]
        parts = _split_terms(inner) if inner else []
        out.append(frozenset(by_term[_norm(p)] for p in parts))
    return out


def _norm(term: str) -> str:
    return term.replace(" ", "").replace("'", "")


def _split_terms(s: str) -> list[str]:
    parts, depth, cur, quoted = [], 0, "", False
    for ch in s:
        if ch == "'":
            quoted = not quoted
        if not quoted and ch == "(":
            depth += 1
        if not quoted and ch == ")":
            depth -= 1
        if ch == "," and depth == 0 and not quoted:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur:
        parts.append(cur)
    return parts


def _run_swipl(program: str) -> list[str]:
    if not Path(SWIPL).exists():
        raise PrologError(f"SWI-Prolog not found at {SWIPL} (set SWIPL env var)")
    with tempfile.NamedTemporaryFile("w", suffix=".pl", delete=False, encoding="utf-8") as fh:
        fh.write(program)
        path = fh.name
    try:
        proc = subprocess.run(
            [SWIPL, "-q", "-f", "none", "-g", "main", "-t", "halt", path],
            capture_output=True, text=True, timeout=120,
        )
    finally:
        os.unlink(path)
    if proc.returncode != 0:
        raise PrologError(f"swipl failed (rc={proc.returncode}): {proc.stderr[-800:]}")
    return [ln for ln in proc.stdout.splitlines() if ln.startswith("[")]


def _one_mode_per_component(faults: tuple[Fault, ...]) -> bool:
    seen = set()
    for f in faults:
        key = (FAULT_LAYER[f.kind], f.args)
        if key in seen:
            return False
        seen.add(key)
    return True
