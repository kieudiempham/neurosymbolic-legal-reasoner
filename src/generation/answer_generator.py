"""Generate final answers: template_grounded (default) or llm_grounded — only from conclusion + proof + evidence."""

from __future__ import annotations

from typing import Any, Callable

from generation.legal_citations import (
    build_legal_citations_from_evidence,
    finalize_answer_citations,
    link_answer_text_to_citations,
)
from schemas.answer import FinalAnswer
from schemas.evidence import EvidenceBundle, EvidenceSnippet
from schemas.proof import ProofObject
from schemas.rule import RuleRecord


def _proof_lines(proof: ProofObject | None, *, max_steps: int = 6) -> list[str]:
    if not proof or not proof.proof_steps:
        return []
    lines: list[str] = []
    for s in proof.proof_steps[:max_steps]:
        d = (s.description or "").strip()
        if d:
            lines.append(d)
    return lines


def _proof_sketch(proof: ProofObject | None, *, max_chars: int = 420) -> str:
    plines = _proof_lines(proof, max_steps=5)
    if not plines:
        if not proof:
            return ""
        base = proof.conclusion or proof.derived_conclusion
        if not base and (proof.satisfied_premises or proof.missing_premises):
            sat = ", ".join(proof.satisfied_premises[:3])
            mis = ", ".join(proof.missing_premises[:2])
            base = f"satisfied=[{sat}] missing=[{mis}]"
        return (base or "")[:max_chars]
    s = " → ".join(plines[:4])
    return s if len(s) <= max_chars else s[: max_chars - 1] + "…"


