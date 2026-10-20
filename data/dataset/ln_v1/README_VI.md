# Cross-Layer MBD — 40 câu Liên ngành (DRAFT)

**Không phải gold test chính thức.** Đây là bản thảo sinh từ 18 văn bản do người dùng cung cấp, chuẩn schema của repo. Chưa chạy Prolog, chưa có chuyên gia pháp luật duyệt, chưa tạo F1–F6.

- Tổng: 40 application cases `LN-001`–`LN-040`.
- Tất cả câu có ít nhất hai loại văn bản thuộc các lĩnh vực khác nhau trong `legal_basis`.
- `info_level`: {'complete': 25, 'missing': 13, 'exception_or_conflict': 2}; `expected`: {'true': 22, 'insufficient': 13, 'false': 5}.
- 26 cấu hình facts/goal riêng biệt; 11 nhóm lặp cấu hình (nếu có).
- `facts.span`: khớp nguyên văn, `legal_basis.quote`: xuất hiện trong đúng điều luật của corpus trích xuất; mọi `reasoning_chain` kiểm tra dependency syntactic.
- Predicate mới: 19, khai báo duy nhất tại lần đầu dùng; dùng registry cộng dồn từ BHXH, DN, Thuế, Lao động.
- Gold policy v2: thiếu premise luật chung có ảnh hưởng -> insufficient; không nhắc ngoại lệ -> đánh giá theo luật chung (giả định benchmark, không chứng minh ngoại lệ false); ngoại lệ kích hoạt một phần mà thiếu dữ kiện quyết định -> insufficient.

## Lưu ý pháp lý và nghiên cứu

- Cần rà độc lập tất cả 40 kết luận, nhất là nhóm TNHH+thuế suất, branch+VAT, chi phí lương và phân loại quản lý doanh nghiệp.
- Với trường hợp thiếu dữ kiện, reasoning chain thể hiện giả định cần kiểm chứng, **không phải proof thực sự đã suy ra kết luận**.
- Nhiều câu cùng họ logic có thể gây leakage; hãy group by topic/profile và parent legal scenario khi chia split.
- Corpus nguồn có bản VBHN Luật Doanh nghiệp, trong khi các văn bản sửa đổi/hiệu lực cần rà mốc thời gian nếu chốt test 2026.
- MBD F1–F6 phải tạo sau từ trạng thái parser/reasoner/KB thật; `missing` hay `exception` trong QA không tự động là diagnostic fault.
- **Không dùng dữ liệu này để hiệu chỉnh KB rồi tiếp tục gọi nó là independent held-out test.**

## Files

- `lien_nganh_40_DRAFT.jsonl`: đầy đủ câu hỏi + nhãn dự thảo
- `benchmark_inputs.jsonl`: chỉ câu hỏi đầu vào
- `gold_annotations_DRAFT.jsonl`: nhãn dự thảo tách riêng
- `predicate_registry_new.json` và `predicate_registry_cumulative.json`: registry thống nhất
- `source_anchors.json`: trích luật kiểm chứng văn bản
- `review_queue.csv`: trạng thái duyệt từng record
- `validation_report.json`: kiểm thử schema/span/nguồn/trace dạng tĩnh

Chạy validator repository (trên máy của bạn):

```powershell
$env:PYTHONPATH='src'
.venv_diag/Scripts/python -m diagnosis.kbx.validate_dataset 'data/dataset/lien_nganh_40_DRAFT.jsonl'
```
