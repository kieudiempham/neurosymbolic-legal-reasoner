# rule_grouping_schema

**Nguồn sự thật:** Không có file Excel riêng tên `rule_grouping`. Thông tin **gom nhóm** được **vật liệu hóa** trong `data/processed/rulebase/rulebase_seed.xlsx` (cột `rule_group_id`) và trong mã sinh rule (`RuleBuilder`, `rule_group_id` trên `RuleSeed` trong `law_side/law_rulebase_models.py`).

---

## 1. Purpose

- **Gom các rule** xuất phát từ cùng một **cụm thủ tục / cùng mẫu fan-out / cùng khía cạnh pháp lý** để quản lý trace, dedup và báo cáo theo nhóm.
- Hỗ trợ **truy vết**: cùng một `frame_id` có thể sinh nhiều `rule_id`; `rule_group_id` cho phép nhóm các rule “cùng họ” mà không gộp một dòng.

---

## 2. Position in Pipeline

| Thứ tự | Vai trò |
|--------|---------|
| **Sau** | Legal frame + predicate normalization |
| **Cùng file** | `rulebase_seed.xlsx` — không phải bước export riêng |
| **Dùng cho** | Đọc nhóm trong review, chuẩn bị dedup / báo cáo coverage theo nhóm; **chưa** thấy bảng `merged_rule_ids` hay fingerprint nội dung trong Excel hiện tại |

---

## 3. Core Entities

- **Rule group:** một nhãn logic `rule_group_id` gắn cho nhiều dòng rule; quan hệ với `frame_id`, `candidate_id`, `source_ref` để trace.

---

## 4. Column Schema (trong rulebase_seed)

| Cột | Kiểu | Bắt buộc | Ý nghĩa |
|-----|------|----------|---------|
| `rule_group_id` | string | có (trong snapshot đủ 331 dòng) | Định danh nhóm — ví dụ tiền tố `RG_LUATDN_...` gắn với điều khoản / mẫu thủ tục |
| `frame_id` | string | có | Khung nguồn (một frame → nhiều rule) |
| `candidate_id` | string | có | Candidate nguồn |
| `source_unit_id` | string | nên có | Unit gốc |
| `source_ref` | string | có | Tham chiếu văn bản |

**Không có trong snapshot:** cột `merged_rule_ids`, `fingerprint`, bảng grouping độc lập — nếu cần, phải **thiết kế thêm** và ghi rõ phiên bản pipeline.

---

## 5. Controlled Values / Enumerations

- `rule_group_id`: **~93 giá trị khác nhau** trên 331 rule (snapshot) — định dạng có cấu trúc (ví dụ `RG_LUATDN_D113_K1_CAP_GIAY_CHUNG_NHAN_DANG_KY`, `RG_LUATDN_D113_K1_AP_DUNG_QUY_DINH_LOAI_TRU`). Không liệt kê hết tại đây; coi file Excel là danh sách đầy đủ.

---

## 6. Quality Checks

| Pass | Fail |
|------|------|
| Mỗi rule có `rule_group_id` khi pipeline yêu cầu nhóm | `rule_group_id` trống hoặc lệch format → khó pivot theo nhóm |
| Cùng `rule_group_id` thực sự cùng mục đích nhóm (kiểm thử thủ công trên mẫu) | Gán nhóm sai → dedup / báo cáo sai |

---

## 7. Relationship to Downstream Files

- `rule_group_id` có thể đi kèm export **JSONL** / **ProbLog** như nhãn nhóm (meta) — không bắt buộc trong logic suy luận nếu chỉ cần `rule_id`.
- `extraction_pattern` (cùng file rulebase) mô tả **cách fan-out** từ frame (ví dụ `khung_thoi_han_fanout_thoi_han`) — bổ sung ngữ cảnh cho “nhóm” thao tác trích xuất, khác với `rule_group_id` mang tính **nghiệp vụ pháp lý**.

---

## 8. Domain Adaptation Notes

- Domain mới: quy ước đặt tên `rule_group_id` (prefix RG + mã văn + mã điều + khái niệm ngắn) nên **ổn định** trước khi scale.
- Nếu sau này cần **dedup theo nội dung**, nên thêm cột hoặc bảng phụ (hash nội dung) — hiện **chưa có** trong Excel.
