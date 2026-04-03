# Xuất `rulebase_seed.xlsx` sang JSONL và logic JSON

## Mục đích

- **`rulebase.jsonl`**: một dòng = một rule, cấu trúc phân khối (identity, provenance, classification, …), giữ **toàn bộ** cột Excel (ô trống → `null`) để retrieval, audit, sinh câu trả lời, ontology.
- **`rulebase_logic.json`**: mảng các biểu diễn **có cấu trúc** (`head` / `body` / `auxiliary_clauses` / `metadata`) phục vụ suy luận symbolic, chuyển tiếp ProbLog/Datalog/engine tùy chỉnh, **không** cắt bỏ nội dung pháp lý: phần chưa atom hóa được nằm trong `metadata.raw_fields_preserved` và `body` dạng `raw_text`.

## Cách sinh

Từ thư mục gốc repo:

```text
python scripts/export_rulebase_formats.py
```

Mặc định:

- Đầu vào: `data/processed/rulebase/rulebase_seed.xlsx`
- Đầu ra: `data/processed/rulebase/rulebase.jsonl`, `data/processed/rulebase/rulebase_logic.json`

Script **không** sửa file Excel.

---

## Schema JSONL (ổn định)

Các khối và khóa cố định (xem `law_side/rulebase_export_formats.JSONL_BLOCKS`):

- `identity`: `rule_id`, `rule_group_id`, `frame_id`, `candidate_id`, `source_unit_id`
- `provenance`: `doc_id`, `doc_code`, `source_ref`, `source_ref_full`, `heading`, `parent_context`, `source_text`, `van_ban_dan_chieu`
- `classification`: `rule_type`, `tinh_chat_phap_ly`, `canonical_predicate`, `typed_predicate`, `predicate_family`
- `core_legal_content`: chủ thể, điều kiện, hành vi, hậu quả, `pham_vi_ap_dung`, …
- `threshold`, `deadline`, `dossier`, `authority`, `exception`
- `generation_support`: `grounded_summary`, `answer_template`, `explanation_template`
- `quality`: độ đầy đủ, độ tin cậy, `can_ra_soat`, `extraction_pattern`, `notes`

---

## Schema logic JSON

Mỗi phần tử trong `rules[]`:

| Trường | Ý nghĩa |
|--------|---------|
| `rule_id`, `rule_group_id`, `rule_type` | Định danh và loại quy tắc gốc |
| `logic_form` | Dạng suy luận: `obligation`, `permission`, `deadline`, `threshold`, … (ánh xạ từ `rule_type`) |
| `head` | `{ "predicate": "...", "args": [ ... ] }` — kết luận / mệnh đề chính |
| `body` | Danh sách mệnh đề điều kiện; có thể chứa `{ "type": "raw_text", "field": "...", "text": "..." }` khi chưa tách atom sạch |
| `auxiliary_clauses` | Các mệnh đề phụ cùng `rule_id` (deadline, hồ sơ, cơ quan, ngưỡng phụ) khi rule chính không phải loại đó nhưng slot vẫn có dữ liệu |
| `metadata` | `tinh_chat_phap_ly`, predicate, `provenance` (doc, source_ref, source_text), `review`, `raw_fields_preserved` |

File bọc ngoài gồm `version`, `source_file`, `rule_count`, `rule_type_to_logic_form`.

---

## Ánh xạ `rule_type` → `logic_form`

| `rule_type` | `logic_form` |
|-------------|----------------|
| `quy_tac_nghia_vu` | `obligation` |
| `quy_tac_quyen` | `permission` |
| `quy_tac_cam_doan` | `prohibition` |
| `quy_tac_thoi_han` | `deadline` |
| `quy_tac_ho_so` | `dossier` |
| `quy_tac_hanh_dong_co_quan` | `authority_action` |
| `quy_tac_ngoai_le` | `exception_rule` |
| `quy_tac_nguong_dinh_luong` | `threshold` |
| `quy_tac_ket_qua_phap_ly` | `legal_effect` |
| `quy_tac_dieu_kien` | `applicability_condition` |
| `quy_tac_thu_tuc` | `procedure_step` |

Loại không khớp bảng → `logic_form` = `generic_rule`.

---

## Quy tắc “suy luận giàu”

- **Ngưỡng:** Nếu có `gia_tri_tu` và `gia_tri_den` → `head` dùng `threshold_range`; ngược lại → `threshold` với `gia_tri_nguong` / `toan_tu_so_sanh`.
- **Thời hạn phụ:** Nếu rule chính không phải `quy_tac_thoi_han` nhưng có `thoi_han_so`, thêm `auxiliary_clauses` kiểu `deadline_fact`.
- **Hồ sơ phụ:** Tương tự với `dossier_fact` khi có `thanh_phan_ho_so` nhưng loại chính không phải `quy_tac_ho_so`.
- **Ngoại lệ:** Văn bản `ngoai_le` vẫn có trong JSONL; trong logic, gắn vào `body` / `head` tùy loại, và giữ trong `metadata.raw_fields_preserved`.

---

## Kiểm tra chất lượng sau export

1. Số dòng JSONL = số dòng Excel (trừ header).
2. Số phần tử `rules` trong logic JSON = số rule.
3. Mỗi `rule_id` trong JSONL khớp một `rule_id` trong `rules`.
4. Soát nhanh: các `rule_type` quan trọng có `head`/`body` không rỗng hoặc có `metadata` đầy đủ.

---

## Hướng chuẩn hóa thêm (ProbLog / ontology “đẹp” hơn)

- Chuẩn hóa **mã chủ thể / hành vi** sang ID ontology thay vì chuỗi tiếng Việt đầy đủ trong `args`.
- Tách `dieu_kien_ap_dung` từ `raw_text` sang các atom logic (hiện giữ nguyên trong `body` khi chưa parse).
- Thống nhất đơn vị thời gian (`ngay` vs `ngay_lam_viec`) trong một taxonomy.
- Với khoảng ngưỡng, map `kieu_khoang` sang functor riêng (đóng/mở đầu).
