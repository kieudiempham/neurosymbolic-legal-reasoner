# Mô tả phương pháp đã implement — dùng để viết Mục 3 và 4

Tài liệu này mô tả **đúng những gì code đang làm** (commit hiện tại, `src/diagnosis/`). Mỗi phần gồm: ý chính
(tiếng Việt), định nghĩa/câu gợi ý bằng tiếng Anh để đưa vào paper, và file code tương ứng. Số liệu thực nghiệm xem
`docs/paper_section5_draft.md` và `experiments/final_tables.md`.

---

## 0. Tổng quan pipeline

```
Câu hỏi q ──► Parser (GPT-4o) ──► tập dữ kiện F0 (literal + span)
                                     │      goal g (cho sẵn, oracle)
                                     ▼
                       Lập luận tiến 3 giá trị trên KB  ──► Reasoning State S
                                     │
                     ┌───────────────┴────────────────┐
                     ▼                                ▼
          Truy vết phụ thuộc ngược           Cặp rule cạnh tranh
          (required, checked)                 (competing pairs)
                     └───────────────┬────────────────┘
                                     ▼
                    Quan sát O  ──►  MBD trong SWI-Prolog  ──► tập chẩn đoán tối thiểu D
                                     ▲                         │ (nhiều chẩn đoán)
                     phép đo NLI / KB verification ◄───────────┘ chọn phép đo phân biệt
                                     │ (1 chẩn đoán, hoặc mơ hồ ⇒ hỏi người dùng)
                                     ▼
              Sửa lỗi theo tầng (đầu vào trước, KB sau) ──► suy luận lại (≤ 3 vòng)
                                     ▼
                Kết luận (có / không / chưa đủ dữ kiện / không kết luận) + IRAC
```

Ba tầng có thể gây lỗi: **người dùng** (câu hỏi thiếu thông tin), **parser** (bỏ sót, hiểu sai, thêm dữ kiện),
**KB** (chồng lấn luật giải quyết được, xung đột chưa giải quyết).

| Thành phần | File |
|---|---|
| KB, rule, quan hệ ngoại lệ | `kb.py`, `data/diag/kb_*.yaml` |
| Lập luận tiến, truy vết | `reasoner.py` |
| Mô hình chẩn đoán (Prolog) | `mbd.pl` |
| Quan sát, gọi Prolog, tìm chẩn đoán | `mbd_engine.py` |
| Bộ điều khiển (đo, chẩn đoán, hỏi lại, sửa lỗi) | `controller.py` |
| Phép đo NLI | `nli.py`, `nli_openai.py`, `kaggle/` |
| Parser LLM | `llm_parser.py` |
| Sinh câu trả lời IRAC | `ask.py` (ANSWER_PROMPT), `e2e.py` |

---

## 1. Tri thức pháp luật (Mục 3.1–3.3)

### 1.1 KB
- 5 KB theo lĩnh vực: 
  **422 quan hệ ngoại lệ** `exception_of`; **không có quan hệ ưu tiên** (P = ∅).
- Mỗi rule có nguồn (văn bản, điều, khoản, điểm). Không mã hóa phạm vi áp dụng hay hiệu lực thời gian.
- Nguồn gốc: 18 văn bản → 7.906 rules→ chọn theo điều luật mà bộ câu hỏi
  trích dẫn, viết lại trên bộ vị từ chung, rà soát.
- Một số rule có thân rỗng: rule mặc định chung (ví dụ "thu nhập không được miễn thuế"), và mỗi trường hợp miễn trừ
  được mã hóa là ngoại lệ của rule đó (`defeated_by_all`).

> **Definition (Legal KB).** K = (R, E, P, S): R a set of Horn rules over literals, E ⊆ R × R the exception
> relation ((r_e, r_g) ∈ E: r_e is an exception to r_g), P ⊆ R × R a priority relation (empty in our KBs), and S the
> source of each rule (document, article, clause, point).

