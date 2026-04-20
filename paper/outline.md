TITLE
Mục tiêu

Tên paper phải cho reviewer nhìn ra ngay 3 thứ:

đây là legal QA
đây là Vietnamese law
đây là neuro-symbolic / verification / reasoning-driven
Nên có gì

Tên nên chứa ít nhất 2 trong 3 trục sau:

neuro-symbolic / verification-guided / proof-aware
legal question answering
Vietnamese law / Vietnamese legal QA
Tránh gì
đừng đặt tên quá thiên về RAG
đừng đặt tên như một chatbot system chung chung
đừng để title làm người đọc nghĩ đây chỉ là KG retrieval paper
ABSTRACT
Mục tiêu

Tóm toàn paper trong 1 đoạn ngắn, trả lời đủ:

bài toán là gì
prior work đang thiếu gì
bạn đề xuất gì
bạn đánh giá ra sao
kết quả/chốt chính là gì
Cấu trúc nên viết
Câu 1–2: bài toán

Viết legal QA tiếng Việt khó vì:

câu hỏi thiếu dữ kiện
luật có điều kiện, ngoại lệ, thời hạn
retrieval đơn thuần không đủ để reasoning
Câu 3–4: khoảng trống

Nói rằng:

Vietnamese legal QA prior chủ yếu nghiêng về retrieval / KG / RAG
các hướng NeSy hiện có chưa trực tiếp giải quyết nhu cầu riêng của legal QA tiếng Việt:
rule construction từ luật,
missing fact handling,
clarification,
intermediate-state verification.
Câu 5–7: phương pháp

Tóm framework:

law-side rule construction tạo reasoning-ready legal rules
dual-layer query parsing
backward requirement discovery
clarification over missing facts
forward proof construction
multi-mode neuro-symbolic verification + repair loop.
Câu 8–9: evaluation

Viết bạn đánh giá theo:

parse / retrieval / reasoning / answer
end-to-end legal QA
baselines và ablations
Câu cuối: take-away

Chốt:

framework cải thiện grounding, traceability, proof-aware reasoning
phù hợp cho Vietnamese legal QA
Tránh gì
đừng liệt kê module quá dài như list manual
đừng viết abstract như intro thứ hai
đừng claim “first” nếu chưa chắc tuyệt đối
1. INTRODUCTION
Mục tiêu

Đây là nơi định vị paper.
Section này phải khiến reviewer hiểu:

paper này là một verification-centric neuro-symbolic framework specialized for Vietnamese legal QA, chứ không phải một RAG paper có thêm chút logic.

1.1. Problem context
Cần viết gì

Mở bằng difficulty của legal QA:

legal questions thường mơ hồ hoặc thiếu dữ kiện
legal conclusions phụ thuộc vào điều kiện áp dụng, ngoại lệ, thời hạn
legal answers cần căn cứ và khả năng truy vết
trong luật Việt Nam, nguồn pháp lý đến từ luật + nghị định + cấu trúc điều/khoản rõ ràng.
Mục tiêu ngầm

Dẫn người đọc tới chỗ: bài toán không chỉ là tìm đúng đoạn văn bản, mà là reasoning under incomplete legal facts.

1.2. Limits of existing directions
Cần viết gì

Chia 3 hướng:

LLM-only: fluent nhưng dễ hallucinate, thiếu kiểm chứng
retrieval/KG/RAG-centric legal QA: giúp grounding tốt hơn nhưng thường chưa giải quyết được requirement reasoning và missing facts
generic NeSy methods: mạnh về reasoning substrate nhưng chưa chuyên biệt hóa cho Vietnamese legal QA.
Cách viết

Không cần công kích RAG.
Nói trung tính:

retrieval hữu ích cho evidence access
nhưng retrieval alone không đủ để:
decide applicability,
identify missing facts,
construct proofs,
validate intermediate reasoning objects
1.3. Gap and positioning
Đây là đoạn quan trọng nhất của intro

