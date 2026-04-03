"""Turn Proof objects into explanatory text for evaluation and UI."""

from __future__ import annotations

from typing import Any

from schemas.proof_schema import Proof


class ProofToText:
    """Linearizes proofs for human reading."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def render(self, proof: Proof) -> str:
        """Render numbered steps with citations to rules."""
        raise NotImplementedError
