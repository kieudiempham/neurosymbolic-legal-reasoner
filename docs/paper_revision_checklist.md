# Checklist sửa Mục 3–4 (và vài chỗ liên quan) cho khớp method đã implement

Đối chiếu với code cuối (`src/diagnosis/`, commit hiện tại). Mỗi mục ghi: chỗ cần sửa → nội dung đúng theo code →
câu tiếng Anh gợi ý để chép vào LaTeX. Số liệu Mục 5 xem `docs/paper_section5_draft.md`.

---

## Mục 3 — Mô hình hóa (KB, luật, xung đột)

### 3.1 Knowledge base (Def. 1)
- **Đúng theo code:** 5 KB theo lĩnh vực (BHXH 149 rule, Doanh nghiệp 70, Thuế 200, Lao động 129, Liên ngành 88;
  tổng 636 rule) và 422 quan hệ ngoại lệ `exception_of`. **Không có quan hệ ưu tiên (P = ∅).** Mỗi rule có nguồn
  (văn bản, điều, khoản, điểm); **không mã hóa phạm vi/hiệu lực thời gian**. KB được xây từ 7.906 rule nháp do
  GPT-4o-mini trích theo từng điều, chọn theo điều luật được trích dẫn, viết lại trên bộ vị từ chung và rà soát; bản vá
  chỉ lấy từ lỗi trên dev.
- > "The KB consists of five domain KBs (636 Horn rules, 422 exception relations, no priority relations, P = ∅).
  > Each rule records its source (document, article, clause, point); scope and temporal validity are not encoded.
  > Rules were obtained from 7,906 LLM-extracted candidates (GPT-4o-mini, one call per article) by selecting the
  > articles relevant to the benchmark, re-expressing them over a shared predicate registry and reviewing them;
  > KB patches were derived only from development-split failures."
- Một số rule có tiền đề rỗng (rule mặc định chung, ví dụ "thu nhập không được miễn thuế trừ khi thuộc danh mục"),
  và mỗi trường hợp miễn trừ là `exception_of` của rule đó → nêu: "general default rules (empty body) whose
  enumerated exemptions are encoded as exceptions".

### 3.2 Rule (Def. 2)
- Tiền đề là **literal** p hoặc ¬p; kết luận là một literal.
- > "A rule r = (B_r → h_r) has a body of literals p or ¬p and a single literal head."

### 3.3 Xung đột (Def. 3)
- `Inc(ri, rj)` khi hai kết luận cùng vị từ, khác cực tính, cho **một chủ thể duy nhất** của câu hỏi.
- Một cặp xung đột là **resolvable** khi có `exception_of` giữa hai rule (rule ngoại lệ thắng); ngược lại là
  **unresolved**.
- > "Two applicable rules conflict when their heads are the same predicate with opposite polarity for the single
  > case subject; the conflict is resolvable iff an encoded exception relation orders them."

### 3.4 Ngữ nghĩa ba giá trị và thế giới mở (Def. 4) — **SỬA**
- **Bỏ** đoạn checklist cũ nói "vị từ ngoại lệ mặc định là false". Code hiện **không dùng mặc định nào**
  (`KB_EXCEPTION_DEFAULTS=0`): dữ kiện hoàn toàn open-world.
- Ngoại lệ được xử lý bằng **cơ chế treo (suspension)**: rule chung bị **treo** (không bắn) khi một ngoại lệ của nó
  được xác lập **một phần** — có ít nhất một tiền đề **riêng của ngoại lệ** (không tính tiền đề chung với rule chung)
  đã thỏa, không tiền đề nào bị bác bỏ, còn tiền đề chưa biết. Ngoại lệ không được nhắc tới → rule chung bắn bình
  thường. Ngoại lệ được xác lập đầy đủ → cả hai rule bắn → xung đột, được giải quyết ở tầng KB (xem 4.6).
