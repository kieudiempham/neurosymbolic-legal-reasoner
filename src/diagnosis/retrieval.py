"""Candidate Rule Retrieval (the second module of the ICOCO pipeline).

Given the legal goal and the parsed case facts of a question, select from the domain KB the rules that can take
part in deriving, blocking or contradicting the goal:
  1. goal-directed closure: every rule whose head is the goal predicate (either polarity), and recursively every
     rule whose head is a derived predicate in the body of a selected rule;
  2. exception/priority partners of every selected rule (an exception can suspend or defeat it), with their own
     closure;
  3. each selected rule keeps its metadata (source document, article, clause, point; domain by KB).
The parsed facts rank the candidates (rules whose body mentions a stated fact first) for inspection and proof
display; they do not remove goal-relevant rules, since a premise the question does not mention is exactly what
the diagnostic layer must be able to trace.

Forward reasoning, backward tracing and diagnosis then run on the candidate KB only.
Set CANDIDATE_RETRIEVAL=0 to reason over the whole domain KB (the earlier configuration).
"""

from __future__ import annotations

import os

from .kb import KB

ENABLED = os.environ.get("CANDIDATE_RETRIEVAL", "1") == "1"


def candidate_rule_ids(kb: KB, goal: str) -> set[str]:
    partners: dict[str, set[str]] = {}
    for a, b in kb.exception_of | kb.priority_over:
        partners.setdefault(a, set()).add(b)
        partners.setdefault(b, set()).add(a)
    selected: set[str] = set()
    preds, seen_preds = [goal], set()
    while preds:
        p = preds.pop()
        if p in seen_preds:
            continue
        seen_preds.add(p)
        frontier = [r.id for r in kb.rules_concluding(p)]
        while frontier:
            rid = frontier.pop()
            if rid in selected:
                continue
            selected.add(rid)
            r = kb.rules[rid]
            preds.append(r.conclusion.pred)
            preds += [l.pred for l in r.premises]  # any premise some rule can derive (whatever its declared kind)
            frontier += list(partners.get(rid, ()))
    return selected


def retrieve(kb: KB, goal: str, facts: dict | None = None) -> KB:
    """Candidate KB for one question (same vocabulary, rules and relations restricted to the candidates)."""
    ids = candidate_rule_ids(kb, goal)
    stated = set(facts or ())
    order = sorted(ids, key=lambda i: (not any(l.pred in stated for l in kb.rules[i].premises), i))
    rules = {i: kb.rules[i] for i in order}
    keep = lambda rel: {(a, b) for a, b in rel if a in ids and b in ids}  # noqa: E731
    return KB(rules, keep(kb.exception_of), keep(kb.priority_over), kb.vocab)
