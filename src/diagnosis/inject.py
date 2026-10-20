"""Controlled fault injection: turns gold cases into labelled diagnostic instances."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .kb import KB, GoldCase
from .reasoner import Fact, backward_trace_required, forward_reason, proof_support


@dataclass
class Instance:
    iid: str
    case_id: str
    category: str  # gold diagnostic category or "Normal"
    gold_fault: str  # e.g. "ParserOmission(paid_wage)" or "" for normal
    origin: str  # natural | injected
    question: str
    goal: str
    parsed: dict[str, Fact]
    user_answers: dict[str, bool]  # simulated user knowledge (complete gold facts)
    question_facts: dict[str, bool]  # what the (possibly edited) question actually states
    expected_answer: str
    kb_variant: list[tuple[str, str]] = field(default_factory=list)  # relations removed from the KB


def _delete_span(question: str, span: str) -> str:
    q = question.replace(span, "", 1)
    q = re.sub(r"\s+([,.;?])", r"\1", q)
    q = re.sub(r"([,;])\s*([,.;?])", r"\2", q)
    q = re.sub(r"\s{2,}", " ", q).strip()
    return q


def _parse(facts: dict[str, tuple[bool, str]]) -> dict[str, Fact]:
    return {p: Fact(p, v, "parser", s) for p, (v, s) in facts.items()}


def _reachable_inputs(kb: KB, goal: str) -> list[str]:
    out, seen, stack = [], set(), [goal]
    while stack:
        g = stack.pop()
        if g in seen:
            continue
        seen.add(g)
        for r in kb.rules_concluding(g):
            for lit in r.premises:
                if kb.vocab[lit.pred]["kind"] == "input":
                    if lit.pred not in out:
                        out.append(lit.pred)
                else:
                    stack.append(lit.pred)
    return out


def build_instances(kb: KB, cases: list[GoldCase], max_unsupported: int = 2) -> list[Instance]:
    out: list[Instance] = []
    for case in cases:
        gold_vals = {p: v for p, (v, _) in case.facts.items()}
        base = _parse(case.facts)

        if case.expected == "unknown":
            out.append(
                Instance(f"{case.id}#natural", case.id, "MissingCaseInformation",
                         f"MissingCaseInformation({','.join(case.natural_missing)})", "natural",
                         case.question, case.goal, base, {}, gold_vals, "clarification_requested")
            )
            continue

        st0 = forward_reason(kb, case.goal, base)
        if case.expected == "abstain":
            pair = sorted({(a, b) for a, b, _ in st0.competing_pairs})[0]
            out.append(Instance(f"{case.id}#natural", case.id, "UnresolvedKBConflict",
                                f"UnresolvedKBConflict({', '.join(pair)})", "natural", case.question, case.goal,
                                base, gold_vals, gold_vals, "abstain"))
            continue

        if st0.competing_pairs:
            pair = sorted({(a, b) for a, b, _ in st0.competing_pairs})[0]
            out.append(Instance(f"{case.id}#natural", case.id, "ResolvableRuleOverlap",
                                f"ResolvableRuleOverlap({', '.join(pair)})", "natural", case.question, case.goal,
                                base, gold_vals, gold_vals, case.expected))
            out.append(Instance(f"{case.id}#kbconflict", case.id, "UnresolvedKBConflict",
                                f"UnresolvedKBConflict({', '.join(pair)})", "injected", case.question, case.goal,
                                base, gold_vals, gold_vals, "abstain", kb_variant=[pair]))
        else:
            out.append(Instance(f"{case.id}#normal", case.id, "Normal", "", "natural", case.question, case.goal,
                                base, gold_vals, gold_vals, case.expected))

        for c, (val, span) in case.facts.items():
            dropped = {p: f for p, f in base.items() if p != c}
            st = forward_reason(kb, case.goal, dropped)
            if c in backward_trace_required(kb, st):
                q_missing = _delete_span(case.question, span)
                qf = {p: v for p, v in gold_vals.items() if p != c}
                out.append(Instance(f"{case.id}#missing:{c}", case.id, "MissingCaseInformation",
                                    f"MissingCaseInformation({c})", "injected", q_missing, case.goal, dropped,
                                    gold_vals, qf, case.expected))
                out.append(Instance(f"{case.id}#omission:{c}", case.id, "ParserOmission",
                                    f"ParserOmission({c})", "injected", case.question, case.goal, dropped,
                                    gold_vals, gold_vals, case.expected))
            flipped = dict(base)
            flipped[c] = Fact(c, not val, "parser", span)
            st = forward_reason(kb, case.goal, flipped)
            if c in proof_support(kb, st) and st.status != st0.status:
                out.append(Instance(f"{case.id}#misinterp:{c}", case.id, "ParserMisinterpretation",
                                    f"ParserMisinterpretation({c})", "injected", case.question, case.goal, flipped,
                                    gold_vals, gold_vals, case.expected))

        n_unsup = 0
        defaults = kb.defaults()
        for x in _reachable_inputs(kb, case.goal):
            if x in case.facts or n_unsup >= max_unsupported:
                continue
            for v in (True, False):
                if defaults.get(x) == v:
                    continue  # asserting the default value changes nothing observable
                added = dict(base)
                added[x] = Fact(x, v, "parser", "")
                st = forward_reason(kb, case.goal, added)
                if x in proof_support(kb, st) and st.status != st0.status:
                    out.append(Instance(f"{case.id}#unsupported:{x}={v}", case.id, "UnsupportedParserFact",
                                        f"UnsupportedParserFact({x})", "injected", case.question, case.goal, added,
                                        gold_vals, gold_vals, case.expected))
                    n_unsup += 1
                    break
    return out
