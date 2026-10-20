# Bộ ứng viên BHXH v1 — Cross-Layer MBD Legal QA

**Trạng thái:** `DRAFT / PENDING LEGAL + KB REVIEW` — *chưa phải benchmark test cuối cùng.*

## Phạm vi

- 90 records QA thuộc domain `bhxh`, xây từ **Luật BHXH số 41/2024/QH15** và **Nghị định số 158/2025/NĐ-CP** nằm trong corpus đã tải lên.
- Tuân thủ `schema.json` do nhóm cung cấp. Các cột `facts.span` được lấy từ câu hỏi, `legal_basis.quote` là đoạn trích có mặt trong bản trích xuất điều khoản; predicate mới khai báo tại lần dùng đầu.
- Mặc định áp dụng khung quy định của các văn bản nêu trên trong năm 2026, sau mốc 01/07/2025, nếu câu hỏi không ghi thời điểm khác. Nội dung văn bản sửa đổi khác và hiệu lực đặc thù vẫn cần người phụ trách kiểm tra.
- **Không** dùng câu trả lời Qwen, GPT-4o hoặc NeSy của paper trước làm ground truth.
- **Không** chứa sẵn dữ liệu inject lỗi parser/KB F1–F6; đó là lớp đánh giá kế tiếp, dựa trên lần chạy hệ thống mới.

## Báo cáo tự động

| Chỉ tiêu | Kết quả |
|---|---:|
| QA records | 90 |
| Đủ thông tin (`complete`) | 54 |
| Thiếu điều kiện (`missing`) | 23 |
| Ngoại lệ / quy định tương tác (`exception_or_conflict`) | 13 |
| Expected `true` / `false` / `insufficient` | 48 / 19 / 23 |
| Câu hỏi `application` | 90 (100%) |
| Có 2+ bước ghi trong reasoning_chain | 75 (83.3%); **không đồng nghĩa** 75 ca là multi-hop không điều kiện |
| Khớp schema + span + trích dẫn trong bản trích xuất | 90/90 |
| Câu hỏi trùng nguyên văn | 0 |
| Predicate mới được khai báo | 15 |
| Cấu hình pháp lý khác biệt theo `(goal, expected, predicates+boolean values, missing_facts)` | **45** |
| Biến thể cách diễn đạt / tham số có cùng signature trên | **45** |
| Kiểm tra luật bởi chuyên gia | **Chưa** |
| Chạy validator trong repo do người dùng giữ | **Chưa** |

**Giới hạn quan trọng:** 90 câu *không* phải 90 mẫu pháp lý độc lập. Một số câu khác nhau về vai trò, thời hạn, địa điểm hoặc cách diễn đạt nhưng có cùng vector predicate theo vocabulary hiện hành. Không chia các biến thể cùng `semantic_group_id` vào các tập đánh giá khác nhau; cần **mở rộng thành các luật/điều kiện mới** nếu mục tiêu là 90 tình huống pháp lý thực sự khác nhau.

## Các file

- `bhxh_90.jsonl`: dữ liệu gồm schema, câu hỏi và nhãn dự thảo; **chưa ký duyệt gold**.
- `bhxh_canonical_legal_cases.jsonl`: 45 câu đại diện, một câu cho mỗi signature pháp lý khác nhau; ưu tiên review và chạy pilot.
- `bhxh_paraphrase_variants.jsonl`: 45 biến thể còn lại; có thể dùng để kiểm tra độ ổn định ngôn ngữ, **không dùng như mẫu độc lập**.
- `benchmark_inputs.jsonl`: chỉ chứa ID, domain và question; **nên dùng làm model input** để giảm rò rỉ gold.
- `gold_annotations.jsonl`: nhãn dự thảo tách rời model inputs.
- `semantic_groups.csv`: chỉ ra các phiên bản có cùng signature; dùng để nhóm khi split và khi bootstrap CI.
- `review_queue.csv`: checklist kiểm duyệt pháp lý và kiểm duyệt KB từng câu.
- `predicate_registry.json`: predicate từ handoff và predicate mới khai báo.
- `source_anchors.json`: điều luật + vị trí anchor cụ thể dùng khi soát source text.
- `validation_report.json`: báo cáo QA kỹ thuật và cảnh báo về tính độc lập.
- `dataset_handoff_schema.json`, `dataset_handoff_predicates.md`: sao chép hướng dẫn nguyên gốc để tiện đối chiếu.

## Trước benchmark chính thức

1. **Kiểm duyệt pháp lý** từng `legal_basis`: kiểm tra điểm/khoản, ngữ cảnh, ngoại lệ, hiệu lực, đặc biệt ca chủ hộ kinh doanh, người quản lý không hưởng lương, lao động nước ngoài.
2. **Soát `reasoning_chain` với KB runtime**: mọi `derived` intermediate và vị từ phủ định phải có rule tương ứng và xử lý phạm vi đúng; hiện tại mới kiểm tra diễn dịch cơ bản theo chuỗi được ghi, chưa chạy SWI-Prolog thật.
3. Chạy validator chính thức trong repo của nhóm (thay đường dẫn bằng path thật):

   ```powershell
   PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.kbx.validate_dataset data/dataset/bhxh_90.jsonl
   ```

   Không thể thực hiện chính lệnh repo trên ở đây vì source code/venv của repo không được đính kèm.
4. Chọn tập final từ các ca được review; **không chỉnh sửa KB hoặc thuật toán dựa trên kết quả final test**. Có thể dùng bộ canonical 45 trước cho pilot và bản paraphrase cho robustness.
5. Sau khi chạy NeSy mới và lưu `Reasoning State`, tạo riêng diagnostic cases F1–F6 với `injection`, `ground_truth_diagnosis`, `expected_recovery` và no-fault cases.

## Ghi chú về trích dẫn

`legal_basis.quote` khớp với **văn bản đã trích xuất** trong ZIP, nhưng điều đó **không tự chứng minh** rằng quy phạm được áp dụng đúng cho mọi tình huống. Toàn bộ 90 câu vì vậy vẫn được đánh dấu PENDING review. Một số trích dẫn liên hệ khoản/phần ngữ nghĩa rộng, cần kiểm định thủ công và chỉnh trước khi công bố.
