# Batch Lao động — 30 câu hỏi (DRAFT)

**Trạng thái: DRAFT / PENDING LEGAL REVIEW.** File này không phải gold benchmark cuối cùng và chưa có F1–F6 fault injections.

- **30 application questions** (`LD-001`–`LD-030`).
- Mức thông tin: **18 complete, 7 missing, 5 exception_or_conflict**.
- Nhãn kết luận: **{'true': 14, 'insufficient': 7, 'false': 9}**.
- Chuỗi suy luận ghi từ 2 bước trở lên: **17/30** (được kiểm tra tính phụ thuộc syntactic; CHƯA là proof SWI-Prolog).
- **30/30** cấu hình `(goal, facts)` riêng biệt, không chỉ đổi tên người.
- **39 căn cứ trích dẫn** khớp nguyên văn trích xuất tại ĐÚNG Điều được đánh dấu; chỉ là kiểm tra đoạn trích tồn tại, không bảo chứng cách áp dụng pháp luật đúng.
- Tham chiếu **Bộ luật Lao động 45/2019/QH14** và **Nghị định 145/2020/NĐ-CP** trong ZIP nguồn, không dùng paper cũ.
- **60 predicate mới**, registry cộng dồn từ BHXH + Doanh nghiệp + Thuế + Lao động. Predicate mới chỉ được khai báo ở record xuất hiện đầu tiên.

## Gold annotation policy v2

1. `insufficient` phản ánh quy định pháp luật và dữ kiện cung cấp, không phải thiếu rules của KB hiện hữu.
2. Thiếu premise của quy định chung có ảnh hưởng kết luận -> `insufficient`.
3. Ngoại lệ hoàn toàn không xuất hiện trong câu -> mặc định đánh giá theo rule chung trong benchmark, không chứng minh ngoại lệ thực tế là false.
4. Ngoại lệ kích hoạt một phần mà còn thiếu premise quyết định -> `insufficient`.

## Tệp

- `lao_dong_30_DRAFT.jsonl`: annotations ở dạng schema yêu cầu.
- `benchmark_inputs.jsonl`: chỉ id/domain/question, đưa vào parser, KHÔNG chứa gold.
- `gold_annotations_DRAFT.jsonl`: nhãn dự thảo tách khỏi input.
- `predicate_registry_new.json`, `predicate_registry_cumulative.json`: tên predicate nhất quán liên miền.
- `source_anchors.json`: trích nguồn thực tế và article ID.
- `review_queue.csv`: kiểm duyệt từng case bằng `id`.
- `validation_report.json`: kiểm tra máy, không đồng nghĩa legal correctness.

## Các trường hợp cần rà thêm

- `LD-004`: dưới 15 tuổi phải ký văn bản với cả người đại diện; kiểm tra phạm vi của hình thức lời nói.
- `LD-011`: chỉ biết thử việc 50 ngày chưa đủ nếu không xác định nhóm nghề; annotation `missing` cần xem các nhánh khác ngoài nhóm cao đẳng.
- `LD-016`: quyền nghỉ ngay vì trả thiếu lương có ngoại lệ theo Điều 97.4; benchmark mặc định không kích hoạt ngoại lệ khi không nhắc, cần ghi giới hạn.
- `LD-021`: `missing_facts` biểu diễn thiếu phân loại ngày bằng một predicate boolean đơn giản; schema nên tiến hóa để biểu diễn nhiều loại ngày có tính loại trừ nhau.
- `LD-022`: không được ép làm thêm trong trường hợp thông thường; soát Điều 108 về trường hợp đặc biệt.
- `LD-027`: yêu cầu đăng ký nội quy và nội dung cụ thể của nội quy cần phân biệt, tránh coi đăng ký là tự động hợp lệ.
- `LD-030`: sự đồng ý cho làm ban đêm chỉ gỡ rào cản Điều 137.1.b, không chứng minh đủ mọi yêu cầu lao động khác.
- Cần kiểm tra văn bản sửa đổi/chuyển tiếp, hiệu lực tại thời điểm hỏi khi chốt gold.

## Chạy repo validator trên Windows

```powershell
$env:PYTHONPATH='src'
.venv_diag/Scripts/python -m diagnosis.kbx.validate_dataset 'data/dataset/lao_dong_30_DRAFT.jsonl'
```

Chưa có runtime của `diagnosis.kbx.validate_dataset` trong môi trường hiện tại, nên lệnh trên CHƯA được chạy. Sau khi duyệt cần xây KB và chạy reasoner để kiểm tra reasoning chains, rồi giữ test set độc lập với KB tuning.
