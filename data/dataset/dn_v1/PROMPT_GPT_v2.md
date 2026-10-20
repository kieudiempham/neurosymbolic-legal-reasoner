# Hướng dẫn tạo dataset (đưa nguyên file này + `predicates.md` + `examples.jsonl` + 18 văn bản cho GPT)

## Vai trò
Bạn là chuyên gia pháp luật Việt Nam, xây bộ câu hỏi đánh giá cho hệ thống hỏi đáp pháp luật **suy luận ký hiệu**. Hệ thống biểu diễn luật thành rule dạng `điều kiện1 ∧ điều kiện2 ∧ … → kết luận`, mỗi điều kiện là một **predicate** (mệnh đề đúng/sai về người hỏi hoặc vụ việc). Vì vậy, câu hỏi và nhãn gold phải được viết bằng **đúng các predicate** đó.

## Văn bản nguồn (18 file)
- Bảo hiểm xã hội: Luật BHXH 41/2024/QH15; NĐ 158/2025/NĐ-CP.
- Lao động: Bộ luật Lao động 45/2019/QH14; NĐ 145/2020/NĐ-CP.
- Doanh nghiệp: Luật Doanh nghiệp (VBHN 67/VBHN-VPQH); NĐ 168/2025/NĐ-CP; văn bản sửa đổi.
- Thuế: Luật Quản lý thuế 108/2025/QH15; NĐ 126/2020; NĐ 123/2020; Luật thuế GTGT 48/2024/QH15; NĐ 181/2025; Luật TNDN 67/2025/QH15; NĐ 320/2025; NĐ 70/2025; TT 32/2025/TT-BTC; TT 69/2025/TT-BTC; Luật 71/2014/QH13.

Chỉ dùng nội dung trong 18 văn bản này. Không dùng kiến thức ngoài, không bịa điều khoản.

## Yêu cầu về câu hỏi
1. **Khoảng 300 câu**, phân bổ gợi ý: BHXH 90, Doanh nghiệp 70, Thuế 70, Lao động 30, Liên ngành 40 (ví dụ: chấm dứt HĐLĐ (BLLĐ) → hưởng BHXH một lần (Luật BHXH); thu nhập từ HĐLĐ (BLLĐ) → nghĩa vụ thuế).
2. **Câu hỏi áp dụng điều kiện** (`question_type: application`) chiếm ít nhất 80%: người hỏi kể một **tình huống cụ thể** rồi hỏi có/không. Ví dụ: "Tôi ký HĐLĐ 12 tháng, đang hưởng lương hưu, có phải đóng BHXH bắt buộc không?". Câu hỏi tra cứu thuần (định nghĩa, hồ sơ, thủ tục) tối đa 20%, đánh dấu `lookup`.
3. Viết như người dân hỏi thật: xưng "tôi", văn nói, có chi tiết thừa vừa phải, **không** chép nguyên văn điều luật.
4. Phân bổ theo **mức thông tin**:
   - **~60% đủ dữ kiện**: trả lời chắc chắn có hoặc không (`expected: true/false`).
   - **~25% thiếu dữ kiện**: thiếu một điều kiện then chốt (`expected: insufficient`) và ghi rõ `missing_facts`.
   - **~15% có ngoại lệ hoặc nhiều quy định cùng áp dụng**: ví dụ quy định chung và ngoại lệ, hoặc luật và nghị định hướng dẫn. Ghi rõ trong `legal_basis` quy định nào thắng và vì sao.
5. Ít nhất 30% câu cần **suy luận 2 bước trở lên** (kết luận trung gian rồi mới tới kết luận cuối), ghi đủ trong `reasoning_chain`.
6. Không lặp tình huống: mỗi câu phải khác các câu khác ở ít nhất một dữ kiện có ảnh hưởng tới kết luận.

## Yêu cầu về nhãn gold
- `goal`: predicate kết luận mà câu hỏi hỏi tới, ví dụ `compulsory_si`.
- `facts`: **chỉ** những dữ kiện mà câu hỏi thực sự nêu. Mỗi fact gồm `pred`, `value` (true/false) và `span`, trong đó **span phải là chuỗi con nguyên văn của câu hỏi**. Không thêm dữ kiện suy đoán.
  - Dữ kiện suy ra được trực tiếp từ câu chữ thì ghi luôn. Ví dụ "HĐLĐ 12 tháng" thì ghi cả `term_at_least_1_month = true` và `term_at_least_12_months = true`, cùng span "12 tháng".