def _build_template_grounded(
    *,
    question: str,
    conclusion: str,
    proof: ProofObject | None,
    evidence: list[EvidenceSnippet],
    goal_achieved: bool,
    rule: RuleRecord | None,
    missing_facts: list[str] | None = None,
) -> tuple[str, str, float, dict[str, str], list]:
    """Returns answer_text, proof_summary, confidence, sections, legal_citations list."""
    pl = _proof_lines(proof)
    proof_summary = " ".join(pl) if pl else ((proof.conclusion or proof.derived_conclusion) if proof else "")
    citations = build_legal_citations_from_evidence(evidence, rule=rule, max_citations=6)

    opening = "Kính gửi Quý khách hàng,"

    issue = f"Vấn đề pháp lý: {question.strip()[:220]}"
    if goal_achieved:
        rule_line = "Quy tắc áp dụng: hệ thống đã đối chiếu quy tắc pháp lý liên quan và xác nhận hướng suy luận phù hợp."
    else:
        rule_line = "Quy tắc áp dụng: có quy tắc liên quan nhưng còn thiếu dữ kiện hoặc căn cứ để kết luận chắc chắn."

    sketch = _proof_sketch(proof)
    analysis_parts: list[str] = []
    analysis_parts.append("Áp dụng vào tình huống: " + (sketch or "cần bổ sung thêm dữ kiện thực tế để đối chiếu điều kiện pháp lý."))
    if citations:
        refs = []
        for c in citations[:3]:
            dl = c.display_label.strip()
            if dl:
                refs.append(f"[{dl}]")
        if refs:
            analysis_parts.append(
                "Các tham chiếu văn bản (đoạn trích chi tiết có thể mở tại liên kết tương ứng): "
                + ", ".join(refs)
                + "."
            )
    else:
        analysis_parts.append(
            "(Chưa có đoạn corpus khớp; căn cứ chủ yếu từ quy tắc đã chọn trong suy luận và "
            "thông tin đã cung cấp.)"
        )

    # Build conclusion with conditional logic if missing facts
    if missing_facts and len(missing_facts) > 0:
        # Conditional legal answer format: state missing facts, then conditional branches
        missing_facts_str = "; ".join(str(f).strip() for f in missing_facts[:3] if f)
        conclusion_line = (
            f"Về nguyên tắc, kết luận: {conclusion}. "
            f"(Kết luận này có điều kiện do còn thiếu thông tin: {missing_facts_str}. "
            f"Nếu xác nhận các thông tin trên, kết luận này sẽ chính thức hơn.)"
        )
    else:
        conclusion_line = (
            f"Về nguyên tắc, kết luận: {conclusion}."
            if goal_achieved
            else f"Về nguyên tắc, kết luận: {conclusion or 'chưa đủ căn cứ kết luận chắc chắn'}; cần xác định thêm tình tiết còn thiếu."
        )

    analysis = "\n\n".join(analysis_parts)
    answer_text = (
        f"{opening}\n\n"
        f"1) {issue}\n"
        f"2) {rule_line}\n"
        f"3) {analysis}\n"
        f"4) {conclusion_line}\n\n"
        "Trân trọng."
    )

    conf = 0.82 if goal_achieved else 0.38
    if not evidence:
        conf *= 0.92

    sections = {
        "opening": opening.strip(),
        "legal_issue": issue.strip(),
        "legal_rule": rule_line.strip(),
        "application": analysis.strip(),
        "conclusion": conclusion_line.strip(),
        "conclusion_lead": conclusion_line.strip(),
        "analysis": analysis.strip(),
        "closing": "Trân trọng.",
    }
    return answer_text, proof_summary, conf, sections, citations


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
    evidence_bundle: EvidenceBundle | None = None,
    mode: str = "template_grounded",
    llm_generate: Callable[..., str] | None = None,
    rule: RuleRecord | None = None,
    missing_facts: list[str] | None = None,
) -> FinalAnswer:
    """
    Grounded answer: conclusion + proof + evidence; citations chỉ từ evidence/provenance rule.

    Modes:
    - ``template_grounded``: deterministic Vietnamese layout (default).
    - ``llm_grounded``: narrative từ LLM nhưng tham chiếu bracket chỉ từ evidence đã build.
    """
    citations = build_legal_citations_from_evidence(evidence, rule=rule, max_citations=6)
    if evidence_bundle is not None:
        # Keep a stable attachment to first-class evidence stage for downstream audit.
        evidence = list(evidence)

    if mode == "llm_grounded" and llm_generate is not None:
        citations = build_legal_citations_from_evidence(evidence, rule=rule, max_citations=6)
        plines = _proof_lines(proof)
        proof_summary = " ".join(plines) if plines else ((proof.conclusion or proof.derived_conclusion) if proof else "")
        llm_body = _llm_grounded_answer(
            question=question,
            conclusion=conclusion,
            proof_summary=proof_summary,
            evidence=evidence,
            goal_achieved=goal_achieved,
            llm_generate=llm_generate,
        )
        llm_body = (llm_body or "").strip()[:4000]
        opening = (
            "Kính gửi Quý khách hàng,\n\n"
            "Phần trình bày sau đây được tóm tắt từ kết luận suy luận và tài liệu tham chiếu đã cung cấp "
            "(không tự thêm điều khoản ngoài danh sách tham chiếu).\n\n"
        )
        mid = f"Về nguyên tắc: {conclusion}.\n\n"
        cite_line = ""
        if citations:
            cite_line = "Tham chiếu văn bản: " + ", ".join(
                f"[{c.display_label.strip()}]" for c in citations[:5] if c.display_label.strip()
            )
            if cite_line.endswith(" "):
                cite_line = cite_line.strip()
            cite_line = cite_line + ".\n\n" if cite_line else ""
        analysis = f"{llm_body}\n\n{cite_line}".strip() + "\n\n"
        closing = (
            "Tuy nhiên, cần đối chiếu văn bản gốc và ngữ cảnh cụ thể. Trân trọng."
        )
        answer_text = opening + mid + analysis + closing
        sections = {
            "opening": opening.strip(),
            "conclusion_lead": f"Về nguyên tắc: {conclusion}.",
            "analysis": (mid + llm_body + "\n\n" + cite_line).strip(),
            "closing": closing,
        }
        spans = link_answer_text_to_citations(answer_text, citations)
        return FinalAnswer(
            answer_text=answer_text,
            conclusion=conclusion,
            proof_summary=proof_summary,
            evidence_snippets=evidence,
            confidence=0.75 if goal_achieved else 0.4,
            verification_summary=f"goal_achieved={goal_achieved};mode=llm_grounded;evidence_hits={len(evidence)}",
            generation_mode="llm_grounded",
            legal_citations=citations,
            citation_spans=spans,
            answer_sections=sections,
        )

    answer_text, proof_summary, conf, sections, citations = _build_template_grounded(
        question=question,
        conclusion=conclusion,
        proof=proof,
        evidence=evidence,
        goal_achieved=goal_achieved,
        rule=rule,
        missing_facts=missing_facts,
    )
    spans = link_answer_text_to_citations(answer_text, citations)
    return FinalAnswer(
        answer_text=answer_text,
        conclusion=conclusion,
        proof_summary=proof_summary,
        evidence_snippets=evidence,
        confidence=conf,
        verification_summary=f"goal_achieved={goal_achieved};mode=template_grounded;evidence_hits={len(evidence)}",
        generation_mode="template_grounded",
        legal_citations=citations,
        citation_spans=spans,
        answer_sections=sections,
        extra={
            "evidence_bundle_id": evidence_bundle.bundle_id if evidence_bundle else None,
            "evidence_linkage": evidence_bundle.linkage_map if evidence_bundle else None,
        },
    )


