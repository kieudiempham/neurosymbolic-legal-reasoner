"""Serialize Pydantic models to JSON-compatible dicts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


def model_to_json_dict(model: BaseModel) -> dict[str, Any]:
    """Serialize using Pydantic v2 model_dump."""
    return model.model_dump(mode="json")
