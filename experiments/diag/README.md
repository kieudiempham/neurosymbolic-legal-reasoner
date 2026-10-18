# Thực nghiệm Cross-Layer MBD (ACIIDS)

## Cách chạy lại

```bash
# môi trường riêng (không cần quyền Admin)
python -m venv .venv_diag
.venv_diag/Scripts/python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv_diag/Scripts/python -m pip install transformers sentencepiece protobuf pyyaml openai python-dotenv
# SWI-Prolog 10.0.2: giải nén bộ cài chính thức vào .tools/swipl (hoặc đặt biến SWIPL trỏ tới swipl.exe)

PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.run_eval          # 4 cấu hình
PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.run_llm_baseline  # cần LLM_API_KEY trong .env
PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.make_tables       # -> experiments/diag/tables.md
```

## Thành phần

| File | Vai trò |
|---|---|
| `data/diag/vocabulary.yaml` | Vocabulary predicate dùng chung cho parser và KB, mỗi predicate có câu template (NLI) và câu hỏi làm rõ |
| `data/diag/kb_bhxh.yaml` | Diagnostic KB viết tay từ Luật BHXH 41/2024 (+ BLLĐ 2019 Điều 24): rule, `exception_of`, `priority_over` |
| `data/diag/gold_cases.yaml` | Câu hỏi gold: dữ kiện + span nguyên văn + kết luận đúng |
| `data/diag/legal_context_bhxh.txt` | Nguyên văn các điều luật dùng làm ngữ cảnh cho baseline LLM |
| `src/diagnosis/reasoner.py` | Forward chaining 3 trị (satisfied/contradicted/unknown), Reasoning State, backward dependency tracing |
| `src/diagnosis/mbd.pl` | Mô hình chẩn đoán (system model + fault modes) cho SWI-Prolog |
| `src/diagnosis/mbd_engine.py` | Sinh ứng viên, gọi SWI-Prolog kiểm tra nhất quán, lọc set-minimal |
| `src/diagnosis/nli.py` | NLI 3 nhãn: mDeBERTa-v3-base-xnli-multilingual-nli-2mil7 |
| `src/diagnosis/controller.py` | Vòng chẩn đoán: trigger → observation → MBD → đo có định hướng → recovery → suy luận lại |
| `src/diagnosis/inject.py` | Inject lỗi có kiểm soát để tạo ca có nhãn |
| `src/diagnosis/run_eval.py` | Chạy 4 cấu hình, tính metric |
| `src/diagnosis/run_llm_baseline.py` | Baseline Neural LLM (câu hỏi + nguyên văn điều luật) |

## Thiết kế benchmark

- **Ca gốc:** câu hỏi BHXH lấy từ `evaluation/qa_290_exp_cases_gold_mode.jsonl` (giữ id gốc) cộng câu tự viết (`source: synthetic`) để có đủ ca đầy đủ dữ kiện, ca có ngoại lệ và ca có xung đột.
- **Ca thiếu dữ kiện tự nhiên:** câu thật mà KB không đủ dữ kiện để kết luận → gold = MissingCaseInformation.
- **Inject lỗi** (mỗi ca một lỗi chính):
  - MissingCaseInformation(C): xoá span của C khỏi câu hỏi và khỏi kết quả parse.
  - ParserOmission(C): giữ câu hỏi, xoá C khỏi kết quả parse.
  - ParserMisinterpretation(C): đảo giá trị C trong kết quả parse (chỉ giữ khi kết luận thay đổi).
  - UnsupportedParserFact(X): thêm fact X không có trong câu hỏi (chỉ giữ khi X tham gia proof và làm đổi kết luận).
  - ResolvableRuleOverlap: ca tự nhiên có hai rule cùng áp dụng, kết luận trái nhau, KB có `exception_of`.
  - UnresolvedKBConflict: (a) tự nhiên, ví dụ thử việc (BLLĐ Đ24) và "tên gọi khác" (Luật BHXH Đ2.1.a) không có quan hệ mã hóa; (b) inject bằng cách xoá quan hệ `exception_of` khỏi bản sao KB.
- **Parser** trong benchmark là parse gold có lỗi được inject, nên biết chắc nguồn lỗi. Chưa đánh giá parser LLM thật.
- **Người dùng giả lập:** khi hệ thống hỏi làm rõ, trả lời bằng giá trị gold. Ca thiếu dữ kiện tự nhiên không có câu trả lời, nên kết quả đúng là "clarification_requested".

## Cấu hình

| Tên | Mô tả |
|---|---|
| `neural_llm` | LLM trả lời từ câu hỏi + nguyên văn điều luật (temperature 0) |
| `base_nesy` | Parse → forward reasoning → trả lời; không chẩn đoán |
| `nesy_diag` | Đầy đủ: Reasoning State + MBD/SWI-Prolog + đo có định hướng + recovery + suy luận lại |
| `no_mbd` | Ablation: gán thẳng triệu chứng → nguyên nhân (thiếu điều kiện → Missing; xung đột → KB conflict), không thu thêm bằng chứng |
| `exhaustive_evidence` | Ablation: chạy mọi phép đo (NLI cho mọi mệnh đề liên quan, KB verify mọi cặp) trước rồi mới MBD |

## Metric

- **Diag. Acc.:** chẩn đoán vòng đầu duy nhất và chứa đúng lỗi gold (đúng loại + đúng mệnh đề/cặp rule). Được phép có thêm Overlap thật, hoặc Missing cho mệnh đề mà câu hỏi thật sự không nêu.
- **P/R/F1 theo loại:** theo loại chính dự đoán (lỗi không phải Overlap đầu tiên; Overlap; Normal; Ambiguous).
- **Recovery:** tỉ lệ ca có lỗi mà chẩn đoán đúng và câu trả lời cuối đúng.
- **Final Acc.:** câu trả lời cuối (true/false/abstain/clarification_requested) khớp kỳ vọng.
- **Measurements/query:** số lần gọi NLI + KB verification (cùng một phép đo trên cùng input không tính lại).
- **NLI:** accuracy, macro-F1, confusion trên mọi phép đo NLI; nhãn gold suy ra từ cách dựng ca.

## Giới hạn cần ghi trong bài

- KB nhỏ, viết tay, một domain (BHXH). Có rule suy ngược (`a_contrario`) được đánh dấu riêng.
- Lỗi chủ yếu là inject có kiểm soát; câu tự viết chiếm phần lớn ca đủ dữ kiện.
- Mỗi ca giả định một lỗi chính.
- NLI dùng model có sẵn, không fine-tune và không chọn trên tập validation riêng (chưa đủ dữ liệu để tách).
# CLI
PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.ask
Gõ câu hỏi vào. Nếu thiếu dữ kiện, hệ thống sẽ hỏi lại (trả lời c / k / Enter). Có thể truyền câu hỏi thẳng làm đối số, thêm --no-clarify để không hỏi lại, hoặc --json để lấy kết quả dạng JSON.

Mỗi câu trả lời gồm:

câu hỏi pháp lý được chọn;
các fact mà parser trích được;
chẩn đoán và cách đã xử lý;
kết luận;
danh sách rule kèm điều luật đã dùng;
số phép đo;
câu trả lời theo IRAC: Vấn đề, Quy định, Áp dụng, Kết luận.