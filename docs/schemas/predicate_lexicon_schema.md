# predicate_lexicon_schema

**Nguồn sự thật:** `data/processed/ontology/predicate_lexicon.xlsx`  
**Mã:** `PredicateNormalizer.build_predicate_lexicon`, `PredicateLexiconEntry`, export `_PREDICATE_LEXICON_COLUMNS` trong `law_side/export_to_excel.py`.

---

## 1. Purpose

- Chuẩn hóa **cụm hành vi** từ `hanh_vi` (surface) trong legal frame sang **predicate** có thể truy vết: hai tầng **`hanh_vi_chuan`** và **`hanh_vi_chuan_chi_tiet`** để vừa **gom nhóm** vừa **giữ chi tiết** phục vụ suy luận và không gộp quá thô làm mất khác biệt pháp lý.
- Ghi **nhóm hành vi** (`nhom_hanh_vi`) và **gợi ý slot bắt buộc** (`can_thoi_han`, `can_ho_so`, `can_ngoai_le`, `can_nguong_dinh_luong`) để rule builder / evaluation biết rule cần kiểm tra thêm trường nào.

---

## 2. Position in Pipeline

| Thứ tự | Vai trò |
|--------|---------|
| **Sau** | `legal_frames_review.xlsx` |
| **Trước** | `rulebase_seed.xlsx` — `canonical_predicate` / `typed_predicate` / `predicate_family` lấy từ ánh xạ surface → chuẩn |
| **Normalization** | Giảm phân tán từ khóa đồng nghĩa (`bien_the_ngon_ngu`, `surface_form`) → **precision** ontology và **trace** ngược văn bản |

Stage 4 trong `LawRulebasePipeline`.

---

## 3. Core Entities

- **Predicate lexicon entry:** một dòng ánh xạ từ **một surface** (hoặc nhóm biến thể) sang **predicate chuẩn** + metadata nhóm và cờ slot.

---

## 4. Column Schema

| Cột | Kiểu | Bắt buộc | Ý nghĩa |
|-----|------|----------|---------|
| `predicate_id` | string | có | Khóa dòng |
| `surface_form` | string | có | Cụm hành vi như xuất hiện / đại diện |
| `bien_the_ngon_ngu` | text | tùy | Các cách diễn đạt khác (có thể phân tách bằng `;` hoặc chuỗi dài — theo thực tế file) |
| `hanh_vi_chuan` | string | có | Tầng gộp (ví dụ nhóm hành vi đăng ký) |
| `hanh_vi_chuan_chi_tiet` | string | nên có | Tầng chi tiết (phân biệt nộp / cấp / thay đổi) |
| `nhom_hanh_vi` | enum-like | nên có | Nhóm nghiệp vụ — xem mục 5 |
| `chu_the_mac_dinh` | text | tùy | Chủ thể mặc định khi văn bản không nêu rõ |
| `doi_tuong_mac_dinh` | text | tùy | Đối tượng mặc định |
| `co_quan_mac_dinh` | text | tùy | Cơ quan mặc định |
| `can_thoi_han` | co/khong | có | Predicate này thường đi kèm thời hạn |
| `can_ho_so` | co/khong | có | Cần slot hồ sơ |
| `can_ngoai_le` | co/khong | có | Cần xét ngoại lệ |
| `can_nguong_dinh_luong` | co/khong | có | Cần ngưỡng định lượng |
| `ghi_chu_ap_dung` | text | không | Ghi chú phạm vi dùng |

**Vì sao không gộp quá thô:** Nếu chỉ một `hanh_vi_chuan` chung cho mọi biến thể “đăng ký”, sẽ mất phân biệt giữa **đăng ký thành lập** và **đăng ký thay đổi** — ảnh hưởng `rule_type` và kiểm chứng điều kiện. Tầng `hanh_vi_chuan_chi_tiet` giữ lớp phân hóa đó.

**Snapshot hiện tại:** `can_ngoai_le` và `can_nguong_dinh_luong` đều là `khong` trên toàn bộ 25 dòng — phản ánh **lexicon Luật DN lô hiện tại**, không có nghĩa luật không có ngoại lệ; khi mở rộng văn bản cần cập nhật cờ.

---

## 5. Controlled Values / Enumerations

**nhom_hanh_vi** (11 giá trị trong snapshot):  
`dang_ky`, `nop_ho_so`, `uy_quyen_va_lay_y_kien`, `cap_nhat`, `cap_giay`, `chi_nhanh_van_phong_dai_dien`, `hanh_dong_co_quan`, `von_va_gop_von`, `yeu_cau_bao_cao`, `thong_bao`, `thu_hoi`.

**can_thoi_han / can_ho_so / can_ngoai_le / can_nguong_dinh_luong:** `co`, `khong` (trong snapshot chủ yếu `khong` trừ vài dòng `can_thoi_han` / `can_ho_so` = `co`).

---

## 6. Quality Checks

| Pass | Fail |
|------|------|
| `predicate_id` duy nhất; mỗi `surface_form` có `hanh_vi_chuan` rõ | Trùng surface hai dòng khác chuẩn → rule `typed_predicate` không ổn định |
| `bien_the_ngon_ngu` bao phủ biến thể thực tế trong frame | Thiếu biến thể → các frame vẫn dùng surface lạ không map được |
| Cờ `can_*` khớp quy tắc nghiệp vụ đã thống nhất | Cờ sai → evaluation báo thiếu slot dù văn không yêu cầu |

---

## 7. Relationship to Downstream Files

- `hanh_vi_chuan` / `hanh_vi_chuan_chi_tiet` → `rulebase_seed.canonical_predicate`, `typed_predicate`, `predicate_family`.
- `surface_form` + `bien_the_ngon_ngu` → tra cứu khi **reverse** từ rule về văn gốc hoặc khi mở rộng corpus.
- Cờ `can_*` → kiểm tra tính đầy đủ rule (`muc_do_day_du`, `can_ra_soat`).

---

## 8. Domain Adaptation Notes

- Domain **thuế / lao động**: bổ sung **nhom_hanh_vi** mới (khai báo, khấu trừ, giải quyết tranh chấp) và **predicate** tương ứng; tránh tái dụng `hanh_vi_chuan` của doanh nghiệp cho khái niệm không tương đương.
- Khi có nhiều **thuật ngữ đồng nghĩa địa phương**, mở rộng `bien_the_ngon_ngu` thay vì tạo `predicate_id` trùng nghĩa.
- Nếu cần ontology OWL/JSONL: export từ lexicon nên giữ **predicate_id** ổn định qua phiên bản.
