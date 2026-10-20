# Danh sách sửa paper ACIIDS cho khớp implementation (sau commit sửa NLI/rule-check)

Đối chiếu bản `ACIIDS (1).pdf` (15 trang) với code trong `src/diagnosis/`. Câu tiếng Anh dưới đây là gợi ý, có thể chép thẳng vào LaTeX.

## A. Đã sửa bằng code (paper giữ nguyên ý, chỉ cần mô tả cụ thể)

### A1. NLI acceptance (Sec. 4.4, Eq. 11)
Code (`nli.verify`): gọi NLI hai lần, với template khẳng định và template phủ định. Nhãn được chấp nhận khi p ≥ 0,70 **và** hai lần không mâu thuẫn. Nếu không đạt thì là ⊥ và không đưa vào Prolog.
> "A raw NLI prediction becomes an observation only if it passes an acceptance test: the proposition is verbalised with its positive and its negative template, the positive-template label must have probability at least τ = 0.70, and the negative-template label must not contradict it. Rejected measurements yield ⊥ and add no observation (Algorithm 1, line 19)."

### A2. Ambiguity → clarification (Sec. 4.4 cuối, Def. 9)
Code: khi các chẩn đoán còn lại chỉ khác nhau ở miss/omit của một mệnh đề và không còn phép đo nào, hệ thống hỏi người dùng (`Clarify(p)`), sau đó suy luận lại.
> "If the surviving diagnoses differ only in whether a required proposition is missing or omitted and no admissible measurement remains, the controller requests a clarification of that proposition from the user."

### A3. Rule-check baseline (Sec. 4.7, 5.2)
Code: cấu hình `rule_check`. Dùng cùng mọi bằng chứng (NLI đã xác minh cho tất cả mệnh đề liên quan, KB verification cho tất cả cặp rule), rồi gán nhãn theo if-else, lấy nhãn khớp đầu tiên. Đây chính là "matched rule-check baseline… same parser, legal KB, and evidence budget" mà paper hứa.

### A4. Bootstrap CI
Final Acc. và Diag. Acc. có khoảng tin cậy 95% (1.000 lần lấy mẫu lại theo ca). Cần ghi vào phần mô tả metric (Sec. 5.3).

## B. Sửa paper cho đúng code

