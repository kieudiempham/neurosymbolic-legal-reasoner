# Đặc tả: controlled vocabulary (bước nền trước chuẩn hóa rule)

## Mục đích

Trước khi gán lại `canonical_*` trực tiếp lên `rulebase_seed.xlsx` hoặc trước khi xuất logic/JSONL/ontology, cần một **lớp từ vựng kiểm soát** để:

- giảm trùng lặp do diễn đạt khác nhau;
- giữ **phân hóa pháp lý** (không gộp quá thô);
- làm nền cho **suy luận giàu** (predicate / object / effect / subject / metric tách bạch).

File `rulebase_seed.xlsx` **không bị sửa** ở bước này. Đầu ra là bảng trung gian + đặc tả này.

---

## Đầu ra bắt buộc

| Tệp | Mô tả |
|-----|--------|
| `data/processed/ontology/controlled_vocabulary.xlsx` | Năm sheet: `predicate_vocabulary`, `object_vocabulary`, `effect_vocabulary`, `subject_authority_scope`, `metric_vocabulary` |

Sinh bằng:

```text
python scripts/build_controlled_vocabulary.py
python scripts/refine_controlled_vocabulary.py
```

Bước `refine_controlled_vocabulary.py` ghi đè cùng file: tách điều kiện/ngoại lệ khỏi `effect_canonical`, lọc object “cue”, chuyển hành vi sang `predicate_vocabulary`, bổ sung metric/entity, thêm sheet `modifier_fragments`.

Tùy chọn build: `--no-lexicon` để không gộp thêm hàng từ `predicate_lexicon.xlsx`.

---

## Nguyên tắc thiết kế (tóm tắt)

### Predicate (3 tầng)

- **`predicate_family`**: nhóm rộng (đăng ký, cấp giấy, thông báo, …) — lấy từ cột `predicate_family` nếu có, hoặc suy từ tiền tố `predicate_canonical`.
- **`predicate_canonical`**: `snake_case`, không dấu — ưu tiên cột `canonical_predicate`; nếu trống thì suy từ `hanh_vi_phap_ly`.
- **`predicate_typed`**: ưu tiên `typed_predicate`; nếu trống thì gợi ý dạng `rule_type:canonical`.

### Object

- Gom từ `doi_tuong_hanh_vi` và từng mục tách từ `thanh_phan_ho_so` (phân tách `;`).
- **`object_family`**: suy luận nhẹ (hồ sơ / vốn / cổ phần / GCN / …) — cần review tay khi domain mới.

### Effect

- Gom từ `he_qua_phap_ly` và `ket_qua_thu_tuc`.
- **`effect_family`**: suy từ tiền tố (`duoc_`, `bi_`, `phai_`, …) hoặc nhóm (cấp giấy, thu hồi, cập nhật CSDL, …).

### Subject / authority / scope

- Cột nguồn: `chu_the`, `loai_chu_the`, `vai_tro_chu_the`, `co_quan_tiep_nhan`, `co_quan_xu_ly`, `pham_vi_ap_dung`.
- **`entity_kind`**: `subject` | `subject_type` | `subject_role` | `authority` | `scope`.
- **`canonical_name`**: `snake_case` từ văn bản; **`raw_variants`**: gom các chuỗi gốc khác nhau map cùng id.

### Metric (ngưỡng)

- Ưu tiên các dòng `rule_type = quy_tac_nguong_dinh_luong`; nếu không đủ dữ liệu thì dùng toàn bộ rule có `ten_chi_so` / `don_vi_nguong`.
- **`metric_canonical`**: từ `ten_chi_so`; **`unit_canonical`**: từ `don_vi_nguong`.

---

## Hàm chuẩn hóa chuỗi → id

Module `law_side/controlled_vocabulary_builder.py` dùng:

- chuyển `đ` → `d`, bỏ dấu Unicode (NFD + lọc ký tự kết hợp);
- lowercase, ký tự không chữ-số → `_`, gộp `_` dư.

Đây là bước **tự động**; các cụm đồng nghĩa cần map tay sẽ thấy trong **`raw_variants`** (object, entity, metric).

---

## Kiểm tra chất lượng (I)

1. **Không tạo canonical trùng chỉ vì khác dấu cách** — đã gom qua `to_snake_id`.
2. **Không gom hai khác biệt pháp lý** — nếu hai câu khác nghĩa nhưng cùng slug, sẽ thấy `raw_variants` dài / đa dạng → **cần tách tay** canonical.
3. **Ưu tiên nhất quán** — bảng này là bản nháp tự động + review.

Mỗi sheet vocabulary có thêm **`can_ra_soat`** (`co` | `khong`) và **`do_tin_cay`** (`cao` | `trung_binh` | `thap`), gán bằng heuristic trong `controlled_vocabulary_builder.py` (`_predicate_qa`, `_object_effect_qa`, `_entity_qa`, `_metric_qa`). Hàng predicate chỉ từ `predicate_lexicon` (chưa có trong seed) luôn `can_ra_soat=co`, `do_tin_cay=thap`.

---

## Bước tiếp theo (sau khi vocabulary ổn định)

1. Review tay các dòng có **nhiều biến thể gốc** (`raw_variants` dài).
2. Chuẩn hóa ngược vào `rulebase_seed` (phiên bản mới) hoặc sinh cột `*_normalized` qua script mapping.
3. Chạy lại `export_rulebase_formats.py` / logic JSON với id đã chuẩn.

---

## Liên kết

- Predicate gốc từ luật: `docs/schemas/predicate_lexicon_schema.md`
- Rule seed: `docs/schemas/rule_schema.md`
