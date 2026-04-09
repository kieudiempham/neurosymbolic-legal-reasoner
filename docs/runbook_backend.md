# Backend Runbook (PowerShell / Windows)

## Entrypoint audit (current repo)
- FastAPI app entrypoint: `app.main:app` in `backend/app/main.py`.
- You should run commands from repo root: `neurosymbolic-legal-reasoner`.
- Python environment: repo local venv at `.venv`.
- Minimal env vars required to boot: none (defaults are loaded from `backend/app/config.py` and optional `.env`).
- Optional env file: `.env` at repo root with `LEGAL_QA_*` overrides.

# Start backend (PowerShell)
```powershell
cd neurosymbolic-legal-reasoner
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
```

Alternative convenience script:
```powershell
cd neurosymbolic-legal-reasoner
.\scripts\start_backend.ps1
```

# Health check (PowerShell)
```powershell
cd neurosymbolic-legal-reasoner
.\.venv\Scripts\Activate.ps1
try {
  $r = Invoke-WebRequest -Uri http://127.0.0.1:8001/health -UseBasicParsing -TimeoutSec 20
  Write-Output "health_status=$($r.StatusCode)"
  Write-Output $r.Content
} catch {
  Write-Output "health_error=$($_.Exception.Message)"
}
```

Alternative convenience script:
```powershell
cd neurosymbolic-legal-reasoner
.\scripts\healthcheck_backend.ps1
```

Expected minimum health result:
- `health_status=200`
- JSON body contains at least `"status":"ok"`.

# Run 30-case audit (PowerShell)
```powershell
cd neurosymbolic-legal-reasoner
.\.venv\Scripts\Activate.ps1
python tests/run_30_case_audit.py --base-url http://127.0.0.1:8001 --input tests/fixtures/30_tests.json --output-dir tests/output --timeout 45
```

Expected output files:
- `tests/output/30_case_audit_results.json`
- `tests/output/30_case_audit_summary.json`
- `tests/output/raw/*.json`
