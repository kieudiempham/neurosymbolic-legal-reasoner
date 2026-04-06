"""Validator for domain-agnostic legal frames."""

from __future__ import annotations

from typing import Any

from schemas.legal_frame_v2 import GenericLegalFrame


_REQUIRED_SLOTS: dict[str, list[str]] = {
    "obligation": ["subject", "predicate"],
    "permission": ["subject", "predicate"],
    "prohibition": ["subject", "predicate"],
    "procedure": ["subject", "predicate"],
    "document_requirement": ["subject", "document"],
    "deadline": ["subject", "deadline"],
    "condition": ["condition"],
    "exception": ["exception"],
    "legal_effect": ["predicate", "object"],
    "authority_action": ["authority", "predicate"],
    "threshold": ["threshold"],
}


def validate_generic_frame(frame: GenericLegalFrame) -> tuple[bool, list[str]]:
    """Validate generic frame slots and return status plus diagnostics."""
    errors: list[str] = []
    required = _REQUIRED_SLOTS.get(frame.frame_type, [])
    for slot in required:
        value = getattr(frame, slot, None)
        if not value:
            errors.append(f"missing_required_slot:{slot}")

    if frame.frame_type in {"deadline", "threshold"} and frame.deadline is None and frame.threshold is None:
        errors.append("missing_temporal_threshold_value")

    if frame.frame_type == "authority_action" and frame.authority is not None:
        if len(frame.authority.strip()) < 4:
            errors.append("authority_too_short")

    if frame.subject is not None and len(frame.subject.strip()) < 3:
        errors.append("subject_too_short")
    if frame.predicate is not None and len(frame.predicate.strip()) < 4:
        errors.append("predicate_too_short")

    if frame.frame_type == "document_requirement" and frame.document is None:
        errors.append("document_requirement_missing_document")

    return len(errors) == 0, errors


def frame_to_dict(frame: GenericLegalFrame) -> dict[str, Any]:
    return frame.model_dump()
