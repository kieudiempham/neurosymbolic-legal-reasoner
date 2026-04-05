"""Evidence retrieval: BM25 multi-query + structured rerank (RAG support, not rule synthesis)."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from retrieval.bm25_index import BM25Index
from retrieval.hybrid_rule_ranker import normalize_scores
from retrieval.retrieval_query import build_evidence_query_variants
from schemas.evidence import EvidenceSnippet
from schemas.question_parse import Layer1Parse, Layer2Parse
from schemas.rule import RuleRecord
from utils.text import lower_fold

logger = logging.getLogger(__name__)

_configured_evidence_path: Path | None = None
_retriever: EvidenceRetriever | None = None


def configure_evidence_path(path: Path | None) -> None:
    global _configured_evidence_path, _retriever
    _configured_evidence_path = path
    _retriever = None


def _load_chunks(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        logger.warning("evidence corpus missing: %s — using empty list", path)
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return list((data.get("chunks") or data.get("evidence_chunks") or []))


def _chunk_document(ch: dict[str, Any]) -> str:
    parts = [
        str(ch.get("text") or ""),
        str(ch.get("source_doc") or ch.get("doc") or ""),
        str(ch.get("article_clause") or ch.get("clause") or ""),
        str(ch.get("article") or ""),
        str(ch.get("point") or ""),
        " ".join(str(x) for x in (ch.get("rule_ids") or [])),
    ]
    return "\n".join(p for p in parts if p)


def _article_num(s: str | None) -> str | None:
    if not s:
        return None
    m = re.search(r"(\d+)", s)
    return m.group(1) if m else None


def _split_article_clause(ac: str | None) -> tuple[str | None, str | None, str | None]:
    if not ac:
        return None, None, None
    s = ac.strip()
    m = re.search(r"Điều\s*(\d+)", s, re.IGNORECASE)
    article = f"Điều {m.group(1)}" if m else None
    mk = re.search(r"khoản\s*(\d+)", s, re.IGNORECASE)
    clause = f"khoản {mk.group(1)}" if mk else None
    return article, clause, None


class EvidenceRetriever:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _configured_evidence_path
        if self._path is None:
            logger.warning("evidence path not configured")
            self._chunks: list[dict[str, Any]] = []
        else:
            self._chunks = _load_chunks(self._path)

    def retrieve(
        self,
        *,
        question: str,
        rule: RuleRecord | None,
        conclusion: str,
        top_k: int = 5,
        proof_summary: str = "",
        goal: dict[str, Any] | None = None,
        modality_text: str = "",
        layer1: Layer1Parse | None = None,
        layer2: Layer2Parse | None = None,
    ) -> list[EvidenceSnippet]:
        """
        Hybrid: max BM25 across query variants + structured boosts (rule, source_ref, article).
        """
        rid = rule.rule_id if rule else None
        sr = (rule.source_ref_full or rule.source_ref) if rule else None
        head_pred = rule.head.predicate if rule else None
        g = goal or {}

        variants = build_evidence_query_variants(
            question=question,
            conclusion=conclusion or "",
            proof_summary=proof_summary or "",
            goal=g,
            source_ref=sr,
            rule_id=rid,
            modality_text=modality_text or "",
            layer1=layer1,
            layer2=layer2,
            used_rule_head_predicate=head_pred,
        )

        if not self._chunks:
            return []

        documents = [_chunk_document(ch) for ch in self._chunks]
        idx = BM25Index()
        idx.fit(documents)

        n = len(self._chunks)
        bm25_max = [0.0] * n
        variant_hits: list[str] = ["primary"] * n
        q_labels = list(variants.keys())
        for label, qstr in variants.items():
            if not (qstr or "").strip():
                continue
            raw = idx.scores(qstr)
            for i in range(n):
                if raw[i] > bm25_max[i]:
                    bm25_max[i] = raw[i]
                    variant_hits[i] = label

        bm25_n = normalize_scores(bm25_max)
        sr_article = _article_num(sr)
        q_low = lower_fold(question[:500] if question else "")

        struct_scores: list[dict[str, float]] = []
        for i, ch in enumerate(self._chunks):
            text = str(ch.get("text") or "")
            ac = str(ch.get("article_clause") or ch.get("clause") or "")
            rids = ch.get("rule_ids") or []
            ch_art = _article_num(ac) or _article_num(str(ch.get("article") or ""))

            comp: dict[str, float] = {
                "bm25_raw": bm25_max[i],
                "bm25_norm": bm25_n[i],
                "lexical_variant": 0.0,
                "rule_id_match": 0.0,
                "source_ref_substring": 0.0,
                "article_align": 0.0,
                "conclusion_overlap": 0.0,
                "question_token_overlap": 0.0,
            }
            comp["lexical_variant"] = 0.1 if variant_hits[i] != "primary" else 0.0

            if rid and isinstance(rids, list) and rid in rids:
                comp["rule_id_match"] = 6.0
            if sr and len(str(sr)) > 8 and str(sr)[:40] in text:
                comp["source_ref_substring"] = 3.5
            elif sr and len(str(sr)) > 8 and str(sr)[:24] in text:
                comp["source_ref_substring"] = 2.5

            if sr_article and ch_art and sr_article == ch_art:
                comp["article_align"] = 2.5

            if conclusion and lower_fold(conclusion[:100]) in lower_fold(text):
                comp["conclusion_overlap"] = 2.2

            lowt = lower_fold(text)
            for tok in q_low.split():
                if len(tok) > 3 and tok in lowt:
                    comp["question_token_overlap"] += 0.12

            s_struct = float(sum(comp[k] for k in comp if k not in ("bm25_raw", "bm25_norm")))
            comp["structured_total"] = s_struct
            struct_scores.append(comp)

        struct_totals = [c["structured_total"] for c in struct_scores]
        struct_n = normalize_scores(struct_totals)
        hybrid = [0.42 * bm25_n[i] + 0.58 * struct_n[i] for i in range(n)]

        scored: list[tuple[float, EvidenceSnippet]] = []
        for i, ch in enumerate(self._chunks):
            cid = str(ch.get("chunk_id") or ch.get("id") or "chunk")
            text = str(ch.get("text") or "")
            doc = ch.get("source_doc") or ch.get("doc") or ""
            ac = ch.get("article_clause") or ch.get("clause") or ""
            art, cl, pt = _split_article_clause(str(ac) if ac else None)
            bd = struct_scores[i]
            bd["hybrid"] = hybrid[i]
            bd["bm25_variant_used"] = variant_hits[i]
            rr = (
                f"multi_query_bm25_max={bd['bm25_raw']:.3f};variant={variant_hits[i]};"
                f"struct={bd['structured_total']:.3f}"
            )
            scored.append(
                (
                    hybrid[i],
                    EvidenceSnippet(
                        chunk_id=cid,
                        text=text[:1200],
                        source_doc=str(doc) if doc else None,
                        article_clause=str(ac) if ac else None,
                        rule_id=rid,
                        score=hybrid[i],
                        retrieval_reason=rr,
                        linked_rule_id=rid,
                        score_breakdown=bd,
                        doc_id=str(doc) if doc else None,
                        article=art,
                        clause=cl,
                        point=pt,
                    ),
                )
            )

        scored.sort(key=lambda x: -x[0])
        return [s for _, s in scored[:top_k]]


def get_evidence_retriever() -> EvidenceRetriever:
    global _retriever
    if _retriever is None:
        _retriever = EvidenceRetriever()
    return _retriever
