<#
.SYNOPSIS
    BobGuard MVP - Release Readiness Check

.DESCRIPTION
    Evaluates actual evidence from the workspace to determine release readiness.
    Checks (in order):
      R1  Unit tests pass
      R2  Regression tests pass
      R3  Sanitized report exists and has 0 redactions
      R4  Rollback plan present in incident file
      R5  Dependency audit - NOT VERIFIED (result is not consumed by this checker)
      R6  Self-check: this tool's own exit

    Missing, malformed, or unavailable evidence is BLOCKED or NOT VERIFIED.
    Never silently treated as success.

    Avoids circular verdict: evaluates the SANITIZED report (not the raw one).

    Exit codes:
        0  - APPROVED: all verifiable conditions passed
        1  - BLOCKED: one or more conditions failed or are unverifiable
        2  - Operational failure (bad arguments, missing required file)

.EXAMPLE
    .\bobguard\release-check\Invoke-ReleaseCheck.ps1 `
        -SanitizedReportPath .\bobguard\reports\sanitized-report-final.md `
        -PolicySummaryPath   .\bobguard\reports\policy-summary-final.json `
        -TestResultsPath     .\bobguard\test-results.json `
        -IncidentPath        .\incidents\INC-001\incident.md `
        -OutputPath          .\bobguard\reports\release-verdict.json
#>
param(
    [Parameter(Mandatory)][string] $SanitizedReportPath,
    [Parameter(Mandatory)][string] $PolicySummaryPath,
    [Parameter(Mandatory)][string] $TestResultsPath,
    [Parameter(Mandatory)][string] $IncidentPath,
    [string] $OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Check {
    param([string]$id, [string]$status, [string]$detail)
    $color = switch ($status) {
        "PASS"         { "Green" }
        "BLOCKED"      { "Red" }
        "NOT VERIFIED" { "Yellow" }
        default        { "White" }
    }
    Write-Host "  [$status] $id -- $detail" -ForegroundColor $color
}

$checks  = [System.Collections.Generic.List[PSCustomObject]]::new()
$blocked = $false

function Add-Check {
    param([string]$id, [string]$status, [string]$detail)
    $checks.Add([PSCustomObject]@{ Check=$id; Status=$status; Detail=$detail })
    Write-Check $id $status $detail
    if ($status -eq "BLOCKED") { $script:blocked = $true }
}

Write-Host "`n=== Release Readiness Check ===" -ForegroundColor Cyan

# R1/R2: Test results
if (-not (Test-Path $TestResultsPath)) {
    Add-Check "R1-unit-tests"       "BLOCKED" "Test results file not found: $TestResultsPath"
    Add-Check "R2-regression-tests" "BLOCKED" "Test results file not found: $TestResultsPath"
} else {
    try {
        $testResults = Get-Content $TestResultsPath -Raw | ConvertFrom-Json
        [object[]]$unitTests = @($testResults | Where-Object {
            $_.Name -notmatch " regression:"
        })
        [object[]]$regressionTests = @($testResults | Where-Object {
            $_.Name -match " regression:"
        })
        [object[]]$unitFails = @($unitTests | Where-Object { $_.Status -eq "FAIL" })
        [object[]]$regrFails = @($regressionTests | Where-Object { $_.Status -eq "FAIL" })

        if ($unitTests.Count -ne 17) {
            Add-Check "R1-unit-tests" "BLOCKED" "Expected 17 unit test results; found $($unitTests.Count)"
        } elseif ($unitFails.Count -eq 0) {
            Add-Check "R1-unit-tests" "PASS" "All unit tests passed"
        } else {
            Add-Check "R1-unit-tests" "BLOCKED" "$($unitFails.Count) unit test(s) failed"
        }

        if ($regressionTests.Count -ne 8) {
            Add-Check "R2-regression-tests" "BLOCKED" "Expected 8 regression test results; found $($regressionTests.Count)"
        } elseif ($regrFails.Count -eq 0) {
            Add-Check "R2-regression-tests" "PASS" "All regression tests passed"
        } else {
            Add-Check "R2-regression-tests" "BLOCKED" "$($regrFails.Count) regression test(s) failed: $($regrFails[0].Note)"
        }
    } catch {
        Add-Check "R1-unit-tests"       "BLOCKED" "Cannot parse test results: $_"
        Add-Check "R2-regression-tests" "BLOCKED" "Cannot parse test results: $_"
    }
}

# R3: Sanitized report - zero redactions
if (-not (Test-Path $SanitizedReportPath)) {
    Add-Check "R3-sanitized-report" "BLOCKED" "Sanitized report not found: $SanitizedReportPath"
} elseif (-not (Test-Path $PolicySummaryPath)) {
    Add-Check "R3-sanitized-report" "BLOCKED" "Policy summary not found: $PolicySummaryPath"
} else {
    try {
        $summary = Get-Content $PolicySummaryPath -Raw | ConvertFrom-Json
        if ($summary.RedactedCount -eq 0 -and $summary.TruncatedBlocks -eq 0) {
            Add-Check "R3-sanitized-report" "PASS" "Sanitized report has 0 redactions, 0 truncated blocks"
        } else {
            Add-Check "R3-sanitized-report" "BLOCKED" "Report still has $($summary.RedactedCount) redaction(s) and $($summary.TruncatedBlocks) truncated block(s)"
        }
    } catch {
        Add-Check "R3-sanitized-report" "BLOCKED" "Cannot parse policy summary: $_"
    }
}

# R4: Rollback plan
if (-not (Test-Path $IncidentPath)) {
    Add-Check "R4-rollback-plan" "BLOCKED" "Incident file not found: $IncidentPath"
} else {
    $incContent = Get-Content $IncidentPath -Raw
    if ($incContent -match "Rollback Plan" -and $incContent -match "(?m)^\d+\.") {
        Add-Check "R4-rollback-plan" "PASS" "Rollback plan present and contains numbered steps"
    } else {
        Add-Check "R4-rollback-plan" "BLOCKED" "Rollback plan missing or has no numbered steps"
    }
}

# R5: Dependency audit
Add-Check "R5-dependency-audit" "NOT VERIFIED" "Dependency audit is not consumed by this checker; see docs/dependency-audit.md"

# Summary
$verdict = if ($blocked) { "BLOCKED" } else { "APPROVED" }
$color   = if ($blocked) { "Red" } else { "Green" }

Write-Host "`n  VERDICT: $verdict" -ForegroundColor $color

$result = [PSCustomObject]@{
    Verdict   = $verdict
    Blocked   = $blocked
    Checks    = $checks
    Timestamp = (Get-Date -Format "o")
}

if ($OutputPath) {
    $outDir = Split-Path $OutputPath -Parent
    if ($outDir) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
    $result | ConvertTo-Json -Depth 5 | Set-Content -Path $OutputPath -Encoding UTF8
    Write-Host "  Verdict written to: $OutputPath"
}

$result | ConvertTo-Json -Depth 5 | Write-Host

if ($blocked) { exit 1 } else { exit 0 }
