# Section 5 draft — Experiments and Results (4 main tables)

All numbers are reproducible from `experiments/` (per-instance results) and the experiment bundle; further
breakdowns (per domain, per fault category, KB-independent F1–F4 set) are in the supplementary material.

---

## 5.1 Data

**Legal corpus and KB.** 18 Vietnamese legal documents (laws, decrees and circulars on social insurance,
labour, enterprises and taxation; 106 chapters, 1,159 articles). An LLM extractor (GPT-4o-mini, one call per
article) produced 7,906 candidate rules. For each domain, the articles cited by the benchmark were selected and
their rules re-expressed over a shared predicate registry and reviewed, giving five domain KBs with 636 rules and
422 encoded exception relations. KB patches were derived only from development-split failures.

**Questions.** 300 synthetic Vietnamese application questions generated with GPT-4o from the cited provisions
(social insurance 90, enterprise 70, tax 70, labour 30, cross-domain 40; 225 distinct legal cases), each
annotated with the legal goal, the case facts with verbatim spans, the gold conclusion (yes 144 / no 85 /
insufficient 71) and the legal basis. "Insufficient" is defined by the law, independently of the KB: a missing
general condition makes a case insufficient; an exception the question does not raise does not apply; an
exception raised only partially makes the case insufficient. Questions are split by legal case into development
(194) and held-out test (106); all social-insurance questions are development. All choices (measurement model,
prompt, acceptance threshold, controller design) were made on the development split.

**Diagnostic instances.** From every question whose gold conclusion the KB reproduces, controlled faults are
injected in each layer — a fact removed from the question (Missing Case Information), removed from the parse
(Parser Omission), negated (Parser Misinterpretation), an unstated fact added (Unsupported Parser Fact), and, where
two encoded rules compete, the overlap kept or its exception removed (Resolvable Rule Overlap / Unresolved KB
Conflict); an instance is kept only if its fault is observable in the reasoning. This gives 1,499 development and
451 test single-fault instances, and 349 / 104 instances with two simultaneous faults on different propositions
(cross-layer pairs: missing + misinterpreted, omitted + misinterpreted, missing + unsupported, misinterpreted +
unsupported).

## 5.2 Systems and setup

- **GPT-4o (pure LLM)**: question only, fixed prompt, temperature 0; verdict and IRAC answer. No KB, no
  retrieval, no parsed or gold facts.
- **Symbolic QA**: GPT-4o semantic parser → domain KB → three-valued forward reasoner; no diagnosis.
- **Heuristic diagnosis**: Symbolic QA plus an IF–THEN classifier over the same evidence as Ours (accepted NLI
  measurements of all relevant propositions, KB verification of all competing rule pairs) and the same recovery.
- **Ours (cross-layer MBD)**: Symbolic QA plus consistency-based diagnosis over user, parser and KB components,
  diagnosis-directed measurement, clarification on missing-vs-omitted ambiguity and layer-ordered recovery.

All systems use the gold legal goal (results are end-to-end under an oracle goal). The NLI measurement is the mean
label distribution of mDeBERTa-v3 (XNLI) and GPT-4o-mini (option-letter probabilities, temperature 0), accepted as
an observation if its probability is at least τ = 0.50 (otherwise ⊥). In the fault-injection experiments a
simulated user answers clarification questions with the gold case facts; in end-to-end QA no user is simulated
and a clarification request counts as the answer "insufficient".

## 5.3 Metrics

QA accuracy (verdict = gold conclusion). Diagnosis is evaluated at the fault level, as is standard for
model-based diagnosis: a reported fault is a true positive only if it was injected, so every additional reported
fault (including an unstated condition reported as missing) lowers precision; we report fault precision, recall
and F1, exact isolation (reported set = injected set) and the mean number of faults per diagnosis. Recovery gain is
the QA accuracy on faulty inputs minus that of Symbolic QA. Interaction cost is the number of clarification
questions per query and the number of *unnecessary* ones (about a proposition that is not faulty); measurement cost
is the number of NLI measurements per query. 95% intervals are paired bootstrap intervals (2,000 resamples).
IRAC = 100·(0.10·I + 0.35·R + 0.40·A + 0.15·C), each component 0 / 0.5 / 1, on all 300 questions (1,200 answers),
blind and shuffled, judged by GPT-4.1 (not the GPT-4o baseline) given the gold conclusion and legal basis; R = 1
requires the correct document and article numbers of the governing provisions.¹ Language is not scored.

