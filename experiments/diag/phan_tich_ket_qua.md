# Phân tích kết quả thực nghiệm (ACIIDS, ngày 18/10/2026)

Bảng số liệu đầy đủ: [tables.md](tables.md). Dữ liệu từng ca: `results.json`, `results_llm.json`, `results_real_parser.json`.

## Thiết lập tóm tắt
- KB chẩn đoán: 28 rule viết tay (21 rule tường minh, 7 rule suy ngược), 34 predicate, 9 quan hệ `exception_of`, chuỗi suy luận sâu tối đa 4 bước. Nguồn: Luật BHXH 41/2024 và BLLĐ 2019 Điều 24.
- 40 ca gold: 18 câu thật (bộ 290 câu), 22 câu tự viết. Từ đó sinh 263 ca chẩn đoán, đánh giá trên **125 ca lấy mẫu phân tầng** (giữ toàn bộ ca tự nhiên và ca tầng KB).
- Hệ thống dùng: NLI mDeBERTa-v3-base-xnli; SWI-Prolog 10.0.2; GPT-4o (`gpt-4o-2024-08-06`, temperature 0) cho baseline, parser và re-parse.

## Kết quả chính (125 ca)

| | GPT-4o | Base NeSy | NeSy + Diagnosis |
|---|---|---|---|
| Final Acc. (tất cả) | 78,4 | 30,4 | **87,2** |
| Final Acc. (ca có lỗi) | 75,5 | 11,2 | **86,7** |
| Ca thiếu dữ kiện | 48,1 | 0 | **88,9** |
| Xung đột KB chưa giải quyết | 0 | 100 | **100** |

- **Diagnosis accuracy 66,4%**, Recovery 57,1%, trung bình **3,96 phép đo/câu**.
- **NLI:** accuracy 86,1%, macro-F1 81,0 (467 phép đo). Lỗi chính là gán *neutral* thành *entail* (33 ca), đặc biệt với con số và thời hạn.

## Các luận điểm số liệu ủng hộ
1. **Cùng triệu chứng nhưng khác nguyên nhân.** Không có MBD (gán thẳng triệu chứng → nguyên nhân) thì Diagnosis Acc. giảm từ 66,4 xuống 48,0, và Final Acc. trên ca lỗi giảm từ 86,7 xuống 57,1.
2. **LLM trả lời quá tự tin.** Ở 27 ca thiếu dữ kiện, GPT-4o đưa kết luận có/không trong 20 ca mà không hỏi lại. Hệ chẩn đoán luôn hỏi lại (0/27 kết luận khi thiếu căn cứ). Ở ca xung đột KB chưa giải quyết, GPT-4o luôn kết luận, còn hệ chẩn đoán từ chối kết luận đúng 6/6.
3. **Lỗi parser có thật, không chỉ do inject.** Với parser GPT-4o thật trên 93 câu, chỉ 46% câu được parse hoàn toàn đúng (fact F1 83,2). Base NeSy đúng 23,7%, NeSy + Diagnosis đúng 87,1%. Trên 50 câu parser làm sai: tăng từ 14,0% lên 80,0%.
4. **Cặp dễ nhầm:**
   - Missing và Omission: 6/27 ca Missing bị gán thành Omission, 8/20 ca Omission bị gán thành Missing. Nguồn lỗi là NLI phân biệt kém *neutral* và *entail* khi span bị xoá để lại câu không tự nhiên.
   - Resolvable và Unresolved: phân biệt đúng hoàn toàn (5/5 và 6/6), vì phép đo là kiểm tra ký hiệu trên KB.

## Những điểm phải viết thẳng trong bài
- **Tiết kiệm phép đo nhỏ:** đo có định hướng 3,96 phép đo/câu, đo toàn bộ 4,25 (khoảng 7%), độ chính xác như nhau. Lý do: trigger (iii) đã kiểm tra gần hết các fact trong proof. Không nên nhấn mạnh hiệu quả ở điểm này.
- **Unsupported Parser Fact khó nhất:** F1 52,6. 8/20 ca bị gán thành Misinterpretation, vì NLI trả *contra* cho fact bịa mà câu hỏi ngầm phủ định (ví dụ "chỉ thử việc" trong khi câu nói đã ký HĐLĐ). Recovery vẫn đưa về đáp án đúng ở 75% ca.
- **Lỗi bỏ sót nằm ngoài proof thì không thấy được** (parser thật, S05/S19): khi một nhánh vẫn kết luận được, chẩn đoán không được kích hoạt nên xung đột tiềm ẩn bị bỏ qua.
- **Nhầm giữa hai predicate gần nghĩa** (S08): `reached_retirement_age` và `retirement_age_at_signing`. Vocabulary cần ràng buộc chặt hơn hoặc thêm phép đo phân biệt.
- **Normal 85,2%:** 4/27 ca bình thường bị báo lỗi giả, do NLI sai. Final Acc. ca Normal giảm từ 100 (Base) xuống 88,9, tức chẩn đoán có làm hỏng câu trả lời đúng ở một số ca.
- **Phạm vi nhỏ:** KB một domain, viết tay; đa số ca đủ dữ kiện là câu tự viết; một lỗi chính mỗi ca; tập con 125/263 ca.

## Sửa lỗi trong quá trình thực nghiệm (để minh bạch)
Lần chạy đầu sửa lỗi tầng parser và tầng KB trong cùng một lượt. Kết quả khi đó: Final Acc. 80,8, Unsupported 40%. Bản cuối sửa tầng đầu vào trước, suy luận lại, rồi mới xét tầng KB. Đây là thay đổi thiết kế, không phải tinh chỉnh theo tập test, và nên mô tả trong mục 3.9 của bài.
