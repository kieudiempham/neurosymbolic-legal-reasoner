Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$venvActivate = Join-Path $repoRoot ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $venvActivate)) {
    throw "Virtual environment activation script not found: $venvActivate"
}

. $venvActivate

& python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
