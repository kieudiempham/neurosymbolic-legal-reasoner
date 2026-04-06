"""Canonical legal frame schema for Stage 3 multi-domain extraction."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


GENERIC_FRAME_TYPES = (
    "obligation",
    "permission",
    "prohibition",
    "procedure",
    "document_requirement",
    "deadline",
    "condition",
    "exception",
    "legal_effect",
    "authority_action",
    "threshold",
)


class GenericLegalFrame(BaseModel):
    """A normalized, domain-agnostic legal frame for multi-rule construction."""

    frame_id: str
    source_doc_id: str
    source_ref: str | None = None
    raw_text: str | None = None
    frame_type: Literal[
        "obligation",
        "permission",
        "prohibition",
        "procedure",
        "document_requirement",
        "deadline",
        "condition",
        "exception",
        "legal_effect",
        "authority_action",
        "threshold",
    ]
    subject: str | None = None
    predicate: str | None = None
    object: str | None = None
    authority: str | None = None
    condition: str | None = None
    exception: str | None = None
    deadline: str | None = None
    threshold: str | None = None
    document: str | None = None
    sanction: str | None = None
    modality: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='before')
    @classmethod
    def check_frame_type_valid(cls, values: dict[str, Any]) -> dict[str, Any]:
        frame_type = values.get("frame_type")
        if frame_type not in GENERIC_FRAME_TYPES:
            raise ValueError(f"Unknown generic frame_type: {frame_type}")
        return values

    class Config:
        validate_assignment = True
        anystr_strip_whitespace = True
        json_schema_extra = {
            "example": {
                "frame_id": "ENT_001",
                "source_doc_id": "DOC_LUAT_DOANH_NGHIEP_67",
                "source_ref": "Luật DN, Điều 10, Khoản 1",
                "raw_text": "Doanh nghiệp phải đăng ký thay đổi nội dung đăng ký trong 15 ngày",
                "frame_type": "obligation",
                "subject": "doanh nghiệp",
                "predicate": "đăng ký thay đổi nội dung đăng ký",
                "object": "thay đổi nội dung đăng ký",
                "authority": "cơ quan đăng ký kinh doanh",
                "condition": "nếu doanh nghiệp thay đổi thông tin",
                "deadline": "15 ngày",
                "modality": "obligation",
                "meta": {"domain": "enterprise", "layer": "statute"},
            }
        }