### 1.2 Rule
- Tiền đề là **literal** p hoặc ¬p; kết luận là một literal. Vị từ có loại `input` (dữ kiện vụ việc) hoặc
  `derived` (kết luận trung gian/goal). Mỗi vị từ có câu diễn đạt khi đúng và khi sai (template), dùng cho parser,
  NLI và câu hỏi lại.

> **Definition (Rule).** r = (B_r → h_r) with body B_r a set of literals p or ¬p and head h_r a single literal.

### 1.3 Xung đột
- Hai rule **xung đột** khi cùng áp dụng được và kết luận cùng vị từ nhưng ngược cực tính, cho một chủ thể duy nhất của
  câu hỏi. Xung đột **giải quyết được** khi có quan hệ ngoại lệ giữa hai rule (rule ngoại lệ thắng); ngược lại là
  **chưa giải quyết**.

> **Definition (Conflict).** Inc(r_i, r_j) iff both rules are applicable and h_{r_i} = ¬h_{r_j}. The conflict is
> resolvable iff (r_i, r_j) ∈ E ∪ P or (r_j, r_i) ∈ E ∪ P; the winner is the exception (or the prioritised rule).
> (`kb.py: KB.resolution`)

---

## 2. Lập luận (Mục 3.4, 4.2)

### 2.1 Ngữ nghĩa ba giá trị, thế giới mở
- Mỗi mệnh đề có giá trị **true / false / unknown**. Unknown không bị coi là false. **Không dùng giá trị mặc định nào.**
- Trạng thái tiền đề: satisfied / contradicted / unknown. Trạng thái rule: *applicable* (mọi tiền đề thỏa),
  *not applicable* (có tiền đề bị bác bỏ), *undetermined* (còn tiền đề chưa biết), *blocked* (bị chặn khi sửa lỗi KB).

### 2.2 Cơ chế treo (ngoại lệ chỉ áp dụng khi được nêu)
- Rule chung r bị **treo** nếu một ngoại lệ e của nó đang được xác lập **một phần**: e có ít nhất một tiền đề **riêng
  của e** (không tính tiền đề chung với r) đã thỏa, không tiền đề nào bị bác bỏ, và còn tiền đề chưa biết. Khi đó kết
  luận của r để unknown.
- Ngoại lệ **không được nhắc tới** → r bắn bình thường (đúng quy ước của bộ dữ liệu: ngoại lệ không được nêu thì không
  áp dụng). Ngoại lệ **được xác lập đầy đủ** → cả hai rule bắn → xung đột → xử lý ở tầng KB.

> "An exception applies only once established. While an exception e of rule r is partially established — at least one
> premise of e not shared with r is satisfied, none is contradicted and some are unknown — r is suspended and its
> conclusion stays unknown; an exception the case does not raise leaves r in force." (`reasoner.py: suspended_by`)

### 2.3 Lập luận tiến
- Lặp tới điểm bất động: rule applicable, không bị treo, không bị chặn thì bắn.
- Hai kết luận trái nhau **không được khẳng định**: vị từ đó để unknown và cặp rule được ghi lại là **cặp cạnh tranh**.
  Việc giải quyết làm **ngoài** lập luận tiến, qua KB verification và recovery (chặn rule thua, suy luận lại).
- Kết quả là **Reasoning State** S: dữ kiện (nguồn parser/người dùng/suy diễn), trạng thái từng rule và tiền đề, rule
  bị treo, cặp cạnh tranh, phụ thuộc của mỗi kết luận, trạng thái goal (true/false/unknown/conflict).
  (`reasoner.py: forward_reason, ReasoningState`)

### 2.4 Truy vết phụ thuộc ngược
Hai tập mệnh đề được trích từ S:

