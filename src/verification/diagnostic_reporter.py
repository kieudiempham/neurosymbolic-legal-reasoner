"""Deprecated stub — diagnostics live on `VerificationRecord` from `NeSyEngine` (v5)."""

from __future__ import annotations

from typing import Any

from schemas.verification import VerificationResult


class DiagnosticReporter:
    """Deprecated: use session `verification_logs` + `VerificationRecord.diagnostic_errors`."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def report(self, results: list[VerificationResult]) -> dict[str, Any]:
        raise NotImplementedError("Aggregate VerificationRecord list from session.verification_logs")
