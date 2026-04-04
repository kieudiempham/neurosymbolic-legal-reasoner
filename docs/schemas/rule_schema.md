# rule_schema

**Nguồn sự thật:** `data/processed/rulebase/rulebase_seed.xlsx`  
**Mã:** `RuleBuilder`, `RuleSeed`, thứ tự cột `RULEBASE_SEED_COLUMNS` / `_RULEBASE_COLUMNS` trong `law_side/export_to_excel.py` và `run_rulebase_seed_only.py`.  
**Lưu ý:** `src/schemas/rule.py` (Pydantic `RuleRecord` cho suy luận symbolic) là **mô hình runtime khác** — không phải bản sao cột Excel; Excel là ground truth cho pipeline xây dựng rulebase.

---

## 1. Purpose

- **Đầu ra giàu nhất** của nhánh luật: mỗi dòng là một **rule seed** có thể đưa vào answer templates, giải thích, và sau này **JSONL / ProbLog / ontology** — kèm **trace** đầy đủ về nguồn và nhóm.
- Gom **phân loại** (`rule_type`), **nội dung pháp lý** (chủ thể, điều kiện, hành vi, hậu quả), **thời hạn**, **ngưỡng**, **thủ tục / hồ sơ / cơ quan**, **chất lượng** và **pattern trích xuất**.

---

## 2. Position in Pipeline

| Thứ tự | Vai trò |
|--------|---------|
| **Sau** | `predicate_lexicon.xlsx` + toàn bộ interim phía trên |
| **Trước** | Export JSONL / engine suy luận / đánh giá — hiện pipeline cung cấp seed Excel làm bước cuối của `LawRulebasePipeline` |
| **Fan-out** | Một `frame_id` có thể → nhiều `rule_id` (thể hiện qua `extraction_pattern` dạng `*_fanout_*`) |

Stage 5: `RuleBuilder.build(...)`.

---

## 3. Core Entities

- **Rule seed:** một quy tắc pháp lý nguyên tử (ở mức seed), định danh `rule_id`, gắn trace và template.

---

## 4. Column Schema

Nhóm theo `export_to_excel` (khớp thứ tự cột trong code).

### A. Nhận diện & nhóm

| Cột | Kiểu | Bắt buộc | Ý nghĩa |
|-----|------|----------|---------|
| `rule_id` | string | có | Khóa chính duy nhất |
| `rule_group_id` | string | có | Gom nhóm nghiệp vụ — xem `rule_grouping_schema.md` |
| `frame_id` | string | có | Frame nguồn |
| `candidate_id` | string | có | Candidate nguồn |
| `source_unit_id` | string | nên có | Unit gốc |
| `doc_id`, `doc_code` | string | có | Manifest |

### B. Truy vết nguồn

| Cột | Kiểu | Bắt buộc |
|-----|------|----------|
| `source_ref` | string | có |
| `source_ref_full` | string | nên có |
| `heading`, `parent_context` | text | nên có |
| `source_text` | text | có — **văn gốc điều khoản; không chỉnh sửa trong các vòng refine nghiệp vụ** |

### C. Phân loại rule

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `rule_type` | enum | Loại quy tắc — xem mục 5 |
| `tinh_chat_phap_ly` | enum | Bắt buộc / được phép / cấm / … |
| `canonical_predicate` | string | Predicate chuẩn (sau lexicon) |
| `typed_predicate` | string | Predicate có kiểu / slot |
| `predicate_family` | string | Họ predicate |

### D. Nội dung pháp lý cốt lõi

| Cột | Ý nghĩa |
|-----|---------|
| `chu_the`, `loai_chu_the`, `vai_tro_chu_the` | Chủ thể |
| `dieu_kien_ap_dung`, `bieu_thuc_dieu_kien` | Điều kiện (tự nhiên / biểu thức) |
| `hanh_vi_phap_ly`, `doi_tuong_hanh_vi` | Hành vi và đối tượng |
| `he_qua_phap_ly` | Hậu quả pháp lý (grounded, tránh câu chung chung) |

### E. Ngưỡng định lượng

| Cột | Ý nghĩa |
|-----|---------|
| `ten_chi_so` | Tên chỉ số (ví dụ thời hạn, tỷ lệ) |
| `toan_tu_so_sanh` | Toán tử: snapshot `eq`, `>=` |
| `gia_tri_nguong` | Một ngưỡng (một phía) |
| `don_vi_nguong` | `ngay`, `ngay_lam_viec`, `phan_tram`, … |
| `gia_tri_tu`, `gia_tri_den`, `kieu_khoang` | Khoảng — snapshot có thể trống; script `refine_rulebase_seed_round.py` bổ sung khi văn có khoảng |

### F. Thời hạn

| Cột | Ý nghĩa |
|-----|---------|
| `thoi_han_so`, `don_vi_thoi_han`, `moc_tinh_thoi_han`, `bieu_thuc_thoi_han` | Cấu trúc thời hạn |

### G. Thủ tục / hồ sơ / cơ quan