- **required(S)**: các mệnh đề đầu vào chưa biết chặn goal, trên **đường liên quan**:
  1. Rule mở (undetermined) là liên quan nếu có ≥ 1 tiền đề đã thỏa, hoặc đang bị treo, hoặc có tiền đề dẫn xuất chưa
     biết mà bản thân có đường liên quan. Nếu không rule nào liên quan → xét mọi rule mở.
  2. Trong các rule liên quan của cùng một vị từ, **chỉ giữ rule được hỗ trợ nhiều nhất** (nhiều tiền đề đã xác lập
     nhất; rule bị treo được tính là hỗ trợ tối đa).
  3. Rule bị treo → truy tiếp vào tiền đề chưa biết của ngoại lệ đang treo nó.
  4. **Chọn nhánh bằng câu hỏi**: nếu |required| > 6 (nhiều nhánh thay thế, ví dụ danh mục 34 trường hợp không chịu
     thuế), đo NLI mọi mệnh đề required và chỉ giữ nhánh có mệnh đề mà câu hỏi thật sự nói tới (nhãn chấp nhận là
     entail/contra). Các nhãn đã đo được giữ làm quan sát.
- **checked(S)**: các dữ kiện do parser sinh ra mà chứng minh của goal (hoặc rule chặn goal) dựa vào.

(`reasoner.py: backward_trace_required, proof_support`; `controller.py: _observations, PATH_SELECTION_LIMIT`)

---

## 3. Mô hình chẩn đoán (Mục 4.3)

### 3.1 Thành phần và chế độ lỗi
| Tầng | Thành phần | Chế độ lỗi | Ý nghĩa |
|---|---|---|---|
| Người dùng | mỗi c ∈ required | `missing(c)` | câu hỏi không nêu c |
| Parser | mỗi c ∈ required | `omission(c)` | câu hỏi có nêu c nhưng parser bỏ sót |
| Parser | mỗi c ∈ checked | `misinterp(c)` | parser đảo cực tính của c |
| Parser | mỗi c ∈ checked | `unsupported(c)` | parser thêm c, câu hỏi không nêu |
| KB | mỗi cặp cạnh tranh (r_i, r_j) | `overlap(r_i, r_j)` | chồng lấn, giải quyết được bằng quan hệ đã mã hóa |
| KB | mỗi cặp cạnh tranh | `kbconflict(r_i, r_j)` | xung đột, chưa có quan hệ giải quyết |

### 3.2 Quan sát
- `required(c)`, `checked(c)`, `parsed(c, pos|neg)`, `q(c, ℓ)` với ℓ ∈ {entail, neutral, contra} (nhãn NLI đã chấp
  nhận), `competing(r_i, r_j)`, `resolution(r_i, r_j, yes|no)` (kết quả KB verification).
- Nhãn NLI chưa đo được coi là **bất kỳ** trong 3 nhãn (giá trị chưa biết).

### 3.3 Hành vi từng thành phần (đúng như `mbd.pl`)
- **Người dùng** bình thường nêu mọi mệnh đề required: nhãn ≠ neutral. `missing` ⇒ nhãn = neutral.
- **Parser**:

| Chế độ | entail | contra | neutral |
|---|---|---|---|
| bình thường | pos | neg | none |
| omission | none | none | – |
| misinterp | neg | pos | – |
| unsupported | – | – | pos hoặc neg |

- **KB**: `overlap` ⇔ resolution ∈ {yes, unknown}; `kbconflict` ⇔ resolution ∈ {no, unknown}.

> **Definition (Diagnosis).** A candidate Δ (a set of fault atoms, at most one mode per component) is a diagnosis iff
> SD ∪ O ∪ {AB(x) : x ∈ Δ} ∪ {¬AB(x) : x ∉ Δ} is consistent, i.e. every relevant proposition and every competing
> pair admits a behaviour consistent with its mode and the observations. Δ is minimal if no proper subset is a
> diagnosis (Reiter).

### 3.4 Tìm chẩn đoán tối thiểu
- Liệt kê trong **SWI-Prolog 10.0.2** (một tiến trình server dùng lâu dài) theo **lực lượng tăng dần** (0, 1, 2, …),
  bỏ mọi tập chứa một chẩn đoán đã tìm thấy → các chẩn đoán **tối thiểu theo tập**. Tối đa **5 lỗi**.
- **Giới hạn không gian**: k bị hạ tới mức Σ_{j≤k} C(n, j) ≤ 2·10⁵ (n = số nguyên tử lỗi).
- **Tách thành phần độc lập**: nếu tìm kiếm chung có giới hạn không ra chẩn đoán, chẩn đoán từng thành phần (một mệnh
  đề hoặc một cặp rule) riêng, kể cả các phép đo của nó, rồi lấy tích. **Chính xác** vì mọi ràng buộc của mô hình chỉ
  chạm đúng một thành phần.

