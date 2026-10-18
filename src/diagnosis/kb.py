"""Loading the curated diagnostic KB, predicate vocabulary and gold cases."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import os

import yaml

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "diag"


@dataclass(frozen=True)
class Literal:
    pred: str
    value: bool  # True = pred must hold, False = ~pred

    @staticmethod
    def parse(text: str) -> "Literal":
        text = text.strip()
        if text.startswith("~"):
            return Literal(text[1:], False)
        return Literal(text, True)

    def __str__(self) -> str:
        return self.pred if self.value else f"~{self.pred}"


@dataclass(frozen=True)
class Rule:
    id: str
    premises: tuple[Literal, ...]
    conclusion: Literal
    source: str
    basis: str


@dataclass
class KB:
    rules: dict[str, Rule]
    exception_of: set[tuple[str, str]]  # (A, B): A is an exception of B
    priority_over: set[tuple[str, str]]  # (A, B): A has priority over B
    vocab: dict[str, dict[str, Any]]

    def rules_concluding(self, pred: str) -> list[Rule]:
        return [r for r in self.rules.values() if r.conclusion.pred == pred]

    def input_preds(self) -> set[str]:
        return {p for p, v in self.vocab.items() if v.get("kind") == "input"}

    def defaults(self) -> dict[str, bool]:
        """Closed-world defaults for statutory-exception predicates.

        Off by default: case facts are open-world (unknown != false), as in the paper. Set
        KB_EXCEPTION_DEFAULTS=1 only to reproduce the earlier curated benchmark, which assumed them."""
        if os.environ.get("KB_EXCEPTION_DEFAULTS", "0") != "1":
            return {}
        return {p: bool(v["default"]) for p, v in self.vocab.items() if "default" in v}

    def resolution(self, r1: str, r2: str) -> tuple[str, str] | None:
        """Return (winner, loser) if an encoded exception/priority relation resolves the pair."""
        for a, b in ((r1, r2), (r2, r1)):
            if (a, b) in self.exception_of or (a, b) in self.priority_over:
                return a, b
        return None

    def without_relations(self, pairs: list[tuple[str, str]]) -> "KB":
        """Copy of the KB with the relations between the given rule pairs removed (KB fault injection)."""
        drop = {frozenset(p) for p in pairs}
        keep = lambda rel: {x for x in rel if frozenset(x) not in drop}  # noqa: E731
        return KB(self.rules, keep(self.exception_of), keep(self.priority_over), self.vocab)


def load_kb(kb_file: str = "kb_bhxh.yaml", vocab_file: str = "vocabulary.yaml") -> KB:
    vocab = yaml.safe_load((DATA_DIR / vocab_file).read_text(encoding="utf-8"))["predicates"]
    raw = yaml.safe_load((DATA_DIR / kb_file).read_text(encoding="utf-8"))
    rules = {}
    for r in raw["rules"]:
        rule = Rule(
            id=r["id"],
            premises=tuple(Literal.parse(p) for p in r["premises"]),
            conclusion=Literal.parse(r["conclusion"]),
            source=r["source"],
            basis=r.get("basis", "explicit"),
        )
        for lit in (*rule.premises, rule.conclusion):
            if lit.pred not in vocab:
                raise ValueError(f"{rule.id}: predicate '{lit.pred}' not in vocabulary")
        rules[rule.id] = rule
    exc = {tuple(x) for x in raw.get("exception_of") or []}
    pri = {tuple(x) for x in raw.get("priority_over") or []}
    for a, b in exc | pri:
        if a not in rules or b not in rules:
            raise ValueError(f"relation references unknown rule: {a}, {b}")
    return KB(rules, exc, pri, vocab)


@dataclass
class GoldCase:
    id: str
    source: str
    question: str
    goal: str
    facts: dict[str, tuple[bool, str]]  # pred -> (value, span)
    expected: str  # "true" | "false" | "unknown" | "abstain"
    natural_missing: list[str] = field(default_factory=list)


def load_cases(path: str = "gold_cases.yaml", kb: KB | None = None) -> list[GoldCase]:
    raw = yaml.safe_load((DATA_DIR / path).read_text(encoding="utf-8"))["cases"]
    out = []
    for c in raw:
        facts = {}
        for f in c["facts"]:
            if f["span"] not in c["question"]:
                raise ValueError(f"{c['id']}: span '{f['span']}' not found in question")
            if kb is not None and kb.vocab.get(f["pred"], {}).get("kind") != "input":
                raise ValueError(f"{c['id']}: '{f['pred']}' is not an input predicate")
            facts[f["pred"]] = (bool(f["value"]), f["span"])
        exp = c["expected"]
        exp = {True: "true", False: "false"}.get(exp, exp)
        out.append(
            GoldCase(c["id"], c["source"], c["question"], c["goal"], facts, str(exp), c.get("natural_missing") or [])
        )
    return out
