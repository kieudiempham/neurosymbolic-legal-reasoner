# Diagnostic benchmark F1--F6 (BẢN NHÁP, KHÔNG PHẢI GOLD CHÍNH THỨC)

Bộ này **tách riêng thành file và nhãn chẩn đoán** so với 300 QA: 216 diagnostic fixtures gồm F1=40, F2=40, F3=40, F4=40, F5=16, F6=20, CONTROL=20.

**Đọc trước khi dùng kết quả trong paper:** Đây là bộ thí nghiệm có kiểm soát sinh từ 300 QA DRAFT chưa được thẩm định pháp lý độc lập; code reasoner/KB không được cung cấp, nên chưa có proof-grounded validation, không có kết quả đo accuracy/recovery. KHÔNG nêu 216 là 216 legal gold độc lập.

## Tập đầu vào và gold

- `diagnostic_model_inputs.jsonl`: input dành cho runner. Có `original_question`, oracle `goal`, `parsed_facts`, và `kb_fixture` (nếu là F5/F6). **Không chứa nhãn F1--F6**.
- `diagnostic_gold_labels_DRAFT.jsonl`: nhãn lỗi, target, NLI/evidence expectation, action recovery; **KHÔNG đưa cho parser / MBD**.
- `diagnostic_cases_DRAFT.jsonl`: file thuận tiện cho audit **có đáp án**; không đưa toàn bộ cho model.
- `fault_injection_manifest.jsonl`: log thao tác tiêm lỗi và SHA-256 fingerprint nguồn.
- `f5_real_kb_mapping_QUEUE.jsonl`: danh sách ca F5 cần map `rule_id` và `exception_of` thực tế.
- `f6_isolated_synthetic_kb_fixtures.jsonl`: 20 cặp rule **TỔNG HỢP** trong micro-KB; **KHÔNG phải** xung đột pháp luật thực.
- `source_grouping_and_split_warnings.jsonl`: nhóm theo QA gốc và signature để hạn chế leakage.
- `build_report.json`: báo cáo tổng hợp.

## Các chế độ

**F1**: Người dùng thực sự chưa cung cấp dữ kiện pháp lý quyết định. Lấy trực tiếp từ câu thiếu dữ kiện theo GOLD DRAFT, không chỉnh parser. NLI thường neutral/unknown. Không có "fault injection"; đây là một trạng thái đầu vào.

**F2**: Parser bỏ sót một fact thật, có nguyên văn span trong câu hỏi và được dùng trong annotated rule premise. Input xóa fact, câu hỏi không đổi. NLI theo gold: entailment. Recovery: bổ sung fact.

**F3**: Parser đảo cực tính một fact quan trọng (thay thế, không thêm). NLI theo gold: contradiction. Recovery: phục hồi cực tính ban đầu.

**F4**: Parser thêm một fact KHÔNG ĐƯỢC NÊU trong câu hỏi thiếu thông tin từ tập F1 (kiểu hallucination-neutral). Fact được chọn chính là một premise quyết định trong `missing_facts`. Gold NLI là `neutral_or_explicitly_unknown`. Source question giống hệt ca F1 ghép đôi; parser output có **thêm** một fact và vì vậy khác F1. Đây không phải ca xung đột polarity/multiset. Cần proof tracing xác nhận fact tiêm được dùng trong reasoning trước khi tính recovery end-to-end.

**F5**: 16 **ứng viên** general/exception. Có `kb_fixture` mô hình hóa hai phía theo gold, nhưng `real_kb_rule_ids=null`, và `exception_of` ở đây chỉ thuộc fixture. **Chưa được gọi là 16 F5 thực**. Map sang real KB, xác minh cả hai rule cùng áp dụng, kết luận xung khắc và quan hệ `exception_of`/priority được encode thật rồi mới đưa vào đánh giá F5 chính thức. Không tự tạo metadata thiếu ở KB.

**F6**: 20 **micro-KB tổng hợp biệt lập**, mỗi micro-KB có hai rule áp dụng được, heads đối nghịch và không có `exception_of`/priority. Khi test PHẢI dùng fixture làm KB duy nhất, không merge vào KB pháp luật. Đây là thí nghiệm synthetic encoded-KB conflict; **không** đại diện cho mâu thuẫn của văn bản Việt Nam.

