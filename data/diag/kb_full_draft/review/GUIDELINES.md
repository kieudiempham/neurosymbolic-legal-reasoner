# Hướng dẫn duyệt rule (draft KB)

Mỗi lô (`batches/batch_XX.md`) gồm nhiều điều luật. Mỗi điều có `[NGUYÊN VĂN]` (văn bản gốc) và `[RULES]` (một rule JSON mỗi dòng, do gpt-4o-mini trích tự động).

Với **mọi** rule, đối chiếu với nguyên văn của chính điều đó rồi cho một nhãn:

- `correct`: điều kiện và kết luận đúng nghĩa văn bản, đủ điều kiện bắt buộc, `source` đúng khoản/điểm.
- `fix`: ý đúng nhưng có lỗi sửa được: thiếu/thừa điều kiện, sai dấu (`~`), gộp các điều kiện "hoặc" vào một rule (khi đó ghi rule đã sửa cho MỘT phương án và nêu trong `reason` rằng cần tách), sai khoản/điểm, sai kết luận, hoặc predicate dùng sai nghĩa.
- `drop`: rule bịa (văn bản không có quy phạm đó), trùng lặp hoàn toàn với rule khác trong cùng điều, hoặc nội dung không phải quy phạm (phạm vi điều chỉnh, giải thích từ ngữ thuần túy, hiệu lực, trách nhiệm thi hành).

Quy ước:
- Premise/conclusion là tên predicate snake_case, thêm `~` ở đầu nếu phủ định. Khi sửa, giữ tên predicate cũ nếu đúng nghĩa; chỉ đặt tên mới khi tên cũ sai nghĩa (đặt ngắn, tiếng Anh, snake_case).
- `exception_to`: nếu rule là ngoại lệ ("trừ trường hợp", "không áp dụng đối với") mà trường này trống hoặc sai thì sửa thành tham chiếu đúng (ví dụ `"khoản 1 Điều 2"`).
- `confidence`: `high` nếu chắc chắn; `low` nếu cần hiểu luật sâu, văn bản mơ hồ hoặc dẫn chiếu sang văn bản khác mà ta không có. Các rule `low` sẽ được người duyệt lại.
- `reason`: một câu tiếng Việt ngắn; bắt buộc khi nhãn là `fix` hoặc `drop`.
- Không bỏ sót rule nào; giữ nguyên `id`.

Định dạng đầu ra: file JSONL, mỗi dòng một rule:

```json
{"id": "...", "verdict": "correct|fix|drop", "confidence": "high|low", "reason": "...",
 "premises": [...], "conclusion": "...", "source": "...", "exception_to": "..."}
```

`premises`, `conclusion`, `source`, `exception_to` là bản ĐÃ SỬA. Nếu nhãn là `correct` thì chép nguyên giá trị cũ; nếu là `drop` thì có thể để rỗng.
