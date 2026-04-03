"""Generate final answers (template or LLM) grounded in proofs — QA pipeline helpers."""

from __future__ import annotations

from typing import Any

from schemas.answer import FinalAnswer
from schemas.evidence import EvidenceSnippet
from schemas.proof import ProofObject


def generate_answer(
    *,
    question: str,
    conclusion: str,
    proof: ProofObject | None,
    evidence: list[EvidenceSnippet],
    goal_achieved: bool,
) -> FinalAnswer:
    if goal_achieved:
        txt = (
            f"Có. Theo các điều kiện đã kiểm tra, kết luận hình thức là: {conclusion}. "
            f"(Luật nguồn trong rulebase đã chọn, không suy diễn ngoài rule.)"
        )
        conf = 0.78
    else:
        txt = (
            f"Không đủ cơ sở để kết luận chắc chắn. "
            f"Kết quả suy luận tượng trưng: {conclusion or 'không suy ra được'}."
        )
        conf = 0.35

    ps = ""
    if proof and proof.proof_steps:
        ps = " ".join(s.description for s in proof.proof_steps[:5])

    evs = " ".join(e.text[:200] for e in evidence[:2])

    return FinalAnswer(
        answer_text=txt,
        conclusion=conclusion,
        proof_summary=ps,
        evidence_snippets=evidence,
        confidence=conf,
        verification_summary=f"goal_achieved={goal_achieved}; evidence_hits={len(evidence)}",
    )


def safe_regenerate_answer(conclusion: str) -> str:
    """One-shot safer template if verification fails."""
    return f"Theo kết luận logic đã kiểm chứng: {conclusion}."


class AnswerGenerator:
    """Legacy stub — use generate_answer() for the QA pipeline."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def generate(self, proof: Any | None, context: dict[str, Any]) -> str:
        raise NotImplementedError
