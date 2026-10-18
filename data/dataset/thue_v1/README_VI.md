# Batch 3 — 70 câu Thuế (Cross-Layer MBD)

**Trạng thái: DRAFT / PENDING HUMAN LEGAL REVIEW.** Đây là ứng viên QA, không phải bộ gold đã kiểm định; **chưa inject F1–F6**.

## Phạm vi

- 70 câu `THUE-001`–`THUE-070`, 100% dạng `application`.
- 45 `complete`, 15 `missing`, 10 `exception_or_conflict`.
- Expected: 27 `true`, 28 `false`, 15 `insufficient`.
- 31 câu có `reasoning_chain` dài >=2 bước; **chưa xác minh bằng proof graph của SWI-Prolog**.
- 61/70 cấu hình `(goal, predicate values)` phân biệt. 9 records nằm trong nhóm trùng cấu hình, xem `semantic_overlap_groups.json`.
- 64 predicate mới so với registry BHXH+Doanh nghiệp, có registry cộng dồn để domain sau tiếp tục dùng thống nhất.
- 179/179 đoạn `legal_basis.quote` được tìm thấy ở **đúng Điều được chỉ định** của bản văn nguồn trích xuất. Đối sánh chuỗi **không chứng minh** kết luận pháp lý đúng.

## Văn bản nguồn hiện đã sử dụng

1. Luật Thuế giá trị gia tăng 48/2024/QH15.
2. Nghị định 181/2025/NĐ-CP (hướng dẫn VAT).
3. Luật Thuế thu nhập doanh nghiệp 67/2025/QH15.
4. Nghị định 320/2025/NĐ-CP (hướng dẫn TNDN).
5. Luật Quản lý thuế 108/2025/QH15 (tình huống sau 01/07/2026).

Chưa phủ hết 11 văn bản Thuế trong ZIP. Đặc biệt quy định hóa đơn NĐ 123/2020 (sửa bởi NĐ 70/2025), TT 32/2025 và TT 69/2025 **chưa được tạo thành nhóm case riêng**. Do đó không mô tả batch này là bao phủ tất cả văn bản.

## Tệp

- `thue_70_DRAFT.jsonl`: 70 câu và nhãn/chuỗi suy luận dự thảo.
- `benchmark_inputs.jsonl`: chỉ ID, domain, question — đầu vào cho model, **không đưa gold vào input**.
- `gold_annotations_DRAFT.jsonl`: nhãn tách riêng từ question.
- `predicate_registry_new.json`: từ vựng mới dùng trong batch.
- `predicate_registry_cumulative.json`: từ vựng hợp nhất với 2 batch trước.
- `source_anchors.json`: vị trí câu trích pháp lý để kiểm tra.
- `semantic_overlap_groups.json`: tình huống trùng facts/goal.
- `review_queue.md`: toàn bộ 70 câu để kiểm duyệt.
- `validation_report.json`: kết quả kiểm tra máy.
- `PROMPT_GPT_v2.md`, `schema.json`: handoff specification kèm theo.

## Gold assumptions (v2)

1. Thiếu điều kiện **quy định chung** có ảnh hưởng kết luận → `insufficient`.
2. Ngoại lệ không có dấu hiệu đề cập → áp dụng quy định chung **theo benchmark policy**, không đồng nghĩa chứng minh thực tế ngoại lệ không tồn tại.
3. Ngoại lệ được nêu một phần, còn thiếu yếu tố quyết định → `insufficient`.
4. Gold độc lập KB, không thay đổi gold để khớp reasoner.

## Cần review trước khi chạy benchmark

- Xác nhận pháp luật đã được áp dụng đúng mốc thời gian 2026 và điều khoản chuyển tiếp/sửa đổi còn hiệu lực; việc xác định đối tượng áp dụng các mức thuế suất và ngoại lệ liên kết cần rà soát kỹ.
- Với tiền VAT đầu vào từ 5 triệu, xác minh hóa đơn và thanh toán cùng tính chất giao dịch; một câu có `insufficient` có thể cần thêm dữ kiện ngoài các facts đã liệt kê.
- Với TNDN, rà soát các ngoại lệ về chứng từ của chi phí được trừ; khẳng định *không đủ điều kiện* phải dựa trên điều khoản cụ thể, không chỉ phép phủ định máy móc.
- Rà lại luật sửa đổi NĐ 70/2025, NĐ 320/2025, TT 32/2025 trước khi khẳng định bao phủ 18 văn bản hoặc biến đây thành held-out benchmark.
- Những `reasoning_chain` của case `insufficient` mô tả **điều kiện cần kiểm chứng để có thể suy luận**, không phải proof đã hoàn thành.
- Các câu trong 9 nhóm overlap không nên chia giữa train/dev và test; split cần theo profile/parent ID.
- **Chưa chạy được repo validator** vì không có repository runtime `diagnosis.kbx.validate_dataset` trong môi trường này.

## Chạy trong repo (Windows PowerShell)

```powershell
PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.kbx.validate_dataset "data/dataset/thue_70_DRAFT.jsonl"
```

Kết quả validator cần được lưu cùng mã commit và thay đổi gold phải có lịch sử phiên bản. **Không dùng 70 câu chưa duyệt làm kết quả báo cáo ACIIDS.**
