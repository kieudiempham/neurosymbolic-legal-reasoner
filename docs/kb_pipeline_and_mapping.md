# Từ văn bản luật đến rule suy luận được, và một câu hỏi được ánh xạ vào rule như thế nào

Tài liệu trả lời hai câu hỏi:
1. Văn bản pháp luật được biến thành **rule lưu trữ được và suy luận được** như thế nào (tổ chức dữ liệu ra sao)?
2. Một **câu hỏi** được nối vào các rule đó như thế nào để ra kết luận?

Mọi ví dụ dưới đây là **dữ liệu thật** của hệ thống (Luật BHXH 41/2024, Điều 2; câu hỏi BHXH-001), lấy từ các file
trong repo và chạy lại bằng code hiện tại.

---

## Phần A. Từ tài liệu đến cơ sở tri thức

```
 18 file .doc/.pdf                  (A1) đọc văn bản
        │
        ▼
 văn bản thuần ──(A2) tách Chương / Điều──► 1.159 bản ghi Điều luật
                                                │
                                                ▼  (A3) LLM trích luật, mỗi Điều 1 lần gọi
                                  7.906 rule nháp (rules.jsonl) + từ điển vị từ (vocabulary.yaml)
                                                │
                                                ▼  (A4) chọn điều luật liên quan, rà soát, chuẩn hóa vị từ,
                                                │       mã hóa quan hệ ngoại lệ, vá lỗi (chỉ từ dev)
                                  5 KB theo lĩnh vực: 636 rule + 422 quan hệ ngoại lệ
                                  (kb_<lĩnh vực>.yaml + kb_<lĩnh vực>_vocabulary.yaml)
                                                │
                                                ▼  (A5) nạp vào bộ nhớ
                                  đối tượng KB: rule theo id, chỉ mục theo kết luận, tập ngoại lệ, từ điển vị từ
```

### A1. Thu thập và đọc văn bản
- 18 văn bản, chia theo thư mục lĩnh vực: `data/raw/legal_corpus/{labor, enterprise, tax}/`
  (Lao động và BHXH: 4 văn bản; Doanh nghiệp: 3; Thuế: 11). Tên file có số thứ tự và số hiệu văn bản, ví dụ
  `10_bao_hiem_xa_hoi_41_2024_QH15.doc`.
- Đọc văn bản: file Word 97–2003 (.doc) đọc trực tiếp cấu trúc nhị phân (piece table), không cần Word; file PDF đọc
  bằng PyMuPDF. Code: `src/diagnosis/kbx/corpus.py` (`read_doc`, `read_pdf`).

### A2. Tách thành từng Điều luật (đơn vị lưu trữ gốc)
- Nhận diện "Chương …" và "Điều N." bằng biểu thức chính quy; mỗi Điều thành một bản ghi:

| Trường | Ví dụ |
|---|---|
| doc_id | `10_bao_hiem_xa_hoi_41_2024_QH15` |
| domain | `labor` |
| number (số Điều) | `2` |
| chapter | `I` |
| title | Đối tượng tham gia bảo hiểm xã hội bắt buộc và bảo hiểm xã hội tự nguyện |
| text | toàn văn Điều (các khoản, điểm) |

- Kết quả: 106 chương, 1.159 Điều. Ví dụ trích nguyên văn Điều 2 khoản 1 điểm a:
  > "Người lao động là công dân Việt Nam thuộc đối tượng tham gia bảo hiểm xã hội bắt buộc bao gồm: a) Người làm việc
  > theo hợp đồng lao động không xác định thời hạn, hợp đồng lao động xác định thời hạn có thời hạn từ đủ 01 tháng
  > trở lên, …"

