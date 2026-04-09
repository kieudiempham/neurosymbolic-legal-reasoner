$ErrorActionPreference = 'Stop'

$baseUrl = 'http://localhost:8001'
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$outDir = 'data/processed/evaluation'
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

$rawJsonl = Join-Path $outDir "uat_backend_10q_raw_$ts.jsonl"
$finalRespJsonl = Join-Path $outDir "uat_backend_10q_final_responses_$ts.jsonl"
$summaryCsv = Join-Path $outDir "uat_backend_10q_summary_$ts.csv"
$reportJson = Join-Path $outDir "uat_backend_10q_report_$ts.json"

$questionsPath = 'data/processed/evaluation/uat_10q_questions.json'
$questions = Get-Content -Raw -Path $questionsPath -Encoding UTF8 | ConvertFrom-Json

function Get-ClarificationValue {
    param(
        [string]$FactKey,
        [string]$ExpectedType,
        [object[]]$Options,
        [string]$QuestionText
    )

    $k = ($FactKey | ForEach-Object { $_.ToLowerInvariant() })
    $q = ($QuestionText | ForEach-Object { $_.ToLowerInvariant() })

    if ($Options -and $Options.Count -gt 0) {
        return $Options[0]
    }

    if ($k -match 'company|loai_hinh|loaihinh|tnhh') { return 'tnhh_mot_thanh_vien' }
    if ($k -match 'vat|gtgt|thue|doanh_thu|khai') { return $true }
    if ($k -match 'lao_dong|hop_dong|overtime|lam_them|nguoi_lao_dong') { return $true }
    if ($k -match 'nguoi_dai_dien|dai_dien') { return $true }

    if ($q -match 'có|không') { return $true }

    if ($ExpectedType -eq 'bool') { return $true }
    if ($ExpectedType -eq 'number') { return 1 }
    return 'có'
}

function Write-JsonlLine {
    param([string]$Path, [object]$Obj)
    $json = $Obj | ConvertTo-Json -Depth 50 -Compress
    Add-Content -Path $Path -Value $json -Encoding UTF8
}

function Get-TopRuleId {
    param([object]$SelectedRule)
    if ($null -eq $SelectedRule) { return $null }
    if ($SelectedRule.PSObject.Properties.Name -contains 'rule_id') { return $SelectedRule.rule_id }
    if ($SelectedRule.PSObject.Properties.Name -contains 'id') { return $SelectedRule.id }
    return $null
}

$rows = @()
$rawRecords = @()
$finalResponses = @()

