"""Retrieve and rank rules from curated rulebase."""

from __future__ import annotations

import logging
from typing import Any

from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord
from retrieval.rulebase_loader import RulebaseIndex, get_rulebase_index
from utils.text import lower_fold

logger = logging.getLogger(__name__)


def _token_overlap(a: str, b: str) -> float:
    ta = set(lower_fold(a).replace("_", " ").split())
    tb = set(lower_fold(b).replace("_", " ").split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, len(ta | tb))


def score_rule(
    rule: RuleRecord,
    *,
    layer1: Layer1Parse,
    layer2: Layer2Parse,
    goal: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    diag: dict[str, Any] = {}
    score = 0.0
    gf = goal.get("predicate")
    if gf == rule.head.predicate:
        score += 10.0
        diag["head_pred_match"] = True
    if layer1.question_focus != "unknown" and layer1.question_focus == rule.logic_form:
        score += 5.0
        diag["logic_form_focus_match"] = True
    ga = [str(x) for x in (goal.get("args") or [])]
    ha = [str(x) for x in rule.head.args]
    for g in ga:
        for h in ha:
            score += 2.0 * _token_overlap(g, h)
    qtext = layer1.subject_text + " " + layer1.action_text
    for atom in ha:
        score += 1.5 * _token_overlap(qtext, atom)
    blob = str(rule.head.args) + str(rule.body)
    for c in layer2.condition_atoms:
        score += 2.0 * _token_overlap(blob, c)
    diag["final_score"] = score
    return score, diag


def retrieve_rules(
    *,
    layer1: Layer1Parse,
    layer2: Layer2Parse,
    top_k: int = 8,
    index: RulebaseIndex | None = None,
) -> list[tuple[RuleRecord, float, dict[str, Any]]]:
    idx = index or get_rulebase_index()
    goal = layer2.goal
    gp = goal.get("predicate")
    pool = idx.all()
    if isinstance(gp, str) and gp and gp != "unknown":
        filtered = [r for r in pool if r.head.predicate == gp]
        if filtered:
            pool = filtered
    ranked: list[tuple[RuleRecord, float, dict[str, Any]]] = []
    for rule in pool:
        s, d = score_rule(rule, layer1=layer1, layer2=layer2, goal=goal)
        ranked.append((rule, s, d))
    ranked.sort(key=lambda x: -x[1])
    return ranked[:top_k]


class RuleRetriever:
    """Legacy stub — use retrieve_rules() for the QA pipeline."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def retrieve(self, layer2: Any, top_k: int) -> list[Any]:
        raise NotImplementedError
