"""Skeleton tests for question-side parsing."""

from __future__ import annotations

import pytest

from question_side.layer1_slot_extractor import Layer1SlotExtractor


def test_layer1_extractor_stub_raises() -> None:
    ex = Layer1SlotExtractor(config={})
    with pytest.raises(NotImplementedError):
        ex.extract("q1", "dummy question")
