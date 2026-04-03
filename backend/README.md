# Legal QA NeSy — Research Demo Backend

Python **FastAPI** **HTTP adapter** for the neuro-symbolic legal QA pipeline. **All business logic lives in `../src/`** (single source of truth). This folder wires **FastAPI**, **config**, **routes**, and **path setup** so `schemas.*`, `pipeline.*`, `session.*`, etc. resolve at runtime.

**Curated rulebase** drives reasoning; **parser** only proposes; **NeSy Verify Engine** (`src/verification/`) checks symbolic + NLI (mock) at each gate; **evidence JSON** supports citations only (no rule synthesis).

## Architecture

```text
question
  → src/question_side/question_parser (Layer 1)
  → src/question_side/question_normalizer (Layer 2)
  → NeSyEngine.verify_parse
  → src/retrieval/rule_retriever (rulebase_reasoning_core.json)
  → src/reasoning/backward_reasoner
  → NeSyEngine.verify_backward
  → [if missing] src/reasoning/clarification_manager
  → src/reasoning/forward_reasoner
  → NeSyEngine.verify_forward
  → src/reasoning/proof_builder
  → src/retrieval/evidence_retriever (evidence_chunks.json)
  → src/generation/answer_generator
  → NeSyEngine.verify_answer
  → JSON response (schemas in src/schemas/)
```

- **Orchestrator**: `src/pipeline/qa_orchestrator.py` (`QAOrchestrator` + `run_ask` / `run_clarify`).
- **Runtime wiring**: `src/pipeline/qa_runtime.py` (`configure_qa_orchestrator`, `get_qa_orchestrator`) — called from `app/main.py` on startup and mirrored in `tests/conftest.py` for `TestClient`.
- **Rule source of truth**: `data/processed/rulebase/rulebase_reasoning_core.json` (repo root, via `app/config.py` `repo_root`).
- **Session store**: in-memory `src/session/storage.py`; swap via `SessionStore` ABC.
- **NLI**: `src/verification/nli_verifier.py` — mock by default; subclass `NLIVerifier` for a real model.

### Backend-only layout

- `app/main.py` — FastAPI app, startup → `configure_qa_orchestrator`
- `app/path_setup.py` — puts repo root + `src/` on `sys.path`
- `app/config.py` — paths, env `LEGAL_QA_*`
- `app/api/routes_*.py` — thin handlers calling `get_qa_orchestrator()` / `get_session_service()`
- `app/api/request_response.py` — optional re-exports from `schemas.http_response`
- `app/utils/logging_utils.py` — logging setup

## Run locally

From the **`backend/`** directory (so `app` is importable):

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000/docs`.

Optional env (see `app/config.py`):

- `LEGAL_QA_DEBUG=true`
- `LEGAL_QA_REPO_ROOT=...` if your layout differs

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health + rule/evidence counts |
| POST | `/ask` | New question; may return `needs_clarification` |
| POST | `/clarify` | Submit answers for missing facts |
| GET | `/session/{session_id}` | Full session snapshot (debug) |

### Example: `/ask`

Request:

```json
{
  "question": "Cổ đông có thể gửi phiếu lấy ý kiến đã trả lời đến công ty bằng thư điện tử không?",
  "session_id": null,
  "user_facts": []
}
```

Response (abbreviated): `session_id`, `needs_clarification`, `layer1`, `layer2`, `verification_trace`, `retrieved_rules`, `selected_rule`, `reasoning`, `proof`, `answer`, `debug_trace`.

### Example: `/clarify`

```json
{
  "session_id": "sess_...",
  "answers": [
    { "fact_key": "exception_applies(...)", "value": true }
  ]
}
```

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

`pytest.ini` adds `..` (repo root) and `../src` so both `pipeline.*` and `schemas.*` import correctly.

## Data files

| File | Role |
|------|------|
| `../data/processed/rulebase/rulebase_reasoning_core.json` | Curated rules |
| `../data/processed/rulebase/rulebase_reasoning_core_mapping.json` | Optional clause mapping |
| `../data/corpus/evidence_chunks.json` | Evidence snippets |

If the rulebase file is missing, retrieval returns no rules (health will show `rule_count: 0`).
