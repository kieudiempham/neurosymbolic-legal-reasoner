# legal_unit_schema

**Nguồn sự thật:** `data/interim/law_parsing/legal_units_review.xlsx`  
**Mã:** `LegalSegmenter`, export `export_to_excel`, dataclass `LegalUnit` trong `law_side/law_rulebase_models.py`.

---

## 1. Purpose

- Là **tầng phân đoạn cấu trúc + gợi ý ngữ nghĩa** đầu tiên trên văn bản đã làm sạch: mỗi dòng ≈ một **đơn vị** (Điều / Khoản / Điểm / …) với văn bản đầy đủ và ngữ cảnh cha.
- Cung cấp **marker** (`has_*_marker`, `deontic_signal`) để tầng candidate **nhớ lại** câu nào có khả năng sinh quy tắc — ảnh hưởng trực tiếp **recall** candidate.

---

## 2. Position in Pipeline

| Thứ tự | Vai trò |
|--------|---------|
| **Sau** | `document_manifest.xlsx` + nội dung văn bản đã load (`DocLoader`). |
| **Trước** | `candidate_normative_sentences.xlsx` — mỗi candidate gắn `unit_id` và trích dẫn `source_ref`. |
| **Enrich** | `deontic_signal` + `has_*_marker` + `actor_hint` / `action_hint` / `object_hint` tăng **precision** của detector (lọc sớm) và **fan-out** hợp lý; `needs_split` cảnh báo đơn vị cần tách thêm trước khi gán rule. |

Stage 1 trong `LawRulebasePipeline`: `LegalSegmenter.segment(doc)`.

---

## 3. Core Entities

- **Legal unit:** một khối văn có ranh giới cấu trúc (điều/khoản/điểm), định danh bởi `unit_id`.

---

## 4. Column Schema

| Cột | Kiểu | Bắt buộc | Ý nghĩa pháp lý / kỹ thuật |
|-----|------|----------|----------------------------|
| `unit_id` | string | có | Khóa chính nội bộ |
| `doc_id`, `doc_code` | string | có | Liên kết manifest |
| `chapter`, `section`, `article`, `clause`, `point` | string / rỗng | tùy | Cấu trúc pháp điển |
| `unit_type` | enum-like | có | `dieu` / `khoan` / `diem` (snapshot: chủ yếu `khoan`, `diem`, `dieu`) |
| `unit_ref_full` | string | nên có | Chuỗi tham chiếu đầy đủ (hiển thị + trace) |
| `sentence_index`, `subsentence_index` | int | có | Chỉ số câu trong đơn vị |
| `list_item_marker` | string | tùy | Đánh dấu list (a), b), …) |
| `heading` | text | tùy | Tiêu đề đơn vị |
| `text` | text | có | Nội dung đơn vị cần parse |
| `parent_context` | text | nên có | Ngữ cảnh cấp trên (giảm ambiguity) |
| `deontic_signal` | enum-like | nên có | Gợi ý khối pháp lý: snapshot gồm `nghia_vu`, `dieu_kien`, `dinh_nghia_ho_tro`, `co_trach_nhiem`, `quyen`, `thoi_han`, `cam_doan`, `mo_ta_pham_vi`, `ho_so`, `hanh_dong_co_quan`, `co_the`, `thu_tuc`, `ngoai_le`, … |
| `topic_tag` | string | tùy | Sau detector: có thể gán theo `candidate_rule_type` |
| `normative_signal` | string | tùy | Theo `normative_pattern` từ candidate |
| `has_condition_marker` | co/khong (string trong Excel) | có | Có dấu hiệu điều kiện |
| `has_deadline_marker` | co/khong | có | Có thời hạn |
| `has_document_marker` | co/khong | có | Có hồ sơ / tài liệu |
| `has_authority_marker` | co/khong | có | Có cơ quan |
| `has_exception_marker` | co/khong | có | Có ngoại lệ |
| `has_threshold_marker` | co/khong | có | Có ngưỡng định lượng |
| `has_cross_reference` | co/khong / bool | tùy | Viện dẫn chéo |
| `cross_reference_text` | text | tùy | Trích đoạn viện dẫn |
| `actor_hint`, `action_hint`, `object_hint` | text | tùy | Gợi ý chủ thể / hành vi / đối tượng (heuristic) |
| `rule_density_estimate` | string | có | Ước lượng mật độ rule (mặc định code: `thap`) |
| `needs_split` | co/khong | có | Cần tách đơn vị nhỏ hơn |
| `split_reason` | text | tùy | Lý do |
| `is_candidate_rule_sentence` | bool / True-False string | có | Có phải câu ứng viên rule (sau detector cập nhật) |
| `source_ref` | string | có | Tham chiếu nguồn cho trace |
| `notes` | text | không | Ghi chú review |

**Lỗi semantic thường gặp:** `deontic_signal` = `dinh_nghia_ho_tro` hoặc `mo_ta_pham_vi` nhưng vẫn bật `is_candidate_rule_sentence` → noise rule downstream; `needs_split` = `co` nhưng không xử lý → frame/rule dính nhiều mệnh đề không kiểm soát được.

---

## 5. Controlled Values / Enumerations

**unit_type** (snapshot ~2509 dòng): `khoan`, `diem`, `dieu`.

**deontic_signal** (13 giá trị trong dữ liệu):  
`nghia_vu`, `dieu_kien`, `dinh_nghia_ho_tro`, `co_trach_nhiem`, `quyen`, `thoi_han`, `cam_doan`, `mo_ta_pham_vi`, `ho_so`, `hanh_dong_co_quan`, `co_the`, `thu_tuc`, `ngoai_le`.

**needs_split:** `khong`, `co`.

**has_*_marker:** `co`, `khong`.

**is_candidate_rule_sentence:** `True`, `False` (kiểu chuỗi trong Excel export).

---

## 6. Quality Checks

| Pass | Fail |
|------|------|
| `unit_id` duy nhất; mọi `doc_id` tồn tại trên manifest | Trùng `unit_id`; `text` rỗng |
| Tỷ lệ `has_*` khớp mẫu đọc thủ công trên mẫu nhỏ | Marker luôn `khong` dù văn có “phải”, “trong thời hạn”, “hồ sơ gồm” → candidate recall sụt |
| `needs_split` = `co` có `split_reason` hoặc backlog xử lý | Bỏ qua split → frame/rule chứa nhiều hành vi trộn |

---

## 7. Relationship to Downstream Files

- `unit_id` → `candidate_normative_sentences.unit_id`; `source_unit_id` ở frame/rule trỏ về đơn vị gốc.
- `deontic_signal` + `has_*_marker` → định hướng **loại candidate** (`candidate_type`, `normative_pattern`).
- `text` + `parent_context` → nguồn **grounding** cho `source_text` ở candidate / frame / rule.

---

## 8. Domain Adaptation Notes

- Luật chuyên ngành thường có **cấu trúc điều khoản khác** — có thể cần điều chỉnh `LegalSegmenter` (không chỉ schema Excel).
- Bổ sung giá trị `deontic_signal` / marker khi xuất hiện mẫu mới (ví dụ “chế tài”, “mức phạt”) và cập nhật detector tương ứng.
- Nếu văn song ngữ hoặc có bảng, `needs_split` và `split_reason` càng quan trọng để tránh **một unit chứa nhiều quy tắc độc lập**.