| # | Vị trí | Hiện viết | Sửa thành |
|---|---|---|---|
| B1 | Sec. 4.4, Eq. 13–14, Def. 8 | Chọn m* = argmax S(m)/cost(m) | Chính sách **first-disagreement**: "the first not-yet-used measurement on which the surviving diagnoses disagree, ordered KB checks → NLI on required propositions → NLI on proof-supporting propositions (name order)". Chuyển Eq. 13–14 sang mục future extension hoặc ghi là "a possible scoring refinement" |
| B2 | Algorithm 1 dòng 11–16 | FilterDiscriminating + SelectMeasurement | `A ← {m ∉ Used : diagnoses in D disagree on target(m)}`; `m ← first(A)` |
| B3 | Sec. 4.5 / 4.6 | Không nói thứ tự | Hai pha: (A) xác minh các parser fact mà proof hoặc các rule bị chặn dựa vào, cùng các cặp rule cạnh tranh; (B) chỉ khi pha A ra chẩn đoán rỗng mới giải thích các mệnh đề required. Recovery: **sửa lỗi tầng đầu vào (user/parser) trước, suy luận lại**; xử lý lỗi KB khi không còn lỗi đầu vào |
| B4 | Def. 4, Sec. 4.2 | "unknown premise is not interpreted as false" | Thêm: "Open-world for case facts; the only exception are predicates that encode statutory exceptions (e.g. receiving a pension, foreign citizenship), which default to false unless stated, mirroring the legal convention that an exception applies only when invoked. Encoded-KB relations are closed-world within the curated scope (an unencoded exception/priority is treated as absent)." |
| B5 | Sec. 4.2 | Candidate retrieval R_q ⊆ R | "In the evaluated configuration the curated KB is small, so R_q = R (no retrieval step)" |
| B6 | Sec. 4.2 / 5.2 | P(q) gồm g | "Experiments use the gold legal goal g (oracle-goal setting); only the parser's fact set F0 is predicted." Ghi rõ đây là **oracle-goal**, chưa phải QA end-to-end hoàn toàn |
| B7 | Sec. 3.1, Def. 1 | S gồm scope, validity; có P | "S records source provenance (document, article, clause, point); scope and validity are not encoded in the current curated KB. The curated KB contains |E| = 9 exception relations and no priority relations (P = ∅); resolvable overlaps in the benchmark are therefore exception-based." |
| B8 | Def. 2 | premise là predicate | "premises are literals p or ¬p" |
| B9 | Def. 3 / Sec. 3.3 | Inc trên chủ thể tương thích | "Inc(ri, rj) holds when the conclusions are the same predicate with opposite polarity for the single case subject." |
| B10 | Sec. 2.2 / 4.3 | "SWI-Prolog is intended to evaluate" | "SWI-Prolog (v10.0.2) evaluates…"; set-minimal enumeration chạy trong Prolog theo lực lượng tăng dần (tối đa 5 fault) |
| B11 | **Sec. 2.3 (sai sự thật)** | "XNLI… evaluation languages do not include Vietnamese" | **XNLI có tiếng Việt.** Sửa: "XNLI covers 15 languages including Vietnamese [3]; the multilingual NLI model we use (mDeBERTa-v3-base, XNLI/MNLI fine-tuned) is therefore trained on Vietnamese NLI data, though not on legal text." |
| B12 | Sec. 5.1 | Validation split để chọn parser/NLI | "No model selection was performed: the NLI model and the parser are fixed pretrained models with default thresholds, so no test data was used for tuning." |
| B13 | Sec. 5.1 | Không nói | Mỗi ca chỉ inject **một** lỗi chính (single-fault). Lỗi tự nhiên đến từ parser GPT-4o thật. Cơ chế hỗ trợ đa lỗi nhưng benchmark không đánh giá đa lỗi |
| B14 | Sec. 5.2 | Neural LLM "retrieved legal context" | "GPT-4o (temperature 0) receives the question and the verbatim text of the relevant articles (Art. 2, 33, 64, 70 of Law 41/2024 and Art. 24 of the Labour Code); no retrieval step" |
| B15 | Table 2, Sec. 5.3 | Cột IRAC | Bỏ cột IRAC, hoặc chỉ đưa vào nếu đã chấm thật (CLI `diagnosis.ask` có sinh câu trả lời IRAC nhưng chưa chấm) |
| B16 | Abstract | "quantitative evaluation remains pending" | Viết lại kèm số, sau khi chạy lại benchmark |
| B17 | Sec. 5.4 | Placeholder | Kết quả + failure analysis (`experiments/diag/phan_tich_ket_qua.md`) + bảng parser thật |

## C. Rủi ro cần quyết định khi có kết quả mới
- **Rule-check có thể ngang MBD trên benchmark single-fault.** Khi mỗi ca chỉ có một lỗi và được đo đủ bằng chứng, if-else khớp-đầu-tiên có thể cho kết quả tương đương. Nếu vậy, nên viết đúng như Sec. 4.7 đã viết sẵn: đóng góp là **cách hình thức hoá và khả năng báo mơ hồ / hỏi lại có nguyên tắc**, không phải độ chính xác cao hơn. Đồng thời báo các chỉ số mà rule-check không có: tỉ lệ ca mơ hồ được phát hiện, số phép đo trên mỗi câu.
- **NLI acceptance làm giảm số observation** và tăng số lần hỏi lại. Cần báo acceptance rate, accuracy trước và sau bước chấp nhận (đã có trong Table 5 mới), và so với cấu hình `raw_nli`.

## D. Lệnh chạy lại (khi sẵn sàng)
```bash
# mỗi cấu hình một tiến trình, chạy song song; --subset 0 = đủ 263 ca
for c in base_nesy nesy_diag no_mbd rule_check exhaustive_evidence raw_nli; do
  PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.run_eval --configs $c --subset 0 &
done
PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.run_eval --merge
PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.run_real_parser
PYTHONPATH=src .venv_diag/Scripts/python -m diagnosis.make_tables
```
