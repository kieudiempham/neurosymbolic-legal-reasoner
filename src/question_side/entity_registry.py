"""Lightweight entity mentions + role linking (not production NER)."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field


_MENTION_CUT_CUES = (
    " nếu ",
    " khi ",
    " mà ",
    " để ",
    " theo ",
    " do ",
    ",",
    ";",
    ":",
    "?",
    "!",
)


def _clean_mention_surface(surface: str) -> str:
    text = " ".join((surface or "").strip().split())
    if not text:
        return ""
    low = f" {text.lower()} "
    cut_idx = len(text)
    for cue in _MENTION_CUT_CUES:
        pos = low.find(cue)
        if pos > 0:
            cut_idx = min(cut_idx, max(0, pos - 1))
    text = text[:cut_idx].strip(" .,;:?!-\"'()[]{}")
    text = re.sub(r"\s+", " ", text)
    if len(text) < 3:
        return ""
    if not re.search(r"[A-Za-zÀ-ỹà-ỹ]", text):
        return ""
    return text[:72]


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
    primary_subject_id: str = "unknown_subject_x"

    def register(self, rec: EntityRecord) -> None:
        self.records[rec.entity_id] = rec

    def link_mentions(self, text: str) -> list[EntityMention]:
        if not text.strip():
            return []
        mentions: list[EntityMention] = []
        patterns: list[tuple[str, str]] = [
            (r"(?i)(doanh nghiệp cho thuê lại lao động|doanh nghiep cho thue lai lao dong)[^?.]{0,40}", "labor_leasing_enterprise"),
            (r"(?i)(người sử dụng lao động|nguoi su dung lao dong|bên sử dụng lao động|ben su dung lao dong)[^?.]{0,40}", "employer"),
            (r"(?i)(người lao động|nguoi lao dong)[^?.]{0,40}", "employee"),
            (r"(?i)(người nộp thuế|nguoi nop thue|người đóng thuế|nguoi dong thue|người chịu thuế|nguoi chiu thue)[^?.]{0,40}", "taxpayer"),
            (r"(?i)(hộ kinh doanh|ho kinh doanh)[^?.]{0,30}", "business_household"),
            (r"(?i)(công ty|cong ty|doanh nghiệp|doanh nghiep)[^?.]{0,40}", "company"),
            (r"(?i)(thành viên|thanh vien)(?:\s+công ty|\s+cong ty)?[^?.]{0,40}", "member"),
            (r"(?i)(cổ đông|co dong)[^?.]{0,30}", "shareholder"),
            (r"(?i)(người đại diện|dai dien|đại diện pháp luật)[^?.]{0,40}", "legal_representative"),
            (r"(?i)(nhà đầu tư|nha dau tu|sáng lập|sang lap)[^?.]{0,30}", "founder"),
            (r"(?i)(cơ quan|co quan|sở kế hoạch)[^?.]{0,30}", "authority"),
        ]
        for pat, role in patterns:
            for m in re.finditer(pat, text):
                cleaned = _clean_mention_surface(m.group(0))
                if not cleaned:
                    continue
                mentions.append(
                    EntityMention(surface=cleaned, start=m.start(), end=m.end(), role_guess=role)
                )
        if not mentions:
            return []

        mentions.sort(key=lambda x: (x.start, x.end - x.start, _ROLE_PRIORITY.get(x.role_guess, 10)))
        deduped: list[EntityMention] = []
        seen: set[tuple[str, int]] = set()
        for m in mentions:
            key = (m.surface.lower(), m.start)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(m)
        return deduped


ACTOR_ROLE_TO_ENTITY_ID = {
    "company": "company_x",
    "enterprise": "enterprise_x",
    "employer": "employer_x",
    "employee": "employee_x",
    "labor_leasing_enterprise": "labor_leasing_enterprise_x",
    "taxpayer": "taxpayer_x",
    "member": "member_x",
    "shareholder": "shareholder_x",
    "legal_representative": "legal_representative_x",
    "founder": "founder_x",
    "business_household": "business_household_x",
    "authority": "authority_body_x",
    "unknown": "unknown_subject_x",
}


_ROLE_PRIORITY = {
    "employer": 1,
    "employee": 1,
    "labor_leasing_enterprise": 1,
    "taxpayer": 2,
    "business_household": 2,
    "enterprise": 3,
    "company": 3,
    "member": 4,
    "shareholder": 4,
    "legal_representative": 5,
    "founder": 5,
    "authority": 9,
    "unknown": 10,
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
        low = layer1_blob.lower()
        if "doanh nghiệp" in low or "doanh nghiep" in low or "công ty" in low or "cong ty" in low:
            eid = "enterprise_x"
            role = "enterprise"
        else:
            eid = "unknown_subject_x"
            role = "unknown"
        reg.register(
            EntityRecord(
                entity_id=eid,
                entity_role=role,
                mention_texts=[layer1_blob[:80]] if layer1_blob.strip() else [],
            )
        )
        reg.primary_subject_id = eid
        return eid, role, reg, []

    # Prefer strongest legal actor role, then earliest mention.
    prim = min(mentions, key=lambda m: (_ROLE_PRIORITY.get(m.role_guess, 10), m.start))
    role = prim.role_guess
    eid = ACTOR_ROLE_TO_ENTITY_ID.get(role, "unknown_subject_x")
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