def safe_regenerate_final_answer(
    conclusion: str,
    *,
    proof: ProofObject | None = None,
    evidence: list[EvidenceSnippet] | None = None,
    rule: RuleRecord | None = None,
    goal_achieved: bool = True,
) -> FinalAnswer:
    """Shorter template when verification rejects — vẫn grounded, giữ citation package."""
    ev = evidence or []
    citations = build_legal_citations_from_evidence(ev, rule=rule, max_citations=5)
    ps = " ".join(_proof_lines(proof, max_steps=3)) if proof else ""
    opening = "Kính gửi,"
    issue = "Vấn đề pháp lý: xác định quyền/nghĩa vụ theo dữ kiện đã cung cấp."
    core = f"Quy tắc trọng tâm: {conclusion}."
    tail = ""
    if ps:
        tail += f" Cơ sở luận giải rút gọn: {ps[:280]}"
    cite_bits = []
    for c in citations[:2]:
        if c.display_label.strip():
            cite_bits.append(f"[{c.display_label.strip()}]")
    if cite_bits:
        tail += " Tham chiếu: " + ", ".join(cite_bits) + "."
    application = f"Áp dụng: {tail.strip() or 'cần đối chiếu thêm dữ kiện để áp dụng chính xác.'}"
    conclusion_line = f"Về nguyên tắc, kết luận: {conclusion}."
    answer_text = (
        f"{opening}\n\n"
        f"1) {issue}\n"
        f"2) {core}\n"
        f"3) {application}\n"
        f"4) {conclusion_line}\n\n"
        "Trân trọng."
    )
    sections = {
        "opening": opening.strip(),
        "legal_issue": issue,
        "legal_rule": core,
        "application": application,
        "conclusion": conclusion_line,
        "conclusion_lead": conclusion_line,
        "analysis": application,
        "closing": "Trân trọng.",
    }
    spans = link_answer_text_to_citations(answer_text, citations)
    return FinalAnswer(
        answer_text=answer_text,
        conclusion=conclusion,
        proof_summary=ps,
        evidence_snippets=ev,
        confidence=0.55 if goal_achieved else 0.35,
        verification_summary="mode=safe_regenerate_final",
        generation_mode="template_grounded",
        legal_citations=citations,
        citation_spans=spans,
        answer_sections=sections,
    )