¹ The Rule criterion was made precise after a pilot scoring of 40 questions, in which a looser wording let the
judge give 0.5 to answers naming no article; it was then fixed and applied unchanged to all methods and questions.

## 5.4 Results

**Table 2. Main comparison.** End-to-end QA with the real parser (106 test questions; all 300 in parentheses),
IRAC on all 300 questions, and diagnosis and recovery on the 451 injected test instances.

| System | QA end-to-end | IRAC | QA on faulty inputs | Recovery gain (pp) | Clarif./query | NLI meas./query |
|---|---|---|---|---|---|---|
| GPT-4o (pure LLM) | **70.8** (71.3) | 58.0 | – | – | – | – |
| Symbolic QA | 61.3 (65.7) | 66.2 | 4.3 | – | 0.00 | 0.00 |
| Heuristic diagnosis | 66.0 (79.0) | **70.9** | **85.7** | **+81.5** | 3.71 | 5.79 |
| **Ours (cross-layer MBD)** | 65.1 (78.3) | 70.7 | **85.7** | **+81.5** | **1.70** | **5.56** |

**Table 3. Fault-level diagnosis (test).** Every reported fault that was not injected is a false positive.
Δ = Ours − Heuristic with 95% paired-bootstrap intervals.

| Setting | Method | Fault P | Fault R | Fault F1 | Exact isolation | Faults / diagnosis | Unnecessary clarif./query | QA acc. |
|---|---|---|---|---|---|---|---|---|
| 1 fault (n = 451) | Heuristic | 24.0 | 74.8 | 36.4 | 59.0 | 3.07 | 3.54 | 85.1 |
| | **Ours** | **34.5** | 73.5 | **47.0** | 58.8 | **2.10** | **1.53** | 85.1 |
| | Δ [95% CI] | +10.5 [6.5, 14.9] | | +10.6 [6.5, 14.6] | | | −2.00 [−2.84, −1.26] | |
| 2 faults (n = 104) | Heuristic | 40.8 | 48.1 | 44.2 | 7.7 | 2.40 | 5.54 | 81.7 |
| | **Ours** | **56.7** | 46.6 | **51.2** | 7.7 | **1.68** | **2.12** | 81.7 |
| | Δ [95% CI] | +15.9 [0.0, 28.9] | | +7.0 [0.0, 12.5] | | | −3.42 [−5.83, −1.56] | |

**Table 4. Ablation and equal clarification budget (injected faults, test, n = 451).** QA accuracy when the
simulated user answers at most B clarification questions per query.

| Variant | Fault F1 | QA, B = 0 | QA, B = 1 | QA, unlimited | Clarif./query |
|---|---|---|---|---|---|
| **Ours (full)** | **47.0** | 71.4 | 81.6 | 85.1 | 1.70 |
| − acceptance test (raw NLI labels) | 46.0 | 72.7 | 82.0 | 85.1 | 1.69 |
| − MBD (symptom → most common cause) | 14.1 | 20.6 | 48.6 | 57.0 | 3.16 |
| − diagnosis and recovery (Symbolic QA) | – | 15.3 | 15.3 | 15.3 | 0.00 |
| Heuristic IF–THEN (same evidence) | 36.4 | 72.5 | 82.7 | 85.1 | 3.71 |

**Table 5. Effect of the measurement model on Ours (KB-independent F1–F4 fault set, test).**

