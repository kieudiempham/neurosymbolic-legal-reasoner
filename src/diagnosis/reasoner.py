"""Three-valued forward chaining over the diagnostic KB, producing a structured Reasoning State."""

from __future__ import annotations

from dataclasses import dataclass, field

from .kb import KB, Literal, Rule

SATISFIED, CONTRADICTED, UNKNOWN = "satisfied", "contradicted", "unknown"
APPLICABLE, NOT_APPLICABLE, UNDETERMINED = "applicable", "not_applicable", "undetermined"


@dataclass
class Fact:
    pred: str
    value: bool
    origin: str  # parser | user | reparse | default | derived
    span: str = ""
    rule: str = ""  # deriving rule when origin == derived


@dataclass
class ReasoningState:
    goal: str
    status: str  # true | false | unknown | conflict
    facts: dict[str, Fact]
    applied_rules: list[str]
    rule_status: dict[str, str]
    premise_status: dict[str, dict[str, str]]
    proof_dependencies: dict[str, list[str]]  # derived pred -> premise preds of its deriving rule
    competing_pairs: list[tuple[str, str, str]]  # (rule1, rule2, pred) applicable with incompatible conclusions
    blocked_rules: set[str] = field(default_factory=set)
    suspended: dict[str, str] = field(default_factory=dict)  # general rule -> partially established exception

    def parser_facts(self) -> dict[str, Fact]:
        return {p: f for p, f in self.facts.items() if f.origin in ("parser", "reparse")}


def _premise_status(lit: Literal, facts: dict[str, Fact]) -> str:
    f = facts.get(lit.pred)
    if f is None:
        return UNKNOWN
    return SATISFIED if f.value == lit.value else CONTRADICTED


def _rule_status(rule: Rule, facts: dict[str, Fact]) -> tuple[str, dict[str, str]]:
    ps = {str(p): _premise_status(p, facts) for p in rule.premises}
    if any(s == CONTRADICTED for s in ps.values()):
        return NOT_APPLICABLE, ps
    if all(s == SATISFIED for s in ps.values()):
        return APPLICABLE, ps
    return UNDETERMINED, ps


def forward_reason(
    kb: KB,
    goal: str,
    input_facts: dict[str, Fact],
    blocked_rules: set[str] | None = None,
) -> ReasoningState:
    """Fire applicable rules to a fixed point. Conflicting conclusions are not asserted and are recorded."""
    blocked = set(blocked_rules or ())
    facts: dict[str, Fact] = dict(input_facts)
    for pred, val in kb.defaults().items():
        if pred not in facts:
            facts[pred] = Fact(pred, val, "default")

    # exceptions (and priority winners) that can defeat each rule
    defeaters: dict[str, list[str]] = {}
    for a, b in sorted(kb.exception_of | kb.priority_over):
        defeaters.setdefault(b, []).append(a)

    def suspended_by(rule_id: str) -> str | None:
        """An exception applies only once established (open world); while it is partially established
        (some premise satisfied, none contradicted, some unknown) the general rule is suspended."""
        shared = {str(p) for p in kb.rules[rule_id].premises}
        for e in defeaters.get(rule_id, []):
            if e in blocked:
                continue
            st_e, ps_e = _rule_status(kb.rules[e], facts)
            # only premises specific to the exception count; those shared with the general rule are
            # satisfied whenever the general rule applies and say nothing about the exception
            if st_e == UNDETERMINED and any(v == SATISFIED for k, v in ps_e.items() if k not in shared):
                return e
        return None

    applied: list[str] = []
    derived_by: dict[str, list[tuple[str, bool]]] = {}
    conflicted: set[str] = set()
    changed = True
    while changed:
        changed = False
        for rule in kb.rules.values():
            if rule.id in blocked or rule.id in applied:
                continue
            st, _ = _rule_status(rule, facts)
            if st != APPLICABLE or suspended_by(rule.id):
                continue
            applied.append(rule.id)
            c = rule.conclusion
            derived_by.setdefault(c.pred, []).append((rule.id, c.value))
            values = {v for _, v in derived_by[c.pred]}
            if len(values) > 1:
                # incompatible conclusions: retract and leave the predicate unresolved
                conflicted.add(c.pred)
                if c.pred in facts and facts[c.pred].origin == "derived":
                    del facts[c.pred]
            elif c.pred not in facts and c.pred not in conflicted:
                facts[c.pred] = Fact(c.pred, c.value, "derived", rule=rule.id)
            changed = True

    rule_status, premise_status, suspended = {}, {}, {}
    for rule in kb.rules.values():
        st, ps = _rule_status(rule, facts)
        if st == APPLICABLE and rule.id not in applied:
            e = suspended_by(rule.id)
            if e:
                st, suspended[rule.id] = UNDETERMINED, e
        if rule.id in applied:
            st = APPLICABLE
        if rule.id in blocked:
            st = "blocked"
        rule_status[rule.id], premise_status[rule.id] = st, ps

    competing = []
    for pred in sorted(conflicted):
        pos = [r for r, v in derived_by[pred] if v]
        neg = [r for r, v in derived_by[pred] if not v]
        competing += [(a, b, pred) for a in pos for b in neg]

    deps = {
        p: [lit.pred for lit in kb.rules[f.rule].premises] for p, f in facts.items() if f.origin == "derived"
    }

    if goal in conflicted:
        status = "conflict"
    elif goal in facts:
        status = "true" if facts[goal].value else "false"
    elif any(rule_status[r.id] == UNDETERMINED for r in kb.rules_concluding(goal)):
        status = "unknown"
    else:
        status = "false"  # no applicable rule establishes the goal

    return ReasoningState(goal, status, facts, applied, rule_status, premise_status, deps, competing, blocked,
                          suspended)


