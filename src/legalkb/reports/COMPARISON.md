# So sánh pipeline trên KB mẫu — 2026-10-23

**Kết luận:** MBD chưa vượt heuristic về F1 và độ đúng hành động trên test. Không điều chỉnh theo kết quả test.

539 ca: 261 dev, 278 test; gồm 80 / 83 ca hai lỗi. Cùng số đo NLI LLM cho mọi hệ thống. Chọn trên dev: τ=0,8, pos_only.

| Hệ thống | F1 dev | Hành động dev | F1 test | Hành động test | Báo động control dev/test |
|---|---:|---:|---:|---:|---:|
| MBD | 0.700 | 0.912 | 0.705 | 0.896 | 0.143 / 0.250 |
| Heuristic | 0.700 | 0.904 | 0.706 | 0.896 | 0.143 / 0.250 |
| Symbolic QA | 0.000 | 0.054 | 0.000 | 0.058 | 0.000 / 0.000 |
| Direct mapping | 0.318 | 0.785 | 0.329 | 0.809 | 0.143 / 0.250 |
| Bỏ chấp nhận nhãn | 0.680 | 0.912 | 0.705 | 0.896 | 0.214 / 0.250 |
| Bỏ MBD | 0.000 | 0.054 | 0.000 | 0.058 | 0.000 / 0.000 |
| Bỏ chẩn đoán và sửa | 0.000 | 0.199 | 0.000 | 0.201 | 0.143 / 0.250 |

F1 dùng chẩn đoán đứng đầu, khớp lỗi một-một và tính false positive ở control. Symbolic/no-MBD không chẩn đoán nên F1=0 là theo định nghĩa thước đo, không phải điểm QA.

## Phân tích lỗi và giới hạn

- Trên dev cũ, 19/36 lỗi misinterp và 10/16 lỗi unsupported không có thành phần đích trong bảng đo; không thể sửa bằng thay ngưỡng. Thu thập cả dữ kiện parser không còn nằm trong proof giải quyết lỗ hổng quan sát này.
- Recall test mới của MBD: misinterp 0,977; unsupported 0,811; missing 0,333. Missing vẫn là điểm yếu: câu thiếu thông tin có thể đã bị parser tự bổ sung, và nhãn benchmark không định vị dữ kiện thiếu.
- Dev còn 2/14 control bị báo động (BHXH-001, BHXH-015). Các base chỉ được coi là “sạch” vì kết luận trùng gold; NLI vẫn phát hiện đầu ra parser sai/không được nêu. Không loại các ca này khỏi mẫu để tăng điểm.
- Test có 4/16 control bị báo động. Đây là hạn chế chưa giải quyết, không được che bằng độ đúng hành động tổng hợp.
- Bộ 539 ca không có cặp proof đối nghịch chưa giải quyết hoặc cạnh hỗ trợ xung đột. Vì vậy nó chưa đo được lợi thế hitting set trên xung đột liên tầng dùng chung nguyên nhân. Test Prolog riêng xác nhận một lỗi parser có thể giải thích hai xung đột, đồng thời giữ phương án hai lỗi KB tối thiểu.
- Hai lỗi đồng thời: exact isolation dev/test của MBD là 0,388/0,361; heuristic là 0,400/0,386. Có khả năng xử lý nhiều lỗi không đồng nghĩa đã vượt baseline.
- Không so trực tiếp F1 này với 0,490 cũ: số ca, số thành phần được đo, cách chấm và NLI đều khác. Bộ mới dùng gpt-4.1 NLI đơn; bộ cũ dùng ensemble LLM+mDeBERTa. Raw scores và thông tin nguồn được lưu để replay.

## Ngân sách hỏi lại

Bảng injection chấm hành động đầu tiên: B=1,2,không giới hạn giống nhau khi chưa có câu trả lời của người dùng. Tất cả giá trị B đều có trong sample_comparison.json. B=0 chuyển yêu cầu hỏi/xác nhận thành unresolved.

Thí nghiệm hội thoại offline dùng hai câu deadline của KB mẫu, Prolog thật và dữ kiện trả lời được khai báo trước (quan sát fixture, không phải điểm NLI đo được):

| Số dữ kiện thiếu | B=0 | B=1 | B=2 | Không giới hạn |
|---|---|---|---|---|
| 0 | Đúng (0 lượt) | Đúng (0 lượt) | Đúng (0 lượt) | Đúng (0 lượt) |
| 1 | Chưa kết luận (0 lượt) | Đúng (1 lượt) | Đúng (1 lượt) | Đúng (1 lượt) |
| 2 | Chưa kết luận (0 lượt) | Chưa kết luận (1 lượt) | Đúng (2 lượt) | Đúng (2 lượt) |

## Kiểm chứng và phần chờ

- 29 kiểm tra reasoner gốc pass; 9 ca MBD đã lưu pass offline; 22 test pytest pass, bao gồm deadline/sanction, liên tầng, hai lỗi, 5 domain, split, ngân sách, chấm hành động, HTTP handler và kiểm tra trung thành.
- Không sửa chat.py/server.py; kiểm tra đường đi thực qua các lớp này bằng model fixtures không mạng.
- Hàm chấm đã duyệt đủ 300 ID: 29 câu có kết quả hoàn chỉnh, 271 câu thiếu cache. 11/29 hành động đúng, 11 trường hợp thiếu tự tin trong phần đã chạy. Không gọi đây là độ chính xác trên 300 câu.
- API đã dừng theo yêu cầu. Lệnh tiếp tục và ước lượng khoảng 5.900 lời gọi chưa cache, 3–9 triệu input token, 0,12–0,35 triệu output token nằm trong ../PIPELINE_FULL.md; chỉ chạy sau khi được cho phép.

Dữ liệu: sample_injections.jsonl, sample_calibration.json, sample_comparison.json, dev_error_analysis.json, budget_protocol.json, batch300_cache_coverage.json, provenance.json.
