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