def safe_regenerate_answer(
    conclusion: str,
    *,
    proof: ProofObject | None = None,
    evidence: list[EvidenceSnippet] | None = None,
    rule: RuleRecord | None = None,
    goal_achieved: bool = True,
) -> str:
    """One-shot safer template if verification rejects — string API for repair handlers."""
    return safe_regenerate_final_answer(
        conclusion,
        proof=proof,
        evidence=evidence,
        rule=rule,
        goal_achieved=goal_achieved,
    ).answer_text


def generate_honest_degraded_answer(
    *,
    question: str,
    reason: str,
    selected_rule: RuleRecord | None = None,
    goal: dict[str, Any] | None = None,
    retrieved_rules: list[RuleRecord] | None = None,
) -> FinalAnswer:
    """Honest fallback with provisional legal guidance when full grounding is unavailable."""
    rule_hint = str(selected_rule.rule_id) if selected_rule else ""
    top_rule = selected_rule or ((retrieved_rules or [None])[0] if retrieved_rules else None)
    top_hint = str(getattr(top_rule, "rule_id", "") or "")
    pred = str((goal or {}).get("predicate") or "")

    opening = "Kính gửi Quý khách hàng,"
    issue = f"Vấn đề pháp lý: {question.strip()[:220]}"
    if top_hint:
        rule_line = (
            f"Quy tắc/điều kiện có khả năng liên quan: {top_hint}. "
            "Đây là căn cứ tạm thời, cần đối chiếu thêm trước khi kết luận chắc chắn."
        )
    elif pred:
        rule_line = f"Quy tắc/điều kiện có khả năng liên quan: nhóm {pred}; hiện chưa đủ căn cứ để chọn quy tắc khớp hoàn toàn."
    else:
        rule_line = "Quy tắc/điều kiện có khả năng liên quan: chưa xác định chắc chắn từ dữ liệu hiện có."

    application = (
        "Áp dụng tạm thời: nếu tình tiết thực tế đúng với điều kiện của quy tắc liên quan thì có thể đi theo hướng kết luận tương ứng; "
        "hiện còn thiếu dữ kiện mốc thời gian/chủ thể/điều kiện ngoại lệ để chốt kết luận."
    )
    conclusion_line = (
        f"Về nguyên tắc, chưa đủ căn cứ grounded để kết luận dứt điểm (reason={reason or 'grounding_unavailable'}); "
        "cần xác định thêm dữ kiện then chốt."
    )
    answer_text = (
        f"{opening}\n\n"
        f"1) {issue}\n"
        f"2) {rule_line}\n"
        f"3) {application}\n"
        f"4) {conclusion_line}\n\n"
        "Trân trọng."
    )
    return FinalAnswer(
        answer_text=answer_text,
        conclusion="chua_du_can_cu_grounded",
        proof_summary="",
        evidence_snippets=[],
        confidence=0.2,
        verification_summary=f"mode=degraded_honest;reason={reason or 'grounding_unavailable'}",
        generation_mode="degraded_honest",
        legal_citations=[],
        citation_spans=[],
        answer_sections={
            "opening": opening,
            "legal_issue": issue,
            "legal_rule": rule_line,
            "application": application,
            "conclusion": conclusion_line,
            "conclusion_lead": conclusion_line,
            "analysis": application,
            "closing": "Trân trọng.",
        },
        extra={
            "degraded": True,
            "reason": reason or "grounding_unavailable",
            "selected_rule_id": rule_hint or None,
            "provisional_rule_id": top_hint or None,
        },
    )


def apply_answer_text_and_refresh_citations(ans: FinalAnswer, new_text: str) -> None:
    """After answer repair loop: update text và map lại spans (metadata citation giữ nguyên)."""
    ans.answer_text = new_text
    ans.citation_spans = finalize_answer_citations(ans.answer_text, ans.legal_citations)


class AnswerGenerator:
    """Legacy stub — use generate_answer() for the QA pipeline."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def generate(self, proof: Any | None, context: dict[str, Any]) -> str:
        raise NotImplementedError
