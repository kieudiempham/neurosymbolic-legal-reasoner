"""Clarification generation — delegates to clarification_manager + clarification_types (v5)."""

from __future__ import annotations

from typing import Any

from reasoning.clarification_manager import build_clarification_prompts_from_requirements
from schemas.reasoning import RequirementItem


class ClarificationGenerator:
    """Produces structured clarification rows (not only bare strings)."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def generate_rows(
        self,
        missing_keys: list[str],
        requirement_set: list[RequirementItem],
        *,
        backward_plan: dict[str, Any] | None = None,
        related_rule_id: str | None = None,
    ) -> list[dict[str, Any]]:
        return build_clarification_prompts_from_requirements(
            missing_keys,
            requirement_set,
            backward_plan=backward_plan,
            related_rule_id=related_rule_id,
        )
