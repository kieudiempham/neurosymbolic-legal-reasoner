# Rà soát codebase cho thực nghiệm ACIIDS (Cross-Layer MBD)

Ngày rà: 18/10/2026. Chỉ đọc code và dữ liệu, chưa chạy pipeline.

## 1. Kết luận nhanh

| Thành phần trong bài | Hiện trạng trong repo | Mức sẵn sàng |
|---|---|---|
| Legal KB dạng Horn rule (premise là predicate) | 1.269 canonical rule, nhưng **0 rule có premise dạng predicate**. Body hoặc rỗng (451), hoặc một khối chữ `{"predicate":"condition","text":...}` | ❌ Chặn |
| Quan hệ `exception_of` / `priority_over` / `incompatible` | Code có đọc (`runtime/conflict_resolution_policy.py`), nhưng **dữ liệu không có trường nào**. `logic_form: exception` có 120 rule nhưng không trỏ tới rule bị ngoại lệ | ❌ Chặn |
| Parsed fact có `polarity`, `origin`, `source_span` | `StructuredFact` (`schemas/structured_fact.py`) có `fact_origin`, `provenance`. Không có polarity, không có span | 🟡 Thêm trường |
| Forward reasoning nhiều bước | `run_forward_path` chạy **từng rule riêng**. Ghi chú trong code: "Single-rule base case… hook for future multi-rule expansion" (`reasoning/semantics/forward_engine.py`) | 🟡 Cần viết |
| Premise 3 trạng thái satisfied/contradicted/unknown | `atom_truth_status_ctx` trả `true/false/missing` (`reasoning/fact_matching.py`). Nhưng `_classify_rule` gộp positive=`false` vào missing (`semantics/backward_plan.py`) | 🟡 Sửa nhỏ |
| Reasoning State | `ReasoningState`, `BackwardCandidate`, `FailedPathRecord`, `ProofObject` có gần đủ nguyên liệu | 🟢 Gom lại |
| MBD + SWI-Prolog | Không có. Không dùng pyswip/problog lúc chạy (ProbLog chỉ export offline) | ❌ Viết mới |
| Backward dependency tracing | Không có. Repair chỉ route mã lỗi **đầu tiên** (`verification/repair_routing.py`) | ❌ Viết mới |
| NLI 3 nhãn | mDeBERTa-v3-base-xnli (`backend/app/config.py`), 3 nhãn, đã chạy được | 🟢 Dùng lại |
| Template câu cho predicate (cho NLI) | `controlled_verbalizer.py` chỉ có template cho 5 họ goal. Điều kiện dùng câu chung chung | 🟡 Viết theo vocabulary |
| Targeted re-parsing | `repair_layer1_slots_llm`, `build_layer2(forced_condition_atoms=...)` dùng lại được | 🟢 Dùng lại |
| Clarification | Có template câu hỏi theo kiểu target. `needs_clarification` bị **hard-code False**. Eval clarification có 2 bug | 🟡 Sửa |
| Abstain khi KB xung đột | `conflict_too_large` là dead code (`phase3_result=None`) | 🟡 Viết lại |
| Bộ câu hỏi | 290 câu có gold answer, 91 câu có `gold_missing_facts` (BHXH 90, DN 70, Thuế 70, Liên ngành 60). **Không có gold parse/gold fact/gold rule** | 🟡 Cần gán nhãn thêm |
| Kết quả cũ | Baseline GPT-4.1 trong `evaluation/results/baseline/` là **placeholder**. Run NeSy 290 câu: 253 câu lỗi. IRAC trong `compute_eval_tables.py` là heuristic, không so với gold | ❌ Không dùng được |

## 2. Hệ quả cho thiết kế thực nghiệm

MBD chỉ chạy được khi premise là predicate dùng chung vocabulary với parser. KB hiện tại không có điều đó, nên không thể chạy diagnosis trên toàn bộ KB.

Đề xuất: xây một **Diagnostic KB con** (curated) và một **diagnostic benchmark** có kiểm soát:

