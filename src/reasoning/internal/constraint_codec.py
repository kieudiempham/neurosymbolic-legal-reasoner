"""Stable session keys for structured constraints (không dùng làm source of truth chính — `Atom` mới là)."""

from __future__ import annotations

from typing import Any

from reasoning.internal.models import (
    DeadlineConstraint,
    DossierConstraint,
    ThresholdConstraint,
    ThresholdNoteConstraint,
)


def serialize_constraint_session_key(c: Any) -> str:
    """Một khóa duy nhất cho `known_facts` / missing_facts khi cần boundary string."""
    if isinstance(c, ThresholdConstraint):
        m = c.metric or ""
        o = c.operator or ""
        v = c.value if c.value is not None else ""
        u = c.unit or ""
        return f"constraint:threshold:{m}:{o}:{v}:{u}"
    if isinstance(c, DeadlineConstraint):
        inner = ",".join(str(x) for x in c.raw_args)
        return f"constraint:deadline:{inner}"
    if isinstance(c, DossierConstraint):
        inner = ",".join(str(x) for x in c.raw_args)
        return f"constraint:dossier:{inner}"
    if isinstance(c, ThresholdNoteConstraint):
        inner = ",".join(str(x) for x in c.raw_args)
        return f"constraint:threshold_note:{inner}"
    return f"constraint:other:{type(c).__name__}"