Bạn phải viết rất rõ:

Vietnamese legal QA prior work phần lớn tập trung vào retrieval, data enrichment, KG, RAG, legal IR
trong khi legal QA thực tế đòi hỏi:
transform statutes thành reasoning-ready rules
discover missing legal facts
ask clarification
verify intermediate reasoning states
đó là khoảng trống mà paper này nhắm tới.
Câu chuyện phải chốt

Paper nằm ở giao điểm:

của neuro-symbolic reasoning
và Vietnamese legal QA

Không viết như đang benchmark để thắng RAG.
Viết như đang specialize NeSy to legal QA.

1.4. Core idea
Cần viết gì

Một paragraph ngắn mô tả hệ:

luật/nghị định → curated reasoning-ready rule base
question text → dual-layer parsing
retrieval → top-k candidate rules
backward chaining → rule selection + requirement set + missing facts
clarification → ask only when facts missing
forward chaining → proof + legal conclusion
NeSy engine → verify parse / rule / backward / forward / answer
repair loop → fix failing module instead of regenerating blindly.
Cần nhấn mạnh gì
LLM không là legal source of truth
RAG không là reasoning mặc định
verification không chỉ ở answer cuối.
1.5. Contributions
Nên viết thành 3 contribution lớn
Contribution 1: Law-side rule construction

Một pipeline chuyển statutory provisions của Việt Nam thành reasoning-ready rules với:

explicit conditions
effects
exceptions
deadlines
provenance.
Contribution 2: Requirement-driven legal QA

Một quy trình legal QA gồm:

dual-layer query parsing
backward requirement discovery
clarification over missing facts
forward proof construction.
Contribution 3: Verification-centric NeSy architecture

Một kiến trúc kiểm tra intermediate reasoning objects thay vì chỉ final answers, với:

symbolic + NLI checks
module-specific repair
improved grounding and traceability.
Có thể thêm contribution 4 nếu bạn có đủ thực nghiệm
một benchmark/evaluation protocol đa tầng cho Vietnamese legal QA
1.6. Paper organization

Viết ngắn, 1 đoạn.

Tránh gì trong Introduction
không mở đầu bằng mô tả tool quá sớm
không sa đà vào implementation
không để đoạn contribution giống checklist kỹ thuật
không đóng khung novelty là “chúng tôi dùng RAG + logic”
2. RELATED WORK
Mục tiêu

Section này phải phục vụ positioning mới.
Không chia theo legal RAG trước rồi NeSy sau một cách mờ nhạt.
Phải chia theo logic:

NeSy methods
Vietnamese legal QA systems
Gap and positioning
2.1. Neuro-symbolic reasoning methods
Câu hỏi section này phải trả lời

“Paper của tôi thuộc họ NeSy nào, và khác prior NeSy ở đâu?”

Cần viết gì

Review ngắn gọn 4 họ:

probabilistic logic NeSy
solver-oriented / ASP / constraint-based NeSy
differentiable logic / soft logical regularization
rule learning / abductive learning
Mỗi họ nên viết gì
họ này mạnh ở điểm nào
thường dùng cho loại reasoning nào
hạn chế gì khi áp sang Vietnamese legal QA
Câu chốt subsection

Các hướng này cung cấp reasoning substrate hữu ích, nhưng chưa trực tiếp giải quyết các yêu cầu đặc thù của legal QA tiếng Việt:

statutory rule construction,
missing-fact clarification,
proof-grounded legal answering,
intermediate-state verification.
2.2. Vietnamese legal QA systems
Câu hỏi cần trả lời

“Trong Vietnamese legal QA, người ta đang làm đến đâu?”

Cần viết gì

Chia nhóm:

retrieval / legal IR
data enrichment / weak labeling
knowledge graph / ontology
RAG-based answer generation
classic QA systems for legal or public administrative services
Cách viết