> "Set-minimal diagnoses are enumerated by increasing cardinality in SWI-Prolog, up to five faults, the bound being
> lowered when the candidate space exceeds 2·10⁵. Since every model constraint involves a single component, the
> minimal diagnoses are the products of the per-component minimal diagnoses; this exact decomposition is used when
> the bounded joint search returns none." (`mbd.pl: minimal_diagnoses`; `mbd_engine.py: effective_k`;
> `controller.py: _mbd_decomposed`)

---

## 4. Thu thập bằng chứng (Mục 4.4)

### 4.1 Phép đo NLI
- Đầu vào: câu hỏi gốc q và **câu khẳng định** của mệnh đề c (template_pos).
- Phân bố nhãn = **trung bình** của:
  - mDeBERTa-v3-base (fine-tune XNLI, có tiếng Việt), phân loại 3 nhãn;
  - GPT-4o-mini: prompt hỏi mệnh đề là A (đúng), B (không xác định) hay C (sai) dựa trên câu hỏi, nói rõ "người hỏi
    chính là người lao động/doanh nghiệp trong mệnh đề", cho phép suy luận hiển nhiên (so sánh số, thời hạn, đồng
    nghĩa), cấm suy diễn từ việc câu hỏi không nhắc tới; lấy xác suất của 3 chữ cái ở token đầu (temperature 0).
- **Kiểm tra chấp nhận**: nhãn có xác suất lớn nhất được nhận làm quan sát q(c, ℓ) nếu ≥ **τ = 0,50**; ngược lại
  phép đo trả về ⊥ và không thêm quan sát nào.
- Mô hình đo, prompt và τ được **chọn trên dev**, theo tiêu chí đặt trước: trung bình của độ chính xác chẩn đoán và
  1 − tỉ lệ báo lỗi oan. Các ứng viên đã thử: mDeBERTa, Qwen2.5-7B-Instruct, GPT-4o-mini, mDeBERTa + Qwen,
  mDeBERTa + GPT-4o-mini (chọn).

> "A measurement compares the original question with the positive verbalisation of c. Its label distribution is the
> mean of a multilingual NLI classifier (mDeBERTa-v3, XNLI) and an LLM (GPT-4o-mini, probabilities of three answer
> options, temperature 0). The label becomes an observation only if its probability is at least τ = 0.50; otherwise
> the measurement returns ⊥." (`nli.py: verify, NLIModel`; `nli_openai.py`)

### 4.2 KB verification
- Với cặp cạnh tranh (r_i, r_j): nếu cả hai applicable và kết luận ngược nhau → `yes` nếu có quan hệ ngoại lệ/ưu tiên
  đã mã hóa, `no` nếu không; nếu không thật sự xung đột → `no_conflict`. (`controller.py: _kb_verify`)

### 4.3 Chọn phép đo (first-disagreement)
- Khi còn > 1 chẩn đoán: chọn **phép đo chưa dùng đầu tiên mà các chẩn đoán còn lại bất đồng**, theo thứ tự:
  KB verification các cặp cạnh tranh → NLI trên mệnh đề required → NLI trên mệnh đề checked (theo tên). Đo xong thì
  tính lại chẩn đoán; lặp tới khi còn 1 chẩn đoán hoặc không còn phép đo phân biệt được.
- Các dữ kiện parser mà chứng minh dựa vào được đo NLI **trước** khi chẩn đoán.

> Algorithm 1 (lines 11–16): A ← {m ∉ Used : diagnoses in D disagree on target(m)}; m ← first(A) in the order
> KB checks, NLI on required, NLI on checked. (`controller.py: _pick_measurement, _mbd_loop`)

---

## 5. Điều khiển chẩn đoán và sửa lỗi (Mục 4.5–4.6)

