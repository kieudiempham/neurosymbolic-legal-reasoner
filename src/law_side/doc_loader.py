"""Document ingest for the law rule-base pipeline."""

from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from utils.ids import stable_hash
from utils.logger import get_logger
from law_side.doc_to_text import DocToTextConverter
from law_side.law_rulebase_models import LegalDocument


class DocLoader:
    """Load `.doc` files and create `LegalDocument` objects."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}
        self._converter = DocToTextConverter(config=self._config.get("doc_to_text", {}))
        self._log = get_logger(self.__class__.__name__)

    def load_documents(self, doc_dir: Path, doc_files: list[str]) -> list[LegalDocument]:
        """Load documents in the given order."""
        docs: list[LegalDocument] = []
        for fname in doc_files:
            doc_path = doc_dir / fname
            raw_text, cleaned_text = self._converter.convert(doc_path)

            meta = self._parse_metadata_from_filename(fname, cleaned_text)
            docs.append(
                LegalDocument(
                    raw_text=raw_text,
                    cleaned_text=cleaned_text,
                    **meta,
                )
            )
        return docs

    def _parse_metadata_from_filename(self, filename: str, cleaned_text: str) -> dict[str, Any]:
        stem = Path(filename).stem
        parts = stem.split("_")
        filename_key = filename.lower()

        # Fixed high-confidence mapping for current 2 real files.
        known_by_filename: dict[str, dict[str, str]] = {
            "01_luat_doanh_nghiep_vbhn_67_vbhn_vpqh.doc": {
                "doc_id": "DOC_LUAT_DOANH_NGHIEP_67_VBHN_2025",
                "doc_title": "Luật Doanh nghiệp",
                "doc_code": "67/VBHN-VPQH",
                "doc_type": "law",
                "issuing_body": "Văn phòng Quốc hội",
                "domain_scope": "doanh_nghiep",
                "domain_subscope": "quyen_nghia_vu_quan_tri_dang_ky",
                "document_role": "van_ban_hop_nhat",
                "expected_rule_density": "rat_cao",
                "parse_strategy": "uu_tien_nghia_vu_quyen_dieu_kien",
                "is_consolidated_version": "co",
                "amends_doc_codes": "",
                "has_appendix_forms": "khong",
                "priority": "rat_cao",
                "status": "selected",
                "legal_scope_note": "quy định nền về thành lập, đăng ký, tổ chức và hoạt động doanh nghiệp",
                "notes": "nhieu_quy_tac_ve_quyen_nghia_vu_theo_loai_hinh_doanh_nghiep",
            },
            "02_nghi_dinh_dang_ky_doanh_nghiep_168_2025_nd_cp.doc": {
                "doc_id": "DOC_ND_DANG_KY_DOANH_NGHIEP_168_2025",
                "doc_title": "Nghị định về đăng ký doanh nghiệp",
                "doc_code": "168/2025/NĐ-CP",
                "doc_type": "decree",
                "issuing_body": "Chính phủ",
                "domain_scope": "doanh_nghiep",
                "domain_subscope": "thu_tuc_ho_so_dang_ky",
                "document_role": "nghi_dinh_thu_tuc",
                "expected_rule_density": "rat_cao",
                "parse_strategy": "uu_tien_thu_tuc_ho_so_thoi_han",
                "is_consolidated_version": "khong",
                "amends_doc_codes": "",
                "has_appendix_forms": "co",
                "priority": "rat_cao",
                "status": "selected",
                "legal_scope_note": "quy định hồ sơ, trình tự, thủ tục đăng ký doanh nghiệp và đăng ký thay đổi",
                "notes": "nhieu_quy_dinh_ve_ho_so_va_thoi_han",
            },
        }

        # Defaults for unknown filenames.
        doc_id = f"DOC_{parts[0]}" if parts and parts[0].isdigit() else stem
        doc_code = "_".join(parts[1:]) if len(parts) >= 2 else stem
        doc_title = stem.replace("_", " ")
        doc_type = "decree" if "nghi_dinh" in filename_key else "law" if "luat" in filename_key else ""
        issuing_body = self._extract_issuing_body(cleaned_text) or ("Chính phủ" if doc_type == "decree" else "")
        domain_scope = "doanh_nghiep"
        domain_subscope = ""
        document_role = ""
        expected_rule_density = "trung_binh"
        parse_strategy = "uu_tien_nghia_vu_quyen_dieu_kien"
        is_consolidated_version = "khong"
        amends_doc_codes = ""
        has_appendix_forms = "khong"
        priority = "cao"
        status = "selected"
        legal_scope_note = ""
        notes = ""

        if filename_key in known_by_filename:
            # Precision-first: exact mapping for seed corpus.
            mapped = known_by_filename[filename_key]
            doc_id = mapped["doc_id"]
            doc_title = mapped["doc_title"]
            doc_code = mapped["doc_code"]
            doc_type = mapped["doc_type"]
            # Keep text parsing first, but do not keep weak guesses.
            issuing_body = self._extract_issuing_body(cleaned_text) or mapped["issuing_body"]
            domain_scope = mapped["domain_scope"]
            domain_subscope = mapped["domain_subscope"]
            document_role = mapped["document_role"]
            expected_rule_density = mapped["expected_rule_density"]
            parse_strategy = mapped["parse_strategy"]
            is_consolidated_version = mapped["is_consolidated_version"]
            amends_doc_codes = mapped["amends_doc_codes"]
            has_appendix_forms = mapped["has_appendix_forms"]
            priority = mapped["priority"]
            status = mapped["status"]
            legal_scope_note = mapped["legal_scope_note"]
            notes = mapped["notes"]
        else:
            # Generic rule-based fallback for future docs.
            parsed_code = self._extract_doc_code(cleaned_text)
            if parsed_code:
                doc_code = parsed_code
            domain_scope = "doanh_nghiep"
            domain_subscope = "khac"
            document_role = "van_ban_khac"
            expected_rule_density = "trung_binh"
            parse_strategy = "uu_tien_nghia_vu_quyen_dieu_kien"

        issue_date = self._extract_first_date(cleaned_text)
        effective_date = self._extract_effective_date(cleaned_text)

        return {
            "doc_id": str(doc_id),
            "doc_code": str(doc_code),
            "doc_title": str(doc_title),
            "doc_type": str(doc_type),
            "issuing_body": str(issuing_body),
            "issue_date": issue_date,
            "effective_date": effective_date,
            "source_file_name": filename,
            "source_format": "doc",
            "domain_scope": str(domain_scope),
            "domain_subscope": str(domain_subscope),
            "document_role": str(document_role),
            "expected_rule_density": str(expected_rule_density),
            "parse_strategy": str(parse_strategy),
            "is_consolidated_version": str(is_consolidated_version),
            "amends_doc_codes": str(amends_doc_codes),
            "has_appendix_forms": str(has_appendix_forms),
            "legal_scope_note": str(legal_scope_note),
            "priority": str(priority),
            "status": str(status),
            "notes": str(notes),
        }

    def _infer_domain_scope(self, doc_type: str, doc_code: str) -> str:
        t = (doc_type or "").lower()
        c = (doc_code or "").lower()
        if "nd-cp" in t or "nd-cp" in c:
            return "regulation"
        if "vbhn" in t or "vpqh" in c:
            return "law_compilation"
        return "legal_corpus"

    def _extract_first_date(self, text: str) -> str | None:
        # Patterns like: "ngày 01 tháng 01 năm 2024"
        m = re.search(
            r"ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}",
            text,
            flags=re.IGNORECASE,
        )
        if not m:
            return None
        return m.group(0)

    def _extract_effective_date(self, text: str) -> str | None:
        # Patterns like: "có hiệu lực từ ngày 01 tháng 01 năm 2025"
        m = re.search(
            r"có\s+hiệu\s+lực\s+từ\s+ngày\s+\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}",
            text,
            flags=re.IGNORECASE,
        )
        if not m:
            return None
        return m.group(0)

    def _extract_doc_code(self, text: str) -> str | None:
        head = text[:3000]

        m_vbhn = re.search(r"\b(\d{1,4})\s*/\s*VBHN-?VPQH\b", head, flags=re.IGNORECASE)
        if m_vbhn:
            return f"{m_vbhn.group(1)}/VBHN-VPQH"

        m_ndcp = re.search(r"\b(\d{1,4})\s*/\s*(\d{4})\s*/\s*N[ĐD]-CP\b", head, flags=re.IGNORECASE)
        if m_ndcp:
            return f"{m_ndcp.group(1)}/{m_ndcp.group(2)}/NĐ-CP"

        return None

    def _extract_issuing_body(self, text: str) -> str | None:
        head_lower = text[:3000].lower()
        if "văn phòng quốc hội" in head_lower:
            return "Văn phòng Quốc hội"
        if "chính phủ" in head_lower:
            return "Chính phủ"
        return None

