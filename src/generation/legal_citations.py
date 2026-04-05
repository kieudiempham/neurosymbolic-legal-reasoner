"""Build legal citations and citation spans only from evidence / rule provenance (no invention)."""

from __future__ import annotations

import re
from typing import Any

from schemas.citation import CitationSpan, LegalCitation, OpenPdfPayload, PdfAnchor
from schemas.evidence import EvidenceSnippet
from schemas.rule import RuleRecord
from utils.text import slug_token


def _short_excerpt(text: str, *, max_len: int = 320) -> str:
    t = (text or "").strip().replace("\n", " ")
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


def _norm_doc_id(source_doc: str | None, explicit: str | None) -> str | None:
    if explicit and explicit.strip():
        return explicit.strip()
    if source_doc and source_doc.strip():
        return slug_token(source_doc)[:96] or None
    return None


def format_citation_display_label(
    *,
    article_clause: str | None,
    article: str | None,
    clause: str | None,
    point: str | None,
    source_doc: str | None,
) -> str:
    """Human-readable label for inline brackets (Vietnamese legal style, short)."""
    parts: list[str] = []
    ac = (article_clause or "").strip()
    if ac:
        parts.append(ac)
    else:
        bits = [x for x in (article, clause, point) if x and str(x).strip()]
        if bits:
            parts.append(" ".join(bits))
    doc = (source_doc or "").strip()
    if doc:
        short = doc[:72] + ("…" if len(doc) > 72 else "")
        if parts:
            return f"{parts[0]} — {short}"
        return short
    return parts[0] if parts else "Tham chiếu pháp lý"


def _snippet_to_citation(
    ev: EvidenceSnippet,
    idx: int,
    *,
    dedupe: set[str],
) -> LegalCitation | None:
    key = f"{ev.chunk_id}|{ev.article_clause or ''}|{ev.source_doc or ''}"
    if key in dedupe:
        return None
    dedupe.add(key)

    display = format_citation_display_label(
        article_clause=ev.article_clause,
        article=ev.article,
        clause=ev.clause,
        point=ev.point,
        source_doc=ev.source_doc,
    )
    excerpt = _short_excerpt(ev.text)
    doc_id = _norm_doc_id(ev.source_doc, ev.doc_id)
    page = ev.page
    src_ref = ev.source_ref or (ev.article_clause or "")

    pdf = PdfAnchor(page=page, bbox=None, anchor_text=excerpt[:120] if excerpt else None)
    payload = OpenPdfPayload(
        doc_id=doc_id,
        page=page,
        source_ref=src_ref or None,
        chunk_id=ev.chunk_id,
    )

    return LegalCitation(
        citation_id=f"cit_{idx}",
        label=display[:120],
        display_label=display,
        doc_id=doc_id,
        source_ref=src_ref or None,
        article=ev.article,
        clause=ev.clause,
        point=ev.point,
        excerpt=excerpt,
        tooltip_excerpt=excerpt[:280] if excerpt else None,
        pdf_anchor=pdf,
        open_pdf_payload=payload,
        chunk_id=ev.chunk_id,
    )


def _rule_to_citation(rule: RuleRecord, idx: int, dedupe: set[str]) -> LegalCitation | None:
    prov = (rule.metadata or {}).get("provenance") or {}
    srf = (prov.get("source_ref_full") or rule.source_ref_full or "").strip()
    sr = (prov.get("source_ref") or rule.source_ref or "").strip()
    st = (prov.get("source_text") or "").strip()
    key = f"rule|{rule.rule_id}"
    if key in dedupe or not (srf or sr):
        return None
    dedupe.add(key)

    label_core = srf if srf else sr
    display = label_core[:200] if len(label_core) <= 200 else label_core[:197] + "…"
    excerpt = _short_excerpt(st) if st else ""

    return LegalCitation(
        citation_id=f"cit_{idx}",
        label=display[:120],
        display_label=display,
        doc_id=slug_token(prov.get("doc_code") or "")[:64] or None,
        source_ref=sr or None,
        article=None,
        clause=None,
        point=None,
        excerpt=excerpt,
        tooltip_excerpt=excerpt[:280] if excerpt else None,
        pdf_anchor=PdfAnchor(page=None),
        open_pdf_payload=OpenPdfPayload(
            doc_id=None,
            page=None,
            source_ref=sr or label_core[:120],
            chunk_id=None,
            extra={"rule_id": rule.rule_id},
        ),
        chunk_id=None,
    )


def build_legal_citations_from_evidence(
    evidence: list[EvidenceSnippet],
    *,
    rule: RuleRecord | None = None,
    max_citations: int = 6,
) -> list[LegalCitation]:
    """Grounded citations: evidence snippets first, then optional rule provenance if no overlap."""
    out: list[LegalCitation] = []
    dedupe: set[str] = set()
    for ev in evidence:
        if len(out) >= max_citations:
            break
        c = _snippet_to_citation(ev, len(out) + 1, dedupe=dedupe)
        if c:
            out.append(c)
    if rule and len(out) < max_citations:
        c = _rule_to_citation(rule, len(out) + 1, dedupe)
        if c:
            out.append(c)
    for j, c in enumerate(out, start=1):
        c.citation_id = f"cit_{j}"
    return out


def link_answer_text_to_citations(answer_text: str, citations: list[LegalCitation]) -> list[CitationSpan]:
    """Find bracketed display_label substrings in answer_text."""
    spans: list[CitationSpan] = []
    for c in citations:
        dl = c.display_label.strip()
        if not dl:
            continue
        escaped = re.escape(f"[{dl}]")
        for m in re.finditer(escaped, answer_text):
            spans.append(
                CitationSpan(
                    citation_id=c.citation_id,
                    label=c.label,
                    text_span=f"[{dl}]",
                    start=m.start(),
                    end=m.end(),
                )
            )
    return spans


def ensure_bracket_labels_for_citations(
    answer_text: str,
    citations: list[LegalCitation],
    *,
    max_append: int = 3,
) -> str:
    """If analysis has no bracket for a citation, append a short reference line (grounded labels only)."""
    if not citations:
        return answer_text
    missing: list[LegalCitation] = []
    for c in citations[:max_append]:
        dl = c.display_label.strip()
        if dl and f"[{dl}]" not in answer_text:
            missing.append(c)
    if not missing:
        return answer_text
    tail = " ".join(f"[{c.display_label.strip()}]" for c in missing[:max_append])
    return answer_text.rstrip() + "\n\n" + f"Căn cứ tham chiếu thêm: {tail}"


def finalize_answer_citations(answer_text: str, citations: list[LegalCitation]) -> list[CitationSpan]:
    """Recompute spans after answer_text mutation (e.g. answer repair loop)."""
    return link_answer_text_to_citations(answer_text, citations)