Không cần review quá dài từng paper nếu literature mỏng.
Quan trọng là rút ra pattern:

mạnh về access to legal text
mạnh về structured indexing
mạnh về retrieval-enhanced answer generation
nhưng ít nhấn mạnh requirement-driven legal reasoning và clarification.
2.3. Gap and positioning
Đây là đoạn chốt Related Work

Viết rõ:

NeSy prior: mạnh về reasoning machinery
Vietnamese legal QA prior: mạnh về retrieval/structured access
paper này: specialized NeSy for Vietnamese legal QA
Cần nhấn mạnh

Không dùng structured knowledge chỉ để retrieval.
Bạn transform legal provisions into reasoning-ready rules và tổ chức QA như một verification-guided reasoning pipeline.

Tránh gì
đừng để Related Work đọc như survey về RAG
đừng dành quá nhiều đất cho paper mẫu kiểu KG/RAG
đừng claim trực tiếp “first NeSy legal QA for Vietnam” nếu chưa verify tuyệt đối
3. PROBLEM FORMULATION
Mục tiêu

Làm paper có tính method rõ ràng.
Người đọc phải hiểu chính xác bài toán và object của bạn là gì.

3.1. Inputs
Cần viết gì

Định nghĩa input gồm:

user legal question q
curated legal rule base R
legal source documents / statutes D
optional clarification answers C
possibly retrieved evidence passages E cho answer support.
Nên viết rõ

Phân biệt 3 tầng nguồn tri thức:

source of truth: statutes / decrees
structured ground truth: curated rule base
supporting evidence: retrieved passages.
3.2. Outputs
Cần viết gì

Đầu ra không chỉ là answer text.
Phải nêu đầy đủ:

parsed logical objects
selected rule
requirement set
missing facts
clarification question if needed
final conclusion
proof
evidence citations
answer text
verification statuses
Ý nghĩa

Section này giúp reviewer hiểu tại sao paper bạn có thể evaluate từng stage.

3.3. Legal rule representation
Cần viết gì

Định nghĩa rule ở dạng logic:

if-body
then-conclusion
optional exception
optional deadline/threshold
provenance metadata.
Nên có ví dụ

Ví dụ doanh nghiệp:
changeLegalRepresentative(X) → obligation(X, registerChange)

Có thể thêm deadline rule:
changeLegalRepresentative(X) → deadline(X, registerChange, 10_days)

3.4. Query-side logical objects
Cần viết gì

Định nghĩa:

semantic slots
condition atoms
facts
goal
query-rule-candidate
Ý nghĩa

Đây là bridge từ language sang reasoning.

3.5. Task objective
Cần viết gì

Mục tiêu của hệ không chỉ là maximize answer correctness, mà là:

produce a legally grounded conclusion,
identify missing facts when conclusion is under-specified,
generate proof and provenance,
avoid unsupported legal claims.
3.6. Inference states
Nên thêm

Định nghĩa các trạng thái đầu ra:

answered
answered_with_caveat
needs_clarification
failed / unsupported
Tác dụng

Rất quan trọng để Evaluation và Discussion sau này chặt hơn.

4. FRAMEWORK OVERVIEW
Mục tiêu

Cho người đọc cái nhìn toàn cục trước khi đào từng module.

4.1. System pipeline
Cần viết gì

Mô tả pipeline bằng prose + figure:
question
→ dual-layer parsing
→ parse verification
→ rule retrieval
→ backward chaining
→ clarification if needed
→ forward chaining
→ proof and conclusion
→ evidence retrieval
→ answer generation
→ answer verification.

Nên có figure

Có 1 hình tổng thể, càng sạch càng tốt.

4.2. Core design principles
Cần viết gì

Viết thành 4–5 nguyên tắc:

legal source of truth không nằm ở LLM
question-side parsing và law-side parsing là hai pipeline khác nhau
retrieval only proposes candidates; backward reasoning selects
forward reasoning requires satisfied requirements
verification acts on intermediate objects, not only final answers
RAG is evidence support or fallback expansion, not default reasoning.
4.3. Running example
Nên có

Một ví dụ chạy xuyên suốt paper.
Ví dụ doanh nghiệp đổi người đại diện theo pháp luật.

Cần thể hiện
câu hỏi
layer 1 slots
layer 2 objects
candidate rules
selected rule
requirement set
missing facts / clarification
proof
final answer
Tác dụng

Giúp paper dễ đọc hơn rất nhiều.

5. LAW-SIDE RULE CONSTRUCTION AND MULTI-RULEBASE ARCHITECTURE
Mục tiêu

Đây là nơi “legal knowledge construction” của bạn xuất hiện, nhưng phải kể theo hướng rulebase phục vụ reasoning, không phải chỉ tri thức để retrieval.

5.1. Legal source scope
Cần viết gì

Nêu domain(s):

enterprise
tax
labor
nếu paper hiện đang multi-domain.

Nếu paper chính chỉ chốt enterprise ở method example thì cũng nói rõ:

prototype illustrated on enterprise
extended architecture supports multiple legal domains
5.2. Law-side extraction pipeline
Cần viết gì

Luồng:

source document preprocessing
segmentation theo điều/khoản/điểm
normative sentence detection
legal frame extraction
predicate normalization
rule generation
validation
provenance attachment.
Cần nhấn mạnh

Law-side pipeline cần:

stable
deterministic
auditable
khác với question-side parsing linh hoạt hơn.
5.3. Legal frame and rule schema
Cần viết gì

Định nghĩa legal frame trung gian:

subject_type
conditions
modality
action
exceptions
deadline / threshold

Sau đó mapping thành logical rule.

Nên có ví dụ

Ít nhất 1 rule obligation, 1 rule deadline, 1 rule exception.

5.4. Rule storage and provenance
Cần viết gì

Phân biệt:

logic form
JSON structured form
metadata fields:
rule_id
source_doc
article
clause
point
source_text_span
version.
Tác dụng

Đây là nền của traceability.

5.5. Multi-rulebases architecture
Cần viết gì

Đây là phần hấp thụ multi-rulebases:

statute-specific packs
domain-level rulebases
shared-layer motifs / bridge rules
runtime reasoning core
domain routing and conflict handling.
Cần nhấn mạnh

Shared layer không thay domain rules; nó hỗ trợ:

abstraction,
transfer,
routing,
cross-domain reasoning when appropriate.
5.6. Why this architecture matters
Kết subsection bằng gì
legal knowledge becomes reasoning-ready
provenance is preserved
multi-domain extension becomes feasible
evaluation at the rule level becomes possible
Tránh gì
đừng biến section này thành dump pipeline extraction quá chi tiết implementation
đừng kể file names/tool names quá sớm trong body chính
6. DUAL-LAYER QUESTION PARSING
Mục tiêu

Giải thích cách hiểu question user mà vẫn cho verification và reasoning can thiệp được.

6.1. Why direct text-to-logic is insufficient
Cần viết gì

Nói vì sao không nên parse thẳng:

khó phát hiện lỗi cục bộ
khó repair theo slot
khó tách ambiguity giữa language understanding và logic normalization.
6.2. Layer 1: semantic slot extraction
Cần viết gì

Mô tả từng slot:

utterance_type
subject_text
condition_text
action_text
modality_text
time/deadline_text
exception_text
question_focus
assertion_status.
Với mỗi slot

Không cần giải thích quá dài, chỉ cần:

nó là gì
phục vụ bước nào sau này
6.3. Layer 2: logical object normalization
Cần viết gì

Mô tả object:

subject_normalized
condition_atoms
facts
goal
query_rule_candidate.
Cần nhấn mạnh

Layer 2 là reasoning interface, không phải language interface.