- `expected`: `true` / `false` / `insufficient`.
- `missing_facts`: các predicate còn thiếu (chỉ khi `insufficient`).
- `reasoning_chain`: các bước suy luận theo dạng `"pred_a ∧ ~pred_b → pred_c [Điều X khoản Y điểm z, <văn bản>]"`.
- `legal_basis`: danh sách căn cứ, gồm `doc`, `article`, `clause`, `point` và `quote` (trích ngắn nguyên văn, tối đa 40 từ).
- `answer`: đáp án bằng lời, 2–4 câu, có trích điều khoản.

## Quy tắc predicate (quan trọng nhất)
- **Dùng lại predicate trong `predicates.md`** khi nghĩa trùng khớp. Ưu tiên nhóm A (chuẩn).
- Nếu cần predicate mới: tên tiếng Anh, snake_case, ngắn, không chứa con số của riêng vụ việc. Ngưỡng luật định thì được đưa vào tên, ví dụ `term_at_least_12_months`.
  - Khai báo predicate mới trong `new_predicates` của **câu đầu tiên dùng nó**, gồm `kind` (`input` = dữ kiện người dùng cung cấp; `derived` = kết luận pháp lý), `template_pos`, `template_neg` (câu tiếng Việt khi đúng / khi sai) và `ask` (câu hỏi làm rõ, chỉ cho `input`).
  - Các câu sau dùng lại **đúng tên đó**. Một khái niệm chỉ được có một tên.
- Phủ định dùng `value: false`, không tạo predicate `not_...`.
- Kết luận trái nghĩa dùng cùng predicate và đổi `value` (ví dụ `compulsory_si` true/false), không tạo hai predicate riêng.

## Định dạng đầu ra
File **JSONL**, mỗi dòng một câu, đúng schema trong `schema.json`. Xem 3 ví dụ trong `examples.jsonl`. Nếu output dài, chia thành nhiều phần theo domain nhưng **giữ đúng tên predicate xuyên suốt các phần**: gửi kèm danh sách predicate mới đã tạo ở các phần trước.

## Tự kiểm tra trước khi trả
- [ ] Mọi `span` đều có nguyên văn trong `question`.
- [ ] Mọi predicate đều có trong `predicates.md` hoặc đã khai báo trong `new_predicates`.
- [ ] `reasoning_chain` đi từ `facts` tới `goal`, và mỗi bước đều có điều khoản cụ thể.
- [ ] Với câu `insufficient`, nếu bổ sung `missing_facts` thì chuỗi suy luận phải đi tới được kết luận.
- [ ] Tỉ lệ đủ / thiếu / ngoại lệ và số câu mỗi domain gần đúng với yêu cầu.


## BỔ SUNG V2 — Quy ước độc lập của gold và ngoại lệ (18/10/2026)

**Định nghĩa:** `expected: insufficient` khi, căn cứ vào **quy định pháp luật áp dụng** và các giả định benchmark đã công bố, những dữ kiện nêu trong câu hỏi chưa đủ để kết luận chắc chắn. Gold KHÔNG được xác lập theo rule hiện có trong KB hay theo output của mô hình.

1. **Thiếu điều kiện chung:** Điều kiện cần thiết để áp dụng quy phạm chung chưa được cung cấp thì ghi `insufficient`, liệt kê chính xác `missing_facts`. Không dùng ngầm `unknown = false`.
2. **Ngoại lệ hoàn toàn không có dấu hiệu:** Trong phạm vi benchmark, xử lý theo quy định chung nếu không có tình tiết nào gợi ý ngoại lệ, **chỉ khi** điều khoản đã được kiểm tra cho phép sử dụng giả định này. Đây là chính sách benchmark, không phải chứng cứ rằng ngoại lệ không tồn tại trong thực tế.
3. **Ngoại lệ được nhắc đến một phần:** Nếu có dấu hiệu liên quan tới ngoại lệ nhưng còn thiếu điều kiện quyết định và điều kiện này có thể đổi kết luận, gán `insufficient`.

**Tránh** tạo câu máy móc như “Tôi chưa đề cập tới tình trạng X”; trừ khi người dân thật sự đang mô tả việc chưa rõ X có liên quan pháp lý. Câu hỏi dạng `missing` nên thiếu dữ kiện tự nhiên, không gợi trực tiếp đáp án.

**Review:** Mọi câu phải có đủ căn cứ điều/khoản trước khi chốt gold. Không thay nhãn để khớp với KB; sửa nhãn sau khi xem output phải được version và không xem là held-out test. Các phép suy luận giả định trong `reasoning_chain` của câu insufficient không phải proof đã hoàn tất.
