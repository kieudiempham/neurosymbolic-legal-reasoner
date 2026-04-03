"""Skeleton tests for backward reasoning."""

from __future__ import annotations

import pytest

from reasoning.backward_chainer import BackwardChainer
from schemas.question_schema import Layer2LogicObjects


def test_backward_chainer_stub_raises() -> None:
    c = BackwardChainer(config={})
    layer2 = Layer2LogicObjects(question_id="q", objects=[])
    with pytest.raises(NotImplementedError):
        c.chain(layer2, rules=[])
