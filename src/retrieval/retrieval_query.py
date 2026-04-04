"""Build lexical + semantic retrieval query strings from v5 parse (Layer1 + Layer2)."""

from __future__ import annotations

from typing import Any

from schemas.question_parse import Layer1Parse, Layer2Parse


def build_rule_retrieval_query(
    layer1: Layer1Parse,
    layer2: Layer2Parse,
    *,
    goal: dict[str, Any] | None = None,
) -> str:
    """Concatenate signals for BM25 / hybrid rule retrieval (not a user-facing string)."""
    g = goal if goal is not None else layer2.goal
    parts: list[str] = []
    parts.append(str(g.get("predicate") or ""))
    for a in g.get("args") or []:
        parts.append(str(a))
    parts.append(layer1.question_focus or "")
    parts.append(layer1.modality_text or "")
    parts.append(layer1.subject_text or "")
    parts.append(layer1.action_text or "")
    parts.append(layer1.condition_text or "")
    parts.append(layer1.time_text or "")
    parts.append(layer1.deadline_text or "")
    parts.append(layer1.exception_text or "")
    for atom in layer2.condition_atoms or []:
        parts.append(str(atom))
    parts.append(layer2.subject_normalized or "")
    parts.append(layer2.subject_type_guess or "")
    parts.append(layer2.query_rule_candidate or "")
    return " ".join(p for p in parts if p).strip()


def build_evidence_retrieval_query(
    *,
    question: str,
    conclusion: str,
    proof_summary: str,
    goal: dict[str, Any],
    source_ref: str | None,
    rule_id: str | None,
    modality_text: str,
) -> str:
    """Grounded evidence query: conclusion + proof + law pointer + goal, not question-only."""
    chunks = [
        conclusion or "",
        proof_summary or "",
        source_ref or "",
        rule_id or "",
        str(goal.get("predicate") or ""),
        " ".join(str(x) for x in (goal.get("args") or [])[:6]),
        modality_text or "",
        question[:400] if question else "",
    ]
    return "\n".join(c for c in chunks if c).strip()
