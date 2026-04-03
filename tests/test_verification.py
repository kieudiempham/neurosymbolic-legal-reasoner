"""Skeleton tests for verification."""

from __future__ import annotations

import pytest

from schemas.verification_schema import VerificationResult
from verification.nli_validator import NLIValidator


def test_nli_validator_stub_raises() -> None:
    v = NLIValidator(config={})
    with pytest.raises(NotImplementedError):
        v.verify("premise", "hypothesis")


def test_verification_result_model() -> None:
    r = VerificationResult(verifier_name="t", target_id="x", passed=True)
    assert r.passed is True
