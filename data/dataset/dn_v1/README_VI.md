# Dataset Doanh nghiệp — batch 2 (draft)

**Trạng thái:** `DRAFT / PENDING HUMAN LEGAL REVIEW`. Dùng để làm bước chuẩn hóa/kiểm thử, **chưa được dùng làm held-out benchmark gold**.

## Đã tạo

- 70 records `DN-001`–`DN-070` theo `schema.json` và `PROMPT_GPT_v2.md`.
- 40 complete, 19 missing, 11 exception_or_conflict.
- 27 true, 24 false, 19 insufficient.
- 62 fact/goal signatures phân biệt trong tổng 70 câu; còn 8 gần trùng và cần đánh giá riêng.
- 6 record ghi explicit reasoning chain >=2 bước có intermediate legal conclusion. Đây là số nhỏ; **chưa đạt** 30% multi-hop mục tiêu trong domain này.
- 56 predicate khai báo mới; file predicate_registry_cumulative.json giữ chung danh mục từ batch BHXH và batch này.
- 107/107 đoạn quote tìm thấy trong đúng điều luật của bản nguồn đã trích xuất. **Quote matching không tương đương thẩm định pháp lý.**

## Phạm vi luật đã dùng

Các record hiện bám theo **Luật Doanh nghiệp 2020, bản hợp nhất 67/VBHN-VPQH (2025)**. Chưa tạo case độc lập dựa vào Nghị định 168/2025/NĐ-CP; cần mở rộng độ bao phủ nếu muốn tuyên bố tập doanh nghiệp bao quát cả ba văn bản.

## Quy tắc gán gold

- Gold phải độc lập KB: sử dụng văn bản nguồn và giả định bench được chốt trước.
- Điều kiện chung thiếu → insufficient. Ngoại lệ hoàn toàn vắng bóng → theo quy định chung khi đã kiểm tra điều khoản cho phép. Ngoại lệ được kích hoạt một phần và chưa rõ kết luận → insufficient.
- Không dùng những nhãn đã tạo từ model cũ.
- Các điều kiện giả định trong `reasoning_chain` khi expected insufficient **không phải proof thực tế**; đối chiếu lại source text.

## Các file

- `doanh_nghiep_70_DRAFT.jsonl`: các record có question/gold draft
- `benchmark_inputs.jsonl`: chỉ ID, domain, question; dùng làm input cho parser/model
- `gold_annotations_DRAFT.jsonl`: tách metadata/gold, không đưa vào input
- `predicate_registry_new.json`: predicate mới ở domain Doanh nghiệp
- `predicate_registry_cumulative.json`: registry đã gộp với BHXH 90
- `source_anchors.json`: quote và điều khoản dùng để đối chiếu nguồn
- `review_queue.csv`: rà soát pháp lý theo ID và semantic group
- `validation_report.json`: kiểm tra kỹ thuật và thống kê
- `PROMPT_GPT_v2.md`: hướng dẫn được bổ sung định nghĩa gold/ngoại lệ

## Kiểm tra đã chạy

- JSON Schema draft 2020-12: 70/70 pass.
- Every `facts.span` appears exactly in `question`.
- Predicate goal/facts/missing/intermediate: đã khai báo trong handoff, BHXH batch, hoặc new registry.
- Quote là chuỗi nguyên văn của Điều được chỉ định: 107/107.
- ID trùng nội bộ: 0. Exact question duplicates: 0.

## Kiểm tra chưa chạy

- **Legal expert review**, bao gồm hiệu lực, khoản/điểm, tính áp dụng, biến cố và ngoại lệ của từng case.
- **SWI-Prolog / repo validator**: repo và KB runtime chưa được cung cấp.
- Đánh giá multi-hop thật bằng actual proof graph, external independent annotation, held-out dataset.

## Lưu ý để không gây leakage

90 BHXH trước đó đã có tương tác trong quá trình phát triển KB và 5 câu tranh luận về ngoại lệ; nên xem là **development data** cho tới khi version gold ổn định. 70 câu này cũng cần kiểm duyệt độc lập trước khi trộn vào test. Không chỉnh KB bằng gold thuộc tập final held-out rồi báo cáo kết quả như dữ liệu chưa thấy.

## Validator của repo

```powershell
PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.kbx.validate_dataset data/dataset/doanh_nghiep_70_DRAFT.jsonl
```

Kiểm định kỹ thuật tại đây không thay thế validator chính thức của repo.