### A3. Trích rule nháp bằng LLM
- Mỗi Điều là **một lần gọi** GPT-4o-mini (temperature 0, đầu ra JSON). Prompt yêu cầu (`kbx/extract.py`):
  - mỗi quy phạm "nếu … thì …" → một **rule Horn**: các điều kiện *đồng thời* là tiền đề, hệ quả là kết luận;
  - điều kiện **thay thế nhau** (các điểm a, b, c; "hoặc") → **tách thành nhiều rule**;
  - điều kiện phủ định ("không", "chưa", "trừ") → literal phủ định;
  - quy phạm ngoại lệ ("trừ trường hợp…") → ghi `exception_to`;
  - ghi đúng nguồn "Điều X khoản Y điểm z" và một đoạn trích nguyên văn;
  - **dùng lại tên vị từ đã có** trong từ điển chung nếu nghĩa trùng khớp, nếu không thì khai báo vị từ mới (kèm câu
    tiếng Việt khi đúng/khi sai và câu hỏi người dùng).
- Kết quả: **7.906 rule nháp** (`data/diag/kb_full_draft/rules.jsonl`), mỗi dòng một rule. Ví dụ thật (Điều 2 sinh ra
  17 rule nháp):

```json
{"id": "LAB-10-D2-000", "type": "condition",
 "premises": ["signed_labor_contract", "term_at_least_1_month", "paid_wage", "under_management"],
 "conclusion": "compulsory_si",
 "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 2 khoản 1 điểm a",
 "exception_to": "", "quote": "Người lao động là công dân Việt Nam thuộc đối tượng tham gia BHXH bắt buộc bao gồm: …",
 "review_status": "draft"}
{"id": "LAB-10-D2-001", "type": "condition", "premises": ["is_civil_servant"], "conclusion": "compulsory_si",
 "source": "10_bao_hiem_xa_hoi_41_2024_QH15, Điều 2 khoản 1 điểm b", "quote": "Cán bộ, công chức, viên chức;", …}
```

### A4. Chọn, rà soát và chuẩn hóa thành KB dùng để suy luận
Rule nháp **chưa dùng trực tiếp** vì còn lỗi (thiếu điều kiện, vị từ trùng nghĩa khác tên, chưa có quan hệ ngoại lệ).
Các bước:
1. **Chọn điều luật liên quan**: lấy các Điều mà bộ câu hỏi trích làm căn cứ, cộng các Điều được tham chiếu bởi quy
   phạm ngoại lệ của chúng (`kbx/build_kb.py`).
2. **Rà soát từng rule** (gắn nhãn đúng / sửa / bỏ / thêm), ghi nguồn gốc rà soát vào trường `basis`
   (`llm_reviewed:fix`, `llm_reexpressed`, `patch`, …) (`kbx/review.py`, `kbx/registry_kb.py`).
3. **Chuẩn hóa vị từ**: mọi rule của một lĩnh vực dùng **một bộ vị từ chung** (cũng là bộ vị từ dùng để chú thích
   câu hỏi), nhờ vậy dữ kiện trích từ câu hỏi khớp được với tiền đề của rule.
4. **Thêm tầng trung gian** khi một khoản liệt kê nhiều trường hợp: ví dụ "thuộc điểm a khoản 1 Điều 2"
   (`covered_point_a`) là một vị từ dẫn xuất, rồi Nghị định 158 nối `covered_point_a → compulsory_si`.
5. **Mã hóa quan hệ ngoại lệ** `exception_of = (rule ngoại lệ, rule chung)`.
6. **Vá lỗi**: chỉ dựa trên lỗi của câu hỏi tập dev, mỗi bản vá ghi lý do (`data/diag/kb_*_patches.yaml`).

Kết quả: **5 KB, 636 rule, 422 quan hệ ngoại lệ** (BHXH 149, Doanh nghiệp 70, Thuế 200, Lao động 129, Liên ngành 88).

### A5. Tổ chức lưu trữ (cơ sở dữ liệu tri thức)

Mỗi KB gồm **hai file văn bản có cấu trúc** (YAML), quản lý phiên bản bằng Git:

