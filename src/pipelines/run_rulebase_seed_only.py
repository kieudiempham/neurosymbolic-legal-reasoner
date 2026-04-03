"""Build only rulebase_seed.xlsx from current intermediate Excel files."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from law_side.law_rulebase_models import LegalFrame
from law_side.rule_builder import RuleBuilder
from pipelines._paths import legal_qa_nesy_root
from utils.io import read_yaml


RULEBASE_SEED_COLUMNS = [
    # A. Nhóm nhận diện
    "rule_id",
    "rule_group_id",
    "frame_id",
    "candidate_id",
    "source_unit_id",
    "doc_id",
    "doc_code",
    # B. Nhóm truy vết nguồn
    "source_ref",
    "source_ref_full",
    "heading",
    "parent_context",
    "source_text",
    # C. Nhóm phân loại rule
    "rule_type",
    "tinh_chat_phap_ly",
    "canonical_predicate",
    "typed_predicate",
    "predicate_family",
    # D. Nhóm nội dung pháp lý cốt lõi
    "chu_the",
    "loai_chu_the",
    "vai_tro_chu_the",
    "dieu_kien_ap_dung",
    "bieu_thuc_dieu_kien",
    "hanh_vi_phap_ly",
    "doi_tuong_hanh_vi",
    "he_qua_phap_ly",
    # E. Nhóm định lượng / ngưỡng
    "ten_chi_so",
    "toan_tu_so_sanh",
    "gia_tri_nguong",
    "don_vi_nguong",
    "gia_tri_tu",
    "gia_tri_den",
    "kieu_khoang",
    # F. Nhóm thời hạn
    "thoi_han_so",
    "don_vi_thoi_han",
    "moc_tinh_thoi_han",
    "bieu_thuc_thoi_han",
    # G. Nhóm thủ tục / hồ sơ / cơ quan
    "thanh_phan_ho_so",
    "co_quan_tiep_nhan",
    "co_quan_xu_ly",
    "ket_qua_thu_tuc",
    "phuong_thuc_thuc_hien",
    # H. Nhóm ngoại lệ / phạm vi
    "pham_vi_ap_dung",
    "ngoai_le",
    "van_ban_dan_chieu",
    # I. Nhóm phục vụ answer / explanation
    "answer_template",
    "explanation_template",
    "grounded_summary",
    # J. Nhóm chất lượng
    "muc_do_day_du",
    "do_tin_cay_trich_xuat",
    "can_ra_soat",
    "ly_do_can_ra_soat",
    "extraction_pattern",
    "notes",
]


def _to_frames(df: pd.DataFrame) -> list[LegalFrame]:
    def _s(row: pd.Series, k: str) -> str:
        v = row.get(k, "")
        if v is None:
            return ""
        try:
            if pd.isna(v):
                return ""
        except Exception:
            pass
        return str(v)

    frames: list[LegalFrame] = []
    for _, row in df.iterrows():
        frames.append(
            LegalFrame(
                frame_id=_s(row, "frame_id"),
                ns_id=_s(row, "ns_id") or _s(row, "candidate_id"),
                candidate_id=_s(row, "candidate_id"),
                source_unit_id=_s(row, "source_unit_id"),
                doc_id=_s(row, "doc_id"),
                doc_code=_s(row, "doc_code"),
                unit_ref_full=_s(row, "unit_ref_full"),
                source_ref=_s(row, "source_ref"),
                heading=_s(row, "heading"),
                parent_context=_s(row, "parent_context"),
                source_text=_s(row, "source_text"),
                frame_type=_s(row, "frame_type"),
                subject_type=_s(row, "subject_type") or _s(row, "chu_the"),
                subject_role=_s(row, "subject_role") or _s(row, "vai_tro_chu_the"),
                trigger_event=_s(row, "trigger_event"),
                condition_predicates=_s(row, "condition_predicates") or _s(row, "dieu_kien_ap_dung"),
                action_predicate=_s(row, "action_predicate") or _s(row, "hanh_vi"),
                modality=_s(row, "modality") or _s(row, "tinh_chat_phap_ly"),
                deadline_value=_s(row, "deadline_value"),
                deadline_unit=_s(row, "deadline_unit"),
                deadline_anchor=_s(row, "deadline_anchor"),
                required_documents=_s(row, "required_documents"),
                recipient_authority=_s(row, "recipient_authority"),
                legal_effect=_s(row, "legal_effect") or _s(row, "ket_qua_thu_tuc"),
                exception_text=_s(row, "exception_text") or _s(row, "ngoai_le"),
                output_status=_s(row, "output_status"),
                chu_the=_s(row, "chu_the"),
                vai_tro_chu_the=_s(row, "vai_tro_chu_the"),
                hanh_vi=_s(row, "hanh_vi"),
                doi_tuong_hanh_vi=_s(row, "doi_tuong_hanh_vi"),
                tinh_chat_phap_ly=_s(row, "tinh_chat_phap_ly"),
                dieu_kien_ap_dung=_s(row, "dieu_kien_ap_dung"),
                dieu_kien_dinh_luong=_s(row, "dieu_kien_dinh_luong"),
                nguong_so_luong=_s(row, "nguong_so_luong"),
                nguong_ty_le=_s(row, "nguong_ty_le"),
                khoang_gia_tri=_s(row, "khoang_gia_tri"),
                thanh_phan_ho_so=_s(row, "thanh_phan_ho_so"),
                co_quan_tiep_nhan=_s(row, "co_quan_tiep_nhan"),
                co_quan_xu_ly=_s(row, "co_quan_xu_ly"),
                ket_qua_thu_tuc=_s(row, "ket_qua_thu_tuc"),
                thoi_han_so=_s(row, "thoi_han_so"),
                don_vi_thoi_han=_s(row, "don_vi_thoi_han"),
                moc_tinh_thoi_han=_s(row, "moc_tinh_thoi_han"),
                ngoai_le=_s(row, "ngoai_le"),
                van_ban_dan_chieu=_s(row, "van_ban_dan_chieu"),
                ghi_chu_giai_thich=_s(row, "ghi_chu_giai_thich"),
                muc_do_day_du=_s(row, "muc_do_day_du"),
                can_tach_them=_s(row, "can_tach_them"),
                ly_do_can_tach=_s(row, "ly_do_can_tach"),
                notes=_s(row, "notes"),
            )
        )
    return frames


def main() -> None:
    root = legal_qa_nesy_root()
    parser = argparse.ArgumentParser(description="Build only rulebase_seed.xlsx.")
    parser.add_argument(
        "--config",
        type=Path,
        default=root / "configs" / "law_rulebase_pipeline.yaml",
    )
    args = parser.parse_args()
    _ = read_yaml(args.config)

    manifest_path = root / "data/raw/legal_corpus/manifest/document_manifest.xlsx"
    units_path = root / "data/interim/law_parsing/legal_units_review.xlsx"
    candidates_path = root / "data/interim/law_parsing/candidate_normative_sentences.xlsx"
    frames_path = root / "data/interim/law_parsing/legal_frames_review.xlsx"
    lexicon_path = root / "data/processed/ontology/predicate_lexicon.xlsx"
    out_path = root / "data/processed/rulebase/rulebase_seed.xlsx"

    for p in [manifest_path, units_path, candidates_path, frames_path, lexicon_path]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required input: {p}")

    df_frames = pd.read_excel(frames_path)
    df_lex = pd.read_excel(lexicon_path)
    df_units = pd.read_excel(units_path)
    frames = _to_frames(df_frames)

    # Build unit meta for traceability.
    unit_meta: dict[str, dict[str, str]] = {}
    if "unit_id" in df_units.columns:
        for _, r in df_units.iterrows():
            uid = str(r.get("unit_id", "") or "").strip()
            if not uid:
                continue
            unit_meta[uid] = {
                "heading": str(r.get("heading", "") or ""),
                "parent_context": str(r.get("parent_context", "") or ""),
                "source_ref_full": str(r.get("unit_ref_full", "") or ""),
                "doc_code": str(r.get("doc_code", "") or ""),
            }

    # Prefer lexicon map for action surfaces.
    action_map = (
        df_lex.dropna(subset=["surface_form", "hanh_vi_chuan_chi_tiet"])
        .drop_duplicates(subset=["surface_form"], keep="first")
        .set_index("surface_form")["hanh_vi_chuan_chi_tiet"]
        .to_dict()
    )
    predicate_meta = (
        df_lex.dropna(subset=["hanh_vi_chuan_chi_tiet"])
        .drop_duplicates(subset=["hanh_vi_chuan_chi_tiet"], keep="first")
        .set_index("hanh_vi_chuan_chi_tiet")[
            ["hanh_vi_chuan", "nhom_hanh_vi", "ghi_chu_ap_dung"]
        ]
        .to_dict(orient="index")
    )

    seeds = RuleBuilder().build(
        frames,
        action_surface_to_normalized=action_map,
        unit_meta=unit_meta,
        predicate_meta=predicate_meta,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_rules = pd.DataFrame([{c: getattr(r, c) for c in RULEBASE_SEED_COLUMNS} for r in seeds], columns=RULEBASE_SEED_COLUMNS)
    df_rules.to_excel(out_path, index=False)
    print(f"Rulebase seed generated: {out_path}")


if __name__ == "__main__":
    main()

