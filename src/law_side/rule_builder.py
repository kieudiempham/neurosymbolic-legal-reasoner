"""Rule seed construction from enriched legal frames (precision-first, answer-ready)."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from law_side.legal_frame_fanout_enricher import extract_ket_qua_variants
from law_side.law_rulebase_models import LegalFrame, RuleSeed
from law_side.predicate_normalizer import normalize_surface_to_predicate
from utils.ids import stable_hash
from utils.logger import get_logger


class RuleBuilder:
    """Convert extracted legal frames into atomic, reviewable rule seeds."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}
        self._log = get_logger(self.__class__.__name__)

    def build(
        self,
        frames: list[LegalFrame],
        *,
        action_surface_to_normalized: dict[str, str] | None = None,
        unit_meta: dict[str, dict[str, str]] | None = None,
        predicate_meta: dict[str, dict[str, str]] | None = None,
    ) -> list[RuleSeed]:
        """Build rule seeds from enriched frames.

        - action_surface_to_normalized: surface_form -> hanh_vi_chuan_chi_tiet (preferred), fallback normalize_surface_to_predicate
        - unit_meta: unit_id -> {heading, parent_context, source_ref_full, doc_code}
        - predicate_meta: hanh_vi_chuan_chi_tiet -> {hanh_vi_chuan, nhom_hanh_vi, ghi_chu_ap_dung, ...}
        """
        action_surface_to_normalized = action_surface_to_normalized or {}
        unit_meta = unit_meta or {}
        predicate_meta = predicate_meta or {}

        seeds: list[RuleSeed] = []
        global_emit_seq = {"n": 0}
        for frame in frames:
            seeds.extend(
                self._build_for_frame(
                    frame,
                    action_surface_to_normalized=action_surface_to_normalized,
                    unit_meta=unit_meta.get((frame.source_unit_id or "").strip(), {}),
                    predicate_meta=predicate_meta,
                    global_emit_seq=global_emit_seq,
                )
            )
        raw_ct = len(seeds)
        seeds = self._deduplicate_rules(seeds)
        self._log.info("Built %d rule seeds (pre-dedup %d)", len(seeds), raw_ct)
        return seeds

    def _normalize_action(
        self,
        action_surface: str | None,
        action_surface_to_normalized: dict[str, str],
    ) -> str | None:
        if not action_surface:
            return None
        if action_surface in action_surface_to_normalized:
            return self._reduce_action_to_core(action_surface_to_normalized[action_surface])
        return self._reduce_action_to_core(normalize_surface_to_predicate(action_surface))

    def _bieu_thuc_dieu_kien(self, cond_text: str | None) -> str:
        if not cond_text:
            return ""
        parts = [self._to_snake_vi(c.strip()) for c in str(cond_text).split(";") if c and c.strip()]
        cleaned = [p for p in parts if p and len(p) >= 8 and not p.startswith(("theo_", "voi_", "den_"))]
        return " && ".join(cleaned[:3])

    def _build_for_frame(
        self,
        frame: LegalFrame,
        *,
        action_surface_to_normalized: dict[str, str],
        unit_meta: dict[str, str],
        predicate_meta: dict[str, dict[str, str]],
        global_emit_seq: dict[str, int] | None = None,
    ) -> list[RuleSeed]:
        if not self._frame_is_usable(frame):
            return []

        _ges = global_emit_seq if global_emit_seq is not None else {"n": 0}

        def _clean(v: Any) -> str:
            if v is None:
                return ""
            s = str(v).strip()
            return "" if s.lower() == "nan" else s

        chu_the = _clean(frame.chu_the or frame.subject_type)
        if not chu_the or chu_the.lower() == "unknown":
            return []

        hanh_vi_surface = _clean(frame.hanh_vi or frame.action_predicate) or None
        canonical_pred = self._normalize_action(hanh_vi_surface, action_surface_to_normalized) or ""
        if not canonical_pred:
            # Still allow dossier/deadline-only frames to create rules.
            canonical_pred = self._reduce_action_to_core(normalize_surface_to_predicate(hanh_vi_surface or "")) or ""

        nhom = ""
        pred_family = ""
        if canonical_pred and canonical_pred in predicate_meta:
            pred_family = predicate_meta[canonical_pred].get("nhom_hanh_vi", "") or ""
            nhom = predicate_meta[canonical_pred].get("hanh_vi_chuan", "") or ""

        doc_code = _clean(frame.doc_code or unit_meta.get("doc_code"))
        source_ref_full = _clean(frame.unit_ref_full or unit_meta.get("source_ref_full"))
        heading = _clean(getattr(frame, "heading", "") or "") or _clean(unit_meta.get("heading"))
        parent_context = _clean(getattr(frame, "parent_context", "") or "") or _clean(unit_meta.get("parent_context"))
        source_text = _clean(frame.source_text)

        bieu_thuc_dk = self._bieu_thuc_dieu_kien(_clean(frame.dieu_kien_ap_dung or frame.condition_predicates))
        dieu_kien_ap_dung = _clean(frame.dieu_kien_ap_dung or frame.condition_predicates)

        # Grouping: one legal "cluster" per frame.
        rule_group_id = self._make_rule_group_id(doc_code=doc_code, source_ref_full=source_ref_full, canonical_predicate=canonical_pred, frame_id=frame.frame_id)

        # Reliability + review flags
        muc_do_day_du = _clean(frame.muc_do_day_du) or "thieu_vai_slot"
        do_tin_cay = self._do_tin_cay_trich_xuat(frame)
        can_ra_soat, ly_do = self._review_flags(frame, canonical_predicate=canonical_pred)

        # Common base dict
        base = dict(
            rule_group_id=rule_group_id,
            frame_id=frame.frame_id,
            candidate_id=str(frame.candidate_id or "").strip(),
            source_unit_id=str(frame.source_unit_id or "").strip(),
            doc_id=frame.doc_id,
            doc_code=doc_code,
            source_ref=(frame.source_ref or "").strip(),
            source_ref_full=source_ref_full,
            heading=heading,
            parent_context=parent_context,
            source_text=source_text,
            chu_the=chu_the,
            loai_chu_the=self._loai_chu_the(chu_the),
            vai_tro_chu_the=(frame.vai_tro_chu_the or frame.subject_role or "").strip() or "chu_the_thuc_hien",
            dieu_kien_ap_dung=dieu_kien_ap_dung,
            bieu_thuc_dieu_kien=bieu_thuc_dk,
            muc_do_day_du=muc_do_day_du,
            do_tin_cay_trich_xuat=do_tin_cay,
            can_ra_soat=can_ra_soat,
            ly_do_can_ra_soat=ly_do,
            extraction_pattern=self._extraction_pattern(frame),
        )

        rules: list[RuleSeed] = []
        _rid_seq = {"i": 0}
        _row_pin = "|".join(
            [
                (frame.frame_id or "").strip(),
                (frame.candidate_id or "").strip(),
                (frame.source_unit_id or "").strip(),
                (frame.frame_type or "").strip(),
            ]
        )
        _row_h = stable_hash(_row_pin or (frame.frame_id or "FR"), n=12)

        def _rid(kfrag: str) -> str:
            _rid_seq["i"] += 1
            _ges["n"] += 1
            frag = f"E{_ges['n']:06d}_H{_row_h}_{kfrag}_S{_rid_seq['i']}"
            return self._make_rule_id(doc_code=doc_code, source_ref_full=source_ref_full, key=frag)

        # 1) Main action rule (obligation/permission/prohibition/procedure/authority_action)
        if hanh_vi_surface:
            rule_type = self._rule_type_for_frame(frame.frame_type)
            typed_pred = f"{rule_type}:{canonical_pred}" if canonical_pred else rule_type
            rule_id = _rid(canonical_pred or self._to_snake_vi(hanh_vi_surface)[:40] or "MAIN")
            tinh_chat = (frame.tinh_chat_phap_ly or "").strip() or self._tinh_chat_fallback(frame.frame_type)
            hanh_vi_phap_ly = (frame.hanh_vi or frame.action_predicate or "").strip()
            he_qua = (frame.ket_qua_thu_tuc or frame.legal_effect or "").strip()

            answer_t = self._answer_template(rule_type, base, hanh_vi_phap_ly=hanh_vi_phap_ly)
            expl_t = self._explanation_template(base)
            summary = self._grounded_summary(rule_type, base, hanh_vi_phap_ly=hanh_vi_phap_ly)

            rules.append(
                RuleSeed(
                    rule_id=rule_id,
                    **base,
                    rule_type=rule_type,
                    tinh_chat_phap_ly=tinh_chat,
                    canonical_predicate=canonical_pred,
                    typed_predicate=typed_pred,
                    predicate_family=pred_family or nhom,
                    hanh_vi_phap_ly=hanh_vi_phap_ly,
                    doi_tuong_hanh_vi=(frame.doi_tuong_hanh_vi or "").strip(),
                    he_qua_phap_ly=he_qua,
                    # quantitative
                    ten_chi_so="",
                    toan_tu_so_sanh="",
                    gia_tri_nguong="",
                    don_vi_nguong="",
                    gia_tri_tu="",
                    gia_tri_den="",
                    kieu_khoang="",
                    # deadline
                    thoi_han_so=str(frame.thoi_han_so or "").strip(),
                    don_vi_thoi_han=str(frame.don_vi_thoi_han or "").strip(),
                    moc_tinh_thoi_han=str(frame.moc_tinh_thoi_han or "").strip(),
                    bieu_thuc_thoi_han=self._bieu_thuc_thoi_han(frame),
                    # procedure/dossier/authority
                    thanh_phan_ho_so=str(frame.thanh_phan_ho_so or "").strip(),
                    co_quan_tiep_nhan=str(frame.co_quan_tiep_nhan or "").strip(),
                    co_quan_xu_ly=str(frame.co_quan_xu_ly or "").strip(),
                    ket_qua_thu_tuc=str(frame.ket_qua_thu_tuc or "").strip(),
                    phuong_thuc_thuc_hien="",
                    # scope/exception/ref
                    pham_vi_ap_dung="",
                    ngoai_le=(frame.ngoai_le or "").strip(),
                    van_ban_dan_chieu=(frame.van_ban_dan_chieu or "").strip(),
                    # answer/explain
                    answer_template=answer_t,
                    explanation_template=expl_t,
                    grounded_summary=summary,
                    notes="rule_main",
                )
            )

        # 2) Deadline rule
        if _clean(frame.thoi_han_so):
            rule_type = "quy_tac_thoi_han"
            key = f"THOI_HAN_{str(frame.thoi_han_so).strip()}_{str(frame.don_vi_thoi_han or '').strip()}".strip("_")
            rule_id = _rid(key)
            answer_t = self._answer_template(rule_type, base, hanh_vi_phap_ly=(frame.hanh_vi or "").strip())
            rules.append(
                RuleSeed(
                    rule_id=rule_id,
                    **base,
                    rule_type=rule_type,
                    tinh_chat_phap_ly="bat_buoc",
                    canonical_predicate=canonical_pred,
                    typed_predicate=f"{rule_type}:{canonical_pred}" if canonical_pred else rule_type,
                    predicate_family=pred_family or nhom,
                    hanh_vi_phap_ly=(frame.hanh_vi or frame.action_predicate or "").strip(),
                    doi_tuong_hanh_vi=(frame.doi_tuong_hanh_vi or "").strip(),
                    he_qua_phap_ly="",
                    ten_chi_so="",
                    toan_tu_so_sanh="",
                    gia_tri_nguong="",
                    don_vi_nguong="",
                    gia_tri_tu="",
                    gia_tri_den="",
                    kieu_khoang="",
                    thoi_han_so=_clean(frame.thoi_han_so),
                    don_vi_thoi_han=_clean(frame.don_vi_thoi_han),
                    moc_tinh_thoi_han=_clean(frame.moc_tinh_thoi_han),
                    bieu_thuc_thoi_han=self._bieu_thuc_thoi_han(frame),
                    thanh_phan_ho_so="",
                    co_quan_tiep_nhan=str(frame.co_quan_tiep_nhan or "").strip(),
                    co_quan_xu_ly=str(frame.co_quan_xu_ly or "").strip(),
                    ket_qua_thu_tuc="",
                    phuong_thuc_thuc_hien="",
                    pham_vi_ap_dung="",
                    ngoai_le=(frame.ngoai_le or "").strip(),
                    van_ban_dan_chieu=(frame.van_ban_dan_chieu or "").strip(),
                    answer_template=answer_t,
                    explanation_template=self._explanation_template(base),
                    grounded_summary=self._grounded_summary(rule_type, base, hanh_vi_phap_ly=(frame.hanh_vi or "").strip()),
                    notes="rule_deadline",
                )
            )

        # 3) Dossier rule(s) — split `;` list into separate seeds for fan-out
        raw_tp = _clean(frame.thanh_phan_ho_so)
        if raw_tp:
            parts = [p.strip() for p in raw_tp.split(";") if p.strip() and len(p.strip()) >= 5]
            if len(parts) <= 1 and raw_tp.count(",") >= 2 and len(raw_tp) > 55:
                alt = [p.strip() for p in raw_tp.split(",") if p.strip() and len(p.strip()) >= 10]
                if len(alt) >= 3:
                    parts = alt[:18]
            if not parts:
                parts = [raw_tp]
            rule_type = "quy_tac_ho_so"
            for j, item in enumerate(parts[:15]):
                hkey = f"HO_SO_{j}_{stable_hash(item, n=6)}" if len(parts) > 1 else "HO_SO"
                rule_id = _rid(hkey)
                rules.append(
                    RuleSeed(
                        rule_id=rule_id,
                        **base,
                        rule_type=rule_type,
                        tinh_chat_phap_ly="bat_buoc",
                        canonical_predicate=canonical_pred,
                        typed_predicate=f"{rule_type}:{canonical_pred}" if canonical_pred else rule_type,
                        predicate_family="nop_ho_so",
                        hanh_vi_phap_ly="chuẩn bị hồ sơ",
                        doi_tuong_hanh_vi="hồ sơ",
                        he_qua_phap_ly="",
                        ten_chi_so="",
                        toan_tu_so_sanh="",
                        gia_tri_nguong="",
                        don_vi_nguong="",
                        gia_tri_tu="",
                        gia_tri_den="",
                        kieu_khoang="",
                        thoi_han_so="",
                        don_vi_thoi_han="",
                        moc_tinh_thoi_han="",
                        bieu_thuc_thoi_han="",
                        thanh_phan_ho_so=item,
                        co_quan_tiep_nhan=str(frame.co_quan_tiep_nhan or "").strip(),
                        co_quan_xu_ly=str(frame.co_quan_xu_ly or "").strip(),
                        ket_qua_thu_tuc="",
                        phuong_thuc_thuc_hien="",
                        pham_vi_ap_dung="",
                        ngoai_le=(frame.ngoai_le or "").strip(),
                        van_ban_dan_chieu=(frame.van_ban_dan_chieu or "").strip(),
                        answer_template="Hồ sơ gồm: {thanh_phan_ho_so}.",
                        explanation_template=self._explanation_template(base),
                        grounded_summary=f"Hồ sơ gồm: {item}."[:380],
                        notes="rule_dossier_split" if len(parts) > 1 else "rule_dossier",
                    )
                )

        # 4) Exception rule(s)
        raw_ne = _clean(frame.ngoai_le)
        if raw_ne:
            ne_parts = [p.strip() for p in raw_ne.split(";") if p.strip() and len(p.strip()) > 12]
            if len(ne_parts) <= 1:
                ne_parts = [raw_ne]
            rule_type = "quy_tac_ngoai_le"
            for j, ne_item in enumerate(ne_parts[:10]):
                ekey = f"NGOAI_LE_{j}_{stable_hash(ne_item, n=6)}" if len(ne_parts) > 1 else "NGOAI_LE"
                rule_id = _rid(ekey)
                bm = dict(base)
                rules.append(
                    RuleSeed(
                        rule_id=rule_id,
                        **bm,
                        rule_type=rule_type,
                        tinh_chat_phap_ly="co_the",
                        canonical_predicate=canonical_pred,
                        typed_predicate=f"{rule_type}:{canonical_pred}" if canonical_pred else rule_type,
                        predicate_family="ngoai_le",
                        hanh_vi_phap_ly="áp dụng ngoại lệ",
                        doi_tuong_hanh_vi="",
                        he_qua_phap_ly="",
                        ten_chi_so="",
                        toan_tu_so_sanh="",
                        gia_tri_nguong="",
                        don_vi_nguong="",
                        gia_tri_tu="",
                        gia_tri_den="",
                        kieu_khoang="",
                        thoi_han_so="",
                        don_vi_thoi_han="",
                        moc_tinh_thoi_han="",
                        bieu_thuc_thoi_han="",
                        thanh_phan_ho_so="",
                        co_quan_tiep_nhan="",
                        co_quan_xu_ly="",
                        ket_qua_thu_tuc="",
                        phuong_thuc_thuc_hien="",
                        pham_vi_ap_dung="",
                        ngoai_le=ne_item,
                        van_ban_dan_chieu=_clean(frame.van_ban_dan_chieu),
                        answer_template="Ngoại lệ: {ngoai_le}.",
                        explanation_template=self._explanation_template(base),
                        grounded_summary=f"Ngoại lệ: {ne_item}."[:380],
                        notes="rule_exception_split" if len(ne_parts) > 1 else "rule_exception",
                    )
                )

        # 5) Quantitative threshold rule
        if _clean(getattr(frame, "nguong_so_luong", None)) or _clean(getattr(frame, "nguong_ty_le", None)) or _clean(getattr(frame, "khoang_gia_tri", None)):
            rule_type = "quy_tac_nguong_dinh_luong"
            rule_id = _rid("NGUONG_DINH_LUONG")
            raw = _clean(frame.dieu_kien_dinh_luong or frame.nguong_so_luong or frame.nguong_ty_le or frame.khoang_gia_tri)
            rules.append(
                RuleSeed(
                    rule_id=rule_id,
                    **base,
                    rule_type=rule_type,
                    tinh_chat_phap_ly="bat_buoc",
                    canonical_predicate=canonical_pred,
                    typed_predicate=f"{rule_type}:{canonical_pred}" if canonical_pred else rule_type,
                    predicate_family="nguong_dinh_luong",
                    hanh_vi_phap_ly=(frame.hanh_vi or "").strip(),
                    doi_tuong_hanh_vi=(frame.doi_tuong_hanh_vi or "").strip(),
                    he_qua_phap_ly="",
                    ten_chi_so="",
                    toan_tu_so_sanh="",
                    gia_tri_nguong="",
                    don_vi_nguong="",
                    gia_tri_tu="",
                    gia_tri_den="",
                    kieu_khoang="",
                    thoi_han_so="",
                    don_vi_thoi_han="",
                    moc_tinh_thoi_han="",
                    bieu_thuc_thoi_han="",
                    thanh_phan_ho_so="",
                    co_quan_tiep_nhan="",
                    co_quan_xu_ly="",
                    ket_qua_thu_tuc="",
                    phuong_thuc_thuc_hien="",
                    pham_vi_ap_dung="",
                    ngoai_le=(frame.ngoai_le or "").strip(),
                    van_ban_dan_chieu=(frame.van_ban_dan_chieu or "").strip(),
                    answer_template=f"Ngưỡng/điều kiện định lượng: {raw}.",
                    explanation_template=self._explanation_template(base),
                    grounded_summary=f"Ngưỡng/điều kiện định lượng: {raw}."[:380],
                    notes="rule_threshold_raw",
                )
            )

        # 5b) Condition split — multiple `;`-separated clauses → extra `quy_tac_dieu_kien`
        raw_dk = _clean(frame.dieu_kien_ap_dung or frame.condition_predicates)
        if raw_dk and ";" in raw_dk:
            dk_parts = [p.strip() for p in raw_dk.split(";") if p.strip() and len(p.strip()) > 10]
            if len(dk_parts) > 1:
                for j, dk_item in enumerate(dk_parts[:12]):
                    rule_type = "quy_tac_dieu_kien"
                    rule_id = _rid(f"DK_{j}_{stable_hash(dk_item, n=6)}")
                    bieu = self._bieu_thuc_dieu_kien(dk_item)
                    bm = dict(base)
                    bm["dieu_kien_ap_dung"] = dk_item
                    bm["bieu_thuc_dieu_kien"] = bieu
                    rules.append(
                        RuleSeed(
                            rule_id=rule_id,
                            **bm,
                            rule_type=rule_type,
                            tinh_chat_phap_ly="bat_buoc",
                            canonical_predicate=canonical_pred,
                            typed_predicate=f"{rule_type}:{canonical_pred}" if canonical_pred else rule_type,
                            predicate_family="dieu_kien",
                            hanh_vi_phap_ly=(frame.hanh_vi or frame.action_predicate or "").strip(),
                            doi_tuong_hanh_vi=(frame.doi_tuong_hanh_vi or "").strip(),
                            he_qua_phap_ly=_clean(frame.ket_qua_thu_tuc),
                            ten_chi_so="",
                            toan_tu_so_sanh="",
                            gia_tri_nguong="",
                            don_vi_nguong="",
                            gia_tri_tu="",
                            gia_tri_den="",
                            kieu_khoang="",
                            thoi_han_so=str(frame.thoi_han_so or "").strip(),
                            don_vi_thoi_han=str(frame.don_vi_thoi_han or "").strip(),
                            moc_tinh_thoi_han=str(frame.moc_tinh_thoi_han or "").strip(),
                            bieu_thuc_thoi_han=self._bieu_thuc_thoi_han(frame),
                            thanh_phan_ho_so="",
                            co_quan_tiep_nhan=str(frame.co_quan_tiep_nhan or "").strip(),
                            co_quan_xu_ly=str(frame.co_quan_xu_ly or "").strip(),
                            ket_qua_thu_tuc=_clean(frame.ket_qua_thu_tuc),
                            phuong_thuc_thuc_hien="",
                            pham_vi_ap_dung="",
                            ngoai_le=(frame.ngoai_le or "").strip(),
                            van_ban_dan_chieu=(frame.van_ban_dan_chieu or "").strip(),
                            answer_template=f"Điều kiện: {dk_item}.",
                            explanation_template=self._explanation_template(base),
                            grounded_summary=f"Điều kiện áp dụng: {dk_item}."[:380],
                            notes="rule_dieu_kien_split",
                        )
                    )

        # 6) Legal outcome rule (effect-only frames)
        if (frame.frame_type or "").strip().lower() == "khung_ket_qua_phap_ly" and _clean(frame.ket_qua_thu_tuc):
            rule_type = "quy_tac_ket_qua_phap_ly"
            kq = _clean(frame.ket_qua_thu_tuc)
            rule_id = _rid("KET_QUA")
            rules.append(
                RuleSeed(
                    rule_id=rule_id,
                    **base,
                    rule_type=rule_type,
                    tinh_chat_phap_ly=(frame.tinh_chat_phap_ly or "co_the").strip(),
                    canonical_predicate=canonical_pred,
                    typed_predicate=f"{rule_type}:{canonical_pred}" if canonical_pred else rule_type,
                    predicate_family="ket_qua_phap_ly",
                    hanh_vi_phap_ly=(frame.hanh_vi or frame.action_predicate or kq)[:200],
                    doi_tuong_hanh_vi=(frame.doi_tuong_hanh_vi or "").strip(),
                    he_qua_phap_ly=kq,
                    ten_chi_so="",
                    toan_tu_so_sanh="",
                    gia_tri_nguong="",
                    don_vi_nguong="",
                    gia_tri_tu="",
                    gia_tri_den="",
                    kieu_khoang="",
                    thoi_han_so=str(frame.thoi_han_so or "").strip(),
                    don_vi_thoi_han=str(frame.don_vi_thoi_han or "").strip(),
                    moc_tinh_thoi_han=str(frame.moc_tinh_thoi_han or "").strip(),
                    bieu_thuc_thoi_han=self._bieu_thuc_thoi_han(frame),
                    thanh_phan_ho_so="",
                    co_quan_tiep_nhan=str(frame.co_quan_tiep_nhan or "").strip(),
                    co_quan_xu_ly=str(frame.co_quan_xu_ly or "").strip(),
                    ket_qua_thu_tuc=kq,
                    phuong_thuc_thuc_hien="",
                    pham_vi_ap_dung="",
                    ngoai_le=(frame.ngoai_le or "").strip(),
                    van_ban_dan_chieu=(frame.van_ban_dan_chieu or "").strip(),
                    answer_template=self._answer_template(rule_type, {**base, "ket_qua_thu_tuc": kq}, hanh_vi_phap_ly=kq),
                    explanation_template=self._explanation_template(base),
                    grounded_summary=self._grounded_summary(rule_type, {**base, "ket_qua_thu_tuc": kq}, hanh_vi_phap_ly=kq),
                    notes="rule_ket_qua_phap_ly",
                )
            )

        # 7) Additional outcome rules from distinct spans in source_text (fan-out)
        ft_l = (frame.frame_type or "").strip().lower()
        if ft_l in {
            "khung_thu_tuc",
            "khung_hanh_dong_co_quan",
            "khung_ket_qua_phap_ly",
            "khung_nghia_vu",
            "khung_ho_so",
            "khung_quyen",
            "khung_thoi_han",
        }:
            variants = extract_ket_qua_variants(source_text, max_n=18)
            seen_kq: set[str] = set()
            pk = _clean(frame.ket_qua_thu_tuc)
            if pk:
                seen_kq.add(re.sub(r"\s+", " ", pk).strip().lower())
            for kqv in variants:
                nk = re.sub(r"\s+", " ", kqv).strip().lower()
                if nk in seen_kq:
                    continue
                seen_kq.add(nk)
                rule_type = "quy_tac_ket_qua_phap_ly"
                rule_id = _rid(f"OUT_{stable_hash(kqv, n=8)}")
                rules.append(
                    RuleSeed(
                        rule_id=rule_id,
                        **base,
                        rule_type=rule_type,
                        tinh_chat_phap_ly=(frame.tinh_chat_phap_ly or "co_the").strip(),
                        canonical_predicate=canonical_pred,
                        typed_predicate=f"{rule_type}:{canonical_pred}" if canonical_pred else rule_type,
                        predicate_family="ket_qua_phap_ly",
                        hanh_vi_phap_ly=(kqv[:200]),
                        doi_tuong_hanh_vi=(frame.doi_tuong_hanh_vi or "").strip(),
                        he_qua_phap_ly=kqv,
                        ten_chi_so="",
                        toan_tu_so_sanh="",
                        gia_tri_nguong="",
                        don_vi_nguong="",
                        gia_tri_tu="",
                        gia_tri_den="",
                        kieu_khoang="",
                        thoi_han_so=str(frame.thoi_han_so or "").strip(),
                        don_vi_thoi_han=str(frame.don_vi_thoi_han or "").strip(),
                        moc_tinh_thoi_han=str(frame.moc_tinh_thoi_han or "").strip(),
                        bieu_thuc_thoi_han=self._bieu_thuc_thoi_han(frame),
                        thanh_phan_ho_so="",
                        co_quan_tiep_nhan=str(frame.co_quan_tiep_nhan or "").strip(),
                        co_quan_xu_ly=str(frame.co_quan_xu_ly or "").strip(),
                        ket_qua_thu_tuc=kqv,
                        phuong_thuc_thuc_hien="",
                        pham_vi_ap_dung="",
                        ngoai_le=(frame.ngoai_le or "").strip(),
                        van_ban_dan_chieu=(frame.van_ban_dan_chieu or "").strip(),
                        answer_template=self._answer_template(
                            rule_type, {**base, "ket_qua_thu_tuc": kqv, "source_text": source_text}, hanh_vi_phap_ly=kqv[:200]
                        ),
                        explanation_template=self._explanation_template(base),
                        grounded_summary=self._grounded_summary(
                            rule_type, {**base, "ket_qua_thu_tuc": kqv}, hanh_vi_phap_ly=kqv[:200]
                        ),
                        notes="rule_ket_qua_extra",
                    )
                )

        return rules

    def _frame_is_usable(self, frame: LegalFrame) -> bool:
        out = str(frame.output_status or "").lower().strip()
        if out in {"low_confidence", "dropped"}:
            return False
        if not (frame.chu_the or frame.subject_type) or str(frame.chu_the or frame.subject_type).strip().lower() == "unknown":
            return False
        return True

    def _loai_chu_the(self, chu_the: str) -> str:
        s = self._to_snake_vi(chu_the or "")
        if any(k in s for k in ["co_quan", "uy_ban", "bo", "so"]):
            return "co_quan"
        if any(k in s for k in ["doanh_nghiep", "cong_ty", "chi_nhanh", "van_phong_dai_dien"]):
            return "to_chuc"
        if any(k in s for k in ["nguoi", "thanh_vien", "chu_so_huu"]):
            return "ca_nhan"
        return "khac"

    def _reduce_action_to_core(self, action: str | None) -> str | None:
        if not action:
            return None
        a = str(action).strip()
        a = re.sub(
            r"^(cap_tinh_|doanh_nghiep_|co_quan_dang_ky_kinh_doanh_|co_quan_dang_ky_kinh_doanh_cap_tinh_|nguoi_thanh_lap_doanh_nghiep_)+",
            "",
            a,
        )
        a = re.sub(r"_(voi|den|theo|trong|khi|doi_voi|truong_hop|vao)_.*$", "", a)
        a = re.sub(r"_+(va|hoac)_.*$", "", a)
        return re.sub(r"_+", "_", a).strip("_")

    def _is_usable_action(self, action: str | None) -> bool:
        if not action:
            return False
        a = str(action).strip("_")
        if len(a) < 6 or len(a) > 70:
            return False
        if re.search(r"[^a-z0-9_]", a):
            return False
        if re.match(r"^(la|co|duoc|phai|dang_ky|thong_bao|cap|gui)$", a):
            return False
        if re.search(r"^(cap_tinh|doanh_nghiep|co_quan_dang_ky_kinh_doanh|nguoi_thanh_lap_doanh_nghiep)_", a):
            return False
        return True

    def _rule_type_for_frame(self, frame_type: str | None) -> str:
        ft = (frame_type or "").strip().lower()
        mapping = {
            "khung_nghia_vu": "quy_tac_nghia_vu",
            "khung_quyen": "quy_tac_quyen",
            "khung_cam_doan": "quy_tac_cam_doan",
            "khung_thoi_han": "quy_tac_thoi_han",
            "khung_thu_tuc": "quy_tac_thu_tuc",
            "khung_ho_so": "quy_tac_ho_so",
            "khung_hanh_dong_co_quan": "quy_tac_hanh_dong_co_quan",
            "khung_dieu_kien": "quy_tac_dieu_kien",
            "khung_ngoai_le": "quy_tac_ngoai_le",
            "khung_nguong_dinh_luong": "quy_tac_nguong_dinh_luong",
            "khung_ket_qua_phap_ly": "quy_tac_ket_qua_phap_ly",
        }
        return mapping.get(ft, "quy_tac_nghia_vu")

    def _tinh_chat_fallback(self, frame_type: str | None) -> str:
        ft = (frame_type or "").strip().lower()
        if ft == "khung_quyen":
            return "duoc_phep"
        if ft == "khung_hanh_dong_co_quan":
            return "co_trach_nhiem"
        return "bat_buoc"

    def _make_rule_group_id(self, *, doc_code: str, source_ref_full: str, canonical_predicate: str, frame_id: str) -> str:
        doc_token = "LUATDN" if "67/" in (doc_code or "") else "ND168" if "168/" in (doc_code or "") else "DOC"
        key = canonical_predicate or self._to_snake_vi(frame_id)[-18:]
        key2 = re.sub(r"[^0-9a-zA-Z_]+", "_", key).upper()[:28]
        ref = self._compact_ref(source_ref_full)
        return f"RG_{doc_token}_{ref}_{key2}".strip("_")

    def _make_rule_id(self, *, doc_code: str, source_ref_full: str, key: str) -> str:
        doc_token = "LUATDN" if "67/" in (doc_code or "") else "ND168" if "168/" in (doc_code or "") else "DOC"
        ref = self._compact_ref(source_ref_full)
        k_full = (key or "QUY_TAC").strip()
        k = re.sub(r"[^0-9a-zA-Z_]+", "_", k_full).upper()
        k = re.sub(r"_+", "_", k).strip("_")[:22]
        h = stable_hash(k_full, n=14)
        return f"RULE_{doc_token}_{ref}_{k}_{h}".strip("_")

    def _compact_ref(self, source_ref_full: str) -> str:
        s = source_ref_full or ""
        m_d = re.search(r"Điều\s+(\d+[a-z]?)", s, flags=re.I | re.U)
        m_k = re.search(r"khoản\s+(\d+)", s, flags=re.I | re.U)
        m_p = re.search(r"điểm\s+([a-zđ])", s, flags=re.I | re.U)
        parts: list[str] = []
        if m_d:
            parts.append(f"D{m_d.group(1)}")
        if m_k:
            parts.append(f"K{m_k.group(1)}")
        if m_p:
            parts.append(m_p.group(1).upper())
        return "_".join(parts) if parts else "REF"

    def _bieu_thuc_thoi_han(self, frame: LegalFrame) -> str:
        if not frame.thoi_han_so:
            return ""
        bits = [str(frame.thoi_han_so).strip(), str(frame.don_vi_thoi_han or "").strip()]
        if frame.moc_tinh_thoi_han:
            bits.append(str(frame.moc_tinh_thoi_han).strip())
        return "_".join(b for b in bits if b)

    def _do_tin_cay_trich_xuat(self, frame: LegalFrame) -> str:
        out = str(frame.output_status or "").lower().strip()
        if out == "seed_extracted_first_pass":
            return "cao"
        if out == "low_confidence":
            return "thap"
        return "trung_binh"

    def _review_flags(self, frame: LegalFrame, *, canonical_predicate: str) -> tuple[str, str]:
        reasons: list[str] = []
        if not (frame.chu_the or "").strip():
            reasons.append("thieu_chu_the")
        if frame.thoi_han_so and not frame.moc_tinh_thoi_han:
            reasons.append("thieu_moc_tinh_thoi_han")
        if frame.thanh_phan_ho_so and ";" in str(frame.thanh_phan_ho_so) and len(str(frame.thanh_phan_ho_so).split(";")) >= 3:
            reasons.append("ho_so_chua_tach_het_thanh_phan")
        if frame.ngoai_le and len(str(frame.ngoai_le)) > 160:
            reasons.append("ngoai_le_chua_tach_sach")
        if (getattr(frame, "nguong_so_luong", None) or getattr(frame, "nguong_ty_le", None) or getattr(frame, "khoang_gia_tri", None)) and not frame.dieu_kien_dinh_luong:
            reasons.append("co_nguong_nhung_chua_chuan_hoa_toan_tu_gia_tri")
        if canonical_predicate in {"dang_ky", "thong_bao"}:
            reasons.append("predicate_qua_chung")
        if reasons:
            return "co", ";".join(dict.fromkeys(reasons))
        return "khong", ""

    def _extraction_pattern(self, frame: LegalFrame) -> str:
        ft = (frame.frame_type or "").strip()
        if frame.thanh_phan_ho_so and frame.thoi_han_so:
            return f"{ft}_fanout_ho_so_thoi_han"
        if frame.thoi_han_so:
            return f"{ft}_fanout_thoi_han"
        if frame.thanh_phan_ho_so:
            return f"{ft}_fanout_ho_so"
        return f"{ft}_main"

    def _answer_template(self, rule_type: str, base: dict[str, str], *, hanh_vi_phap_ly: str) -> str:
        if rule_type == "quy_tac_ho_so":
            return "Hồ sơ gồm: {thanh_phan_ho_so}."
        if rule_type == "quy_tac_thoi_han":
            return "{chu_the} thực hiện trong thời hạn {thoi_han_so} {don_vi_thoi_han} kể từ {moc_tinh_thoi_han}."
        if rule_type == "quy_tac_hanh_dong_co_quan":
            return "{co_quan_xu_ly} có trách nhiệm {hanh_vi_phap_ly} trong thời hạn {thoi_han_so} {don_vi_thoi_han}."
        if rule_type == "quy_tac_nguong_dinh_luong":
            return "{chu_the} chịu điều kiện định lượng: {dieu_kien_ap_dung} ({source_text})."
        if rule_type == "quy_tac_ket_qua_phap_ly":
            return "Hậu quả pháp lý: {ket_qua_thu_tuc} ({source_text})."
        return "{chu_the} " + ("phải " if base.get("tinh_chat_phap_ly", "") != "duoc_phep" else "được ") + "{hanh_vi_phap_ly} {doi_tuong_hanh_vi}."

    def _explanation_template(self, base: dict[str, str]) -> str:
        return "Quy tắc này được rút ra từ {source_ref_full}, quy định rằng: {source_text}"

    def _grounded_summary(self, rule_type: str, base: dict[str, str], *, hanh_vi_phap_ly: str) -> str:
        if rule_type == "quy_tac_ho_so":
            return f"Hồ sơ gồm: {base.get('thanh_phan_ho_so','')}".strip()[:380]
        if rule_type == "quy_tac_thoi_han":
            return (
                f"Thời hạn: {base.get('thoi_han_so','')} {base.get('don_vi_thoi_han','')} kể từ {base.get('moc_tinh_thoi_han','')}."
            ).strip()[:380]
        if rule_type == "quy_tac_nguong_dinh_luong":
            s = f"Ngưỡng/điều kiện định lượng: {base.get('dieu_kien_ap_dung','') or base.get('dieu_kien_dinh_luong','')}".strip()
            return s[:380]
        if rule_type == "quy_tac_ket_qua_phap_ly":
            s = f"Hậu quả: {base.get('ket_qua_thu_tuc','') or base.get('he_qua_phap_ly','')}".strip()
            return s[:380]
        return (f"{base.get('chu_the','')} {hanh_vi_phap_ly} {base.get('doi_tuong_hanh_vi','')}".strip()).strip()[:380]

    # legacy helpers retained: _to_snake_vi + _reduce_action_to_core

    def _to_snake_vi(self, text: str) -> str:
        s = (text or "").strip().lower()
        s = unicodedata.normalize("NFD", s)
        s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
        s = s.replace("đ", "d")
        s = re.sub(r"[^0-9a-z]+", "_", s)
        return re.sub(r"_+", "_", s).strip("_")

    def _deduplicate_rules(self, rules: list[RuleSeed]) -> list[RuleSeed]:
        """Keep nearly all fan-out rows; collapse only byte-identical `rule_id` strings."""

        kept: dict[str, RuleSeed] = {}
        for r in rules:
            rid = (r.rule_id or "").strip()
            if rid not in kept:
                kept[rid] = r
        out = list(kept.values())
        out.sort(key=lambda x: (x.doc_id, x.source_ref_full, x.rule_type, x.rule_id))
        return out


__all__ = ["RuleBuilder"]