- > "Case facts are open-world: an unknown premise is neither true nor false and no defaults are assumed. An exception
  > applies only once established. While an exception of rule r is partially established — at least one of its
  > own premises (not shared with r) is satisfied, none is contradicted and some are unknown — r is suspended and its
  > conclusion remains unknown; an exception the case does not raise leaves r in force. This mirrors the convention
  > that an exception applies only when invoked."

### 3.5 Lập luận tiến (Forward reasoning)
- Lặp đến điểm bất động; rule áp dụng được và không bị treo thì bắn. Hai kết luận trái nhau **không được khẳng định**:
  vị từ đó để chưa xác định và ghi lại các cặp cạnh tranh (`competing pairs`). Giải quyết xung đột **không** làm trong
  forward reasoning mà qua KB verification + recovery (chặn rule thua rồi suy luận lại).
- > "Forward chaining runs to a fixed point. When two applicable rules derive opposite literals, neither is asserted:
  > the predicate stays unknown and the competing pair is recorded; resolution is performed by KB verification and
  > recovery, which blocks the losing rule and re-reasons."

## Mục 4 — Chẩn đoán xuyên tầng

### 4.1 Parser (Sec. 4.2) và goal
- Parser: **GPT-4o, temperature 0, đầu ra JSON**, nhận danh sách vị từ đầu vào của KB lĩnh vực (kèm câu khi đúng/khi
  sai), trả về literal + đoạn nguyên văn (span). Không có bước truy hồi rule: dùng toàn bộ KB của lĩnh vực (R_q = R).
- **Goal pháp lý là gold (oracle goal)**; chỉ tập dữ kiện F0 là do parser dự đoán.
- > "The semantic parser (GPT-4o, temperature 0, JSON output) maps the question to literals over the domain KB's input
  > predicates, each with a verbatim span. The full domain KB is used (R_q = R). Experiments use the gold legal goal
  > (oracle-goal setting); only the fact set F0 is predicted."

### 4.2 Truy vết phụ thuộc ngược (Sec. 4.3) — **SỬA/BỔ SUNG**
- Tập `required` = các mệnh đề đầu vào chưa biết trên **đường suy luận liên quan** tới goal:
  1. Một rule mở là liên quan nếu nó có ít nhất một tiền đề đã thỏa, hoặc bị treo, hoặc có tiền đề dẫn xuất chưa biết
     mà bản thân có đường liên quan; nếu không rule nào liên quan thì xét mọi rule mở.
  2. Trong các rule liên quan, chỉ giữ **những rule được hỗ trợ nhiều nhất** (số tiền đề đã xác lập lớn nhất).
  3. Với rule bị treo, truy tiếp vào tiền đề của ngoại lệ đang treo nó.
  4. **Chọn nhánh bằng câu hỏi:** nếu còn hơn 6 mệnh đề required (nhiều nhánh thay thế, ví dụ danh mục miễn thuế),
     đo NLI các mệnh đề đó và chỉ giữ nhánh mà câu hỏi thực sự nói tới (nhãn được chấp nhận entail/contra).
- `checked` = các dữ kiện do parser sinh ra mà chứng minh của goal (hoặc rule chặn goal) dựa vào.
- > "Backward tracing collects the unresolved input propositions on the relevant open paths to the goal: rules with an
  > established premise, a suspended rule or a relevant derived premise (all open rules if none is relevant), keeping
  > among alternatives only the best-supported ones (most established premises), and following the premises of the
  > exception that suspends a rule. When more than six propositions remain, they are measured against the question
  > and only the alternatives the question speaks about are kept."

### 4.3 Mô hình chẩn đoán và Prolog (Sec. 4.3–4.4, Def. 5–7)
- Thành phần: người dùng (mỗi mệnh đề required), parser (mỗi mệnh đề required/checked), KB (mỗi cặp cạnh tranh).
  Chế độ lỗi: `missing`, `omission`, `misinterp`, `unsupported`, `overlap`, `kbconflict`.
