# legal_frame_schema

**Nguồn sự thật:** `data/interim/law_parsing/legal_frames_review.xlsx`  
**Mã:** `LegalFrameExtractor`, dataclass `LegalFrame`, cột `_LEGAL_FRAMES_COLUMNS` trong `law_side/export_to_excel.py`.

---

## 1. Purpose

- Là **tầng làm giàu ngữ nghĩa pháp lý** sau candidate: gom văn bản thành các **slot** có thể kiểm chứng (`chu_the`, `hanh_vi`, `dieu_kien_ap_dung`, thời hạn, hồ sơ, cơ quan, ngoại lệ, ngưỡng, …).
- Frame phải **đủ giàu** để **fan-out** sang nhiều **rule** (thời hạn tách, hậu quả + thủ tục, v.v.) trong `RuleBuilder`; cờ `can_tach_them` / `ly_do_can_tach` ghi nhận khi một frame vẫn còn chứa nhiều mệnh đề.

---

## 2. Position in Pipeline

| Thứ tự | Vai trò |
|--------|---------|
| **Sau** | `candidate_normative_sentences.xlsx` |
| **Trước** | `predicate_lexicon.xlsx` (chuẩn hóa hành vi từ `hanh_vi`) và `rulebase_seed.xlsx` |
| **Enrich** | Tăng **slot richness** cho suy luận và cho rubric; `muc_do_day_du` đánh giá mức đầy đủ trước khi build rule |

Stage 3: `LegalFrameExtractor.extract(normative_sentences)`.

---

## 3. Core Entities

- **Legal frame:** một khung nghĩa vụ / điều kiện / thủ tục / ngưỡng / … đã cấu trúc hóa, một-nhiều với rule sau fan-out.

---

## 4. Column Schema

| Cột | Kiểu | Bắt buộc | Ý nghĩa |
|-----|------|----------|---------|
| `frame_id` | string | có | Khóa chính |
| `candidate_id` | string | có | Nguồn candidate |
| `source_unit_id` | string | nên có | Đơn vị gốc |
| `doc_id`, `doc_code` | string | có | Trace |
| `unit_ref_full`, `source_ref` | string | nên có | Tham chiếu |
| `heading`, `parent_context` | text | nên có | Ngữ cảnh |
| `source_text` | text | có | Văn bản căn cứ |
| `frame_type` | enum-like | có | Tiền tố `khung_*` — xem mục 5 |
| `chu_the` | text | nên có | Chủ thể chịu norm |
| `vai_tro_chu_the` | text | tùy | Vai trò (đại diện PL, cổ đông, …) |
| `hanh_vi` | text | nên có | Động từ / cụm hành vi (surface → lexicon) |
| `doi_tuong_hanh_vi` | text | tùy | Đối tượng tác động |
| `tinh_chat_phap_ly` | enum-like | nên có | `bat_buoc`, `duoc_phep`, `bi_cam`, … |
| `dieu_kien_ap_dung` | text | tùy | Điều kiện áp dụng |
| `dieu_kien_dinh_luong` | text | tùy | Điều kiện có số (mô tả) |
| `nguong_so_luong`, `nguong_ty_le` | text | tùy | Ngưỡng số lượng / tỷ lệ (mô tả) |
| `khoang_gia_tri` | text | tùy | Khoảng giá trị (mô tả) |
| `thanh_phan_ho_so` | text | tùy | Thành phần hồ sơ |
| `co_quan_tiep_nhan`, `co_quan_xu_ly` | text | tùy | Cơ quan |
| `ket_qua_thu_tuc` | text | tùy | Kết quả thủ tục |
| `thoi_han_so`, `don_vi_thoi_han`, `moc_tinh_thoi_han` | text/number | tùy | Thời hạn có cấu trúc |
| `ngoai_le` | text | tùy | Ngoại lệ |
| `van_ban_dan_chieu` | text | tùy | Viện dẫn |
| `ghi_chu_giai_thich` | text | không | Giải thích nội bộ |
| `muc_do_day_du` | enum | nên có | `rat_day_du`, `kha_day_du`, `day_du`, `thieu_vai_slot` |
| `can_tach_them` | co/khong | có | Cần tách thêm rule/frame |
| `ly_do_can_tach` | text | tùy | Lý do |

---

## 5. Controlled Values / Enumerations

**frame_type** (10 giá trị, snapshot ~213 dòng):  
`khung_hanh_dong_co_quan`, `khung_ket_qua_phap_ly`, `khung_thoi_han`, `khung_ngoai_le`, `khung_nguong_dinh_luong`, `khung_dieu_kien`, `khung_nghia_vu`, `khung_ho_so`, `khung_thu_tuc`, `khung_quyen`.

**tinh_chat_phap_ly:** `bat_buoc`, `co_trach_nhiem`, `co_the`, `duoc_phep`, `bi_cam`.

**muc_do_day_du:** `rat_day_du`, `kha_day_du`, `day_du`, `thieu_vai_slot`.

**can_tach_them:** `co`, `khong`.

---

## 6. Quality Checks

| Pass | Fail |
|------|------|
| `frame_id` duy nhất; `candidate_id` tồn tại | Frame không nối được candidate |
| `muc_do_day_du` = `rat_day_du` / `kha_day_du` có đủ slot cho rule đích | `thieu_vai_slot` hàng loạt → rule thiếu `he_qua` / `thoi_han` |
| `can_tach_them` = `co` được xử lý hoặc ghi backlog | Bỏ qua → một `extraction_pattern` fan-out quá tải hoặc trùng nội dung |

---

## 7. Relationship to Downstream Files

- `frame_id` → `rulebase_seed.frame_id` (một frame có thể → nhiều rule qua fan-out).
- `hanh_vi` → `predicate_lexicon.surface_form` / `hanh_vi_chuan` → `canonical_predicate` trong rule.
- `tinh_chat_phap_ly`, điều kiện, thời hạn, hồ sơ → các cột tương ứng trong `rulebase_seed` (`rule_type`, `dieu_kien_ap_dung`, `thoi_han_*`, …).
- `frame_type` → tiền tố trong `rulebase_seed.extraction_pattern` (ví dụ `khung_thoi_han_fanout_thoi_han`).

---

## 8. Domain Adaptation Notes

- Domain mới thường cần **frame_type** mới (ví dụ `khung_thue`, `khung_tranh_chap`) — thống nhất với extractor + rule builder.
- Slot **ngưỡng / khoảng** nên đồng bộ với quy ước số trong rule (đơn vị `ngay` vs `ngay_lam_viec`) để tránh lệch ProbLog.
