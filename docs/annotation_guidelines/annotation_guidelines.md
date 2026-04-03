# Phương pháp chuẩn: tách rulebase pháp lý cho domain mới

Tài liệu này tổng hợp từ pipeline hiện tại (`LawRulebasePipeline` trong `src/law_side/law_rulebase_pipeline.py`, các bước manifest → legal units → candidate → frame → predicate lexicon → `rulebase_seed.xlsx`) và bộ schema trong `docs/schemas/`. Mục tiêu là quy trình **lặp lại được** khi mở rộng sang luật khác (thuế, lao động, dân sự, …).

---

## Luồng tổng quát (nhắc nhanh)

1. Nạp văn bản → `document_manifest.xlsx`  
2. Phân đoạn cấu trúc → `legal_units_review.xlsx`  
3. Phát hiện câu chuẩn tắc → `candidate_normative_sentences.xlsx`  
4. Khung ngữ nghĩa → `legal_frames_review.xlsx`  
5. Chuẩn hóa predicate → `predicate_lexicon.xlsx`  
6. Sinh rule seed → `rulebase_seed.xlsx`  

Các bước dưới đây gắn với từng giai đoạn và với **câu hỏi 1–9** đã đặt ra.

---

## 1. Chọn văn bản nguồn như thế nào?

**Luật chính**

- Là lớp nền định nghĩa khái niệm, quyền nghĩa vụ, chế tài chung. Luôn nên có ít nhất một văn “khung” trong corpus domain mới trước khi kỳ vọng rule đầy đủ.

**Nghị định hướng dẫn**

- Bổ chi tiết thủ tục, thời hạn, cơ quan, hồ sơ. Thường là nơi **mật độ rule thủ tục** cao; pipeline hiện tại tách biệt vai trò văn qua `document_role` và `parse_strategy` trên manifest.

**Thông tư / biểu mẫu (khi cần)**

- Dùng khi: (a) luật/NĐ nói “theo hướng dẫn của Bộ …” và nội dung quyết định thực tế nằm ở thông tư; (b) biểu mẫu là phần không tách khỏi nghĩa vụ nộp hồ sơ. Khi đưa vào pipeline, khai báo rõ trong manifest (`has_appendix_forms`, `legal_scope_note`) để không nhầm **trích nhầm** phần chỉ mang tính mẫu điền.

**Nguyên tắc**

- Ưu tiên bộ tài liệu **đóng kín vòng nghiệp vụ** (từ điều kiện áp dụng đến thủ tục và hậu quả) trước khi mở rộng ngang sang văn phụ.

---

## 2. Dùng manifest để ưu tiên nguồn ra sao?

- Gán `domain_scope` / `domain_subscope` đúng domain mới để downstream và ontology không lẫn với bộ Luật DN hiện có.
- Dùng `document_role` để phân biệt **văn hợp nhất**, **NĐ thủ tục**, **thông tư chi tiết** — ảnh hưởng kỳ vọng kiểu rule (định nghĩa vs quy trình).
- Dùng `parse_strategy` để cố định ưu tiên detector: ví dụ ưu tiên **nghĩa vụ / quyền / điều kiện** trước, hay ưu tiên **thủ tục / hồ sơ / thời hạn** — giảm lệch recall giữa các văn trong cùng domain.
- Dùng `priority` + `expected_rule_density` + `status` để **xếp hàng review** và giải thích nếu một văn cho ít rule hơn dự kiến (lỗi nguồn vs lỗi parse).

---

## 3. Legal units phải enrich đến mức nào trước khi làm candidate?

Trước khi chạy (hoặc ngay sau segmenter, trước detector), cần đạt tối thiểu:

- **Cấu trúc đúng:** `unit_type`, `unit_ref_full`, `source_ref`, `text` + `parent_context` đủ để hiểu câu không mất ngữ cảnh.
- **Heuristic ngữ nghĩa:** `deontic_signal` và các `has_*_marker` (điều kiện, thời hạn, hồ sơ, cơ quan, ngoại lệ, ngưỡng) — để candidate không “mù” loại quy phạm.
- **Gợi ý vai tế:** `actor_hint` / `action_hint` / `object_hint` khi segmenter đã có; giúp giảm lỗi gán chủ thể ở frame sau.
- **Tách đơn vị:** `needs_split` + `split_reason` khi một khoản/điểm gói nhiều mệnh đề độc lập — tránh một candidate/frame chứa nhiều rule trộn.

Không cần enrich tay toàn bộ corpus trước candidate, nhưng **các dòng có `needs_split = co` phải có kế hoạch xử lý** (tách unit hoặc ghi chú backlog), kẻo recall tăng giả tạo (một dòng quá dài → nhiều rule lẫn nhau).

---