### 5.1 Hai pha
- **Pha A**: giải thích các dữ kiện checked và các cặp cạnh tranh (tạm bỏ required).
- **Pha B**: giải thích các mệnh đề required. Chạy khi pha A **không có lỗi**, hoặc **chỉ có overlap** (chồng lấn
  giải quyết được là vô hại, không giải thích vì sao goal chưa xác định, nên không được dừng việc tìm lỗi đầu vào).
  (`controller.py: diagnose`)

### 5.2 Mơ hồ → hỏi lại người dùng
- Nếu sau khi hết phép đo phân biệt mà các chẩn đoán còn lại chỉ khác nhau ở **missing hay omission** của một mệnh đề
  c → hỏi người dùng đúng mệnh đề c (câu hỏi lấy từ trường `ask` của vị từ), rồi suy luận lại.

### 5.3 Sửa lỗi theo tầng (tối đa 3 vòng)
Mỗi vòng: chẩn đoán → sửa → suy luận lại. **Sửa lỗi tầng đầu vào trước**; tầng KB chỉ xử lý khi không còn lỗi đầu vào
(vì lỗi đầu vào có thể chính là nguyên nhân sinh ra tương tác giữa rule).

| Lỗi | Cách sửa |
|---|---|
| missing(c) | hỏi người dùng giá trị của c |
| omission(c), misinterp(c) | đặt c theo nhãn NLI đã chấp nhận (entail → true, contra → false); misinterp không có nhãn thay thế → rút dữ kiện nghi ngờ |
| unsupported(c) | bỏ dữ kiện c |
| overlap(r_i, r_j) | chặn rule thua theo quan hệ ngoại lệ, suy luận lại |
| kbconflict(r_i, r_j) | không kết luận (abstain) |

### 5.4 Kết luận
- Goal true/false → **CÓ / KHÔNG**; xung đột chưa giải quyết → **không kết luận**; còn mệnh đề chưa biết → **chưa đủ dữ
  kiện** (kèm danh sách thông tin cần bổ sung, nếu đã hỏi lại thì ghi là yêu cầu bổ sung).

### 5.5 Thuật toán (gợi ý Algorithm 1)
```
Input: question q, goal g, KB K, parser facts F0
F ← F0; Blocked ← ∅
for round = 1..3:
    S ← ForwardReason(K, g, F, Blocked)
    O ← Observations(S)                      # required, checked, parsed, competing
    if |required| > 6: measure NLI on required; restrict to alternatives the question mentions
    measure NLI on checked facts                       # proof verification
    D ← MinimalDiagnoses(O without required)           # phase A (Prolog)
    if D = {∅} or D contains only overlaps: D ← MinimalDiagnoses(O)   # phase B
    while |D| > 1 and some unused measurement m discriminates D:
        m ← first discriminating measurement;  O ← O ∪ result(m);  D ← MinimalDiagnoses(O)
    if D = ∅ (bounded search failed): D ← product of per-component diagnoses
    if |D| > 1:  ask the user about each c on which D differs only by missing/omission; continue
    if D = {∅}: break
    repair input-layer faults of D (or, if none, KB-layer faults); if nothing changed: break
return answer(ForwardReason(K, g, F, Blocked)), IRAC
```

---

## 6. Parser, goal và câu trả lời (Mục 4.2, 4.7)

- **Parser**: GPT-4o, temperature 0, đầu ra JSON; nhận danh sách vị từ đầu vào của KB lĩnh vực (kèm câu khi đúng / khi
  sai); trả về literal + đoạn nguyên văn. Quy tắc: chỉ trích điều câu hỏi nêu hoặc suy ra trực tiếp, không đoán, không
  dùng mặc định. Dùng toàn bộ KB của lĩnh vực (R_q = R, không có bước truy hồi rule). (`llm_parser.py`)
- **Goal pháp lý**: lấy từ gold (oracle goal). Chỉ tập dữ kiện là do parser dự đoán.
- **Câu trả lời IRAC**: GPT-4o diễn đạt lại **chứng minh đã kiểm chứng** — nhận kết luận đã xác minh, dữ kiện đã dùng,
  các rule đã áp dụng (kèm nguồn điều luật); không được đổi kết luận, không thêm căn cứ ngoài danh sách; nếu chưa đủ dữ
  kiện thì liệt kê thông tin cần bổ sung. (`ask.py: ANSWER_PROMPT`)

