# Legal QA (Neuro-Symbolic) — Research Codebase

## Backend Quickstart (PowerShell / Windows)

### Start backend

```powershell
cd neurosymbolic-legal-reasoner
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
```

### Health check

```powershell
cd neurosymbolic-legal-reasoner
.\.venv\Scripts\Activate.ps1
try {
	# First startup can take a few minutes (model load + rulebase bootstrap)
	$r = Invoke-WebRequest -Uri http://127.0.0.1:8001/health -UseBasicParsing -TimeoutSec 180
	Write-Output "health_status=$($r.StatusCode)"
	Write-Output $r.Content
} catch {
	Write-Output "health_error=$($_.Exception.Message)"
}
```

Tip: wait until terminal shows `Application startup complete` before running health check.

### Run 30-case audit

```powershell
cd neurosymbolic-legal-reasoner
.\.venv\Scripts\Activate.ps1
python tests/run_30_case_audit.py --base-url http://127.0.0.1:8001 --input tests/fixtures/30_tests.json --output-dir tests/output --timeout 45
```

Detailed runbook: `docs/runbook_backend.md`

## Manual QA FE + BE (Docker Compose)

### Start both services

```powershell
cd D:\IT\THI\PAPER\project\neurosymbolic-legal-reasoner
docker compose up --build
```

### URLs

- FE: http://localhost:3000
- BE: http://localhost:8001

### Manual test on FE

1. Open FE at http://localhost:3000.
2. Enter Vietnamese question and click Ask.
3. If clarification is requested, fill answers and click Submit Clarification.
4. Check final answer + debug panel (ask/clarify/final JSON, warnings, diagnostics, selected_rule, proof).

Detailed compose runbook: `docs/runbook_manual_qa_compose.md`