6.4. Mapping between layers
Cần viết gì

Viết rõ transformation:

subject_text → subject_normalized
condition_text + subject → condition atoms
action + modality → goal
utterance type + conditions + goal → query-rule-candidate
assertion status → fact/hypothetical status.
6.5. Parsing outputs and error surface
Cần viết gì

Nói dual-layer design giúp detect lỗi ở mức:

subject mismatch
condition mapping error
modality / goal mismatch
assertion status error
missing slot
Tác dụng

Chuẩn bị nền cho parse verification + repair loop.

7. RULE RETRIEVAL AND CANDIDATE SELECTION
Mục tiêu

Nói rõ retrieval là bước đề xuất rule candidates, không phải reasoning quyết định cuối cùng.

7.1. Retrieval inputs
Cần viết gì

Input từ parsing:

goal
action/modality
condition atoms
subject type
question focus.
7.2. Ranking criteria
Cần viết gì

Score có thể gồm:

conclusion predicate match
action match
modality match
subject type match
condition predicate overlap
domain and metadata fit.
Không cần làm gì

Không cần sa quá sâu vào engineering scoring trừ khi đó là contribution mạnh.

7.3. Top-k candidates
Cần viết gì

Kết quả retrieval là top-k candidate rules.
Viết rõ:

top-k only narrows the search space
selected rule is decided by backward reasoning
7.4. Fallback retrieval / expansion
Cần viết gì

Nếu curated rule base thiếu coverage:

retrieve relevant law passages
optionally synthesize candidate rules
verify them before temporary use.
Cần nhấn mạnh

Đây là fallback, không phải mainline paper identity.

8. REQUIREMENT-DRIVEN LEGAL REASONING
Mục tiêu

Đây là trái tim reasoning của paper.
Section này phải làm reviewer thấy:

bạn không chỉ “apply rules”
bạn có cơ chế tìm missing facts và điều khiển clarification
8.1. Backward chaining for rule selection
Cần viết gì

Bắt đầu từ goal:

unify goal with candidate rule heads
eliminate incompatible rules
choose best rule
derive requirement set.
Cần nhấn mạnh

Backward chaining là proof-aware refinement over retrieval.

8.2. Requirement set
Cần viết gì

Định nghĩa requirement set formally hoặc bán-formal.
Ví dụ:
Req(goal) = {conditions necessary to justify the goal under the selected rule}

Nên có ví dụ

Goal: obligation(company_x, registerChange)
Req = {changeLegalRepresentative(company_x)}

8.3. Missing fact detection
Cần viết gì

So requirement set với:

parsed facts
asserted conditions
confirmed clarification answers

Đầu ra:

covered requirements
missing facts
uncertain requirements.
8.4. Clarification policy
Cần viết gì

Đây rất quan trọng.
Phải viết policy rõ:

clarification sinh từ missing facts cụ thể
không hỏi lại mơ hồ
nếu đủ fact thì không clarify
nếu thiếu fact quan trọng thì ask user
có thể có provisional answer nếu policy paper cho phép
Cần chọn stance rõ ràng

Hard clarification hay soft conditional answer?
Paper phải chốt một policy nhất quán.

8.5. Forward chaining for proof construction
Cần viết gì

Khi requirements đủ:

apply selected rule(s)
derive conclusion(s)
optionally derive intermediate facts
build proof path.
Nên viết rõ

Forward chaining không tự do generate; nó phải dựa trên:

confirmed facts
selected rule
satisfied body
8.6. Proof object
Cần viết gì

Định nghĩa proof structure:

used facts
used rules
derivation path
final conclusion
maybe support citations.
Ý nghĩa

Proof là bridge giữa symbolic reasoning và answer explanation.

8.7. Relationship between backward and forward
Cần viết gì

Kết thúc section bằng việc chốt:

