# Pipeline full — sample KB

All code changes are confined to the requested files and new files in `src/legalkb`.
`extract.py`, `compile.py`, `db.py`, `chat.py`, `server.py`, and `data/dataset` are unchanged.
The artificial deadline/sanction rules are explicitly marked `SAMPLE/TEST`; they are not legal advice.
The current schema already supports the tested amount/unit/from-event deadlines, monetary ranges and nonmonetary sanctions. No schema change is requested from machine A for these cases.

## Offline verification

Requires Python dependencies already installed and SWI-Prolog (`LEGALKB_SWIPL` may override its path).

```sh
export PYTHONPATH=src
export LEGALKB_OFFLINE=1
export LEGALKB_SAMPLE_DIR=/tmp/legalkb-tests
python -m legalkb.test_reasoner
python -m legalkb.test_mbd
python -m pytest src/legalkb/test_reasoner.py src/legalkb/test_mbd.py src/legalkb/test_pipeline.py -q
python -m legalkb.inject compare --offline --results src/legalkb/reports/sample_injections.jsonl --output /tmp/sample-comparison.json
python -m legalkb.budget_benchmark
```

`test_mbd` defaults to replaying nine stored real NLI measurements. `--live` is explicit opt-in; do not use it without authorization. Offline mode refuses uncached parsing, embeddings, NLI, model downloads, answer generation and faithfulness checks. Missing measurements are errors, never neutral labels. Replay, calibration and all baseline comparisons need no API.

## Changes and evaluation protocol

- Retain positive and negative parser output even when it no longer appears in a surviving proof. Do not ask about missing leaves on irrelevant conditional branches when a certain proof already exists.
- Link conflicting proof pairs to their parser supports. One parser fault can hit several KB conflicts; independent faults require a joint diagnosis. Preserve subset-minimal alternatives, including a two-fault repair when a single-fault alternative also exists.
- Audit retrieval against the candidate dependency/exception closure. Similarity alone no longer establishes an omission.
- A necessary unsupported fact can require both `missing` (user layer) and `unsupported` (parser layer). Necessity is checked by deleting that input and reasoning again, independently of the NLI acceptance threshold.
- Calibrate acceptance only on dev. Freeze the choice before reporting test. Do not infer neutral observations from absence or use gold labels to make diagnoses.
- Score the top diagnosis with one-to-one fault matching. Count control false positives in precision. Historical metrics excluded control predictions and could match one wildcard fault more than once, so new F1 is not numerically interchangeable with historical F1.
- Every baseline sees the same stored scores and selected threshold. `symbolic`, `heuristic`, `direct`, `no_acceptance`, `no_mbd`, and `no_diagnosis_repair` are selectable with `--system` in both batch and injection. Direct mapping assigns checked-fact symptoms to `misinterp`, missing-input symptoms to `missing`, and KB/retrieval symptoms to their fixed causes. Symbolic/no-MBD are intentionally equivalent controls.
- `--budget 0/1/2/unlimited` controls clarification availability. The injection table scores the first action, so positive budgets coincide there. `policy.evaluate_dialogue` executes explicit reply/rerun transitions; `budget_benchmark.py` reports actual 0/1/2/unlimited rounds on two sample deadline questions. Its fixture observations are deterministic, not measured NLI, and are reported separately.
- `batch.score_actions` requires ask for `insufficient`; answer plus the correct conclusion for `true`/`false`. Confirm/warn on clean cases are separately counted as **thiếu tự tin**. Errors remain in the denominator, and cache coverage is reported separately.
- Step 5 requires a stored successful step-4 action. Unsupported/contradicted/uncertain answer sentences trigger one retry, then a deterministic abstention if fidelity still fails. Tests exercise the actual Asker → Dialogue → HTTP handler path with model boundaries replaced by fixtures; no HTTP socket or live model is required.

## Splits and KB v2 handoff

`splits.py` first reads `data/dataset/<domain>/split.json`, then the actual dataset-directory manifest (`dn_v1/split.json`, etc.). IDs must be disjoint and complete. Missing BHXH manifests retain the historical odd/even split; other domains retain named dev/test files. All injected siblings inherit their base question's split.

Injection derives perturbable facts from the supplied KB vocabulary and supports all five domains. New base caches include KB/program and parser-version fingerprints. Legacy BHXH bases must be explicitly supplied and are only allowed with the sample KB. KB v2 has not been executed on this machine.

Future KB-v2 command (requires API authorization and machine A's files):

```sh
PYTHONPATH=src LEGALKB_OFFLINE=0 python -m legalkb.inject run \
  --kb-db /path/to/kb_v2.sqlite --kb-pl /path/to/kb_v2.pl \
  --base-file /tmp/kb-v2-base.json --results /tmp/kb-v2-injections.jsonl
```

Omit `--domain` for all five domains, or repeat it for a subset. Use a fresh base cache when changing KBs. Injected sample variants are copies, never edits to the original KB.

## API work awaiting permission

The API processes were stopped when requested. The existing 300-question run has 29 completed questions and 271 missing measurements (270 parser-cache misses and one NLI-cache miss). The offline scorer accounted for all 300 IDs, but this is **not** a completed 300-question accuracy experiment. Its coverage is in `reports/batch300_cache_coverage.json`.

Resume the existing default-profile run only after explicit permission, retaining its original threshold/acceptance settings:

```sh
PYTHONPATH=src LEGALKB_OFFLINE=0 LEGALKB_NLI_ENSEMBLE=0 \
LEGALKB_NLI_TAU=0.5 LEGALKB_NLI_RULE=pos_neg \
LEGALKB_SAMPLE_DIR=/tmp/legalkb-batch-sample \
LEGALKB_RUNS_DB=/tmp/legalkb-batch300.sqlite \
python -m legalkb.batch --sample --name sample_full_mbd --system mbd \
  --budget unlimited --retry-errors
```

Do not mix calibration profiles under one batch name. For a fully calibrated run, use a fresh name/database and the frozen profile in `reports/sample_calibration.json` instead. Baseline replay itself requires zero model calls.

Estimate for the 271 outstanding cases, assuming a workload like the 29 completed sample cases: about **5,900 uncached calls** (roughly 1 parse + 14.45 NLI + 1.14 generations + 5.10 faithfulness calls per case), **3–9 million input tokens**, and **0.12–0.35 million output tokens**. These are planning estimates, not measured token usage; cache reuse and unsupported domains can reduce them substantially. Retry failures can increase them. A fresh 300-case profile has an upper planning estimate of about 6,500 calls before cache reuse. No IRAC judge is needed or invoked.