**(1) File rule — `data/diag/kb_bhxh_v1.yaml`**
```yaml
rules:
  - id: P-A1
    premises: ['~foreign_citizen', 'signed_labor_contract', 'term_at_least_1_month']
    conclusion: covered_point_a
    source: '10_bao_hiem_xa_hoi_41_2024_QH15, Điều 2 khoản 1 điểm a'
    basis: patch
  - id: LAB-11-D3-000
    premises: ['covered_point_a']
    conclusion: compulsory_si
    source: '11_nghi_dinh_158_2025_ND-CP, Điều 3 khoản 1'
    basis: llm_reviewed:fix
  - id: LAB-10-D2-100
    premises: ['receiving_pension']
    conclusion: '~compulsory_si'
    source: '10_bao_hiem_xa_hoi_41_2024_QH15, Điều 2 khoản 7 điểm a'
    basis: llm_reviewed:fix
exception_of:                 # (rule ngoại lệ, rule chung): ngoại lệ thắng khi cả hai cùng áp dụng
  - [LAB-10-D2-100, LAB-11-D3-000]
  - [LAB-10-D2-101, LAB-11-D3-000]
priority_over: []
```
Dấu `~` là phủ định. Một rule là **một mệnh đề Horn có nguồn gốc điều/khoản/điểm**.

**(2) File từ điển vị từ — `data/diag/kb_bhxh_v1_vocabulary.yaml`**
```yaml
predicates:
  signed_labor_contract:
    kind: input                                    # dữ kiện vụ việc, lấy từ câu hỏi
    template_pos: Người lao động đã ký hợp đồng lao động.
    template_neg: Người lao động không ký hợp đồng lao động.
    ask: Bạn đã ký hợp đồng lao động với bên sử dụng lao động chưa?
  compulsory_si:
    kind: derived                                  # kết luận pháp lý, chỉ suy ra bằng rule
    template_pos: Người lao động thuộc đối tượng tham gia bảo hiểm xã hội bắt buộc.
    template_neg: Người lao động không thuộc đối tượng tham gia bảo hiểm xã hội bắt buộc.
```
Câu `template_pos/neg` dùng cho parser (biết mỗi vị từ nghĩa là gì), cho NLI (so với câu hỏi) và để viết câu trả lời;
`ask` dùng khi cần hỏi lại người dùng.

**Sơ đồ quan hệ dữ liệu**
```
 Văn bản (doc_id) 1──n Điều (number) 1──n Rule (id, premises[], conclusion, source, basis)
 Rule n──n Vị từ (pred, kind, templates, ask)     [qua premises và conclusion]
 Rule 1──n exception_of ──1 Rule                  [rule ngoại lệ → rule chung]
```

**Khi nạp vào bộ nhớ** (`src/diagnosis/kb.py: load_kb`): kiểm tra mọi vị từ trong rule đều có trong từ điển và mọi
quan hệ ngoại lệ trỏ tới rule có thật, rồi tạo đối tượng `KB`:
- `rules`: từ điển id → Rule (tiền đề và kết luận là các Literal (vị từ, đúng/sai));
- `rules_concluding(pred)`: tra các rule có kết luận là một vị từ (dùng cho truy vết ngược);
- `exception_of`, `priority_over`: tập cặp rule;
- `vocab`: từ điển vị từ.

**Vì sao lưu như vậy mà suy luận được:** mọi tri thức nằm ở dạng **mệnh đề Horn trên một bộ vị từ hữu hạn, đặt tên
thống nhất**, nên suy luận chỉ là **so khớp tên vị từ và giá trị đúng/sai**, không cần hiểu ngôn ngữ ở bước suy luận.
Phần hiểu ngôn ngữ (đọc câu hỏi) chỉ xảy ra ở parser và ở phép đo NLI, cả hai đều quy về cùng bộ vị từ này.

---

## Phần B. Một câu hỏi được ánh xạ vào rule như thế nào

Câu hỏi **BHXH-001**:
> "Tôi là công dân Việt Nam. Tôi đang làm nhân viên bán hàng ở Bình Dương. Công việc của tôi không phải giúp việc gia
> đình. Tôi ký hợp đồng lao động xác định thời hạn 1 tháng. Tôi không hưởng lương hưu hay trợ cấp BHXH hoặc trợ cấp
> hằng tháng. Vậy tôi có thuộc diện tham gia BHXH bắt buộc không?"

Đáp án gold: **CÓ** (Luật BHXH Điều 2 khoản 1 điểm a; Nghị định 158 Điều 3 khoản 1).

