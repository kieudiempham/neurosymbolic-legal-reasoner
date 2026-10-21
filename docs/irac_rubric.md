# IRAC rubric (fixed before any answer was scored)

IRAC = 100 × (0.10·I + 0.35·R + 0.40·A + 0.15·C), each component scored 0 / 0.5 / 1.

Language & presentation is deliberately not scored: the study measures legal correctness and reasoning,
and a fluency criterion would favour the free-text LLM baseline.

| Component | Weight | 1 | 0.5 | 0 |
|---|---|---|---|---|
| I — Issue | 0.10 | States precisely the legal question to decide (the right legal relation / status). | Identifies the issue only in general terms, not its core. | Off-topic or misses the core issue. |
| R — Rule | 0.35 | Cites the governing provisions correctly and completely, matching the gold `legal_basis` (an equivalent valid provision is accepted). | Cites the right law but incompletely (missing a key clause, or the implementing decree/circular), or mixes in an inapplicable provision. | Wrong provision, repealed/superseded law, or key provisions missing. |
| A — Application | 0.40 | Maps each stated fact to the conditions of the rule, handles exceptions, and explains why the rule does (not) apply; with missing facts, says which condition cannot be decided. | Relates facts to the rule but the reasoning is incomplete or not convincing (an exception or condition ignored). | Restates facts and rules without connecting them, or reasons incorrectly. |
| C — Conclusion | 0.15 | Conclusion equals the gold answer (yes / no / insufficient; for insufficient, names what must be supplied) and is consistent with A. | Partly correct, or correct but hedged/ambiguous. | Wrong, or no direct answer. |

Protocol
- 40 questions, stratified over the 5 domains and the 3 gold conclusions (true / false / insufficient),
  taken from the held-out test split where one exists (social insurance has none: dev).
- The same 40 questions for all 4 methods; answers anonymised (method name removed) and shuffled.
- LLM judge: a model other than GPT-4o (GPT-4o is a compared method). The judge sees the question, the
  gold conclusion and gold legal basis, the rubric, and one anonymised answer at a time.
- Human check: at least 20 questions scored by hand with the same rubric; agreement with the judge
  reported (Cohen's kappa per component, and correlation of the total).
- The rubric is not changed after seeing results.

## Revision v2 (post hoc, after the first scoring; reported alongside v1)
The v1 Rule levels overlap ("a key provision missing" = 0.5 vs "key provisions missing" = 0), and the judge
gave 0.5 to answers that name no article at all. v2 makes R precise; I, A, C unchanged; all methods
re-scored with the same judge:
- R = 1: correct document (name/number) and the article (clause) numbers of the governing provisions, complete;
  an equivalent provision is accepted only from a document in force.
- R = 0.5: correct document and at least one correct key article, but another key provision or the
  implementing document is missing.
- R = 0: no specific article number (only "under the Law on …"), a wrong article, or a superseded document.
