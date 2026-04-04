"""Evidence retrieval: BM25 over legal passages + structured rerank (RAG support, not rule synthesis)."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from retrieval.bm25_index import BM25Index
from retrieval.hybrid_rule_ranker import normalize_scores
from retrieval.retrieval_query import build_evidence_retrieval_query
from schemas.evidence import EvidenceSnippet
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
        " ".join(str(x) for x in (ch.get("rule_ids") or [])),
    ]
    return "\n".join(p for p in parts if p)


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
    ) -> list[EvidenceSnippet]:
        """
        Hybrid: BM25 on passage text + boosts for rule linkage and source_ref overlap.
        Query is grounded on conclusion + proof + rule pointer + goal, not question-only.
        """
        rid = rule.rule_id if rule else None
        sr = (rule.source_ref_full or rule.source_ref) if rule else None
        g = goal or {}
        qfull = build_evidence_retrieval_query(
            question=question,
            conclusion=conclusion or "",
            proof_summary=proof_summary or "",
            goal=g,
            source_ref=sr,
            rule_id=rid,
            modality_text=modality_text or "",
        )

        if not self._chunks:
            return []

        documents = [_chunk_document(ch) for ch in self._chunks]
        idx = BM25Index()
        idx.fit(documents)
        bm25_raw = idx.scores(qfull)

        struct_scores: list[float] = []
        for i, ch in enumerate(self._chunks):
            cid = str(ch.get("chunk_id") or ch.get("id") or "chunk")
            text = str(ch.get("text") or "")
            doc = ch.get("source_doc") or ch.get("doc") or ""
            ac = ch.get("article_clause") or ch.get("clause") or ""
            rids = ch.get("rule_ids") or []
            s_struct = 0.0
            if rid and isinstance(rids, list) and rid in rids:
                s_struct += 6.0
            if sr and str(sr)[:24] and str(sr)[:24] in text:
                s_struct += 3.0
            if conclusion and lower_fold(conclusion[:80]) in lower_fold(text):
                s_struct += 2.0
            lowq = lower_fold(qfull)
            for tok in lowq.split():
                if len(tok) > 3 and tok in lower_fold(text):
                    s_struct += 0.15
            struct_scores.append(s_struct)

        bm25_n = normalize_scores(bm25_raw)
        struct_n = normalize_scores(struct_scores)
        hybrid = [0.45 * b + 0.55 * s for b, s in zip(bm25_n, struct_n, strict=True)]

        scored: list[tuple[float, EvidenceSnippet]] = []
        for i, ch in enumerate(self._chunks):
            cid = str(ch.get("chunk_id") or ch.get("id") or "chunk")
            text = str(ch.get("text") or "")
            doc = ch.get("source_doc") or ch.get("doc") or ""
            ac = ch.get("article_clause") or ch.get("clause") or ""
            art, cl, pt = _split_article_clause(str(ac) if ac else None)
            rr = "bm25+structured; " + "; ".join(
                [
                    f"bm25_raw={bm25_raw[i]:.3f}",
                    f"struct={struct_scores[i]:.3f}",
                ]
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
                        score_breakdown={
                            "bm25_raw": bm25_raw[i],
                            "bm25_norm": bm25_n[i],
                            "structured": struct_scores[i],
                            "hybrid": hybrid[i],
                        },
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
