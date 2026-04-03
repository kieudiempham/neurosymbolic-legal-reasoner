# Legal QA (Neuro-Symbolic) — Research Codebase

Paper-first layout: top-level folders mirror **question-side parsing**, **law-side rule construction**, **retrieval**, **reasoning**, **verification**, **generation**, and **evaluation**. Config, data artifacts, experiments, and paper drafts are separated from library code under `src/`.

## Research goal

Build a **traceable** neuro-symbolic pipeline for legal question answering: neural components handle language and soft matching; symbolic components handle rules, inference, and verification. The repository prioritizes **reproducibility** (configs, versioned interim files, experiment logs) over production deployment.

## Project structure (high level)

| Path | Role |
|------|------|
| `configs/` | YAML for paths, each subsystem, and experiment bundles under `configs/experiments/`. |
| `data/raw/` | Immutable inputs (corpus PDF/txt, user questions, external sources). |
| `data/interim/` | Machine-generated traces (parsing, law parsing, retrieval, reasoning, verification). |
| `data/processed/` | Curated rulebase, ontology, evaluation sets, QA splits, reports. |
| `data/splits/` | IDs for parse / rule / QA / experiment splits. |
| `src/` | Python modules aligned with paper sections (see package READMEs under each subfolder). |
| `experiments/` | Run outputs: `logs/`, `predictions/`, plus topic folders for ad-hoc runs; `tables/`, `figures/` for paper. |
| `paper/` | Writing: outline, sections, LaTeX export. |
| `docs/` | Annotation guidelines and design notes (schemas documented in markdown). |
| `notebooks/` | Exploratory analysis linked to interim artifacts. |
| `tests/` | Pytest skeleton; extend as implementations land. |

## Artifact flow

1. **Raw** questions and legal corpus enter `data/raw/`.
2. **Question pipeline** writes layer-1/layer-2 JSONL under `data/interim/question_parsing/`.
3. **Law pipeline** writes segmentation, frames, predicates, validation under `data/interim/law_parsing/`, then **processed** rules under `data/processed/rulebase/`.
4. **Retrieval** consumes parsed questions + rule index → `data/interim/retrieval/`.
5. **Reasoning** produces backward/forward traces and proofs → `data/interim/reasoning/`.
6. **Verification** annotates each stage → `data/interim/verification/` and aggregated reports in `data/processed/reports/`.
7. **Generation** can consume proofs for answers and proof-to-text strings; predictions go to `experiments/predictions/`.
8. **Evaluation** reads gold files from `data/processed/datasets/` and writes metrics for `experiments/tables/`.

## Setup

```bash
cd legal-qa-nesy
pip install -e ".[dev]"
pytest
```

Run from the `legal-qa-nesy` directory so `configs/` and `data/` resolve relative to the project root (see `src/pipelines/_paths.py`).

## Running pipelines (skeleton)

Each runner loads YAML and raises `NotImplementedError` until wired. Intended invocation pattern:

```bash
python -m pipelines.run_question_pipeline --config configs/parser.yaml
python -m pipelines.run_law_pipeline --config configs/rule_builder.yaml
python -m pipelines.run_retrieval_pipeline --config configs/retrieval.yaml
python -m pipelines.run_reasoning_pipeline
python -m pipelines.run_verification_pipeline --config configs/verification.yaml
python -m pipelines.run_end2end_pipeline --config configs/experiments/exp_end2end.yaml
```

Use `PYTHONPATH=src` if you run scripts without editable install (not needed after `pip install -e .`).

## Schemas

Pydantic models live in `src/schemas/` (`Layer1SemanticSlots`, `Layer2LogicObjects`, `LegalFrame`, `Rule`, `Proof`, `VerificationResult`). Mirror definitions are described in `docs/schemas/`.

## Note on `document_manifest.xlsx`

Place the corpus manifest under `data/raw/legal_corpus/manifest/` (see `README.md` in that folder). Add `openpyxl` when implementing Excel I/O.