| Measurement | NLI macro-F1 (dev) | Diagnosis acc. | Correct action | QA acc. | Clarif./query |
|---|---|---|---|---|---|
| mDeBERTa-v3 (XNLI) | 0.44 | 35.1 | 51.4 | 56.7 | 1.40 |
| Qwen2.5-7B-Instruct | 0.68 | 32.4 | 35.1 | 80.0 | 4.38 |
| GPT-4o-mini | 0.71 | 62.2 | 64.9 | 71.7 | 0.72 |
| mDeBERTa + Qwen2.5-7B | 0.68 | 45.9 | 59.5 | 75.0 | 3.72 |
| **mDeBERTa + GPT-4o-mini** | 0.70 | **70.3** | **73.0** | 73.3 | **0.55** |
| Perfect measurement (upper bound) | 1.00 | 100.0 | 100.0 | 91.7 | – |

**Discussion.**
*Diagnosis-guided recovery is what makes the symbolic pipeline usable.* With one fault per input, Symbolic QA
answers 4.3% of faulty inputs correctly; diagnosis and recovery raise this to 85.7% (Table 2). Replacing
consistency-based diagnosis by a direct symptom-to-cause mapping loses 28 points of QA accuracy and two thirds of
the fault F1 (Table 4), and with two simultaneous faults it fails almost completely (QA 1.9%).

*MBD versus a matched heuristic.* With identical evidence, MBD and the IF–THEN heuristic reach the same QA
accuracy and the same fault recall, with one and with two faults, and stay within about one point under an equal
clarification budget (Table 4). MBD is significantly more precise: fault F1 +10.6 points [6.5, 14.6] on single
faults and +7.0 on pairs (Table 3), because its set-minimal diagnoses contain about a third fewer faults (2.1 vs
3.1 per diagnosis; the heuristic, which labels every unresolved condition as missing, reports up to 36). This
translates directly into interaction: MBD asks the user about non-faulty conditions 2.0 times less per query on
single faults and 3.4 times less on pairs, i.e. it obtains the same answers with about half the questions. We
therefore claim parity in answer accuracy with more precise, parsimonious fault localisation and less user
interaction — not higher answer accuracy. Two controller design points were needed for this, both identified on
the development set (an encoded, resolvable overlap must not end the search for an input fault; independent
components are diagnosed separately when the bounded joint search finds no diagnosis); the test set was re-run
once after these changes.

*The bottleneck is measurement.* With perfect measurements MBD localises every observable fault of the
KB-independent set (Table 5). Diagnosis quality follows measurement quality; an over-cautious open-weight LLM
(Qwen2.5-7B labels stated facts as "not mentioned") makes the system suspect missing information and ask 4.4
questions per query, which the omniscient simulated user rewards with high QA accuracy despite poor diagnoses.
Averaging a classifier that is precise on stated facts with an LLM that is precise on unstated ones gives the
best diagnoses with the fewest questions. Dropping the acceptance test changes little once the measurement is
good (Table 4).

*GPT-4o versus proof-grounded answers.* End to end, pure GPT-4o is more accurate on the held-out questions
(70.8% vs 65.1%), whereas the KB-based systems are far better on the development questions (85.6–86.1% vs 71.7%),
on which the KBs were completed: the test gap reflects KB coverage of unseen cases (92/106 test
questions are reproducible from gold facts) and parser recall (84.7%; precision 88.9%), not diagnosis. The
proof-grounded answers are clearly better legal answers by IRAC (66–71 vs 58): GPT-4o states the issue well and
argues fluently but rarely names the governing articles (R = 0.12 against 0.51–0.55; several provisions in force
in 2026 postdate its training data), and it recognises insufficient information in only 52% of such questions
(70% for the diagnosing systems). MBD and the heuristic give answers of equal IRAC quality, as both verbalise
the same verified proof.

**Limitations.** Questions and gold labels are LLM-generated and under legal review; injected faults with a
simulated user who knows all case facts; oracle legal goal; LLM-judged IRAC; small test split (106 questions).