```
câu hỏi ──(B1)──► vấn đề pháp lý (goal) = compulsory_si
        ──(B2)──► parser: chọn vị từ trong 97 vị từ input của KB BHXH ──► dữ kiện (literal + đoạn trích)
                                   │ (B3) khớp theo tên vị từ với tiền đề rule
                                   ▼
                    lập luận tiến: rule nào thỏa thì bắn, sinh vị từ dẫn xuất, lặp tới hết
                                   │ (B4) kiểm tra ngoại lệ
                                   ▼
                    goal = true / false / chưa biết ──(B5)──► câu trả lời IRAC dẫn đúng điều luật của rule đã dùng
```

### B1. Xác định vấn đề pháp lý (goal)
Câu hỏi hỏi về **compulsory_si** ("thuộc đối tượng tham gia BHXH bắt buộc"). Trong thực nghiệm, goal được **cho sẵn**
từ chú thích (oracle goal); chỉ phần dữ kiện là do máy trích.

### B2. Parser: câu hỏi → dữ kiện trên bộ vị từ của KB
- Parser (GPT-4o, temperature 0) nhận **danh sách 97 vị từ input** của KB BHXH, mỗi vị từ kèm câu "khi đúng / khi sai",
  và chỉ được trả về các vị từ trong danh sách này, mỗi dữ kiện kèm đoạn nguyên văn làm căn cứ.
- Với câu hỏi trên, **dữ kiện đúng** (gold) là:

| Vị từ | Giá trị | Đoạn trong câu hỏi |
|---|---|---|
| foreign_citizen | sai | "Tôi là công dân Việt Nam" |
| domestic_worker | sai | "không phải giúp việc gia đình" |
| signed_labor_contract | đúng | "ký hợp đồng lao động" |
| term_at_least_1_month | đúng | "xác định thời hạn 1 tháng" |
| term_at_least_12_months | sai | "1 tháng" |
| receiving_pension | sai | "không hưởng lương hưu" |
| monthly_benefit | sai | "không hưởng … trợ cấp hằng tháng" |

### B3. Khớp dữ kiện với rule
Mỗi dữ kiện là một literal trên đúng tên vị từ mà rule dùng, nên việc khớp là **tra theo tên**:
- `foreign_citizen` xuất hiện trong tiền đề của 25 rule; `term_at_least_1_month` trong 3 rule; `receiving_pension` trong
  2 rule; `domestic_worker` trong 1 rule; …
- Mỗi tiền đề của mỗi rule nhận một trong ba trạng thái: **thỏa** (dữ kiện khớp giá trị), **bị bác bỏ** (dữ kiện ngược
  giá trị), **chưa biết** (câu hỏi không nói). Rule **áp dụng** khi mọi tiền đề thỏa, **không áp dụng** khi có tiền đề
  bị bác bỏ, **chưa xác định** khi còn tiền đề chưa biết. Câu hỏi không nói thì không coi là sai (thế giới mở).

### B4. Lập luận tiến (chạy thật bằng code hiện tại)
Các rule được bắn theo thứ tự:

| Bước | Rule | Tiền đề (đều thỏa) | Kết luận | Căn cứ |
|---|---|---|---|---|
| 1 | P-A1 | ¬foreign_citizen ∧ signed_labor_contract ∧ term_at_least_1_month | covered_point_a | Luật BHXH Đ2 k1 điểm a |
| 2 | P-K1a | covered_point_a | covered_art2_khoan1 | Luật BHXH Đ2 k1 |
| 3 | LAB-10-D33-000 | covered_point_a | employee_rate_pension_fund_8pct | Luật BHXH Đ33 k1 điểm a |
| 4 | **LAB-11-D3-000** | covered_point_a | **compulsory_si** | NĐ 158/2025 Đ3 k1 |

**Kiểm tra ngoại lệ.** Rule LAB-11-D3-000 có 6 ngoại lệ trong KB. Mỗi ngoại lệ được xét:
- LAB-10-D2-100 (đang hưởng lương hưu → không bắt buộc): **không áp dụng**, vì `receiving_pension` = sai.
- LAB-10-D2-101 (giúp việc gia đình): **không áp dụng**, vì `domestic_worker` = sai.
- P-X-MB (hưởng trợ cấp hằng tháng): **không áp dụng**.
- P-X-PT (làm bán thời gian, lương dưới mức tối thiểu): **chưa xác định**. Tiền đề duy nhất đã thỏa của nó là
  `covered_point_a`, mà đó cũng là tiền đề của chính rule chung, nên **không tính**. Câu hỏi không hề nhắc tới làm bán
  thời gian, nên ngoại lệ này **không được coi là đang được nêu** và không treo rule chung.
