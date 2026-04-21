# Manual QA with Docker Compose (PowerShell)

## Prerequisites
- Docker Desktop is running.
- Open PowerShell at repo root: `D:\IT\THI\PAPER\project\neurosymbolic-legal-reasoner`.

## Start backend + frontend
```powershell
cd D:\IT\THI\PAPER\project\neurosymbolic-legal-reasoner
docker compose up --build
```

## URLs
- FE: http://localhost:3000
- BE: http://localhost:8001
- BE health: http://localhost:8001/health

## Quick health check (PowerShell)
```powershell
try {
  $r = Invoke-WebRequest -Uri http://localhost:8001/health -UseBasicParsing -TimeoutSec 20
  Write-Output "health_status=$($r.StatusCode)"
  Write-Output $r.Content
} catch {
  Write-Output "health_error=$($_.Exception.Message)"
}
```

## Script-only API artifact rule
- For API output artifacts, always use `tests/run_test.ps1`.
- Do not manually save `/ask` responses via `Invoke-RestMethod | Out-File`.
- This avoids UTF-16/empty artifact issues and keeps one canonical output path.

Run it against compose backend (8001):
```powershell
cd D:\IT\THI\PAPER\project\neurosymbolic-legal-reasoner
powershell -ExecutionPolicy Bypass -File tests/run_test.ps1 -ApiUrl "http://127.0.0.1:8001/ask"
```

Expected artifact path:
- `tests/output/case_tax_delay_after_layer1_prompt_patch.json`

## Manual test flow on FE
1. Open http://localhost:3000
2. Input a Vietnamese legal question in Question Input.
3. Click Ask.
4. If Clarification Area appears, fill each answer field (or keep blank to use placeholder) and click Submit Clarification.
5. Check Final Answer Area for:
   - answer text
   - final_status
   - answer_quality
   - answer_quality_reason
6. Open Debug panel for:
   - ask response JSON
   - clarify response JSON
   - final merged state JSON
   - warnings, diagnostics, selected_rule, proof summary

## Example question
- Enterprise: `Doanh nghiep co bat buoc su dung hoa don dien tu khong?`

## Stop services
```powershell
docker compose down
```