---

## 7. Baseline Heuristic (để mô tả trong Mục 4.7 / 5.2)
- Dùng **cùng bằng chứng** (đo NLI mọi mệnh đề required và checked, KB verification mọi cặp cạnh tranh) và **cùng cơ chế
  sửa lỗi**; chỉ khác bước gán nhãn lỗi, theo luật if–else khớp đầu tiên:
  1. dữ kiện checked mà NLI nói ngược với parser → misinterp; NLI nói neutral → unsupported;
  2. nếu không có lỗi ở bước 1: mỗi mệnh đề required → omission nếu câu hỏi có nêu (entail/contra), missing nếu không;
  3. mỗi cặp cạnh tranh → overlap nếu có quan hệ giải quyết, kbconflict nếu không.
  (`controller.py: _rule_check`)
- **Direct mapping (bỏ MBD)**: mỗi required → missing, mỗi cặp cạnh tranh → kbconflict, không đo thêm.

---

## 8. Tham số (tất cả cố định trước khi chạy test)

| Tham số | Giá trị | Ở đâu |
|---|---|---|
| Ngưỡng chấp nhận NLI τ | 0,50 | `NLI_TAU` |
| Luật chấp nhận | chỉ dùng template khẳng định | `NLI_RULE=pos_only` |
| Dụng cụ đo | trung bình mDeBERTa + GPT-4o-mini (prompt v4) | `NLI_BACKEND=ensemble_gpt` |
| Số lỗi tối đa mỗi chẩn đoán | 5 | `controller.py` |
| Giới hạn không gian ứng viên | 2·10⁵ | `MBD_MAX_CANDIDATES` |
| Ngưỡng chọn nhánh bằng câu hỏi | > 6 mệnh đề required | `PATH_SELECTION_LIMIT` |
| Số vòng sửa lỗi tối đa | 3 | `RunConfig.max_rounds` |
| Giá trị mặc định cho vị từ ngoại lệ | không dùng | `KB_EXCEPTION_DEFAULTS=0` |
| Parser / sinh IRAC | GPT-4o, temperature 0 | `LLM_MODEL` |

---

## 9. Ví dụ minh họa (lấy từ log thật, có thể dùng làm hình/ví dụ trong paper)

**THUE-008, lỗi parser bỏ sót** (`experiments/diag_dataset/ensemble_gpt/thue_test/results_all.json`)

- Câu hỏi: *"Tình huống phát sinh trong năm 2026. Doanh nghiệp tôi vận chuyển hành khách bằng xe buýt công cộng.
  Hoạt động này có thuộc đối tượng không chịu thuế GTGT không?"*
- Goal: `vat_non_taxable`. Gold: dữ kiện `vat_public_bus = true` → **CÓ**.
- Lỗi tiêm: parser bỏ sót `vat_public_bus` → goal unknown. Vì không còn dữ kiện nào, mọi rule trong danh mục
  **34 trường hợp không chịu thuế** đều mở → required có 34 mệnh đề.
- **Ours (MBD)**: vì > 6 mệnh đề, hệ thống đo NLI cả 34 mệnh đề với câu hỏi; chỉ `vat_public_bus` được nhận *entail*,
  các mệnh đề khác *neutral*. Chẩn đoán duy nhất: **ParserOmission(vat_public_bus)** → đặt `vat_public_bus = true` →
  suy luận lại → **CÓ**. **Không hỏi người dùng câu nào.**
- **Heuristic** (cùng 34 phép đo): gắn nhãn *missing* cho mọi mệnh đề còn unknown → chẩn đoán 34 lỗi, **hỏi người dùng
  33 câu** rồi mới ra cùng đáp án.

Ví dụ này cho thấy đúng hai điểm khác biệt mà Bảng 2 đo: chẩn đoán gọn (1 lỗi so với 34) và ít câu hỏi thừa.
