"""Generate final answers: template_grounded (default) or llm_grounded — only from conclusion + proof + evidence."""

from __future__ import annotations

from typing import Any, Callable

from schemas.answer import FinalAnswer
from schemas.evidence import EvidenceSnippet
from schemas.proof import ProofObject


def _proof_lines(proof: ProofObject | None, *, max_steps: int = 6) -> list[str]:
    if not proof or not proof.proof_steps:
        return []
    lines: list[str] = []
    for s in proof.proof_steps[:max_steps]:
        d = (s.description or "").strip()
        if d:
            lines.append(d)
    return lines


def _evidence_citations(evidence: list[EvidenceSnippet], *, max_snippets: int = 3) -> list[str]:
    out: list[str] = []
    for e in evidence[:max_snippets]:
        cite = []
        if e.article_clause:
            cite.append(e.article_clause)
        elif e.article or e.clause:
            cite.append(" ".join(x for x in (e.article, e.clause) if x))
        if e.source_doc:
            cite.append(f"({e.source_doc[:120]})")
        if cite:
            out.append(" ".join(cite).strip() + (f" — {e.text[:180]}..." if e.text else ""))
        elif e.text:
            out.append(e.text[:280])
    return out


def _build_template_grounded(
    *,
    question: str,
    conclusion: str,
    proof: ProofObject | None,
    evidence: list[EvidenceSnippet],
    goal_achieved: bool,
) -> tuple[str, str, float]:
    """Returns (answer_text, proof_summary, confidence)."""
    plines = _proof_lines(proof)
    proof_summary = " ".join(plines) if plines else (proof.derived_conclusion if proof else "")

    head = (
        f"Có — phù hợp với kết luận logic đã suy ra: {conclusion}"
        if goal_achieved
        else f"Chưa đủ cơ sở để khẳng định tuyệt đối. Kết luận tượng trưng: {conclusion or 'chưa suy ra'}."
    )
    proof_block = ""
    if plines:
        proof_block = " Luồng chứng minh rút gọn: " + " → ".join(plines[:4]) + "."
    elif proof_summary:
        proof_block = f" Cơ sở suy luận: {proof_summary[:400]}"

    ev_lines = _evidence_citations(evidence)
    ev_block = ""
    if ev_lines:
        ev_block = " Căn cứ đoạn văn bản tham chiếu: " + " | ".join(ev_lines[:2])
    else:
        ev_block = " (Chưa có đoạn corpus khớp; căn cứ chủ yếu từ rulebase đã chọn trong suy luận.)"

    answer_text = head + proof_block + ev_block
    conf = 0.82 if goal_achieved else 0.38
    if not evidence:
        conf *= 0.92
    return answer_text, proof_summary, conf


def _llm_grounded_answer(
    *,
    question: str,
    conclusion: str,
    proof_summary: str,
    evidence: list[EvidenceSnippet],
    goal_achieved: bool,
    llm_generate: Callable[..., str],
) -> str:
    """Strict prompt: chỉ được dùng nội dung trong context (caller supplies bounded llm_generate)."""
    ev_text = "\n".join(f"- {e.text[:500]}" for e in evidence[:5])
    ctx = {
        "question": question[:2000],
        "conclusion": conclusion,
        "proof_summary": proof_summary[:4000],
        "evidence": ev_text[:8000],
        "goal_achieved": goal_achieved,
    }
    return llm_generate(context=ctx)


def generate_answer(
    *,
    question: str,
    conclusion: str,
    proof: ProofObject | None,
    evidence: list[EvidenceSnippet],
    goal_achieved: bool,
    mode: str = "template_grounded",
    llm_generate: Callable[..., str] | None = None,
) -> FinalAnswer:
    """
    Grounded answer: conclusion + proof steps + evidence snippets appear in ``answer_text``.

    Modes:
    - ``template_grounded``: deterministic Vietnamese template (default).
    - ``llm_grounded``: requires ``llm_generate``; must not invent rules beyond context.
    """
    if mode == "llm_grounded" and llm_generate is not None:
        plines = _proof_lines(proof)
        proof_summary = " ".join(plines) if plines else (proof.derived_conclusion if proof else "")
        txt = _llm_grounded_answer(
            question=question,
            conclusion=conclusion,
            proof_summary=proof_summary,
            evidence=evidence,
            goal_achieved=goal_achieved,
            llm_generate=llm_generate,
        )
        return FinalAnswer(
            answer_text=txt,
            conclusion=conclusion,
            proof_summary=proof_summary,
            evidence_snippets=evidence,
            confidence=0.75 if goal_achieved else 0.4,
            verification_summary=f"goal_achieved={goal_achieved};mode=llm_grounded;evidence_hits={len(evidence)}",
            generation_mode="llm_grounded",
        )

    answer_text, proof_summary, conf = _build_template_grounded(
        question=question,
        conclusion=conclusion,
        proof=proof,
        evidence=evidence,
        goal_achieved=goal_achieved,
    )
    return FinalAnswer(
        answer_text=answer_text,
        conclusion=conclusion,
        proof_summary=proof_summary,
        evidence_snippets=evidence,
        confidence=conf,
        verification_summary=f"goal_achieved={goal_achieved};mode=template_grounded;evidence_hits={len(evidence)}",
        generation_mode="template_grounded",
    )


def safe_regenerate_answer(
    conclusion: str,
    *,
    proof: ProofObject | None = None,
    evidence: list[EvidenceSnippet] | None = None,
) -> str:
    """One-shot safer template if verification rejects — vẫn grounded."""
    ev = evidence or []
    ps = " ".join(_proof_lines(proof, max_steps=3)) if proof else ""
    evs = _evidence_citations(ev, max_snippets=1)
    tail = ""
    if ps:
        tail += f" Cơ sở: {ps[:300]}"
    if evs:
        tail += f" Tham chiếu: {evs[0][:200]}"
    return f"Theo kết luận logic đã kiểm chứng: {conclusion}.{tail}"


class AnswerGenerator:
    """Legacy stub — use generate_answer() for the QA pipeline."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def generate(self, proof: Any | None, context: dict[str, Any]) -> str:
        raise NotImplementedError
