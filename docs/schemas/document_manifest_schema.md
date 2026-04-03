# document_manifest_schema

**Nguồn sự thật:** `data/raw/legal_corpus/manifest/document_manifest.xlsx`  
**Mã tương ứng:** `law_side.doc_loader`, `law_side.export_to_excel.export_document_manifest`, dataclass `LegalDocument` trong `law_side/law_rulebase_models.py`.

---

## 1. Purpose

- Quản lý **danh mục văn bản pháp luật** được đưa vào pipeline (một dòng = một văn bản nguồn `.doc` / định dạng đã cấu hình).
- Ghi **bối cảnh domain**, **vai trò văn bản**, **chiến lược parse** và **mức độ ưu tiên** để team và pipeline biết *văn nào quan trọng*, *trích xuất theo hướng nào* (ưu tiên nghĩa vụ/quyền/điều kiện hay thủ tục/hồ sơ/thời hạn).
- Là **điểm neo đầu vào**: mọi `doc_id` / `doc_code` ở các bước sau phải khớp manifest (hoặc được sinh từ cùng lô ingest).

---

## 2. Position in Pipeline

| Thứ tự | Vai trò |
|--------|---------|
| **Sau** | Không có file Excel trước; sinh từ **Stage 0** — nạp file gốc trong `data/raw/legal_corpus/doc/` (theo `configs/law_rulebase_pipeline.yaml`). |
| **Trước** | `legal_units_review.xlsx` — đơn vị cấu trúc gắn `doc_id` / `doc_code` từ manifest. |
| **Enrich** | `domain_scope` / `domain_subscope` / `document_role` / `expected_rule_density` / `parse_strategy` điều hướng **recall vs độ sâu slot** (segmenter + detector đọc cấu hình; manifest là bản ghi nhân bản cho người đọc và audit). |

Pipeline end-to-end: `LawRulebasePipeline.run()` trong `law_side/law_rulebase_pipeline.py` (Stage 0 → export manifest).

---

## 3. Core Entities

- **Entity chính:** một **tài liệu pháp lý** (`LegalDocument`) — không phải điều khoản hay câu.

---

## 4. Column Schema

| Cột | Kiểu thực tế | Bắt buộc | Ý nghĩa | Ví dụ / ghi chú |
|-----|----------------|----------|---------|-----------------|
| `doc_id` | string | có | Định danh nội bộ ổn định | Theo pipeline generate |
| `doc_code` | string | có | Mã hiển thị (số hiệu văn bản) | VD: mã VBHN, NĐ |
| `doc_title` | string | có | Tên đầy đủ | |
| `doc_type` | enum-like string | có | Loại văn | Trong snapshot: `law`, `decree` |
| `issuing_body` | string | có | Cơ quan ban hành | |
| `issue_date` | string / date text | tùy | Ngày ban hành | Có thể rỗng tùy nguồn |
| `effective_date` | string | tùy | Ngày hiệu lực | |
| `source_file_name` | string | có | Tên file gốc | VD: `.doc` |
| `source_format` | string | có | Định dạng | |
| `domain_scope` | enum-like | nên có | Phạm vi luật chính | Snapshot: `doanh_nghiep` |
| `domain_subscope` | enum-like | nên có | Tiểu domain | VD: `quyen_nghia_vu_quan_tri_dang_ky`, `thu_tuc_ho_so_dang_ky` |
| `document_role` | enum-like | nên có | Vai trò trong bộ tài liệu | Snapshot: `van_ban_hop_nhat`, `nghi_dinh_thu_tuc` |
| `expected_rule_density` | enum-like | nên có | Kỳ vọng mật độ rule | Snapshot: `rat_cao` |
| `parse_strategy` | enum-like | nên có | Ưu tiên trích xuất | Snapshot: `uu_tien_nghia_vu_quyen_dieu_kien`, `uu_tien_thu_tuc_ho_so_thoi_han` |
| `is_consolidated_version` | string/bool-like | tùy | Bản hợp nhất? | |
| `amends_doc_codes` | string | tùy | Văn bị sửa đổi/bổ sung | |
| `has_appendix_forms` | string | tùy | Có phụ lục biểu mẫu | |
| `legal_scope_note` | text | tùy | Ghi chú phạm vi áp dụng | |
| `priority` | enum-like | nên có | Ưu tiên xử lý | Snapshot: `rat_cao` |
| `status` | enum-like | nên có | Trạng thái chọn/lọc | Snapshot: `selected`; model mặc định `seed_first_pass` trước export |
| `notes` | text | không | Ghi chú người annotate | |

**Lỗi thường gặp:** `doc_id` lệch giữa manifest và đơn vị pháp sau → downstream join hỏng; `parse_strategy` trống → khó tái lập lý do ưu tiên pattern.

---

## 5. Controlled Values / Enumerations

Giá trị dưới đây lấy từ **snapshot hiện tại** (2 dòng); domain mới cần **mở rộng có kiểm soát**, không bịa thêm nếu chưa có trong dữ liệu.

- `doc_type`: `law`, `decree`
- `document_role`: `van_ban_hop_nhat`, `nghi_dinh_thu_tuc`
- `parse_strategy`: `uu_tien_nghia_vu_quyen_dieu_kien`, `uu_tien_thu_tuc_ho_so_thoi_han`
- `domain_scope`: `doanh_nghiep`
- `domain_subscope`: `quyen_nghia_vu_quan_tri_dang_ky`, `thu_tuc_ho_so_dang_ky`
- `priority`: `rat_cao`
- `status`: `selected`
- `expected_rule_density`: `rat_cao`

---

## 6. Quality Checks

| Pass | Fail / rủi ro |
|------|----------------|
| Mỗi văn có `doc_id` + `doc_code` + `source_file_name` khớp file thật | Trùng `doc_id` hai dòng; file nguồn không tồn tại |
| `domain_scope` / `document_role` / `parse_strategy` đồng bộ với mục tiêu nghiên cứu | `parse_strategy` trống → downstream không giải thích được lệch recall giữa hai văn |
| `priority` + `status` phản ánh lựa chọn corpus | `status` không khớp thực tế (văn bị loại vẫn để `selected`) |

---

## 7. Relationship to Downstream Files

- `doc_id`, `doc_code` → **mọi** bảng: `legal_units_review`, `candidate_normative_sentences`, `legal_frames_review`, `rulebase_seed`.
- `domain_scope` / `domain_subscope` → định hướng **mở rộng ontology** và **predicate_lexicon**; không cột trực tiếp trong rule nhưng giải thích *tại sao* một số nhóm hành vi xuất hiện.
- `parse_strategy` → liên kết mềm với tỷ lệ `deontic_signal` / `candidate_type` (so sánh thống kê giữa hai văn).

---

## 8. Domain Adaptation Notes

Khi chuyển sang **thuế / lao động / dân sự**:

- Bổ sung giá trị `domain_scope` / `domain_subscope` mới (ví dụ `thue`, `lao_dong`) và **ghi rõ trong manifest** trước khi chạy pipeline.
- Điều chỉnh `document_role` (luật chuyên ngành, NĐ hướng dẫn, thông tư) và `expected_rule_density` để đội biết nơi cần **rà soát thủ công** nhiều.
- `parse_strategy` nên có **nhãn mới** phản ánh ưu tiên (ví dụ ưu tiên điều kiện hưởng / mức thuế) — thống nhất trong config + manifest.