## 4. Candidate phải mở recall ra sao để không rớt các loại?

Mục tiêu: **recall cao** ở tầng candidate, lọc tinh ở `should_extract_rule` và ở frame.

Cầu bật đủ kênh sau trong detector / rubric (tương ứng các trường `*_text` trong `candidate_normative_sentences`):

| Loại | Gợi ý vận hành |
|------|----------------|
| **Điều kiện** | Pattern “nếu”, “trong trường hợp”, “khi”, điều kiện định lượng; map `condition_text` + `candidate_type` phù hợp (`dieu_kien_ap_dung`). |
| **Ngoại lệ** | “trừ”, “ngoại trừ”, “không áp dụng đối với”; `exception_text` không được bỏ qua vì hiếm. |
| **Ngưỡng** | Số, %, số ngày, “ít nhất”, “không quá”, khoảng “từ … đến …”; `threshold_text` + subtype ngưỡng. |
| **Hồ sơ** | “hồ sơ gồm”, “kèm theo”, “bản sao”, biểu mẫu; `document_text` + `candidate_type` hồ sơ. |
| **Thời hạn** | “trong thời hạn”, “chậm nhất”, “kể từ ngày”; `deadline_text`. |
| **Cơ quan** | “Cơ quan …”, “Bộ …”, “cơ quan đăng ký …”; `authority_text`. |
| **Kết quả pháp lý** | “được cấp”, “bị thu hồi”, “chấm dứt”, “cập nhật trên CSDL …”; `legal_effect_text` / `ket_qua` tương ứng ở frame. |

Nguyên tắc: **ưu tiên bắt đủ loại** rồi dùng `should_extract_rule = can_nhac` cho biên; tránh cắt sớm khiến domain mới chỉ còn một vài `candidate_type`.

---

## 5. Frame phải làm giàu slot nào để fan-out tốt sang rule?

Frame (`legal_frames_review`) cần đủ để `RuleBuilder` tách **main** vs **fanout** (thể hiện qua `extraction_pattern` trong `rulebase_seed`), đặc biệt:

- **Vai tế hành vi:** `chu_the`, `vai_tro_chu_the`, `hanh_vi`, `doi_tuong_hanh_vi`, `tinh_chat_phap_ly`
- **Điều kiện / ngoại lệ:** `dieu_kien_ap_dung`, `ngoai_le`
- **Định lượng:** `dieu_kien_dinh_luong`, `nguong_so_luong`, `nguong_ty_le`, `khoang_gia_tri` (mô tả trước khi struct hóa ở rule)
- **Thủ tục:** `thanh_phan_ho_so`, `co_quan_tiep_nhan`, `co_quan_xu_ly`, `ket_qua_thu_tuc`, `thoi_han_so` + `don_vi_thoi_han` + `moc_tinh_thoi_han`
- **Chất lượng:** `muc_do_day_du`; **cảnh báo fan-out:** `can_tach_them`, `ly_do_can_tach`

`frame_type` (các nhãn `khung_*`) phải **khớp** loại quy phạm thực tế để downstream `rule_type` và pattern fan-out không bị ép sai.

---

## 6. Predicate mở rộng theo domain ra sao để không normalize quá thô?

- Giữ **hai tầng:** `hanh_vi_chuan` (gom nhóm) và `hanh_vi_chuan_chi_tiet` (phân tách nghiệp vụ). Không gộp mọi “khai / nộp / đăng ký” thành một từ nếu pháp lý phân biệt hậu quả.
- Dùng `surface_form` + `bien_the_ngon_ngu` để bao phủ cách diễn đạt thực tế trước khi thêm `predicate_id` mới.
- Gán `nhom_hanh_vi` theo nghiệp vụ domain (ví dụ thuế: khai, khấu trừ, hoàn thuế; lao động: hợp đồng, sa thải, bảo hiểm).
- Cập nhật cờ `can_thoi_han`, `can_ho_so`, `can_ngoai_le`, `can_nguong_dinh_luong` theo **đặc thù** domain (đừng để toàn `khong` nếu văn thực tế luôn có ngoại lệ hoặc ngưỡng).

---

## 7. Rulebase cuối phải kiểm theo những trục nào?

