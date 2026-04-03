# normative_sentence_schema

**Nguồn sự thật:** `data/interim/law_parsing/candidate_normative_sentences.xlsx`  
**Mã:** `NormativeSentenceDetector`, `NormativeSentence`, export cột `_CANDIDATE_NS_COLUMNS` trong `law_side/export_to_excel.py`.

---

## 1. Purpose

- Là **tầng candidate câu/chuỗi mang tính chuẩn tắc** trích từ legal unit: mục tiêu **cao recall** nhưng vẫn có **lọc ngữ nghĩa** (`candidate_type`, `should_extract_rule`, `candidate_score`).
- Một **unit** có thể sinh **nhiều candidate** (fan-out) — coverage theo điều khoản và theo **loại rule** dự kiến.

---

## 2. Position in Pipeline

| Thứ tự | Vai trò |
|--------|---------|
| **Sau** | `legal_units_review.xlsx` |
| **Trước** | `legal_frames_review.xlsx` (`candidate_id` là khóa nối) |
| **Enrich** | Các trường `*_text` (actor, action, object, condition, deadline, …) làm **slot thô** cho frame; `should_extract_rule` / `extraction_priority` điều tiết **precision** và thứ tự review |

Stage 2 trong `LawRulebasePipeline`: `NormativeSentenceDetector.detect(legal_units)`.

---

## 3. Core Entities

- **Normative sentence (candidate):** một ứng viên đoạn văn có khả năng tạo một hoặc nhiều **legal frame** / **rule**.

---

## 4. Column Schema

| Cột | Kiểu | Bắt buộc | Ý nghĩa |
|-----|------|----------|---------|
| `candidate_id` | string | có | Khóa chính candidate |
| `unit_id` | string | có | Liên kết legal unit |
| `doc_id`, `doc_code` | string | có | Trace manifest |
| `unit_ref_full`, `source_ref` | string | nên có | Tham chiếu đầy đủ |
| `heading`, `parent_context` | text | nên có | Ngữ cảnh |
| `source_text` | text | có | Văn nguồn (thường là căn cứ grounding) |
| `sentence_text` | text | có | Câu/đoạn trích |
| `candidate_type` | enum-like | có | Phân loại ứng viên — xem mục 5 |
| `candidate_subtype` | enum-like | tùy | Tiểu loại (ho_so, cap_giay_chung_nhan, …) |
| `candidate_score` | string/number | tùy | Điểm / hạng máy hoặc sau chỉnh |
| `trigger_patterns` | text | tùy | Mẫu khớp |
| `actor_text` … `legal_effect_text` | text | tùy | Slot: chủ thể, hành vi, đối tượng, điều kiện, thời hạn, cơ quan, hồ sơ, ngoại lệ, ngưỡng, hiệu lực pháp lý |
| `should_extract_rule` | enum | có | Snapshot: `co`, `can_nhac`, `khong` |
| `extraction_priority` | string | tùy | Thứ tự ưu tiên trích |
| `sentence_type` | enum | có | `khoan`, `diem`, `dieu` |
| `normative_pattern` | enum | có | Khối pháp: `nghia_vu`, `thu_tuc`, `ket_qua_phap_ly`, … |
| `subject_span` … `authority_span` | string | tùy | Span debug (offsets hoặc nhãn) |
| `candidate_rule_type` | enum-like | có | Nhãn loại rule dự kiến (khác `candidate_type` — phục vụ rubric) |
| `confidence_manual` | string | tùy | Độ tin sau review tay |
| `ns_id` | string | có | Id nội bộ detector |
| `notes` | text | không | Ghi chú |

**Lỗi thường gặp:** `should_extract_rule` = `co` nhưng slot trống → frame thiếu; `candidate_type` không khớp `normative_pattern` → lệch `frame_type` sau này.

---

## 5. Controlled Values / Enumerations

**candidate_type** (10 giá trị trong snapshot ~218 dòng):  
`ket_qua_phap_ly`, `hanh_dong_co_quan`, `thanh_phan_ho_so`, `thoi_han`, `nguong_so_luong`, `dieu_kien_ap_dung`, `nghia_vu`, `thu_tuc`, `ngoai_le`, `quyen`.

**candidate_subtype:** `ho_so`, `cap_giay_chung_nhan`, `dang_ky_thay_doi`, `xem_xet_ho_so`, `thong_bao`.

**should_extract_rule:** `co`, `can_nhac`, `khong`.

**sentence_type:** `khoan`, `diem`, `dieu`.

**candidate_rule_type** (ví dụ): `hanh_dong_co_quan`, `quy_pham_thoi_han`, `condition`, `ket_qua_phap_ly`, `thanh_phan_ho_so`, `quy_pham_nghia_vu`, `threshold`, `nguong_so_luong`, `quy_pham_quyen`, `quy_pham_ho_so`, `legal_effect`, `ngoai_le`.

**normative_pattern:** `nghia_vu`, `thu_tuc`, `ket_qua_phap_ly`, `thanh_phan_ho_so`, `quyen`, `nguong_so_luong`, `ngoai_le`, `cam`, `ho_so`.

---

## 6. Quality Checks

| Pass | Fail |
|------|------|
| Mỗi `candidate_id` duy nhất; `unit_id` tồn tại | Candidate mồ côi; trùng `candidate_id` |
| Tỷ lệ `should_extract_rule` = `co` có slot đủ để frame | Quá nhiều `co` nhưng `action_text` rỗng → frame/rubric yếu |
| Phân bố `candidate_type` khớp mục tiêu coverage điều/khoản | Chỉ một loại chiếm ưu thế do lệch detector |

---

## 7. Relationship to Downstream Files

- `candidate_id` → `legal_frames_review.candidate_id` → `rulebase_seed.candidate_id`.
- `actor_text` / `action_text` / … → khởi đầu cho `chu_the`, `hanh_vi`, `doi_tuong_hanh_vi` trong frame.
- `threshold_text` → `dieu_kien_dinh_luong` / `nguong_*` / sau đó slot `nguong_*` trong rule.
- `candidate_type` + `normative_pattern` → **`frame_type`** (prefix `khung_*`).

---

## 8. Domain Adaptation Notes

- Bổ sung **candidate_type** / **normative_pattern** khi luật mới có mẫu câu (ví dụ “mức thuế suất”, “hợp đồng vô hiệu”) — cần cập nhật **pattern trong detector**, không chỉ Excel.
- Coverage theo **Điều**: thống kê `sentence_type` + `unit_ref_full` theo `article`; theo **loại rule**: pivot `candidate_type` × văn bản.
