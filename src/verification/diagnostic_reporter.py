"""Aggregate verification failures for error analysis (paper tables)."""

from __future__ import annotations

from typing import Any

from schemas.verification_schema import VerificationResult


class DiagnosticReporter:
    """Collects and categorizes verification outcomes."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def report(self, results: list[VerificationResult]) -> dict[str, Any]:
        """Aggregate errors by category and write data/processed/reports/error_summary.json."""
        raise NotImplementedError