| Cột | Ý nghĩa |
|-----|---------|
| `thanh_phan_ho_so` | Thành phần hồ sơ (có thể `; `) |
| `co_quan_tiep_nhan`, `co_quan_xu_ly` | Cơ quan |
| `ket_qua_thu_tuc` | Kết quả thủ tục |
| `phuong_thuc_thuc_hien` | Phương thức (nộp trực tiếp, qua mạng, …) |

### H. Phạm vi / ngoại lệ / viện dẫn

| Cột | Ý nghĩa |
|-----|---------|
| `pham_vi_ap_dung` | Phạm vi đối tượng áp dụng (không nhầm với điều kiện từng vụ) |
| `ngoai_le` | Ngoại lệ |
| `van_ban_dan_chieu` | Viện dẫn |

### I. Answer / explanation

| Cột | Ý nghĩa |
|-----|---------|
| `answer_template`, `explanation_template` | Mẫu trả lời / giải thích có placeholder |
| `grounded_summary` | Tóm tắt bám văn (thường có tiền tố loại: Hậu quả, Thời hạn, …) |

### J. Chất lượng & trích xuất

| Cột | Ý nghĩa |
|-----|---------|
| `muc_do_day_du` | `rat_day_du`, `kha_day_du`, `day_du`, `thieu_vai_slot` |
| `do_tin_cay_trich_xuat` | Snapshot: thường `trung_binh` |
| `can_ra_soat` | `co` / `khong` |
| `ly_do_can_ra_soat` | Lý do |
| `extraction_pattern` | Mô tả cách tách từ frame — xem mục 5 |
| `notes` | Ghi chú; có thể chứa tag refine (`bo_sung_*`) |

**Vấn đề chất lượng thường gặp:** trùng nội dung `source_text` giữa rule; ngưỡng một phía chưa cấu trúc hóa khoảng; `he_qua_phap_ly` / `thanh_phan_ho_so` nghèo; `kieu_khoang` trống dù cần khoảng — làm **downstream** suy luận / eval khó kiểm chứng.

---

## 5. Controlled Values / Enumerations

**rule_type** (10 giá trị, ~331 dòng):  
`quy_tac_thoi_han`, `quy_tac_ket_qua_phap_ly`, `quy_tac_ho_so`, `quy_tac_nguong_dinh_luong`, `quy_tac_hanh_dong_co_quan`, `quy_tac_ngoai_le`, `quy_tac_nghia_vu`, `quy_tac_dieu_kien`, `quy_tac_thu_tuc`, `quy_tac_quyen`.

**tinh_chat_phap_ly:** `bat_buoc`, `co_the`, `co_trach_nhiem`, `duoc_phep`, `bi_cam`.

**toan_tu_so_sanh:** `eq`, `>=` (ít giá trị hơn số rule ngưỡng — nhiều rule không dùng cột này).

**don_vi_nguong:** `ngay_lam_viec`, `ngay`, `phan_tram`.

**muc_do_day_du:** `rat_day_du`, `kha_day_du`, `day_du`, `thieu_vai_slot`.

**can_ra_soat:** `khong`, `co`.

**extraction_pattern** (ví dụ tần suất cao):  
`khung_hanh_dong_co_quan_fanout_thoi_han`, `khung_ket_qua_phap_ly_fanout_thoi_han`, `khung_thoi_han_fanout_thoi_han`, `khung_ngoai_le_main`, `khung_nguong_dinh_luong_fanout_thoi_han`, … — thể hiện **main** vs **fanout** và loại khung nguồn.

**kieu_khoang:** có thể trống toàn bộ trong snapshot; khi điền: `dong`, `mo_trai`, `mo_phai`, `mo_hai_dau`, `khong_xac_dinh_ro` (theo script refine / quy ước nghiệp vụ).

---

## 6. Quality Checks

| Pass | Fail |
|------|------|
| Mỗi `rule_id` duy nhất; trace `frame_id` / `candidate_id` / `source_ref` đầy đủ | Mất liên kết → không audit được |
| `grounded_summary` + template đồng bộ với slot | Template khác nội dung slot → trả lời sai |
| Ngưỡng: một phía có `gia_tri_nguong` + `toan_tu`; khoảng có `gia_tri_tu`/`gia_tri_den`/`kieu_khoang` khi văn là khoảng | Ngưỡng chỉ nằm trong text → khó export logic |

---

## 7. Relationship to Downstream Files

- Toàn bộ cột pháp lý + trace → **JSONL** (theo schema export tương lai), **ProbLog** (predicate + facts), **ontology** (map `canonical_predicate`, `chu_the`, …).
- `rule_type` + `extraction_pattern` → tài liệu hóa **fan-out** và kiểm thử coverage theo loại rule.
- `rule_group_id` → báo cáo nhóm; không thay thế `rule_id` trong suy luận.

---

## 8. Domain Adaptation Notes

- Bổ sung / điều chỉnh **rule_type** và template khi domain có mẫu quy phạm mới (ví dụ “mức phạt”, “điều kiện hưởng”).
- **Predicate** và **đơn vị ngưỡng** phải đồng bộ với lexicon và đơn vị đo lường domain (ví dụ thuế: đồng, tỷ lệ %).
- Giữ **source_text** bất biến qua các vòng refine; mọi bổ sung vào slot/template phải **grounded**.
