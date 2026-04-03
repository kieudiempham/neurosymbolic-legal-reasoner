"""Predicate normalization for Vietnamese predicate lexicon.

This stage builds `predicate_lexicon.xlsx` from legal frames while keeping
grounded Vietnamese surface forms and normalized Vietnamese snake_case keys.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from law_side.law_rulebase_models import LegalFrame, PredicateLexiconEntry
from utils.ids import stable_hash
from utils.logger import get_logger


_FORBIDDEN_NORMALIZE_PREFIX_RE = re.compile(
    r"^\s*(luật|nghị\s*định|thông\s*tư|điều|khoản|quy\s+định|trường\s+hợp|trong\s+thời\s+hạn|kể\s+từ\s+ngày|thực\s+hiện|quy\s+định|nội\s+dung|khi|đối\s+với|sau\s+khi|trước\s+khi|hồ\s+sơ|bản\s+sao|giấy\s+tờ|thông\s+tin|cơ\s+quan|Luật\s+này|Nghị\s+định\s+này)\b",
    flags=re.IGNORECASE | re.UNICODE,
)


def _looks_like_header_or_definition(surface: str) -> bool:
    return bool(_FORBIDDEN_NORMALIZE_PREFIX_RE.search(surface or ""))


def _strip_diacritics(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return s


_CAMEL_SPLIT_RE = re.compile(r"[^0-9a-zA-Z]+", flags=re.UNICODE)
_NON_WORD_RE = re.compile(r"[^0-9a-zA-Z_]+", flags=re.UNICODE)


def canonicalize_for_predicate(surface: str) -> str:
    s = (surface or "").strip().lower()
    s = _strip_diacritics(s)
    s = s.replace("đ", "d")
    s = re.sub(r"\s+", " ", s)
    return s


def _to_vi_snake(s: str) -> str:
    s2 = canonicalize_for_predicate(s)
    s2 = s2.replace("đ", "d")
    s2 = re.sub(r"[^0-9a-z]+", "_", s2)
    s2 = re.sub(r"_+", "_", s2).strip("_")
    return s2


def clean_surface_form_vi(surface: str) -> str:
    s = re.sub(r"\s+", " ", (surface or "").strip())
    s = s.strip(" ,;:-")
    # Drop common lead-ins and structural tails.
    s = re.sub(r"^(theo\s+quy\s+định[^,.;]{0,120}[,.;]?\s*)", "", s, flags=re.I | re.U)
    s = re.sub(r"^(quy\s+định\s+tại[^,.;]{0,120}[,.;]?\s*)", "", s, flags=re.I | re.U)
    s = re.sub(r"\s+(và|hoặc|đã|theo)\s*$", "", s, flags=re.I | re.U)
    s = re.sub(r":\s*$", "", s).strip(" ,;:-")
    return s


def _strip_non_core_predicate_suffixes(surface: str) -> str:
    s = canonicalize_for_predicate(surface)
    s = re.sub(r"\s+theo quy trinh du phong[^,.;]{0,120}$", "", s, flags=re.I | re.U)
    s = re.sub(r"\s+theo yeu cau cua[^,.;]{0,120}$", "", s, flags=re.I | re.U)
    s = re.sub(r"\s+cua thanh vien co lien quan$", "", s, flags=re.I | re.U)
    s = re.sub(r"\s+voi co quan dang ky kinh doanh[^,.;]{0,80}$", "", s, flags=re.I | re.U)
    s = re.sub(r"\s+den co quan dang ky kinh doanh[^,.;]{0,80}$", "", s, flags=re.I | re.U)
    s = re.sub(r"\s+bang hinh thuc gui thu$", "", s, flags=re.I | re.U)
    s = re.sub(r"\s+va cac bao cao$", "", s, flags=re.I | re.U)
    s = re.sub(r"\s+trong so dang ky thanh vien$", "", s, flags=re.I | re.U)
    s = re.sub(r"\s+theo quy dinh cua phap luat[^,.;]{0,120}$", "", s, flags=re.I | re.U)
    s = re.sub(r"\s+theo quy dinh[^,.;]{0,120}$", "", s, flags=re.I | re.U)
    s = re.sub(r"\s+trong thoi han[^,.;]{0,120}$", "", s, flags=re.I | re.U)
    s = re.sub(r"\s+ke tu ngay[^,.;]{0,120}$", "", s, flags=re.I | re.U)
    s = re.sub(r"\s+doi voi[^,.;]{0,120}$", "", s, flags=re.I | re.U)
    s = re.sub(r"\s+truong hop[^,.;]{0,120}$", "", s, flags=re.I | re.U)
    s = re.sub(r"\s+ma co quan dang ky kinh doanh[^,.;]{0,120}$", "", s, flags=re.I | re.U)
    s = re.split(r"\s*[,;]\s*", s)[0].strip()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _strip_subject_prefixes_vi(normalized: str) -> str:
    s = normalized or ""
    prefixes = (
        "co_quan_dang_ky_kinh_doanh_cap_tinh_",
        "co_quan_dang_ky_kinh_doanh_",
        "nguoi_thanh_lap_doanh_nghiep_",
        "doanh_nghiep_",
        "cap_tinh_",
    )
    for p in prefixes:
        if s.startswith(p):
            s = s[len(p) :]
            break
    s = re.sub(r"^nhan_duoc_", "tiep_nhan_", s)
    return s


def is_plausible_predicate_surface_vi(surface: str) -> bool:
    s = clean_surface_form_vi(surface)
    if not s:
        return False
    if len(s) < 8:
        return False
    low = canonicalize_for_predicate(s)
    if re.match(r"^(trong thoi han|ke tu ngay|truong hop|doi voi|sau khi|truoc khi|quy dinh tai|theo quy dinh)", low):
        return False
    if re.match(r"^(cap|sau|cho|van ban|thong tin|noi dung)$", low):
        return False
    if re.search(r"\b(la ca nhan|la to chuc|duoc hieu la|la viec|la van ban|la day so)\b", low):
        return False
    if low.endswith((" va", " hoac", " da", " theo")):
        return False
    return True


def normalize_surface_to_predicate(surface: str) -> str:
    s = clean_surface_form_vi(surface)
    if not s:
        return ""
    core = _strip_non_core_predicate_suffixes(s)
    low = canonicalize_for_predicate(core)

    if "dang ky thay doi noi dung dang ky doanh nghiep" in low:
        return "dang_ky_thay_doi_noi_dung_dang_ky_doanh_nghiep"
    if "dang ky thay doi noi dung giay chung nhan dang ky doanh nghiep" in low:
        return "dang_ky_thay_doi_noi_dung_giay_chung_nhan_dang_ky_doanh_nghiep"
    if "dang ky thay doi noi dung giay chung nhan dang ky hoat dong chi nhanh" in low:
        return "dang_ky_thay_doi_noi_dung_giay_chung_nhan_dang_ky_hoat_dong_chi_nhanh"
    if low.startswith("dang ky"):
        return "dang_ky_doanh_nghiep" if "doanh nghiep" in low else "dang_ky"
    if "thong bao bang van ban" in low:
        return "thong_bao_bang_van_ban"
    if low.startswith("thong bao"):
        if "thay doi noi dung dang ky" in low:
            return "thong_bao_thay_doi_noi_dung_dang_ky_doanh_nghiep"
        return "thong_bao"
    if low.startswith("gui ho so") or low.startswith("nop ho so"):
        if "chi nhanh" in low:
            return "gui_ho_so_dang_ky_hoat_dong_chi_nhanh"
        return "gui_ho_so"
    if low.startswith("tiep nhan ho so") or low.startswith("nhan ho so"):
        return "tiep_nhan_ho_so"
    if low.startswith("gui phieu lay y kien"):
        return "gui_phieu_lay_y_kien"
    if low.startswith("lay y kien bang van ban"):
        return "lay_y_kien_bang_van_ban"
    if "huy bo quyet dinh thu hoi" in low:
        return "huy_bo_quyet_dinh_thu_hoi"
    if low.startswith("cap dang ky doanh nghiep"):
        return "cap_dang_ky_doanh_nghiep"
    if "giai quyet thu tuc dang ky doanh nghiep" in low:
        return "giai_quyet_thu_tuc_dang_ky_doanh_nghiep"
    if "cap nhat thong tin vao co so du lieu quoc gia ve dang ky doanh nghiep" in low:
        return "cap_nhat_thong_tin_dang_ky_doanh_nghiep"
    if "nhan duoc nghi quyet hoac quyet dinh giai the" in low:
        return "tiep_nhan_nghi_quyet_hoac_quyet_dinh_giai_the"
    if "ban hanh quyet dinh thu hoi giay chung nhan dang ky hoat dong chi nhanh" in low:
        return "ban_hanh_quyet_dinh_thu_hoi_chi_nhanh"
    if "xem xet tinh hop le cua ho so" in low:
        return "xem_xet_tinh_hop_le_cua_ho_so"
    if low.startswith("cap giay chung nhan"):
        if "chi nhanh" in low:
            return "cap_giay_chung_nhan_dang_ky_hoat_dong_chi_nhanh"
        return "cap_giay_chung_nhan_dang_ky_doanh_nghiep"
    if low.startswith("cap nhat"):
        if "thay doi thanh vien" in low:
            return "cap_nhat_thay_doi_thanh_vien"
        return "cap_nhat_thong_tin"
    if low.startswith("luu giu"):
        if "chu so huu huong loi" in low:
            return "luu_giu_danh_sach_chu_so_huu_huong_loi"
        return "luu_giu_thong_tin"
    if low.startswith("uy quyen"):
        return "uy_quyen_bang_van_ban"
    if low.startswith("yeu cau"):
        if "thay doi ten doanh nghiep" in low:
            return "yeu_cau_thay_doi_ten_doanh_nghiep"
        return "yeu_cau"
    if low.startswith("tra cuu"):
        return "tra_cuu_thong_tin"
    if low.startswith("cung cap thong tin"):
        return "cung_cap_thong_tin"
    if low.startswith("thu hoi"):
        return "thu_hoi"
    if low.startswith("khoi phuc"):
        return "khoi_phuc"
    if low.startswith("chiu trach nhiem"):
        return "chiu_trach_nhiem"

    return _strip_subject_prefixes_vi(_to_vi_snake(core))


def _normalize_group_from_surface(surface: str, normalized: str) -> str:
    low = canonicalize_for_predicate(surface)
    norm = normalized or ""
    if "chu_so_huu_huong_loi" in norm or "chu so huu huong loi" in low:
        return "chu_so_huu_huong_loi"
    if any(k in norm for k in ["uy_quyen", "lay_y_kien", "phieu_lay_y_kien"]) or "uy quyen" in low:
        return "uy_quyen_va_lay_y_kien"
    if any(k in norm for k in ["thu_hoi", "khoi_phuc", "huy_bo"]):
        return "thu_hoi_khoi_phuc"
    if any(k in norm for k in ["cong_bo", "cung_cap_thong_tin", "tra_cuu"]):
        return "cong_bo_va_cung_cap_thong_tin"
    if "ho_so" in norm or "ho so" in low or "giay de nghi" in low or "ban sao" in low:
        return "ho_so"
    if any(k in norm for k in ["cap_", "cap_nhat", "xem_xet", "tu_choi", "giai_quyet", "tiep_nhan"]):
        return "hanh_dong_co_quan"
    if "chi_nhanh" in norm or "van_phong_dai_dien" in norm or "dia_diem_kinh_doanh" in norm or "chi nhanh" in low or "van phong dai dien" in low:
        return "chi_nhanh_van_phong_dai_dien"
    if "ten_doanh_nghiep" in norm or "ten doanh nghiep" in low:
        return "ten_doanh_nghiep"
    if "von" in low or "gop von" in low:
        return "von_va_gop_von"
    if "luu_giu" in norm or "luu giu" in low:
        return "luu_giu_thong_tin"
    if "thong_bao" in norm or "thong bao" in low:
        return "thong_bao"
    if "dang_ky" in norm or "dang ky" in low:
        return "dang_ky"
    return "khac"


def _is_overlong_or_weak_normalized(norm: str) -> bool:
    if not norm:
        return True
    if len(norm) <= 70:
        return False
    keep_prefixes = (
        "dang_ky_thay_doi_noi_dung_giay_chung_nhan_dang_ky_doanh_nghiep",
        "dang_ky_thay_doi_noi_dung_giay_chung_nhan_dang_ky_hoat_dong_chi_nhanh",
    )
    return not norm.startswith(keep_prefixes)


def _object_hint_vi(surface: str) -> str | None:
    low = canonicalize_for_predicate(surface)
    if "giay chung nhan dang ky doanh nghiep" in low:
        return "giay_chung_nhan_dang_ky_doanh_nghiep"
    if "noi dung dang ky doanh nghiep" in low:
        return "noi_dung_dang_ky_doanh_nghiep"
    if "dang ky doanh nghiep" in low:
        return "dang_ky_doanh_nghiep"
    if "ho so" in low:
        return "ho_so"
    if "chi nhanh" in low:
        return "chi_nhanh"
    if "chu so huu huong loi" in low:
        return "chu_so_huu_huong_loi"
    return None


def _to_hanh_vi_chuan(chi_tiet: str, nhom: str) -> str:
    s = chi_tiet or ""
    if s.startswith("dang_ky"):
        return "dang_ky"
    if s.startswith("thong_bao"):
        return "thong_bao"
    if s.startswith("cap_giay") or s.startswith("cap_dang_ky"):
        return "cap_giay"
    if s.startswith("cap_nhat"):
        return "cap_nhat"
    if s.startswith("thu_hoi") or s.startswith("khoi_phuc") or s.startswith("huy_bo"):
        return "thu_hoi"
    if s.startswith("cong_bo"):
        return "cong_bo"
    if s.startswith("giai_the"):
        return "giai_the"
    if s.startswith("tam_ngung"):
        return "tam_ngung"
    if s.startswith("chuyen_doi"):
        return "chuyen_doi"
    if s.startswith("gui_ho_so") or s.startswith("nop_ho_so") or "ho_so" in s:
        return "nop_ho_so"
    if s.startswith("yeu_cau"):
        return "yeu_cau_bao_cao"
    if s.startswith("tiep_nhan_"):
        return "tiep_nhan_ho_so"
    if s.startswith("xem_xet_"):
        return "tham_dinh_ho_so"
    if s.startswith("gui_") or s.startswith("nop_"):
        return "nop_ho_so"
    if s.startswith("uy_quyen") or s.startswith("lay_y_kien") or s.startswith("gui_phieu_lay_y_kien"):
        return "yeu_cau_bao_cao"
    if nhom in {"dang_ky", "thong_bao", "cap_nhat", "cong_bo", "thu_hoi", "cap_giay", "giai_the", "tam_ngung", "chuyen_doi", "nop_ho_so", "yeu_cau_bao_cao"}:
        return nhom
    return "khac"


def _make_predicate_id(chi_tiet: str) -> str:
    token = re.sub(r"[^0-9a-zA-Z_]+", "_", (chi_tiet or "").strip("_")).upper()
    token = re.sub(r"_+", "_", token).strip("_")
    if not token:
        token = "HANH_VI"
    return f"PRED_{token[:52]}"


def _bien_the_ngon_ngu(surface: str, frame: LegalFrame) -> str:
    s = clean_surface_form_vi(surface)
    variants: list[str] = [s]
    if frame.recipient_authority and "cơ quan" in frame.recipient_authority.lower():
        variants.append(f"{s} với {frame.recipient_authority}")
    if frame.required_documents and "hồ sơ" in canonicalize_for_predicate(frame.required_documents):
        variants.append(f"{s} kèm hồ sơ")
    return " | ".join(dict.fromkeys(v for v in variants if v))


def _co_khong(flag: bool) -> str:
    return "co" if flag else "khong"


def _ghi_chu_ap_dung(frame: LegalFrame, norm: str, nhom: str) -> str:
    tips: list[str] = [f"map_khi_thay_cum_{norm}"]
    if nhom == "dang_ky":
        tips.append("uu_tien_cho_hanh_vi_dang_ky_noi_dung_phap_ly")
    if nhom == "thong_bao":
        tips.append("khong_dong_nhat_voi_cong_bo")
    if frame.deadline_value:
        tips.append("thuong_di_kem_thoi_han")
    if frame.required_documents:
        tips.append("thuong_di_kem_thanh_phan_ho_so")
    if frame.exception_text:
        tips.append("co_ngoai_le_can_xu_ly_rieng")
    return ";".join(tips)


class PredicateNormalizer:
    """Build normalized predicate lexicon entries from extracted frames."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}
        self._log = get_logger(self.__class__.__name__)

    def normalize(
        self, frame: LegalFrame
    ) -> tuple[list[PredicateLexiconEntry], dict[str, str]]:
        """Normalize one frame; returns (entries, action_surface_map)."""
        entries: list[PredicateLexiconEntry] = []
        action_map: dict[str, str] = {}

        # Only consume sufficiently reliable frames.
        if frame.output_status and str(frame.output_status).lower() != "seed_extracted_first_pass":
            return entries, action_map
        if (frame.subject_type or "").strip().lower() == "unknown":
            return entries, action_map

        if frame.action_predicate and is_plausible_predicate_surface_vi(frame.action_predicate):
            sf = clean_surface_form_vi(frame.action_predicate)
            norm = normalize_surface_to_predicate(sf)
            if norm:
                group = _normalize_group_from_surface(sf, norm)
                is_weak = _is_overlong_or_weak_normalized(norm) or group == "khac"
                if not (is_weak and group == "khac"):
                    action_map[sf] = norm
                    nhom = self._to_nhom_hanh_vi(group, norm)
                    hanh_vi_chuan = _to_hanh_vi_chuan(norm, nhom)
                    entries.append(
                        PredicateLexiconEntry(
                            predicate_id=_make_predicate_id(norm),
                            surface_form=sf,
                            bien_the_ngon_ngu=_bien_the_ngon_ngu(sf, frame),
                            hanh_vi_chuan=hanh_vi_chuan,
                            hanh_vi_chuan_chi_tiet=norm,
                            nhom_hanh_vi=nhom,
                            chu_the_mac_dinh=self._stable_subject(frame),
                            doi_tuong_mac_dinh=frame.doi_tuong_hanh_vi or _object_hint_vi(sf),
                            co_quan_mac_dinh=frame.co_quan_tiep_nhan or frame.co_quan_xu_ly or frame.recipient_authority,
                            can_thoi_han=_co_khong(bool(frame.deadline_value)),
                            can_ho_so=_co_khong(bool(frame.required_documents)),
                            can_ngoai_le=_co_khong(bool(frame.exception_text)),
                            can_nguong_dinh_luong=_co_khong(
                                bool(getattr(frame, "nguong_so_luong", None) or getattr(frame, "nguong_ty_le", None) or getattr(frame, "khoang_gia_tri", None))
                            ),
                            ghi_chu_ap_dung=_ghi_chu_ap_dung(frame, norm, nhom),
                            normalized_predicate=norm,
                            predicate_group=group,
                            frame_role="hanh_dong_chinh",
                            modality_hint=self._modality_hint_vi(frame.modality, frame.frame_type),
                            object_hint=_object_hint_vi(sf),
                            source_doc_id=frame.doc_id,
                            source_ref=frame.source_ref,
                            example_text=frame.source_text,
                            status="ung_vien" if is_weak else "phe_duyet",
                            notes="surface_cleaned; normalized_from_surface; demoted_weak" if is_weak else "surface_cleaned; normalized_from_surface",
                        )
                    )
        if frame.condition_predicates:
            conds = [c.strip() for c in frame.condition_predicates.split(";") if c.strip()]
            for c in conds:
                if _looks_like_header_or_definition(c) or not is_plausible_predicate_surface_vi(c):
                    continue
                sf = clean_surface_form_vi(c)
                norm = normalize_surface_to_predicate(sf)
                if not norm:
                    continue
                entries.append(
                    PredicateLexiconEntry(
                        predicate_id=_make_predicate_id(norm),
                        surface_form=sf,
                        bien_the_ngon_ngu=_bien_the_ngon_ngu(sf, frame),
                        hanh_vi_chuan="dieu_kien_ap_dung",
                        hanh_vi_chuan_chi_tiet=norm,
                        nhom_hanh_vi="dieu_kien",
                        chu_the_mac_dinh=self._stable_subject(frame),
                        doi_tuong_mac_dinh=frame.doi_tuong_hanh_vi or _object_hint_vi(sf),
                        co_quan_mac_dinh=frame.co_quan_tiep_nhan or frame.co_quan_xu_ly or frame.recipient_authority,
                        can_thoi_han=_co_khong(bool(frame.deadline_value)),
                        can_ho_so=_co_khong(bool(frame.required_documents)),
                        can_ngoai_le=_co_khong(bool(frame.exception_text)),
                        can_nguong_dinh_luong=_co_khong(
                            bool(getattr(frame, "nguong_so_luong", None) or getattr(frame, "nguong_ty_le", None) or getattr(frame, "khoang_gia_tri", None))
                        ),
                        ghi_chu_ap_dung="map_cho_ve_dieu_kien_ap_dung;uu_tien_giu_nguyen_ngu_canh",
                        normalized_predicate=norm,
                        predicate_group="dieu_kien",
                        frame_role="dieu_kien",
                        modality_hint=self._modality_hint_vi(frame.modality, frame.frame_type),
                        object_hint=_object_hint_vi(sf),
                        source_doc_id=frame.doc_id,
                        source_ref=frame.source_ref,
                        example_text=frame.source_text,
                        status="ung_vien",
                        notes="surface_cleaned; normalized_from_surface",
                    )
                )
        if frame.required_documents:
            if not _looks_like_header_or_definition(frame.required_documents) and is_plausible_predicate_surface_vi(frame.required_documents):
                sf = clean_surface_form_vi(frame.required_documents)
                norm = normalize_surface_to_predicate(sf)
                if norm:
                    entries.append(
                        PredicateLexiconEntry(
                            predicate_id=_make_predicate_id(norm),
                            surface_form=sf,
                            bien_the_ngon_ngu=_bien_the_ngon_ngu(sf, frame),
                            hanh_vi_chuan="nop_ho_so",
                            hanh_vi_chuan_chi_tiet=norm,
                            nhom_hanh_vi="nop_ho_so",
                            chu_the_mac_dinh=self._stable_subject(frame),
                            doi_tuong_mac_dinh=frame.doi_tuong_hanh_vi or _object_hint_vi(sf),
                            co_quan_mac_dinh=frame.co_quan_tiep_nhan or frame.co_quan_xu_ly or frame.recipient_authority,
                            can_thoi_han=_co_khong(bool(frame.deadline_value)),
                            can_ho_so="co",
                            can_ngoai_le=_co_khong(bool(frame.exception_text)),
                            can_nguong_dinh_luong=_co_khong(
                                bool(getattr(frame, "nguong_so_luong", None) or getattr(frame, "nguong_ty_le", None) or getattr(frame, "khoang_gia_tri", None))
                            ),
                            ghi_chu_ap_dung="map_khi_noi_dung_la_thanh_phan_ho_so_hoac_giay_to_kem_theo",
                            normalized_predicate=norm,
                            predicate_group="ho_so",
                            frame_role="tai_lieu_ho_so",
                            modality_hint=self._modality_hint_vi(frame.modality, frame.frame_type),
                            object_hint=_object_hint_vi(sf),
                            source_doc_id=frame.doc_id,
                            source_ref=frame.source_ref,
                            example_text=frame.source_text,
                            status="ung_vien",
                            notes="surface_cleaned; normalized_from_surface",
                        )
                    )
        return entries, action_map

    def _to_nhom_hanh_vi(self, group: str, norm: str) -> str:
        g = (group or "").strip().lower()
        n = (norm or "").strip().lower()
        if n.startswith("cap_giay") or n.startswith("cap_dang_ky"):
            return "cap_giay"
        if n.startswith("cap_nhat"):
            return "cap_nhat"
        if n.startswith("cong_bo"):
            return "cong_bo"
        if n.startswith("giai_the"):
            return "giai_the"
        if n.startswith("tam_ngung"):
            return "tam_ngung"
        if n.startswith("chuyen_doi"):
            return "chuyen_doi"
        if n.startswith("gui_ho_so") or n.startswith("nop_ho_so"):
            return "nop_ho_so"
        if n.startswith("yeu_cau"):
            return "yeu_cau_bao_cao"
        if g == "hanh_dong_co_quan" and (n.startswith("thu_hoi") or n.startswith("khoi_phuc") or n.startswith("huy_bo")):
            return "thu_hoi"
        if g in {"dang_ky", "thong_bao", "thu_hoi_khoi_phuc"}:
            return "thu_hoi" if g == "thu_hoi_khoi_phuc" else g
        if g == "cong_bo_va_cung_cap_thong_tin":
            return "cong_bo"
        if g == "ho_so":
            return "nop_ho_so"
        return g if g and g != "khac" else "khac"

    def _stable_subject(self, frame: LegalFrame) -> str | None:
        s = (frame.chu_the or frame.subject_type or "").strip()
        if not s:
            return None
        low = canonicalize_for_predicate(s)
        if any(k in low for k in ["doanh nghiep", "cong ty", "co quan dang ky kinh doanh", "co quan thue"]):
            return s
        return None

    def build_predicate_lexicon(
        self, frames: list[LegalFrame]
    ) -> tuple[list[PredicateLexiconEntry], dict[str, str]]:
        """Build lexicon + action surface to normalized mapping."""
        all_entries: list[PredicateLexiconEntry] = []
        action_map: dict[str, str] = {}

        # De-duplicate entries by normalized predicate + group + role.
        seen: set[tuple[str, str, str]] = set()

        for frame in frames:
            entries, amap = self.normalize(frame)
            for k, v in amap.items():
                action_map[k] = v
            for e in entries:
                key = (e.normalized_predicate, e.predicate_group, e.frame_role)
                if key in seen:
                    continue
                seen.add(key)
                all_entries.append(e)

        self._log.info("Built predicate lexicon with %d unique entries", len(all_entries))
        return all_entries, action_map

    def _modality_hint_vi(self, modality: str | None, frame_type: str | None) -> str | None:
        m = (modality or "").strip().lower()
        if "nghia vu" in m or "obligation" in m:
            return "nghia_vu"
        if "quyen" in m or "permission" in m:
            return "quyen"
        if "cam" in m or "prohibition" in m:
            return "cam"
        ft = (frame_type or "").lower()
        if "khung_hanh_dong_co_quan" in ft or "hành động của cơ quan" in ft or "authority" in ft:
            return "hanh_dong_co_quan"
        return None


__all__ = [
    "PredicateNormalizer",
    "canonicalize_for_predicate",
    "normalize_surface_to_predicate",
]