- Hành vi (đúng như `mbd.pl`): người dùng bình thường nêu mọi mệnh đề required (nhãn ≠ neutral); missing ⇒ neutral.
  Parser bình thường: entail→pos, contra→neg, neutral→none; omission: (entail|contra)→none; misinterp: entail→neg,
  contra→pos; unsupported: neutral→(pos|neg). KB: overlap ⇔ resolution ∈ {yes, unknown}; kbconflict ⇔
  resolution ∈ {no, unknown}. Nhãn NLI chưa đo = bất kỳ trong 3 nhãn.
- **Chẩn đoán tối thiểu theo tập (Reiter)**, liệt kê theo lực lượng tăng dần trong **SWI-Prolog 10.0.2**, tối đa 5 lỗi;
  **giới hạn không gian ứng viên** Σ_j≤k C(n, j) ≤ 2·10⁵ (k được hạ khi có nhiều nguyên tử lỗi).
- **Tách thành phần độc lập:** nếu tìm kiếm chung có giới hạn không ra chẩn đoán, chẩn đoán từng thành phần (một mệnh
  đề hoặc một cặp rule) riêng rồi lấy tích; **chính xác** vì mọi ràng buộc của mô hình chỉ chạm một thành phần.
- > "Set-minimal diagnoses are enumerated by increasing cardinality in SWI-Prolog (v10.0.2), up to five faults, the
  > cardinality bound being lowered when the candidate space exceeds 2·10⁵. Since every model constraint involves a
  > single component (one proposition or one rule pair), the minimal diagnoses are the products of the per-component
  > minimal diagnoses; this decomposition is used when the bounded joint search returns none."

### 4.4 Phép đo NLI và kiểm tra chấp nhận (Sec. 4.4, Eq. 11) — **SỬA**
- Bỏ mô tả cũ "mDeBERTa, gọi 2 template, τ = 0,70".
- Đúng theo code: phép đo NLI của mệnh đề c = **trung bình phân bố nhãn của mDeBERTa-v3 (XNLI) và GPT-4o-mini**;
  GPT-4o-mini được hỏi câu hỏi + câu khẳng định của c, chọn A/B/C (đúng / không xác định / sai), lấy xác suất của 3 chữ
  cái (temperature 0). **Chỉ dùng template khẳng định.** Nhãn được chấp nhận nếu xác suất cao nhất ≥ **τ = 0,50**,
  ngược lại là ⊥ và không thêm quan sát. Mô hình, prompt và τ chọn trên dev (tiêu chí đặt trước: trung bình độ chính
  xác chẩn đoán và 1 − tỉ lệ báo oan).
- > "A measurement of proposition c compares the original question with the positive verbalisation of c. Its label
  > distribution is the mean of a multilingual NLI classifier (mDeBERTa-v3, XNLI) and an LLM (GPT-4o-mini, probabilities
  > of the three answer options, temperature 0). The label becomes an observation q(c, ℓ) only if its probability is
  > at least τ = 0.50; otherwise the measurement returns ⊥ and adds no observation. The measurement model, prompt and τ
  > were selected on the development split."
- **Sec. 2.3 (sai sự thật cũ, vẫn phải sửa):** XNLI **có** tiếng Việt.

### 4.5 Chọn phép đo (Sec. 4.4, Eq. 13–14, Def. 8, Algorithm 1 dòng 11–16) — **SỬA**
- Không có argmax S(m)/cost(m). Chính sách **first-disagreement**: phép đo chưa dùng đầu tiên mà các chẩn đoán còn lại
  bất đồng, theo thứ tự KB verification → NLI trên mệnh đề required → NLI trên mệnh đề checked (theo tên). Các dữ kiện
  parser mà chứng minh dựa vào được đo NLI trước khi chẩn đoán (kích hoạt iii).
- Algorithm 1: `A ← {m ∉ Used : diagnoses in D disagree on target(m)}`; `m ← first(A)`.
- Eq. 13–14 chuyển thành "a possible cost-aware refinement" (future work).

### 4.6 Hai pha chẩn đoán, hỏi lại và sửa lỗi (Sec. 4.5–4.6) — **SỬA/BỔ SUNG**
- **Pha A:** giải thích các dữ kiện mà chứng minh dựa vào và các cặp rule cạnh tranh. **Pha B:** giải thích các mệnh
  đề required. Pha B chạy khi pha A không có lỗi **hoặc chỉ có chồng lấn giải quyết được (overlap)** — chồng lấn vô
  hại không giải thích vì sao goal chưa xác định nên không được dừng việc tìm lỗi đầu vào.
