"""Lightweight entity mentions + role linking (not production NER)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


class EntityMention(BaseModel):
    surface: str = ""
    start: int = 0
    end: int = 0
    role_guess: str = "unknown"


class EntityRecord(BaseModel):
    entity_id: str
    entity_role: str
    mention_texts: list[str] = Field(default_factory=list)
    owner_entity_id: str | None = None
    confidence: float = 0.75


class EntityRegistry(BaseModel):
    """Session-scoped registry; stable IDs for pipeline stages."""

    records: dict[str, EntityRecord] = Field(default_factory=dict)
    primary_subject_id: str = "company_x"

    def register(self, rec: EntityRecord) -> None:
        self.records[rec.entity_id] = rec

    def link_mentions(self, text: str) -> list[EntityMention]:
        if not text.strip():
            return []
        mentions: list[EntityMention] = []
        patterns: list[tuple[str, str]] = [
            (r"(?i)(công ty|cong ty|doanh nghiệp|doanh nghiep)[^?.]{0,40}", "company"),
            (r"(?i)(cổ đông|co dong)[^?.]{0,30}", "shareholder"),
            (r"(?i)(người đại diện|dai dien|đại diện pháp luật)[^?.]{0,40}", "legal_representative"),
            (r"(?i)(hộ kinh doanh|ho kinh doanh)[^?.]{0,30}", "business_household"),
            (r"(?i)(nhà đầu tư|nha dau tu|sáng lập|sang lap)[^?.]{0,30}", "founder"),
            (r"(?i)(cơ quan|co quan|sở kế hoạch)[^?.]{0,30}", "authority"),
        ]
        for pat, role in patterns:
            for m in re.finditer(pat, text):
                mentions.append(
                    EntityMention(surface=m.group(0).strip()[:120], start=m.start(), end=m.end(), role_guess=role)
                )
        return mentions


_ROLE_TO_ID = {
    "company": "company_x",
    "enterprise": "enterprise_x",
    "shareholder": "shareholder_x",
    "legal_representative": "legal_representative_x",
    "founder": "founder_x",
    "business_household": "business_household_x",
    "authority": "authority_body_x",
}


def resolve_subject_entity(
    layer1_blob: str,
    *,
    registry: EntityRegistry | None = None,
) -> tuple[str, str, EntityRegistry, list[EntityMention]]:
    """
    Returns (entity_id, role, registry, mentions).
    Source of truth for subject_normalized when using registry path.
    """
    reg = registry or EntityRegistry()
    mentions = reg.link_mentions(layer1_blob)
    if not mentions:
        eid = "company_x"
        role = "company"
        reg.register(
            EntityRecord(
                entity_id=eid,
                entity_role=role,
                mention_texts=[layer1_blob[:80]] if layer1_blob.strip() else [],
            )
        )
        reg.primary_subject_id = eid
        return eid, role, reg, []

    # Pick first non-authority as primary subject if possible
    prim = next((m for m in mentions if m.role_guess != "authority"), mentions[0])
    role = prim.role_guess
    eid = _ROLE_TO_ID.get(role, "company_x")
    reg.primary_subject_id = eid
    reg.register(
        EntityRecord(
            entity_id=eid,
            entity_role=role,
            mention_texts=[m.surface for m in mentions if m.role_guess == role][:5],
            confidence=0.82 if len(mentions) == 1 else 0.68,
        )
    )
    return eid, role, reg, mentions