for ($i = 0; $i -lt $questions.Count; $i++) {
    $qid = $i + 1
    $question = $questions[$i]
    $requestedSessionId = ('uat_10q_{0}_{1:d2}' -f (Get-Date -Format 'yyyyMMdd'), $qid)
    $sessionId = $requestedSessionId

    $askPayload = @{
        question = $question
        session_id = $requestedSessionId
        use_router = $true
    }

    $askStatusCode = $null
    $askResp = $null
    $askErr = $null

    try {
        $askJson = $askPayload | ConvertTo-Json -Depth 20
        $askHttp = Invoke-WebRequest -Uri "$baseUrl/ask" -Method POST -ContentType 'application/json; charset=utf-8' -Body $askJson -TimeoutSec 120
        $askStatusCode = [int]$askHttp.StatusCode
        $askResp = $askHttp.Content | ConvertFrom-Json
        if ($askResp -and $askResp.session_id) {
            # /clarify must use the canonical session id returned by /ask.
            $sessionId = [string]$askResp.session_id
        }
    }
    catch {
        if ($_.Exception.Response) {
            $askStatusCode = [int]$_.Exception.Response.StatusCode.value__
        }
        else {
            $askStatusCode = -1
        }
        $askErr = $_.Exception.Message
    }

    $clarifyStatusCode = $null
    $clarifyResp = $null
    $clarifyErr = $null
    $clarificationAnswers = @()

    if ($askResp -and $askResp.needs_clarification -eq $true -and $askResp.clarification_questions -and $askResp.clarification_questions.Count -gt 0) {
        foreach ($cq in $askResp.clarification_questions) {
            $val = Get-ClarificationValue -FactKey $cq.fact_key -ExpectedType $cq.expected_type -Options $cq.options -QuestionText $cq.question_text
            $clarificationAnswers += @{ fact_key = $cq.fact_key; value = $val }
        }

        $clarifyPayload = @{ session_id = $sessionId; answers = $clarificationAnswers }
        try {
            $clarifyJson = $clarifyPayload | ConvertTo-Json -Depth 20
            $clarifyHttp = Invoke-WebRequest -Uri "$baseUrl/clarify" -Method POST -ContentType 'application/json; charset=utf-8' -Body $clarifyJson -TimeoutSec 120
            $clarifyStatusCode = [int]$clarifyHttp.StatusCode
            $clarifyResp = $clarifyHttp.Content | ConvertFrom-Json
        }
        catch {
            if ($_.Exception.Response) {
                $clarifyStatusCode = [int]$_.Exception.Response.StatusCode.value__
            }
            else {
                $clarifyStatusCode = -1
            }
            $clarifyErr = $_.Exception.Message
        }
    }

    $finalResp = if ($clarifyResp) { $clarifyResp } else { $askResp }
    $evalLog = if ($finalResp) { $finalResp.evaluation_log } else { $null }
    $askEval = if ($askResp) { $askResp.evaluation_log } else { $null }

    $finalStatus = if ($evalLog -and $evalLog.final_status) { $evalLog.final_status } else { $null }
    $finalAnswer = $null
    if ($evalLog -and $evalLog.final_answer) { $finalAnswer = $evalLog.final_answer }
    elseif ($finalResp -and $finalResp.answer -and $finalResp.answer.answer_text) { $finalAnswer = $finalResp.answer.answer_text }

    $needsClarification = if ($finalResp) { [bool]$finalResp.needs_clarification } else { $false }
    $clarificationQuestion = $null
    if ($askEval -and $askEval.clarification_question) { $clarificationQuestion = $askEval.clarification_question }
    elseif ($askResp -and $askResp.clarification_questions) { $clarificationQuestion = $askResp.clarification_questions }

    $predictedDomains = if ($evalLog) { $evalLog.predicted_domains } else { $null }
    $activatedDomains = if ($evalLog) { $evalLog.activated_domains } else { $null }
    $selectedRule = if ($evalLog) { $evalLog.selected_rule } else { $null }
    $selectedRuleId = Get-TopRuleId -SelectedRule $selectedRule
    $proofPresent = $false
    if ($evalLog -and $evalLog.proof) { $proofPresent = $true }
    $errorStageFinal = if ($evalLog) { $evalLog.error_stage_final } else { $null }
    $backendModes = if ($evalLog) { $evalLog.backend_modes } else { $null }

    $group = 'PASS'
    $hasCrash = ($askStatusCode -ne 200) -or (($clarifyStatusCode -ne $null) -and ($clarifyStatusCode -ne 200))
    $hasHardFail = $finalStatus -in @('failed', 'open')
    if ($hasCrash -or $hasHardFail) {
        $group = 'MUST FIX BEFORE FE'
    }
    elseif ([string]::IsNullOrWhiteSpace([string]$finalAnswer) -or $selectedRuleId -eq $null -or -not $proofPresent -or $errorStageFinal) {
        $group = 'PASS BUT NOISY'
    }

    $row = [ordered]@{
        qid = $qid
        question = $question
        ask_status_code = $askStatusCode
        clarify_status_code = $clarifyStatusCode
        final_status = $finalStatus
        final_answer = $finalAnswer
        needs_clarification = $needsClarification
        clarification_question = if ($clarificationQuestion) { $clarificationQuestion | ConvertTo-Json -Depth 20 -Compress } else { $null }
        predicted_domains = if ($predictedDomains) { ($predictedDomains -join '|') } else { $null }
        activated_domains = if ($activatedDomains) { ($activatedDomains -join '|') } else { $null }
        selected_rule = $selectedRuleId
        proof_present = $proofPresent
        error_stage_final = $errorStageFinal
        backend_modes = if ($backendModes) { $backendModes | ConvertTo-Json -Depth 20 -Compress } else { $null }
        group = $group
        clarification_answer = if ($clarificationAnswers.Count -gt 0) { $clarificationAnswers | ConvertTo-Json -Depth 20 -Compress } else { $null }
        pre_clarification_status = if ($askEval) { $askEval.final_status } else { $null }
        post_clarification_status = if ($evalLog) { $evalLog.final_status } else { $null }
        raw_session_id = $sessionId
        requested_session_id = $requestedSessionId
        ask_error = $askErr
        clarify_error = $clarifyErr
    }

    $rawObj = [ordered]@{
        qid = $qid
        question = $question
        session_id = $sessionId
        requested_session_id = $requestedSessionId
        ask_status_code = $askStatusCode
        ask_response = $askResp
        clarify_status_code = $clarifyStatusCode
        clarify_request_answers = $clarificationAnswers
        clarify_response = $clarifyResp
        final_row = $row
    }

    $rows += [pscustomobject]$row
    $rawRecords += $rawObj

    if ($finalResp) {
        $finalResponses += $finalResp
        Write-JsonlLine -Path $finalRespJsonl -Obj $finalResp
    }

    Write-JsonlLine -Path $rawJsonl -Obj $rawObj

    Write-Output ("[{0}/10] qid={1} ask={2} clarify={3} final_status={4} group={5}" -f ($qid), $qid, $askStatusCode, $clarifyStatusCode, $finalStatus, $group)
}

