"""Evidence retrieval from JSON corpus — does not invent rules."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

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
    ) -> list[EvidenceSnippet]:
        rid = rule.rule_id if rule else None
        sr = (rule.source_ref if rule else None) or ""
        qlow = lower_fold(question)
        scored: list[tuple[float, EvidenceSnippet]] = []
        for ch in self._chunks:
            cid = str(ch.get("chunk_id") or ch.get("id") or "chunk")
            text = str(ch.get("text") or "")
            doc = ch.get("source_doc") or ch.get("doc") or ""
            ac = ch.get("article_clause") or ch.get("clause") or ""
            rids = ch.get("rule_ids") or []
            score = 0.0
            if rid and isinstance(rids, list) and rid in rids:
                score += 5.0
            if sr and sr and sr[:20] in text:
                score += 2.0
            for tok in qlow.split():
                if len(tok) > 3 and tok in lower_fold(text):
                    score += 0.4
            if conclusion and lower_fold(conclusion[:40]) in lower_fold(text):
                score += 1.5
            scored.append(
                (
                    score,
                    EvidenceSnippet(
                        chunk_id=cid,
                        text=text[:1200],
                        source_doc=str(doc) if doc else None,
                        article_clause=str(ac) if ac else None,
                        rule_id=rid,
                        score=score,
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