backward discovers what must hold
forward demonstrates what follows
goal ties the two together
clarification connects requirement discovery to user interaction.
9. VERIFICATION-CENTRIC NEURO-SYMBOLIC ENGINE
Mục tiêu

Đây là section “signature” của paper.
Phải viết rất rõ để người đọc thấy đây là điểm trung tâm.

9.1. Why stage-wise verification is needed
Cần viết gì

Lý do:

errors can appear before final answer
final-answer-only checking is too late
different objects need different checks:
parse objects
rules
requirements
proofs
answers.
9.2. Verification modes
Cần viết gì

Mô tả 5 mode:

parse verification
rule verification
backward verification
forward verification
answer verification.
Với mỗi mode, cần nêu
input object
symbolic checks
semantic/NLI checks
what kind of repair it triggers

Có thể trình bày bằng bảng rất đẹp.

9.3. Symbolic checks
Cần viết gì

Nói đây là hard constraints cho:

predicate compatibility
modality consistency
time / deadline / threshold consistency
subject / variable unification
proof validity
body satisfaction.
Cần nhấn mạnh

Nếu symbolic fail cứng, object không được accept chỉ vì NLI có vẻ hợp.

9.4. NLI-based semantic checks
Cần viết gì

Object logic được verbalized có kiểm soát, rồi so sánh với:

original question
law span
conclusion
answer text
Vai trò của NLI
bắt semantic drift
hỗ trợ các lỗi mềm mà symbolic khó thấy
không thay symbolic constraints
9.5. Decision fusion
Cần viết gì

Phải nêu decision policy:

accept
reject
repair
maybe degrade / proceed-with-warning nếu bạn có dùng
Cần chốt rõ
symbolic hard fail > reject/repair
NLI soft mismatch > warning/repair depending on mode
fusion is policy-driven, not arbitrary.
9.6. Repair loop
Cần viết gì

Nói repair is module-specific:

parser repair
normalizer repair
rule extractor repair
backward reasoner repair
forward reasoner repair
answer generator repair.
Cần nhấn mạnh

Repair loop không regenerate toàn pipeline một cách mù.

9.7. Why this is NeSy specialization for legal QA
Đây là câu chốt section

Phải nói:

engine này không chỉ mix neural và symbolic chung chung
nó được specialized cho legal QA bằng:
requirement-aware reasoning objects
clarification-triggering missing facts
proof validation
answer grounding over legal conclusions.
10. ANSWER GENERATION AND LEGAL EVIDENCE SUPPORT
Mục tiêu

Giải thích answer cuối được sinh từ đâu và tại sao vẫn grounded.

10.1. Evidence retrieval
Cần viết gì

Retrieve relevant statute passages để:

support explanation
attach provenance
enrich answer text
aid answer verification.
Cần chốt

Evidence retrieval hỗ trợ explanation, không thay symbolic proof.

10.2. Answer generation
Cần viết gì

Answer generator dùng:

final conclusion
proof
missing facts status
legal evidence
Cần nhấn mạnh

Answer should reflect the reasoning state:

direct answer if supported
conditional/provisional answer if facts are missing
explicit uncertainty when conclusion is not fully justified
10.3. Answer verification
Cần viết gì

Check answer against:

conclusion
proof
subject/action/modality/time consistency
unsupported claims.
10.4. Output style and transparency
Cần viết gì

Nêu answer có thể gồm:

final legal conclusion
short explanation
supporting legal basis
proof/provenance snippet
missing conditions if any
11. EXPERIMENTAL SETUP
Mục tiêu

Section này phải chứng minh evaluation của bạn nghiêm túc và phù hợp với claim.

11.1. Research questions
Nên viết hẳn RQ

Ví dụ:

RQ1: framework có cải thiện end-to-end legal QA không?
RQ2: stage-wise verification có cải thiện grounding và traceability không?
RQ3: requirement-driven clarification có giúp under-specified questions không?
RQ4: từng module đóng góp gì theo ablation?
11.2. Domains and legal sources
Cần viết gì

