"""Combine BM25 (lexical) with structured v5 signals for rule ranking."""

from __future__ import annotations

from typing import Any

from retrieval.bm25_index import BM25Index


def normalize_scores(raw: list[float]) -> list[float]:
    if not raw:
        return []
    mx = max(raw) or 1e-9
    return [x / mx for x in raw]


def hybrid_combine(
    lexical_norm: list[float],
    structured_norm: list[float],
    *,
    w_lex: float = 0.35,
    w_struct: float = 0.65,
) -> list[float]:
    assert len(lexical_norm) == len(structured_norm)
    return [
        w_lex * lx + w_struct * sx for lx, sx in zip(lexical_norm, structured_norm, strict=True)
    ]


def bm25_scores_for_documents(documents: list[str], query: str) -> list[float]:
    idx = BM25Index()
    idx.fit(documents)
    return idx.scores(query)
