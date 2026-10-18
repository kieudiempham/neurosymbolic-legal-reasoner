# Hướng dẫn sinh rule cho các nhánh "hoặc" còn thiếu

Mỗi dòng trong `[RULES CẦN TÁCH]` là một rule mà lượt duyệt trước đã sửa thành **một nhánh** (`fixed_branch`). `review_reason` ghi lại các nhánh thay thế khác chưa được mã hoá.

Nhiệm vụ: đọc `[NGUYÊN VĂN]` và tạo rule cho **mọi nhánh còn thiếu**. Không tạo lại nhánh đã có trong `fixed_branch`.

- Mỗi nhánh là một rule riêng; premises là các điều kiện **phải đồng thời** đúng của nhánh đó.
- Giữ cùng kết luận và cùng cách đặt tên predicate như `fixed_branch` khi đúng nghĩa. Nếu cần predicate mới thì đặt tên tiếng Anh, snake_case, ngắn.
- Điều kiện chung của cả khoản (ví dụ "công dân Việt Nam" ở đầu khoản) phải lặp lại trong từng nhánh.
- `source` ghi đúng khoản/điểm của nhánh.
- Nếu đọc kỹ thấy không thật sự có nhánh thay thế (lượt trước nhận định nhầm), thì không tạo rule mới và ghi một dòng `{"parent": "<id>", "none": true, "reason": "..."}`.
- `confidence`: `high` hoặc `low`, theo nghĩa như lượt duyệt trước.

Định dạng đầu ra: JSONL, mỗi dòng một rule mới:

```json
{"id": "<parent_id>-s1", "parent": "<parent_id>", "premises": [...], "conclusion": "...",
 "source": "<doc_id>, Điều X khoản Y điểm z", "exception_to": "", "confidence": "high|low", "reason": "<nhánh nào>"}
```

Đánh số `-s1`, `-s2`, … theo từng rule gốc.
