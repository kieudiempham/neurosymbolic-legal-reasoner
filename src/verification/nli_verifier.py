"""NLI verifier interface + mock implementation."""

from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from typing import Literal

from schemas.verification import NLIResult


NLILabel = Literal["entailment", "contradiction", "neutral"]


class NLIVerifier(ABC):
    @abstractmethod
    def verify(self, premise: str, hypothesis: str) -> NLIResult:
        raise NotImplementedError


class MockNLIVerifier(NLIVerifier):
    """
    Deterministic mock: overlap + keyword heuristics.
    Plug a real model by subclassing NLIVerifier.
    """

    def verify(self, premise: str, hypothesis: str) -> NLIResult:
        p = _norm(premise)
        h = _norm(hypothesis)
        if not h:
            return NLIResult(label="neutral", score=0.5)
        if h in p or p in h:
            return NLIResult(label="entailment", score=0.92)
        pt = set(re.findall(r"[a-z0-9_]{4,}", p))
        ht = set(re.findall(r"[a-z0-9_]{4,}", h))
        if pt and ht:
            j = len(pt & ht) / max(1, len(ht))
            if j >= 0.45:
                return NLIResult(label="entailment", score=0.55 + 0.35 * j)
            if j <= 0.05 and len(ht) >= 3:
                return NLIResult(label="contradiction", score=0.4)
        s = int(hashlib.sha256((p + "||" + h).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        if s > 0.72:
            return NLIResult(label="entailment", score=0.55 + 0.2 * s)
        if s < 0.18:
            return NLIResult(label="contradiction", score=0.45)
        return NLIResult(label="neutral", score=0.5)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


class HeuristicNLIVerifier(NLIVerifier):
    """Alias for mock in config."""

    def __init__(self) -> None:
        self._inner = MockNLIVerifier()

    def verify(self, premise: str, hypothesis: str) -> NLIResult:
        return self._inner.verify(premise, hypothesis)
