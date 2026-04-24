param(
    [string]$Question = "",
    [string]$SessionId = "",
    [string]$Domain = "tax",
    [string]$ApiUrl = "http://127.0.0.1:8000/ask",
    [string]$OutputPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Net.Http

# PowerShell 5.1 defaults to legacy code pages; force UTF-8 to avoid mojibake.
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom

if ([string]::IsNullOrWhiteSpace($Question)) {
    # Keep script ASCII-safe for PowerShell 5.1 source decoding.
    $Question = (ConvertFrom-Json '{"q":"K\u1ec3 t\u1eeb khi c\u00f3 thay \u0111\u1ed5i n\u1ed9i dung \u0111\u0103ng k\u00fd doanh nghi\u1ec7p, c\u00f4ng ty ph\u1ea3i g\u1eedi th\u00f4ng b\u00e1o trong th\u1eddi h\u1ea1n m\u1ea5y ng\u00e0y?"}').q
}

if ([string]::IsNullOrWhiteSpace($SessionId)) {
    $SessionId = "sess_acceptance_option3_final_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
}

function Get-ObjectPropertyValue {
    param(
        [object]$Object,
        [string]$Name
    )

    if ($null -eq $Object) {
        return $null
    }

    $prop = $Object.PSObject.Properties[$Name]
    if ($null -ne $prop) {
        return $prop.Value
    }

    return $null
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$outputPath = if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    Join-Path $repoRoot "tests/output/case_tax_delay_after_layer1_prompt_patch.json"
} else {
    if ([System.IO.Path]::IsPathRooted($OutputPath)) {
        $OutputPath
    } else {
        Join-Path $repoRoot $OutputPath
    }
}
$tmpPath = "$outputPath.tmp"

$payload = @{
    question = $Question
    session_id = $SessionId
    domain = $Domain
    use_router = $true
    user_facts = @()
}

try {
    $body = $payload | ConvertTo-Json -Depth 8 -Compress
    $bodyBytes = $utf8NoBom.GetBytes($body)

    $httpClient = $null
    $httpContent = $null
    $httpResult = $null
    $httpClient = New-Object System.Net.Http.HttpClient
    try {
        $httpContent = New-Object System.Net.Http.ByteArrayContent(,$bodyBytes)
        $httpContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("application/json; charset=utf-8")

        $httpResult = $httpClient.PostAsync($ApiUrl, $httpContent).GetAwaiter().GetResult()
        $respBytes = $httpResult.Content.ReadAsByteArrayAsync().GetAwaiter().GetResult()
        $respText = [System.Text.Encoding]::UTF8.GetString($respBytes)

        if (-not $httpResult.IsSuccessStatusCode) {
            throw "HTTP $([int]$httpResult.StatusCode): $respText"
        }

        $response = $respText | ConvertFrom-Json
    }
    finally {
        if ($httpContent) { $httpContent.Dispose() }
        if ($httpResult) { $httpResult.Dispose() }
        if ($httpClient) { $httpClient.Dispose() }
    }

    if ($null -eq $response) {
        throw "Empty response from /ask"
    }

    $json = $response | ConvertTo-Json -Depth 100

    $outDir = Split-Path -Parent $outputPath
    if (-not (Test-Path $outDir)) {
        New-Item -ItemType Directory -Path $outDir | Out-Null
    }

    # Atomic write to avoid leaving a zero-byte file when any later step fails.
    [System.IO.File]::WriteAllText($tmpPath, $json, $utf8NoBom)
    Move-Item -Path $tmpPath -Destination $outputPath -Force

    Write-Host "saved_output: $outputPath"
    Write-Host "session_id: $SessionId"
    Write-Host "needs_clarification: $($response.needs_clarification)"
    Write-Host "evaluation_log.final_status: $($response.evaluation_log.final_status)"

    $artifact = Get-Content -Path $outputPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $selectedRuleId = $artifact.selected_rule.rule_id

    if ($selectedRuleId) {
        Write-Host "selected_rule.rule_id: $selectedRuleId"
    }

    $debugTrace = $artifact.debug_trace
    $selectedTier = $null
    $verificationNode = Get-ObjectPropertyValue -Object $debugTrace -Name "verification"
    $candidateVerdicts = Get-ObjectPropertyValue -Object $verificationNode -Name "candidate_verdicts"
    $ruleBackwardGateRerun = Get-ObjectPropertyValue -Object $debugTrace -Name "rule_backward_gate_rerun"
    $ruleBackwardGate = Get-ObjectPropertyValue -Object $debugTrace -Name "rule_backward_gate"
    $verificationDiagnostics = Get-ObjectPropertyValue -Object $debugTrace -Name "verification_diagnostics"
    $forwardGate = Get-ObjectPropertyValue -Object $debugTrace -Name "forward_gate"
    $forwardTrace = Get-ObjectPropertyValue -Object $verificationNode -Name "forward_trace"

    if (-not $selectedTier -and $candidateVerdicts -and $selectedRuleId) {
        $selectedVerdict = $candidateVerdicts.$selectedRuleId
        if ($selectedVerdict) {
            $selectedTier = $selectedVerdict.semantic_family_match_tier
        }
    }

    if (-not $selectedTier -and $ruleBackwardGateRerun) {
        $tierMatch = @(
            $ruleBackwardGateRerun |
                Where-Object {
                    (Get-ObjectPropertyValue -Object $_ -Name "rule_id") -eq $selectedRuleId -and
                    (Get-ObjectPropertyValue -Object $_ -Name "semantic_family_match_tier")
                }
        ) | Select-Object -First 1
        if ($tierMatch) {
            $selectedTier = Get-ObjectPropertyValue -Object $tierMatch -Name "semantic_family_match_tier"
        }
    }

    if (-not $selectedTier -and $ruleBackwardGate) {
        $tierMatch = @(
            $ruleBackwardGate |
                Where-Object {
                    (Get-ObjectPropertyValue -Object $_ -Name "rule_id") -eq $selectedRuleId -and
                    (Get-ObjectPropertyValue -Object $_ -Name "semantic_family_match_tier")
                }
        ) | Select-Object -First 1
        if ($tierMatch) {
            $selectedTier = Get-ObjectPropertyValue -Object $tierMatch -Name "semantic_family_match_tier"
        }
    }

    if (-not $selectedTier -and $verificationDiagnostics) {
        $tierMatch = @(
            $verificationDiagnostics |
                Where-Object {
                    (Get-ObjectPropertyValue -Object $_ -Name "rule_id") -eq $selectedRuleId -and
                    (Get-ObjectPropertyValue -Object $_ -Name "semantic_family_match_tier")
                }
        ) | Select-Object -First 1
        if ($tierMatch) {
            $selectedTier = Get-ObjectPropertyValue -Object $tierMatch -Name "semantic_family_match_tier"
        }
    }

    if (-not $selectedTier) {
        $selectedTier = "missing"
    }

    $reorderEvent = $null
    if ($ruleBackwardGateRerun) {
        $reorderEvent = @(
            $ruleBackwardGateRerun |
                Where-Object {
                    (Get-ObjectPropertyValue -Object $_ -Name "stage") -eq "candidate_semantic_priority_reorder"
                }
        ) | Select-Object -First 1
    }
    if (-not $reorderEvent -and $ruleBackwardGate) {
        $reorderEvent = @(
            $ruleBackwardGate |
                Where-Object {
                    (Get-ObjectPropertyValue -Object $_ -Name "stage") -eq "candidate_semantic_priority_reorder"
                }
        ) | Select-Object -First 1
    }

    $originalIds = "missing"
    $reorderedIds = "missing"
    if ($reorderEvent) {
        if ($reorderEvent.original_ids) {
            $originalIds = $reorderEvent.original_ids | ConvertTo-Json -Compress
        }
        if ($reorderEvent.reordered_ids) {
            $reorderedIds = $reorderEvent.reordered_ids | ConvertTo-Json -Compress
        }
    }

    $forwardRelax = $null
    if ($forwardGate) {
        $forwardEvent = @(
            $forwardGate |
                Where-Object {
                    (Get-ObjectPropertyValue -Object $_ -Name "forward_soft_match_relaxation_triggered") -ne $null -or
                    (Get-ObjectPropertyValue -Object $_ -Name "stage") -eq "partial_forward_soft_match"
                }
        ) | Select-Object -First 1
        if ($forwardEvent) {
            $forwardRelax = Get-ObjectPropertyValue -Object $forwardEvent -Name "forward_soft_match_relaxation_triggered"
        }
    }
    if ($null -eq $forwardRelax -and $forwardTrace) {
        $forwardRelax = $forwardTrace.forward_soft_match_relaxation_triggered
    }
    if ($null -eq $forwardRelax) {
        $forwardRelax = "missing"
    }

    Write-Host "selected_semantic_tier: $selectedTier"
    Write-Host "semantic_reorder.original_ids: $originalIds"
    Write-Host "semantic_reorder.reordered_ids: $reorderedIds"
    Write-Host "forward_soft_match_relaxation_triggered: $forwardRelax"
}
catch {
    if (Test-Path $tmpPath) {
        Remove-Item -Path $tmpPath -Force -ErrorAction SilentlyContinue
    }
    Write-Error "run_test.ps1 failed: $($_.Exception.Message)"
    exit 1
}