Nêu domain:

enterprise
tax
labor
nếu multi-domain full.

Nêu số lượng statute packs / domain rulebases / shared motifs nếu có.

11.3. Rule base statistics
Cần viết gì

Báo cáo:

số source documents
số canonical rules
số runtime reasoning rules
số shared motifs
số rules theo family (obligation / permission / deadline / etc.) nếu có.
11.4. QA dataset construction
Cần viết gì

Rất quan trọng.
Phải mô tả:

questions đến từ đâu
cách chọn
cách lọc
domain distribution
intent distribution
tỷ lệ câu thiếu fact
tỷ lệ cần clarification
complexity categories
Cần nhấn mạnh

Dataset phải cover:

intent coverage
functional coverage
reasoning diversity.
11.5. Annotation protocol
Cần viết gì

Mỗi QA được annotate cái gì:

gold parse or slot labels nếu có
supporting_rule_ids
required_facts
missing_facts
reasoning_type
needs_clarification
gold conclusion
gold answer.
Tác dụng

Giúp đánh giá từng stage chứ không chỉ end-to-end.

11.6. Baselines and comparison settings
Đây là nơi phải bám yêu cầu positioning mới

Chia 3 nhóm:

Nhóm A: non-NeSy legal QA baselines
direct LLM
RAG-based legal QA
retrieval / KG-assisted QA
Nhóm B: internal framework ablations
no parse verification
no backward verification
no forward verification
no clarification
no repair loop
no symbolic rule selection
no answer verification
Nhóm C: family-level NeSy comparison

Nếu không có prior Vietnamese NeSy papers thật sát, thì so ở mức method family, không ép paper-to-paper direct.

Cần nhấn mạnh

RAG không phải opponent trung tâm; nó là one baseline family among others.

11.7. Metrics
Cần viết theo tầng
Parsing metrics
slot accuracy / F1
goal accuracy
logical object consistency
Retrieval metrics
Recall@k
Hit@k
MRR / nDCG nếu cần
Backward reasoning metrics
selected rule accuracy
requirement set accuracy
missing fact correctness
Clarification metrics
clarification trigger accuracy
clarification usefulness
post-clarification improvement
Forward reasoning metrics
conclusion-goal match
proof validity
unsupported inference rate
End-to-end QA metrics
legal answer correctness
partial correctness / usefulness
grounded-to-rule rate
proof present rate
unsupported answer rate
Verification/repair metrics
verification detection rate
correct repair routing
repair success rate
11.8. Implementation details
Cần viết gì
parser model / prompt mode
NLI model
retrieval setup
top-k
hardware/runtime
major settings relevant to reproducibility
12. RESULTS
Mục tiêu

Cho thấy framework hoạt động và các module đóng góp thực sự.

12.1. Parsing results
Cần viết gì
layer 1 results
layer 2 results
before/after parse verification or repair
common parse error types
12.2. Retrieval results
Cần viết gì
top-k retrieval performance
selected rule present in top-k bao nhiêu
retrieval errors by domain / intent
12.3. Backward reasoning and clarification results
Cần viết gì
selected rule accuracy
requirement set quality
missing fact detection quality
clarification trigger quality
answer improvement after clarification
12.4. Forward reasoning and proof results
Cần viết gì
conclusion-goal match
proof validity
successful proof construction rate
failure patterns
12.5. End-to-end QA results
Cần viết gì

So full system với baselines trên:

correctness
usefulness
grounding
unsupported answer rate
proof presence
Cần chốt narrative

Even when answer fluency is not always highest, the framework improves legal grounding / traceability / support.

12.6. Verification and repair results
Cần viết gì
bao nhiêu lỗi được detect ở từng mode
route đúng module bao nhiêu
repair thành công bao nhiêu
phần nào repair khó nhất
12.7. Ablation study
Cần viết gì

Chạy các biến thể:

