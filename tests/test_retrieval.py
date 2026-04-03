"""Skeleton tests for retrieval."""

from __future__ import annotations

import pytest

from retrieval.rule_retriever import RuleRetriever
from schemas.question_schema import Layer2LogicObjects


def test_rule_retriever_stub_raises() -> None:
    r = RuleRetriever(config={})
    layer2 = Layer2LogicObjects(question_id="q", objects=[])
    with pytest.raises(NotImplementedError):
        r.retrieve(layer2, top_k=5)