def backward_trace_required(kb: KB, state: ReasoningState) -> list[str]:
    """Backward dependency tracing: unresolved input propositions blocking the goal (all relevant paths)."""
    required: list[str] = []
    seen: set[str] = set()

    def unknown_premises(rule_id: str) -> None:
        for lit in kb.rules[rule_id].premises:
            if state.premise_status[rule_id][str(lit)] != UNKNOWN:
                continue
            if kb.vocab[lit.pred]["kind"] == "input":
                if lit.pred not in required:
                    required.append(lit.pred)
            else:
                visit(lit.pred)

    def visit(pred: str) -> None:
        if pred in seen:
            return
        seen.add(pred)
        for rule in kb.rules_concluding(pred):
            if state.rule_status[rule.id] != UNDETERMINED:
                continue
            unknown_premises(rule.id)
            if rule.id in state.suspended:  # blocked only by a partially established exception
                unknown_premises(state.suspended[rule.id])

    if state.status in ("unknown",):
        visit(state.goal)
    return required


def proof_support(kb: KB, state: ReasoningState) -> list[str]:
    """Backward tracing over the proof: parser-originated facts that support the goal or block a goal rule."""
    out: list[str] = []

    def add(p: str) -> None:
        f = state.facts.get(p)
        if f is not None and f.origin in ("parser", "reparse") and p not in out:
            out.append(p)

    def down(pred: str, seen: set[str]) -> None:
        if pred in seen:
            return
        seen.add(pred)
        f = state.facts.get(pred)
        if f is None:
            return
        if f.origin == "derived":
            for p in state.proof_dependencies.get(pred, []):
                down(p, seen)
        else:
            add(pred)

    seen: set[str] = set()
    down(state.goal, seen)
    # facts in the derivation of each side of a conflict
    for r1, r2, _ in state.competing_pairs:
        for rid in (r1, r2):
            for lit in kb.rules[rid].premises:
                down(lit.pred, seen)
    # facts that contradict a premise of a rule for the goal (they decide which rules are blocked)
    frontier = [state.goal]
    visited: set[str] = set()
    while frontier:
        g = frontier.pop()
        if g in visited:
            continue
        visited.add(g)
        for rule in kb.rules_concluding(g):
            for lit in rule.premises:
                st = state.premise_status[rule.id][str(lit)]
                if st == CONTRADICTED:
                    down(lit.pred, seen)
                if kb.vocab[lit.pred]["kind"] == "derived":
                    frontier.append(lit.pred)
    return out