| Trục | Việc làm |
|------|----------|
| **Coverage theo Điều / Khoản** | Pivot `source_ref` / `article` / `unit_ref_full`: điều nào chưa có rule hoặc chỉ có một loại mỏng. |
| **Coverage theo loại rule** | Phân bố `rule_type` và so với kỳ vọng domain (thời hạn vs hồ sơ vs ngưỡng vs ngoại lệ). |
| **Trùng nội dung** | So khớp `source_text` hoặc fingerprint nội dung; cùng `rule_group_id` hoặc khác group nhưng trùng câu. |
| **Độ giàu slot** | `muc_do_day_du`, các ô trống quan trọng (`he_qua_phap_ly`, `ket_qua_thu_tuc`, `thanh_phan_ho_so`, `pham_vi_ap_dung`). |
| **Cấu trúc hóa ngưỡng** | Với `quy_tac_nguong_dinh_luong`: `ten_chi_so`, `toan_tu_so_sanh`, `gia_tri_nguong`, `don_vi_nguong`; với khoảng: `gia_tri_tu`, `gia_tri_den`, `kieu_khoang`. |
| **Tính self-contained** | `grounded_summary` + template phản ánh slot; rule đọc được mà không cần đoán ngoài văn (trừ chỗ cố ý trỏ `van_ban_dan_chieu`). |

Thêm: **`can_ra_soat`** và `extraction_pattern` để lần theo lỗi do fan-out (ví dụ quá nhiều `fanout_thoi_han` từ cùng frame).

---

## 8. Pattern đặc trưng theo domain (định hướng)

### Thuế

- Tần suất cao: **mức, thuế suất, kỳ tính thuế, đối tượng không chịu thuế / miễn giảm**, **khai / nộp / quyết toán / hoàn thuế**.
- Pattern câu: điều kiện đối tượng + công thức / bảng biểu; thường nhiều **thông tư** và **phụ lục số**.
- Candidate: chú ý **ngưỡng tiền / tỷ lệ** và **điều kiện miễn**; frame cần slot định lượng rõ.

### Lao động

- Tần suất: **hợp đồng**, **chấm dứt / sa thải**, **bảo hiểm**, **thời giờ / tiền lương**, **an toàn lao động**.
- Pattern: “người sử dụng lao động / người lao động”, tranh chấp, thời hiệu; nhiều **NĐ/Thông tư** chi tiết.
- Candidate: **điều kiện** và **ngoại lệ** (ví dụ hợp đồng xác định / không xác định thời hạn); frame cần **chu_the** và **doi_tuong_hanh_vi** rõ vai.

### Dân sự

- Tần suất: **giao dịch**, **tuyên bố / vô hiệu / hủy bỏ**, **bồi thường**, **đại diện / ủy quyền**, **thời hiệu khởi kiện**.
- Pattern: điều kiện có hiệu lực, hình thức, chủ thể không đủ năng lực; văn thường **trừu tượng hơn** thủ tục hành chính.
- Candidate: **điều kiện** và **hậu quả pháp lý** mang tính đánh giá; cần cẩn trọng khi gán `ket_qua_phap_ly` để không tổng quát hóa quá mức.

---

## 9. Checklist thực hành (người mới làm theo)

1. **Xác định domain** và chọn bộ văn: luật chính + NĐ (và thông tư / biểu mẫu nếu cần đóng vòng nghiệp vụ).  
2. **Điền manifest** đầy đủ: `doc_id`, `doc_code`, `domain_scope` / `domain_subscope`, `document_role`, `parse_strategy`, `priority`, `expected_rule_density`, `status`.  
3. **Chạy ingest + segmenter**; rà **legal units**: `unit_ref_full`, `parent_context`, `needs_split`.  
4. **Enrich marker** tối thiểu (`deontic_signal`, `has_*_marker`); xử lý hoặc ghi backlog các dòng `needs_split = co`.  
5. **Chạy detector candidate**; kiểm tra phủ **mười loại kênh** (điều kiện, ngoại lệ, ngưỡng, hồ sơ, thời hạn, cơ quan, hiệu lực pháp lý).  
6. **Rà candidate** `should_extract_rule`; điều chỉnh pattern / rubric domain nếu một loại quá thiếu.  
7. **Làm frame**: đủ slot để fan-out; đặt `frame_type` đúng; ghi `can_tach_them` khi cần.  
8. **Mở rộng predicate lexicon** (hai tầng + biến thể + `nhom_hanh_vi`); cập nhật cờ `can_*`.  
9. **Build rulebase seed**; duyệt **`extraction_pattern`** và **`rule_type`**.  
10. **Kiểm 7 trục** (mục 7): coverage điều/khoản, coverage loại rule, trùng lặp, giàu slot, ngưỡng có cấu trúc, self-contained.  
11. **Đánh dấu** `can_ra_soat` / ghi chú cho chỗ cần luật sư hoặc nguồn bổ sung.  
12. **Ghi phiên bản** corpus + config pipeline trong README hoặc `notes` để tái lập.

---

## Tham chiếu nhanh

- Chi tiết cột từng bước: thư mục `docs/schemas/`  
- Pipeline code: `src/law_side/law_rulebase_pipeline.py`  
- Tinh chỉnh rule seed (ví dụ slot phụ): `scripts/refine_rulebase_seed_round.py`