$rows | Export-Csv -Path $summaryCsv -NoTypeInformation -Encoding UTF8

$mustFix = @($rows | Where-Object { $_.group -eq 'MUST FIX BEFORE FE' })
$noisy = @($rows | Where-Object { $_.group -eq 'PASS BUT NOISY' })
$pass = @($rows | Where-Object { $_.group -eq 'PASS' })

$issues = @()
foreach ($r in $rows) {
    if (($r.ask_status_code -ne 200) -or (($r.clarify_status_code -ne $null) -and ($r.clarify_status_code -ne 200))) {
        $issues += "HTTP_ERROR:q$($r.qid)"
    }
    if ($r.error_stage_final) {
        $issues += "ERROR_STAGE:q$($r.qid):$($r.error_stage_final)"
    }
    if (($r.final_status -in @('failed', 'open')) -and -not [string]::IsNullOrWhiteSpace($r.final_status)) {
        $issues += "FINAL_STATUS_BAD:q$($r.qid):$($r.final_status)"
    }
    if ([string]::IsNullOrWhiteSpace([string]$r.selected_rule) -and ($r.final_status -eq 'answered')) {
        $issues += "SELECTED_RULE_NULL_ON_ANSWERED:q$($r.qid)"
    }
    if (($r.proof_present -eq $false) -and ($r.final_status -eq 'answered')) {
        $issues += "PROOF_NULL_ON_ANSWERED:q$($r.qid)"
    }
}

$report = [ordered]@{
    generated_at = (Get-Date).ToString('s')
    raw_jsonl = $rawJsonl
    final_response_jsonl = $finalRespJsonl
    summary_csv = $summaryCsv
    counts = [ordered]@{
        total = $rows.Count
        pass = $pass.Count
        pass_but_noisy = $noisy.Count
        must_fix_before_fe = $mustFix.Count
    }
    top_issues = @($issues | Select-Object -Unique | Select-Object -First 5)
    rows = $rows
}

$report | ConvertTo-Json -Depth 50 | Set-Content -Path $reportJson -Encoding UTF8

Write-Output "RAW_JSONL=$rawJsonl"
Write-Output "FINAL_RESPONSE_JSONL=$finalRespJsonl"
Write-Output "SUMMARY_CSV=$summaryCsv"
Write-Output "REPORT_JSON=$reportJson"
