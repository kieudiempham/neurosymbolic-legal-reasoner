"""Internal reasoning-facing structures (mapped from `RuleRecord`, not stored in rulebase JSON)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RequirementKind = Literal["positive", "negative", "exception", "constraint", "auxiliary"]


class Atom(BaseModel):
    """Normalized logical atom: predicate name + ordered arguments (VN slugs / values)."""

    model_config = ConfigDict(frozen=True)

    predicate: str
    args: tuple[Any, ...] = Field(default_factory=tuple)


class ThresholdConstraint(BaseModel):
    """From `logic_form` / head `threshold` or explicit body clauses."""

    model_config = ConfigDict(frozen=True)

    metric: str | None = None
    operator: str | None = None
    value: float | int | None = None
    unit: str | None = None
    raw_args: tuple[Any, ...] = Field(default_factory=tuple)


class DeadlineConstraint(BaseModel):
    """Temporal constraint from head/body/auxiliary `deadline` shapes."""

    model_config = ConfigDict(frozen=True)

    raw_args: tuple[Any, ...] = Field(default_factory=tuple)


class DossierConstraint(BaseModel):
    """Hồ sơ / thủ tục — tách khỏi điều kiện phủ định."""

    model_config = ConfigDict(frozen=True)

    procedure: str | None = None
    documents: tuple[Any, ...] = Field(default_factory=tuple)
    raw_args: tuple[Any, ...] = Field(default_factory=tuple)


class ThresholdNoteConstraint(BaseModel):
    """Body predicate `threshold_note` — giữ nguyên args gốc."""

    model_config = ConfigDict(frozen=True)

    raw_args: tuple[Any, ...] = Field(default_factory=tuple)


class AuxiliaryRecord(BaseModel):
    """Phần tử `auxiliary_clauses` sau khi chuẩn hóa."""

    model_config = ConfigDict(frozen=True)

    kind: str | None = None
    head: Atom | None = None
    body_atoms: tuple[Atom, ...] = Field(default_factory=tuple)


class ReasoningRule(BaseModel):
    """
    Rule thuần cho reasoner: tách positive / negative / exception / constraint / auxiliary.
    `goal_atom` = (head.predicate, *head.args) — không đổi vocabulary gốc.
    """

    model_config = ConfigDict(frozen=True)

    rule_id: str
    logic_form: str
    goal_atom: tuple[Any, ...]
    positive_conditions: tuple[Atom, ...] = Field(default_factory=tuple)
    negative_conditions: tuple[Atom, ...] = Field(default_factory=tuple)
    exception_conditions: tuple[Atom, ...] = Field(default_factory=tuple)
    constraints: tuple[Any, ...] = Field(default_factory=tuple)
    auxiliary_outputs: tuple[AuxiliaryRecord, ...] = Field(default_factory=tuple)
    source_ref: str | None = None
    source_ref_full: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
