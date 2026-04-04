"""Structured per-check results for symbolic validation (not a single bool)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

CheckStatus = Literal["pass", "fail", "skip"]


@dataclass
class SymbolicCheckResult:
    ok: bool
    issues: list[str] = field(default_factory=list)
    error_codes: list[str] = field(default_factory=list)
    checks: list[dict[str, Any]] = field(default_factory=list)

    def add(
        self,
        name: str,
        status: CheckStatus,
        message: str = "",
        field: str | None = None,
        *,
        code: str | None = None,
    ) -> None:
        row: dict[str, Any] = {"name": name, "status": status, "message": message}
        if field:
            row["field"] = field
        self.checks.append(row)
        if status == "fail":
            self.issues.append(f"{name}: {message}" if message else name)
            if code:
                self.error_codes.append(code)
