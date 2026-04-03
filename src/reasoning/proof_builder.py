"""Assemble backward/forward traces into a Proof object."""

from __future__ import annotations

from typing import Any

from schemas.proof_schema import Proof


class ProofBuilder:
    """Unifies reasoning traces for explainability and evaluation."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def build(self, reasoning_bundle: dict[str, Any]) -> Proof:
        """Fill in Proof and ProofStep records from chainer output."""
        raise NotImplementedError