- **Hỏi lại (Clarify):** khi các chẩn đoán còn lại chỉ khác nhau ở missing/omission của một mệnh đề và không còn phép
  đo phân biệt được → hỏi người dùng đúng mệnh đề đó.
- **Sửa lỗi theo tầng, tối đa 3 vòng, suy luận lại sau mỗi vòng:** sửa lỗi tầng đầu vào trước (missing → hỏi người
  dùng; omission/misinterp → đặt giá trị theo nhãn NLI đã chấp nhận, nếu không có thì rút dữ kiện nghi ngờ;
  unsupported → bỏ dữ kiện); chỉ khi không còn lỗi đầu vào mới xử lý tầng KB (overlap → chặn rule thua theo
  `exception_of`; kbconflict → không kết luận / abstain).
- > "Diagnosis proceeds in two phases: phase A explains the parser facts the proof depends on and the competing rule
  > pairs; phase B explains the unresolved required propositions and runs when phase A finds no fault or only
  > resolvable overlaps, which are benign. Recovery repairs input-layer faults first (asking the user for missing
  > information, setting an omitted or misinterpreted fact from the accepted measurement, withdrawing an unsupported
  > fact), re-reasons, and acts on KB-layer faults only when no input fault remains (a resolvable overlap blocks the
  > losing rule; an unresolved conflict makes the system abstain), for at most three rounds."

### 4.7 Sinh câu trả lời (IRAC)
- Câu trả lời IRAC do GPT-4o **diễn đạt lại chứng minh đã kiểm chứng**: nhận kết luận đã xác minh, dữ kiện đã dùng và
  các rule đã áp dụng (kèm nguồn điều luật); được dặn không đổi kết luận, không thêm căn cứ ngoài danh sách. Khi chưa
  đủ dữ kiện thì liệt kê thông tin cần bổ sung.
- > "The IRAC answer is a verbalisation of the verified proof by GPT-4o, constrained to the verified conclusion, the
  > facts used and the applied rules with their sources; it may not change the conclusion or add legal bases."

### 4.8 Baseline Heuristic (Sec. 4.7, 5.2)
- Cùng bằng chứng (đo NLI mọi mệnh đề required/checked, KB verification mọi cặp cạnh tranh), gán nhãn if–else khớp
  đầu tiên: dữ kiện checked mâu thuẫn → misinterp; neutral → unsupported; nếu không có lỗi đó thì mỗi mệnh đề
  required là omission (nếu câu hỏi nêu) hoặc missing (nếu không); cặp cạnh tranh → overlap/kbconflict theo resolution.
  Cùng cơ chế sửa lỗi.

## Các chỗ khác phải đồng bộ
- **Abstract / Intro:** bỏ "quantitative evaluation remains pending"; nêu kết quả chính và **định vị đóng góp**: chẩn
  đoán xuyên tầng chính xác hơn heuristic cùng bằng chứng (fault F1 +10,6) và hỏi người dùng ít hơn khoảng một nửa,
  với độ chính xác trả lời ngang nhau; **không** tuyên bố hơn GPT-4o về QA end-to-end trên test.
- **Dataset:** ghi rõ câu hỏi là **tổng hợp do GPT-4o sinh** (không phải câu hỏi thu thập), nhãn gold đang thẩm định.
- **Bảng cũ (Table 2–4 placeholder):** thay bằng 4 bảng trong `paper_section5_draft.md` (Table 2–5).
- **Single-fault + 2-fault:** benchmark có cả hai; cơ chế hỗ trợ đa lỗi.
- **Mục 6 (Conclusion/Limitations):** thêm điểm nghẽn là bước đo NLI (trần 100% khi đo hoàn hảo), oracle goal, người
  dùng mô phỏng, nhãn LLM sinh, test nhỏ.