no dual-layer parsing
no backward reasoning
no clarification
no forward verification
no answer verification
no repair loop
no shared layer nếu multi-domain and relevant
Cần rút ra

Module nào là load-bearing nhất.

13. ANALYSIS AND DISCUSSION
Mục tiêu

Đây là nơi bạn chứng minh mình hiểu hệ, không chỉ dump bảng.

13.1. Why the framework works
Cần viết gì

Giải thích vì sao một số module giúp:

dual-layer parsing giúp tách language ambiguity
backward reasoning giúp expose missing facts
forward chaining giúp proof-grounded conclusions
stage-wise verification giúp chặn drift sớm.
13.2. Failure analysis
Cần viết gì

Nhóm lỗi:

parse slot mismatch
retrieval drift
wrong rule family
incomplete requirement set
premature forward inference
answer over-generation
Nên có bảng taxonomy

Một bảng nhỏ rất hữu ích.

13.3. Role of clarification
Cần viết gì

Nói clarification không chỉ là UI feature; nó là một phần của reasoning policy:

legal QA often under-specified
missing-fact questions should not be forced into unsupported direct answers
clarification improves both correctness and trustworthiness.
13.4. Multi-domain observations
Nếu paper có multi-domain

Phân tích:

domain nào dễ/khó
shared layer giúp hay không
cross-domain conflicts xuất hiện ra sao
domain routing có tác động gì.
13.5. Positioning revisited
Cần viết gì

Đây là đoạn rất nên có ở cuối Discussion.
Chốt lại:

framework này không cạnh tranh chủ yếu ở retrieval quality
đóng góp chính là specializing neuro-symbolic reasoning for Vietnamese legal QA
structured legal knowledge ở đây phục vụ reasoning and verification, không chỉ retrieval support.
13.6. Case studies
Nên có 2 ca
một successful case
một failure case
Mỗi case nên trình bày
question
parse
selected rule
requirement set
clarification (if any)
proof
final answer
what went right / wrong
14. LIMITATIONS
Mục tiêu

Chủ động thừa nhận giới hạn, tăng độ tin cậy học thuật.

Cần viết gì
rule base coverage chưa hoàn chỉnh
statute-to-rule extraction vẫn có noise
ambiguity trong legal language còn khó
NLI/verifier cho tiếng Việt pháp lý còn hạn chế
clarification policy hiện vẫn đơn-turn hoặc còn đơn giản
repair loop chưa giải quyết được mọi trường hợp
scaling sang domain rộng hơn cần thêm công sức tri thức.
Tránh gì
đừng viết limitations kiểu xin lỗi
hãy viết như roadmap có kiểm soát
15. CONCLUSION
Mục tiêu

Chốt lại paper đã làm được gì và validated điều gì.

15.1. Recap the framework
Cần viết gì

Nhắc lại ngắn:

reasoning-ready legal rules
dual-layer parsing
backward requirement discovery
clarification
forward proof construction
stage-wise verification and repair.
15.2. Main findings
Cần viết gì

Chốt kết quả chính:

improved grounded reasoning
better handling of under-specified questions
stronger traceability / proof support
lower unsupported-answer tendency
15.3. Broader implication
Cần viết gì

Nói rộng hơn:

legal QA cần more than retrieval
verification-centric NeSy is promising for low-resource legal domains
Vietnamese legal QA is a good testbed for structured reasoning
15.4. Future work
Cần viết gì
richer exception/temporal reasoning
stronger automatic rule induction from statutes
broader domains
better interactive clarification
larger-scale evaluation
APPENDIX
Mục tiêu

Đẩy chi tiết kỹ thuật và tài liệu phụ ra ngoài main paper để bài chính gọn.

Nên đưa vào gì
full slot schema
logical object schema
legal frame schema
more rule examples
prompt templates
verification templates / verbalization examples
more case studies
annotation guideline
error taxonomy
supplementary tables