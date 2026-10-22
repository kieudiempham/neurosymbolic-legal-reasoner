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

Scope: all 300 questions, all 1,950 single-fault diagnostic instances (1,499 from development questions, 451 from
held-out questions) and all 453 two-fault instances (349 + 104). Because the KBs and the controller were developed
on the development questions, results on the held-out part alone are reported where they differ.

**Table 1. Main comparison.** E2E QA: all 300 questions with the real GPT-4o parser. Faulty QA and Clarif./query:
the 1,950 diagnostic instances (1,774 with a fault). IRAC: 300 questions, 1,200 blind-judged answers.

| Method | E2E QA Acc. ↑ | Faulty QA Acc. ↑ | Clarif. / query ↓ | IRAC ↑ |
|---|---|---|---|---|
| GPT-4o (pure LLM) | 71.3 | N/A | N/A | 58.0 |
| Symbolic QA | 65.7 | 3.7 | 0.00 | 66.2 |
| Heuristic diagnosis | **79.0** | **88.7** | 2.27 | **70.9** |
| **Ours (cross-layer MBD)** | 78.3 | 87.9 | **1.14** | 70.7 |

**Table 2. Diagnostic performance.** Single-fault: n = 1,950; two-fault: n = 453. A reported fault counts as
correct only if it was injected.

| Method | Fault F1-score (single-fault) ↑ | Fault F1-score (two-fault) ↑ | Extra faults / query ↓ | Unnecessary questions / query ↓ |
|---|---|---|---|---|
| Direct symptom→cause mapping | 11.6 | 9.3 | 3.69 | 3.24 |
| Heuristic diagnosis | 41.0 | 57.2 | 1.87 | 2.11 |
| **Ours (cross-layer MBD)** | **53.8** | **60.0** | **1.01** | **0.98** |

**Figure 1. QA accuracy vs. clarification budget (n = 1,950)** (`experiments/figures/fig1_clarification_budget.pdf`):
QA accuracy when the simulated user answers at most 0, 1, 2 or unlimited clarification questions per query
(Ours 75.3 / 84.9 / 86.1 / 88.4; Heuristic 76.3 / 86.0 / 87.0 / 89.1; direct mapping 15.5 / 43.1 / 46.9 / 54.6).

**Figure 2. Ablation (n = 1,950)** (`experiments/figures/fig2_ablation.pdf`): QA accuracy, with the fault-level
F1-score under each bar — Ours 88.4 (F1 53.8), without the acceptance test 88.6 (53.8), without MBD 54.6 (11.6),
without diagnosis and recovery 12.4.

**Discussion.**
*Diagnosis-guided recovery is what makes the symbolic pipeline usable.* With one fault per input, Symbolic QA
answers 3.7% of faulty inputs correctly; diagnosis and recovery raise this to 87.9% (Table 1). Replacing
consistency-based diagnosis by a direct symptom-to-cause mapping loses 33.8 points of QA accuracy and most of
the fault F1-score (53.8 → 11.6; Table 2, Figure 2), and with two simultaneous faults it fails almost completely
(QA 1.6% of 453).

*MBD versus a matched heuristic.* With identical evidence, MBD and the IF–THEN heuristic reach almost the same QA
accuracy (88.4 vs 89.1% overall; 87.9 vs 88.7% on faulty inputs) and fault recall (77.6 vs 78.8%), and stay within
about one point at every clarification budget (Figure 1). MBD is significantly more precise: fault F1-score
+12.8 points (95% paired-bootstrap CI [10.9, 14.9]) on single faults and +2.7 [0.4, 5.5] on pairs (Table 2), with
0.87 fewer spurious faults per query [−1.05, −0.69]. This translates directly into interaction: MBD asks 1.13
fewer unnecessary questions per query on single faults ([−1.39, −0.90]) and 1.57 fewer on pairs ([−2.18, −1.02]),
i.e. about half of the heuristic's clarification requests overall (1.14 vs 2.27 per query). We therefore claim
parity in answer accuracy with more precise, parsimonious fault localisation and less user interaction — not
higher answer accuracy. Two controller design points were needed for this, both identified on the development
questions (an encoded, resolvable overlap must not end the search for an input fault; independent components are
diagnosed separately when the bounded joint search finds no diagnosis).

*The bottleneck is measurement.* On the held-out part of the KB-independent F1–F4 fault set, diagnostic accuracy of Ours is 70.3% with
the selected mDeBERTa + GPT-4o-mini measurement, against 62.2% with GPT-4o-mini alone, 35.1% with mDeBERTa alone
and 32.4% with the open-weight Qwen2.5-7B (which labels stated facts as "not mentioned"), and 100% with perfect
measurements: diagnostic accuracy follows measurement quality, and complementary
measurements improve cross-layer fault localisation. Dropping the acceptance test changes neither the fault
F1-score nor the QA accuracy noticeably once the measurement is good (Figure 2).

*GPT-4o versus proof-grounded answers.* Over all 300 questions the KB-based systems answer more questions
correctly than pure GPT-4o (78.3–79.0% vs 71.3%), but this advantage comes from the development questions on
which the KBs were completed (85.6–86.1% vs 71.7%); on the 106 held-out questions GPT-4o is more accurate (70.8%
vs 65.1% for Ours), reflecting KB coverage of unseen cases (92/106 held-out questions are reproducible from gold
facts) and parser recall (84.7%; precision 88.9%), not diagnosis. The proof-grounded answers are clearly better
legal answers by IRAC (66–71 vs 58; Table 1): GPT-4o states the issue well (I = 1.00 vs 0.74–0.76) and argues
fluently (A = 0.83 vs 0.78–0.82) but rarely names the governing articles (R = 0.12 against 0.51–0.55; several
provisions in force in 2026 postdate its training data), and it recognises insufficient information in only 52%
of such questions (70% for the diagnosing systems). MBD and the heuristic give answers of equal IRAC quality, as
both verbalise the same verified proof.

**Limitations.** Questions and gold labels are LLM-generated and under legal review; injected faults with a
simulated user who knows all case facts; oracle legal goal; LLM-judged IRAC; small test split (106 questions).