**CONTROL**: 20 ca QA không bị tiêm lỗi, từ nguồn DRAFT. Dùng để kiểm tra false positive.

## Quy trình tích hợp vào repo

1. Copy các file JSONL đến `data/diagnostic_dataset/` (không thay thế file QA schema). Chạy `python validate_diagnostic_dataset.py` trong thư mục được giải nén để kiểm tra tính nhất quán nội bộ.
2. Dùng `diagnostic_model_inputs.jsonl` để chạy từng record trên runner. Cung cấp **oracle goal** như cấu hình paper hiện tại, tuyệt đối không nạp `diagnostic_gold_labels_DRAFT.jsonl` trong inference.
3. Với F5: điền real `general_rule_id`, `exception_rule_id` từ KB export + xác nhận quan hệ thực tế. Những ca chưa map giữ ở **candidate queue**, không tính vào denominator F5.
4. Với F6: khởi tạo **isolated synthetic KB fixture**, không thêm rule giả vào KB luật đang đánh giá.
5. Chạy NLI, reasoning, backward dependencies và MBD; ghi observed labels/recovery, so sánh với `diagnostic_gold_labels_DRAFT.jsonl` sau khi kết thúc.
6. Đánh giá `diagnosis_accuracy`, `macro-F1` theo mode, `abstention_precision`, `recovery_success`, `unnecessary_intervention_rate`, tách thực nghiệm law-grounded và synthetic; không dùng các nhãn dự báo NLI trong gold làm hard observations nếu chưa xác minh.
7. Audit độc lập `source_legal_basis` và tái duyệt gold QA trước khi khóa test set. BHXH đã dùng để phát triển KB; toàn bộ nhóm BHXH phải là dev/exposed.

## Quy ước gold QA

`insufficient` theo luật hiện hành áp dụng, độc lập KB; thiếu điều kiện quy định chung quan trọng => insufficient. Ngoại lệ hoàn toàn không có dấu hiệu trong câu hỏi => không kích hoạt theo giả định benchmark đã công bố; ngoại lệ được kích hoạt một phần mà thiếu điều kiện có thể thay đổi kết luận => insufficient. Không tạo câu loại "tôi chưa đề cập X". Giả định benchmark này không phải bằng chứng ngoài đời rằng ngoại lệ không tồn tại.

## Trạng thái dữ liệu

- **Có**: manifest tái lập, expected observations dựa trên fact span và fixture, split-warning, synthetic KB overlays, controlled fault labels.
- **Chưa có**: 100% thẩm định pháp lý, chạy SWI-Prolog theo KB mới, xác nhận real rule pairs F5, kiểm thử MBD end-to-end, kiểm soát hoàn toàn paraphrase leakage.
- **Không được làm**: đổi gold theo output KB, tính 216 là 216 trường hợp pháp lý độc lập, gộp F6 synthetic với các KB conflict có thật để báo cáo mà không ghi chú.


## Chạy local

```bash
python validate_diagnostic_dataset.py
# Runner của bạn tạo predictions.jsonl, ví dụ:
# {"id":"DIAG-0001","predicted_mode":"F1","recovery_success":true}
python score_diagnostic_predictions.py predictions.jsonl
# Chỉ khi muốn chấm riêng F6 synthetic:
python score_diagnostic_predictions.py predictions.jsonl --include-f6-synthetic
# Chỉ khi muốn chấm riêng F5 fixture (chưa được xác nhận ở KB thật):
python score_diagnostic_predictions.py predictions.jsonl --include-f5-fixtures
```

`score_diagnostic_predictions.py` **mặc định chỉ chấm 180 ca F1--F4 và CONTROL**. F5 đang đợi xác minh rule_ids; F6 là micro-KB synthetic. Không gộp kết quả các nhánh thành legal diagnosis accuracy. `predictions_TEMPLATE.jsonl` chỉ mô tả dạng file nộp, chưa chứa dự đoán.

`crosslayer_300_DRAFT_SOURCE.jsonl` là bản sao 300 QA đầu vào để truy được trích dẫn và span gốc. Chỉ đưa `diagnostic_model_inputs.jsonl` vào hệ thống chạy suy luận, **không** đưa file gold hoặc manifest vào parser. `build_diagnostic_fixtures.py` và input gốc đi cùng cho phép tái tạo lại với seed `20261018`.
