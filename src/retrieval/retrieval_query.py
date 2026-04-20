"""Build lexical + semantic retrieval query strings from v5 parse (Layer1 + Layer2)."""

from __future__ import annotations

from typing import Any

from retrieval.evidence_query_expansion import expand_query_terms, merge_query_variants
from schemas.question_parse import Layer1Parse, Layer2Parse


def _is_generic_stated_condition(atom: str) -> bool:
    a = str(atom or "").strip().lower()
    return a.startswith("stated_condition(")


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
    specific_atoms = [str(atom) for atom in (layer2.condition_atoms or []) if not _is_generic_stated_condition(str(atom))]
    if specific_atoms:
        parts.extend(specific_atoms)
    else:
        # Keep weak condition text as lexical hint when only generic fallback atom exists.
        parts.append(layer1.condition_text or "")
    parts.append(layer2.subject_normalized or "")
    parts.append(layer2.subject_type_guess or "")
    parts.append(layer2.query_rule_candidate or "")
    # Focus-specific cues for recall (obligation / deadline / procedure / …)
    foc = layer1.question_focus or ""
    if foc:
        parts.append(foc)
    return " ".join(p for p in parts if p).strip()


def _source_ref_tokens(source_ref: str | None) -> str:
    if not source_ref:
        return ""
    # Pull human-readable article/clause fragments if present
    s = source_ref.replace("|", " ")
    return s[:500]


def build_evidence_retrieval_query(
    *,
    question: str,
    conclusion: str,
    proof_summary: str,
    goal: dict[str, Any],
    source_ref: str | None,
    rule_id: str | None,
    modality_text: str,
    layer1: Layer1Parse | None = None,
    layer2: Layer2Parse | None = None,
    used_rule_head_predicate: str | None = None,
) -> str:
    """
    Primary grounded evidence query: conclusion + proof + law pointer + goal + parse cues.
    Not question-only; question is supplementary (short).
    """
    gp = used_rule_head_predicate or str(goal.get("predicate") or "")
    gargs = " ".join(str(x) for x in (goal.get("args") or [])[:8])
    chunks = [
        conclusion or "",
        proof_summary or "",
        _source_ref_tokens(source_ref),
        rule_id or "",
        gp,
        gargs,
        modality_text or "",
    ]
    if layer1:
        chunks.extend(
            [
                layer1.question_focus or "",
                layer1.action_text or "",
                layer1.condition_text or "",
                layer1.deadline_text or layer1.time_text or "",
                layer1.exception_text or "",
            ]
        )
    if layer2:
        chunks.append(" ".join(str(x) for x in (layer2.condition_atoms or [])[:6]))
        chunks.append(layer2.subject_type_guess or "")
    chunks.append((question or "")[:420])
    base = "\n".join(c for c in chunks if c).strip()
    return expand_query_terms(base, goal_predicate=gp or None)


def build_evidence_query_variants(
    *,
    question: str,
    conclusion: str,
    proof_summary: str,
    goal: dict[str, Any],
    source_ref: str | None,
    rule_id: str | None,
    modality_text: str,
    layer1: Layer1Parse | None = None,
    layer2: Layer2Parse | None = None,
    used_rule_head_predicate: str | None = None,
) -> dict[str, str]:
    """
    Multi-pass queries: merged primary, conclusion-centric, source-ref-centric, proof-centric.
    Lexical stage can take max BM25 across variants per chunk (recall).
    """
    gp = used_rule_head_predicate or str(goal.get("predicate") or "")
    primary = build_evidence_retrieval_query(
        question=question,
        conclusion=conclusion,
        proof_summary=proof_summary,
        goal=goal,
        source_ref=source_ref,
        rule_id=rule_id,
        modality_text=modality_text,
        layer1=layer1,
        layer2=layer2,
        used_rule_head_predicate=used_rule_head_predicate,
    )
    conclusion_q = expand_query_terms(
        "\n".join(
            c
            for c in (
                conclusion,
                gp,
                " ".join(str(x) for x in (goal.get("args") or [])[:6]),
                modality_text,
            )
            if c
        ),
        goal_predicate=gp or None,
    )
    sr = _source_ref_tokens(source_ref)
    source_ref_q = expand_query_terms(
        "\n".join(c for c in (sr, rule_id or "", conclusion[:200] if conclusion else "") if c),
        goal_predicate=gp or None,
    )
    proof_q = expand_query_terms(
        "\n".join(c for c in (proof_summary, conclusion[:300] if conclusion else "", gp) if c),
        goal_predicate=gp or None,
    )
    return {
        "primary": primary,
        "conclusion_centric": conclusion_q,
        "source_ref_centric": source_ref_q,
        "proof_centric": proof_q,
    }
