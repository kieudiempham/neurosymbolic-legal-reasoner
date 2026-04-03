"""Skeleton tests for forward reasoning."""

from __future__ import annotations

import pytest

from reasoning.forward_chainer import ForwardChainer


def test_forward_chainer_stub_raises() -> None:
    c = ForwardChainer(config={})
    with pytest.raises(NotImplementedError):
        c.chain(facts={}, rules=[])