- P-X-PR (chỉ thử việc), LAB-11-D3-005 (hưởng trợ cấp mất sức): chưa xác định vì câu hỏi không nhắc tới, nên cũng
  không treo.

→ Không ngoại lệ nào được xác lập, không có xung đột: **compulsory_si = đúng → CÓ**.

### B5. Câu trả lời
Câu trả lời IRAC được viết từ chính các rule đã bắn: vấn đề (compulsory_si), quy định (Đ2 k1 điểm a Luật BHXH, Đ3
k1 NĐ 158), áp dụng (công dân VN, có HĐLĐ từ đủ 1 tháng, không thuộc các trường hợp loại trừ), kết luận CÓ. Mọi căn cứ
pháp lý trong câu trả lời đều lấy từ trường `source` của rule, nên luôn truy ngược được về điều/khoản.

### B6. Khi parser trích sai (chạy thật với parser GPT-4o)
Thực tế parser **bỏ sót** `signed_labor_contract` (chỉ trích 5 dữ kiện). Khi đó rule P-A1 thiếu tiền đề → không suy ra
được `covered_point_a` → goal **chưa biết**. Đây là lúc lớp chẩn đoán làm việc:
1. Truy vết ngược từ goal: các mệnh đề còn thiếu trên đường suy luận là `signed_labor_contract`, `part_time`,
   `wage_at_least_min_base`.
2. Đo NLI từng mệnh đề với câu hỏi: `signed_labor_contract` → câu hỏi **có nêu** (xác suất 1,00).
3. Chẩn đoán: **ParserOmission(signed_labor_contract)** → đặt lại dữ kiện → rule P-A1 bắn lại.

Ví dụ này cũng cho thấy giới hạn của bước đo: NLI nhận nhầm `part_time` (làm bán thời gian) là "có nêu", với xác suất
chỉ 0,55, vừa đủ ngưỡng. Điều đó kích hoạt một phần ngoại lệ P-X-PT, làm rule chung bị **treo**, và hệ thống phải hỏi
người dùng về mức lương. Đây đúng là loại lỗi đo mà paper nêu là điểm nghẽn.

---

## Đoạn tóm tắt có thể đưa vào paper (Mục 3)

> **Knowledge acquisition and storage.** The 18 source documents are segmented into 1,159 articles. An LLM
> (GPT-4o-mini, one call per article) encodes each article as Horn rules over a shared, growing predicate vocabulary,
> splitting alternative conditions into separate rules and recording the clause-level source, a verbatim quote and
> any exception reference (7,906 draft rules). For each domain, the articles cited by the benchmark (plus those they
> reference as exceptions) are selected, their rules reviewed and re-expressed over one predicate registry, intermediate
> legal categories introduced (e.g. *covered by Art. 2(1)(a)*), and exception relations encoded, giving five KBs with
> 636 rules and 422 exception relations. Each KB is stored as two versioned YAML files: the rules (id, body literals,
> head literal, source, provenance) with the exception relation, and the predicate vocabulary (kind input/derived,
> positive and negative Vietnamese verbalisations, clarification question). Because rules, questions and measurements
> share one controlled vocabulary, mapping a question to rules reduces to matching predicate names: the parser maps the
> question to literals over the KB's input predicates, forward chaining fires the rules whose bodies are satisfied, and
> every derived conclusion carries the article that licenses it.

**Lưu ý khi trình bày với thầy:** bộ vị từ của KB được thống nhất với bộ vị từ dùng để chú thích câu hỏi. Điều này
giúp ánh xạ chính xác, nhưng cũng nghĩa là vốn từ vị từ được xây có định hướng theo bộ câu hỏi. Nên nêu rõ điểm này
trong phần hạn chế.
