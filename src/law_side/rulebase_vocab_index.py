"""
Load controlled_vocabulary.xlsx và map rule seed → canonical (in-memory only).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from law_side.controlled_vocabulary_builder import to_snake_id
from law_side.refine_controlled_vocabulary import split_effect_exception_condition


def _cell(v: Any) -> str | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    return s if s else None


@dataclass
class NormalizedVocab:
    predicate_family: str | None = None
    predicate_canonical: str | None = None
    predicate_typed: str | None = None
    object_canonical: str | None = None
    object_family: str | None = None
    effect_canonical: str | None = None
    effect_family: str | None = None
    subject_canonical: str | None = None
    subject_type_canonical: str | None = None
    authority_canonical: str | None = None
    scope_canonical: str | None = None
    metric_canonical: str | None = None
    unit_canonical: str | None = None
    normalization_status: str = "full"
    normalization_notes: list[str] = field(default_factory=list)


class VocabIndex:
    """Chỉ mục từ các sheet vocabulary để lookup theo slug."""

    def __init__(self, vocab_path: Path) -> None:
        xl = pd.ExcelFile(vocab_path)
        self._pred: dict[str, dict[str, Any]] = {}
        if "predicate_vocabulary" in xl.sheet_names:
            df = pd.read_excel(vocab_path, sheet_name="predicate_vocabulary")
            for _, r in df.iterrows():
                k = _cell(r.get("predicate_canonical"))
                if k:
                    self._pred[str(k).strip()] = r.to_dict()

        self._obj: dict[str, dict[str, Any]] = {}
        if "object_vocabulary" in xl.sheet_names:
            df = pd.read_excel(vocab_path, sheet_name="object_vocabulary")
            for _, r in df.iterrows():
                k = _cell(r.get("object_canonical"))
                if k:
                    self._obj[str(k).strip()] = r.to_dict()

        self._eff: dict[str, dict[str, Any]] = {}
        if "effect_vocabulary" in xl.sheet_names:
            df = pd.read_excel(vocab_path, sheet_name="effect_vocabulary")
            for _, r in df.iterrows():
                k = _cell(r.get("effect_canonical"))
                if k:
                    self._eff[str(k).strip()] = r.to_dict()

        self._ent: dict[tuple[str, str], dict[str, Any]] = {}
        if "subject_authority_scope" in xl.sheet_names:
            df = pd.read_excel(vocab_path, sheet_name="subject_authority_scope")
            for _, r in df.iterrows():
                kind = _cell(r.get("entity_kind"))
                name = _cell(r.get("canonical_name"))
                if kind and name:
                    self._ent[(kind, str(name).strip())] = r.to_dict()

        self._metric: dict[tuple[str, str], dict[str, Any]] = {}
        if "metric_vocabulary" in xl.sheet_names:
            df = pd.read_excel(vocab_path, sheet_name="metric_vocabulary")
            for _, r in df.iterrows():
                mc = _cell(r.get("metric_canonical")) or ""
                uc = _cell(r.get("unit_canonical")) or ""
                self._metric[(mc.strip(), uc.strip())] = r.to_dict()

        self._effect_fragment_originals: set[str] = set()
        self._object_fragment_originals: set[str] = set()
        if "modifier_fragments" in xl.sheet_names:
            mf = pd.read_excel(vocab_path, sheet_name="modifier_fragments")
            for _, r in mf.iterrows():
                oc = _cell(r.get("original_canonical"))
                sf = _cell(r.get("split_from"))
                if not oc:
                    continue
                slug = str(oc).strip()
                if sf and "effect" in str(sf).lower():
                    self._effect_fragment_originals.add(slug)
                if sf and "object" in str(sf).lower():
                    self._object_fragment_originals.add(slug)

    def lookup_predicate(self, slug: str | None) -> dict[str, Any] | None:
        if not slug:
            return None
        return self._pred.get(slug.strip())

    def lookup_object(self, slug: str | None) -> dict[str, Any] | None:
        if not slug:
            return None
        return self._obj.get(slug.strip())

    def lookup_effect(self, slug: str | None) -> dict[str, Any] | None:
        if not slug:
            return None
        s = slug.strip()
        if s in self._eff:
            return self._eff[s]
        base, _ = split_effect_exception_condition(s)
        if base != s and base in self._eff:
            return self._eff[base]
        return None

    def lookup_entity(self, kind: str, slug: str | None) -> dict[str, Any] | None:
        if not slug:
            return None
        return self._ent.get((kind, slug.strip()))

    def lookup_metric(self, metric_slug: str, unit_slug: str) -> dict[str, Any] | None:
        return self._metric.get((metric_slug.strip(), unit_slug.strip())) or self._metric.get(
            (metric_slug.strip(), "")
        )

    def is_blocked_object_slug(self, slug: str) -> bool:
        return slug.strip() in self._object_fragment_originals

    def is_blocked_effect_slug(self, slug: str) -> bool:
        return slug.strip() in self._effect_fragment_originals


def _typed_suffix(typed: str | None) -> str | None:
    if not typed:
        return None
    s = typed.strip()
    if ":" in s:
        return s.split(":", 1)[-1].strip()
    return s


def normalize_row_with_vocab(row: pd.Series, idx: VocabIndex) -> NormalizedVocab:
    out = NormalizedVocab()
    notes: list[str] = []

    cp = _cell(row.get("canonical_predicate"))
    hv = _cell(row.get("hanh_vi_phap_ly"))
    tp = _cell(row.get("typed_predicate"))
    slug_cp = to_snake_id(cp) if cp else None
    slug_hv = to_snake_id(hv) if hv else None
    slug_tp = None
    if tp:
        tail = _typed_suffix(tp) or tp
        slug_tp = to_snake_id(tail)

    pred_hit = None
    for candidate in (slug_cp, slug_tp, slug_hv):
        if candidate:
            pred_hit = idx.lookup_predicate(candidate)
            if pred_hit:
                break
    if pred_hit:
        out.predicate_family = _cell(pred_hit.get("predicate_family"))
        out.predicate_canonical = _cell(pred_hit.get("predicate_canonical"))
        out.predicate_typed = _cell(pred_hit.get("predicate_typed"))
    else:
        notes.append("predicate_fallback")
        out.normalization_status = "partial"

    dt = _cell(row.get("doi_tuong_hanh_vi"))
    slug_dt = to_snake_id(dt) if dt else None
    if slug_dt and idx.is_blocked_object_slug(slug_dt):
        notes.append("object_slug_was_split_fragment")
        slug_dt = None
    obj_hit = idx.lookup_object(slug_dt) if slug_dt else None
    if obj_hit:
        out.object_canonical = _cell(obj_hit.get("object_canonical"))
        out.object_family = _cell(obj_hit.get("object_family"))
    elif slug_dt:
        notes.append("object_unmapped")
        out.normalization_status = "partial"

    he = _cell(row.get("he_qua_phap_ly"))
    kt = _cell(row.get("ket_qua_thu_tuc"))
    eff_slug = None
    for text in (he, kt):
        if not text:
            continue
        s = to_snake_id(text)
        if idx.is_blocked_effect_slug(s):
            base, _ = split_effect_exception_condition(s)
            s = base
            notes.append("effect_used_base_after_fragment_match")
        eff_slug = s
        eff_hit = idx.lookup_effect(s)
        if eff_hit:
            out.effect_canonical = _cell(eff_hit.get("effect_canonical"))
            out.effect_family = _cell(eff_hit.get("effect_family"))
            break
    if he or kt:
        if not out.effect_canonical:
            notes.append("effect_unmapped")
            out.normalization_status = "partial"

    chu = _cell(row.get("chu_the"))
    if chu:
        s_chu = to_snake_id(chu)
        ehit = idx.lookup_entity("subject", s_chu)
        if ehit:
            out.subject_canonical = _cell(ehit.get("canonical_name"))
        else:
            notes.append("subject_unmapped")
            out.normalization_status = "partial"

    lct = _cell(row.get("loai_chu_the"))
    if lct:
        s_l = to_snake_id(lct)
        ehit = idx.lookup_entity("subject_type", s_l)
        if ehit:
            out.subject_type_canonical = _cell(ehit.get("canonical_name"))
        else:
            notes.append("subject_type_unmapped")
            out.normalization_status = "partial"

    cqx = _cell(row.get("co_quan_xu_ly"))
    cqt = _cell(row.get("co_quan_tiep_nhan"))
    for raw, kind in ((cqx, "authority"), (cqt, "authority")):
        if not raw:
            continue
        s = to_snake_id(raw)
        ehit = idx.lookup_entity("authority", s)
        if ehit:
            out.authority_canonical = _cell(ehit.get("canonical_name"))
            break
    if (cqx or cqt) and not out.authority_canonical:
        notes.append("authority_unmapped")
        out.normalization_status = "partial"

    pv = _cell(row.get("pham_vi_ap_dung"))
    if pv:
        s_pv = to_snake_id(pv)
        ehit = idx.lookup_entity("scope", s_pv)
        if ehit:
            out.scope_canonical = _cell(ehit.get("canonical_name"))
        else:
            notes.append("scope_unmapped")
            out.normalization_status = "partial"

    ten = _cell(row.get("ten_chi_so"))
    du = _cell(row.get("don_vi_nguong"))
    slug_m = to_snake_id(ten) if ten else ""
    slug_u = to_snake_id(du) if du else ""
    if ten or du:
        mh = idx.lookup_metric(slug_m, slug_u)
        if mh:
            out.metric_canonical = _cell(mh.get("metric_canonical"))
            out.unit_canonical = _cell(mh.get("unit_canonical"))
        else:
            notes.append("metric_unmapped")
            out.normalization_status = "partial"

    if out.normalization_status == "full" and notes:
        out.normalization_status = "partial"
    out.normalization_notes = notes
    return out


__all__ = ["VocabIndex", "NormalizedVocab", "normalize_row_with_vocab"]