- Chọn 1–2 domain có câu hỏi dạng áp dụng điều kiện (BHXH và Doanh nghiệp hợp nhất).
- Viết tay khoảng 60–100 rule với premise dạng predicate, có chuỗi nhiều bước (G ← D ← A, B, C), cùng các quan hệ `exception_of` / `priority_over` / `incompatible` lấy từ điều luật thật. Mỗi rule giữ `source_ref` về văn bản gốc.
- Vocabulary predicate khoảng 80–150 predicate, mỗi predicate có một câu template tiếng Việt (dùng cho cả NLI và câu hỏi làm rõ).
- Mỗi câu hỏi gốc có gold facts, gold goal, gold rule path và gold conclusion. Sau đó **inject lỗi** để sinh ca chẩn đoán có nhãn.

## 3. Các module cần viết (đề xuất đặt trong `src/diagnosis/`)

1. `kb_diag/`: loader cho Diagnostic KB + relations, export sang Prolog facts.
2. `reasoning_state.py`: struct đúng như bài (goal, parsed/derived facts, applied/candidate rules, premise status, proof_dependencies, competing_rule_pairs).
3. `forward_fixpoint.py`: forward chaining nhiều bước, premise 3 trạng thái, rule 3 trạng thái, ghi dependency graph.
4. `observations.py`: Reasoning State → observation (`required/1`, `not_parsed/1`, `used_in_proof/1`, `applicable/1`, `incompatible/2`…).
5. `mbd.pl` + `mbd_engine.py` (pyswip hoặc gọi `swipl` qua subprocess): ràng buộc nhất quán, sinh ứng viên, lọc set-minimal.
6. `measurements.py`: chọn phép đo + backward tracing + NLI (dùng `runtime/nli`) + KB verification.
7. `controller.py`: vòng lặp chẩn đoán, dừng khi còn 1 / ambiguous / hết phép đo.
8. `recovery.py`: clarification (user giả lập trả lời từ gold facts), re-parse có định hướng, bỏ fact, áp dụng priority, abstain. Sau đó re-reason.
9. `fault_injection.py`: sinh ca có nhãn cho 6 loại lỗi.
10. `eval_diag.py`: Diag Acc, P/R/F1 theo loại, NLI acc/macro-F1/confusion, Recovery rate, số phép đo trên mỗi query, ablation.

## 4. Cách inject lỗi (đề xuất)

| Loại | Cách tạo | Nhãn đúng |
|---|---|---|
| Missing Case Information | Xoá câu chứa tình tiết C khỏi câu hỏi; parse chuẩn không có C | `MissingCaseInformation(C)` |
| Parser Omission | Giữ câu hỏi, xoá fact C khỏi kết quả parse | `ParserOmission(C)` |
| Parser Misinterpretation | Đổi polarity hoặc giá trị của fact C đã parse | `ParserMisinterpretation(C)` |
| Unsupported Parser Fact | Chèn fact C không có trong câu hỏi, chọn C sao cho nó tham gia proof | `UnsupportedParserFact(C)` |
| Resolvable Rule Overlap | Ca có 2 rule áp dụng, kết luận xung khắc, KB có `priority_over`/`exception_of` | `ResolvableRuleOverlap(R1,R2)` |
| Unresolved Encoded-KB Conflict | Như trên nhưng xoá quan hệ giải quyết khỏi KB | `UnresolvedKBConflict(R1,R2)` |

Lỗi tự nhiên: chạy parser thật trên câu hỏi gốc, so với gold facts, rồi gán nhãn bằng tay.

## 5. Việc sửa trong code hiện có

- `qa_orchestrator.py`: `needs_clarification` hard-code False (khoảng dòng 2713, 3504).
- `runtime/clarification_evaluation.py`: điều kiện `status=="needs_clarification"` không bao giờ đúng; dict inject thiếu `fact_key`.
- Lỗi runtime trong run 290 câu: `cannot access local variable 'conclusion_line'` (204 ca) và recursion depth (49 ca).
- `compute_eval_tables.py`: IRAC heuristic. Cần thay bằng chấm theo gold (LLM judge + người duyệt, báo cáo κ).
- Baseline: chạy lại thật, cùng backbone với hệ NeSy.
