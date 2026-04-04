"""Tiny Okapi BM25 over tokenized documents (no external deps)."""

from __future__ import annotations

import math
import re
from typing import Sequence

_TOKEN_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "") if len(t) > 1]


class BM25Index:
    def __init__(self, *, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._docs: list[list[str]] = []
        self._df: dict[str, int] = {}
        self._idf: dict[str, float] = {}
        self._avgdl = 0.0
        self._N = 0

    def fit(self, documents: Sequence[str]) -> None:
        self._docs = [tokenize(d) for d in documents]
        self._N = len(self._docs)
        self._df = {}
        for doc in self._docs:
            seen = set(doc)
            for t in seen:
                self._df[t] = self._df.get(t, 0) + 1
        self._idf = {}
        for t, df in self._df.items():
            # Smooth IDF
            self._idf[t] = math.log(1.0 + (self._N - df + 0.5) / (df + 0.5))
        tot = sum(len(d) for d in self._docs)
        self._avgdl = tot / max(1, self._N)

    def scores(self, query: str) -> list[float]:
        q = tokenize(query)
        if not q or not self._docs:
            return [0.0] * len(self._docs)
        scores = []
        for doc in self._docs:
            dl = len(doc)
            tf: dict[str, int] = {}
            for t in doc:
                tf[t] = tf.get(t, 0) + 1
            s = 0.0
            for term in q:
                idf = self._idf.get(term, 0.0)
                if idf == 0.0:
                    continue
                f = tf.get(term, 0)
                if f == 0:
                    continue
                denom = f + self.k1 * (1.0 - self.b + self.b * dl / max(self._avgdl, 1e-6))
                s += idf * (f * (self.k1 + 1)) / denom
            scores.append(s)
        return scores
