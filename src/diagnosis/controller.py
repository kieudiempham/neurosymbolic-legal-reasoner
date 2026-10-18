"""Diagnostic controller: trigger -> observations -> MBD -> directed measurements -> recovery -> re-reasoning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .kb import KB
from .mbd_engine import CATEGORY_NAME, Diagnosis, Fault, Observations, minimal_diagnoses
from .nli import NLIModel, verbalize
from .reasoner import Fact, ReasoningState, backward_trace_required, forward_reason, proof_support

SimUser = Callable[[str], "bool | None"]  # proposition -> answer (None = user cannot answer)


@dataclass
class RunConfig:
    diagnosis: bool = True  # False = Base NeSy
    use_mbd: bool = True  # False = direct symptom-to-cause attribution
    directed: bool = True  # False = collect all evidence up front (exhaustive)
    max_rounds: int = 3


@dataclass
class QueryResult:
    answer: str  # true | false | insufficient | abstain | clarification_requested
    first_diagnosis: list[str]  # faults of the first diagnostic round (empty = normal)
    first_status: str  # unique | ambiguous | none | skipped
    candidates_first: int
    nli_calls: int = 0
    kb_checks: int = 0
    traces: int = 0
    rounds: int = 0
    recovery: list[str] = field(default_factory=list)
    nli_log: list[dict] = field(default_factory=list)
    clarifications: list[str] = field(default_factory=list)
    final_status: str = ""
    final_state: "ReasoningState | None" = None


def _observations(kb: KB, state: ReasoningState) -> Observations:
    obs = Observations()
    obs.required = set(backward_trace_required(kb, state))
    obs.checked = set(proof_support(kb, state))
    pf = state.parser_facts()
    for c in obs.required | obs.checked:
        if c in pf:
            obs.parsed[c] = pf[c].value
    obs.competing = {(a, b) for a, b, _ in state.competing_pairs}
    return obs


def _kb_verify(kb: KB, state: ReasoningState, pair: tuple[str, str]) -> str:
    a, b = pair
    both = state.rule_status.get(a) == "applicable" and state.rule_status.get(b) == "applicable"
    ca, cb = kb.rules[a].conclusion, kb.rules[b].conclusion
    incompatible = ca.pred == cb.pred and ca.value != cb.value
    if not (both and incompatible):
        return "no_conflict"
    return "yes" if kb.resolution(a, b) else "no"


def _faults_on(d: Diagnosis, key) -> frozenset:
    return frozenset(f for f in d if f.args == key)


def _pick_measurement(obs: Observations, diags: list[Diagnosis]):
    """Deterministic, diagnosis-directed: the first unmeasured item on which the diagnoses disagree."""
    for pair in sorted(obs.competing):
        if pair not in obs.resolution and len({_faults_on(d, pair) for d in diags}) > 1:
            return ("kb", pair)
    for c in sorted(obs.required) + sorted(obs.checked - obs.required):
        if c not in obs.q and len({_faults_on(d, (c,)) for d in diags}) > 1:
            return ("nli", c)
    return None


class Diagnoser:
    def __init__(self, kb: KB, nli: NLIModel, cfg: RunConfig,
                 reparse: Callable[[str, str], "bool | None"] | None = None):
        self.kb, self.nli, self.cfg = kb, nli, cfg
        self.reparse = reparse  # targeted re-parsing (question, prop) -> value; None = use NLI label

    def _nli(self, res: QueryResult, question: str, c: str, obs: Observations) -> None:
        # A measurement already performed on the same input is reused, not repeated.
        if c not in self._measured:
            label, scores = self.nli.predict(question, verbalize(self.kb.vocab, c))
            self._measured[c] = label
            res.nli_calls += 1
            res.nli_log.append({"prop": c, "label": label, "scores": scores})
        obs.q[c] = self._measured[c]

    def diagnose(self, question: str, state: ReasoningState, res: QueryResult) -> tuple[list[Diagnosis], Observations]:
        obs = _observations(self.kb, state)
        res.traces += 1
        if not (obs.required or obs.checked or obs.competing):
            return [frozenset()], obs

        if not self.cfg.use_mbd:
            # Ablation: map each symptom directly to its most common cause, no further evidence.
            d = {Fault("missing", (c,)) for c in obs.required}
            d |= {Fault("kbconflict", p) for p in obs.competing}
            return [frozenset(d)], obs

        if not self.cfg.directed:
            # Ablation: collect every available measurement before diagnosing.
            for pair in sorted(obs.competing):
                obs.resolution[pair] = _kb_verify(self.kb, state, pair)
                res.kb_checks += 1
            for c in sorted(obs.required | obs.checked):
                self._nli(res, question, c, obs)
        else:
            # Trigger (iii): the proof is selected for verification -> verify the parser facts it uses.
            for c in sorted(obs.checked - obs.required):
                self._nli(res, question, c, obs)

        # Phase A: verify the facts the current proof depends on and any rule interaction.
        # Phase B (only if phase A finds nothing): explain the unresolved required propositions.
        required = obs.required
        obs.required = set()
        diags = self._mbd_loop(question, state, obs, res)
        if len(diags) == 1 and not diags[0] and required:
            obs.required = required
            diags = self._mbd_loop(question, state, obs, res)
        elif not (len(diags) == 1 and diags[0]):
            obs.required = required
        return diags, obs

    def _mbd_loop(self, question: str, state: ReasoningState, obs: Observations, res: QueryResult) -> list[Diagnosis]:
        diags = minimal_diagnoses(obs, max_size=5)
        while len(diags) > 1:
            m = _pick_measurement(obs, diags)
            if m is None:
                break
            kind, target = m
            if kind == "kb":
                obs.resolution[target] = _kb_verify(self.kb, state, target)
                res.kb_checks += 1
            else:
                self._nli(res, question, target, obs)
            diags = minimal_diagnoses(obs, max_size=5)
        return diags

    def run(self, question: str, goal: str, parsed: dict[str, Fact], sim_user: SimUser) -> QueryResult:
        facts = dict(parsed)
        blocked: set[str] = set()
        self._measured: dict[str, str] = {}
        res = QueryResult(answer="", first_diagnosis=[], first_status="skipped", candidates_first=0)
        abstain = False
        for rnd in range(self.cfg.max_rounds):
            res.rounds = rnd + 1
            state = forward_reason(self.kb, goal, facts, blocked)
            if not self.cfg.diagnosis:
                break
            diags, obs = self.diagnose(question, state, res)
            if rnd == 0:
                res.candidates_first = len(diags)
                res.first_status = "unique" if len(diags) == 1 else ("ambiguous" if diags else "none")
                if len(diags) == 1:
                    res.first_diagnosis = sorted(str(f) for f in diags[0])
                else:
                    res.first_diagnosis = sorted({str(f) for d in diags for f in d})
            if len(diags) != 1 or not diags[0]:
                break
            changed = False
            # Repair the input layers (user, parser) first and re-reason; KB-layer faults are acted on only
            # when no input fault remains, because an input fault can itself create the rule interaction.
            faults = sorted(diags[0], key=str)
            input_faults = [f for f in faults if f.kind not in ("overlap", "kbconflict")]
            for f in (input_faults or faults):
                res.recovery.append(str(f))
                c = f.args[0]
                if f.kind == "missing":
                    ans = sim_user(c)
                    res.clarifications.append(c)
                    if ans is not None:
                        facts[c] = Fact(c, ans, "user")
                        changed = True
                elif f.kind in ("omission", "misinterp"):
                    val = self.reparse(question, c) if self.reparse else None
                    if val is None and obs.q.get(c) in ("entail", "contra"):
                        val = obs.q[c] == "entail"
                    if val is not None:
                        facts[c] = Fact(c, val, "reparse")
                        changed = True
                    elif f.kind == "misinterp":
                        facts.pop(c, None)  # the suspect fact is withdrawn when no replacement is found
                        changed = True
                elif f.kind == "unsupported":
                    facts.pop(c, None)
                    changed = True
                elif f.kind == "overlap":
                    win_lose = self.kb.resolution(*f.args)
                    if win_lose:
                        blocked.add(win_lose[1])
                        changed = True
                elif f.kind == "kbconflict":
                    abstain = True
            if abstain or not changed:
                break
        state = forward_reason(self.kb, goal, facts, blocked)
        res.final_status = state.status
        res.final_state = state
        if abstain or state.status == "conflict":
            res.answer = "abstain"
        elif state.status in ("true", "false"):
            res.answer = state.status
        elif res.clarifications and self.cfg.diagnosis:
            res.answer = "clarification_requested"
        else:
            res.answer = "insufficient"
        return res


def category_of(fault_str: str) -> str:
    return fault_str.split("(", 1)[0]


ALL_CATEGORIES = list(CATEGORY_NAME.values())
