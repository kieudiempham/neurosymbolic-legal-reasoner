param(
    [string]$BaseUrl = "http://127.0.0.1:8001"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$healthUrl = "$($BaseUrl.TrimEnd('/'))/health"
$response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 20

Write-Output ("health_status={0}" -f $response.StatusCode)
Write-Output $response.Content
