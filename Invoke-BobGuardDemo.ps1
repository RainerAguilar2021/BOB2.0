<#
.SYNOPSIS
    BobGuard MVP - Master Orchestration Script
    Runs all phases end-to-end and produces a final verdict.

.DESCRIPTION
    Phase 1: Unit tests with bug present  (suite=Unit)
    Phase 2: Regression test with bug present  -> expected FAIL
    Phase 3: Apply fix
    Phase 4: Regression + full suite after fix  -> must PASS
    Phase 5: Policy filter tests
    Phase 6: Policy filter on raw report -> produce sanitized report
    Phase 7: Release readiness check
    Phase 8: Print final summary

    IMPORTANT: This script MODIFIES app/Invoke-Calculator.ps1 (applies the fix).
    Run from the workspace root.

    NOTE: For demo purposes the fix is already applied. The script detects this
    and skips the apply step, running the full pre-fix sequence using a temporary
    copy of the buggy source instead.
#>
param(
    [switch] $DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root         = $PSScriptRoot
$appFile      = Join-Path $root "app\Invoke-Calculator.ps1"
$testScript   = Join-Path $root "tests\Invoke-Tests.ps1"
$filterTests  = Join-Path $root "bobguard\policy-filter\Invoke-PolicyFilter.Tests.ps1"
$filter       = Join-Path $root "bobguard\policy-filter\Invoke-PolicyFilter.ps1"
$releaseCheck = Join-Path $root "bobguard\release-check\Invoke-ReleaseCheck.ps1"
$rawReport    = Join-Path $root "bobguard\reports\raw-report.md"
$sanitized    = Join-Path $root "bobguard\reports\sanitized-report.md"
$sanitizedFinal = Join-Path $root "bobguard\reports\sanitized-report-final.md"
$policySummary  = Join-Path $root "bobguard\reports\policy-summary.json"
$policySummaryFinal = Join-Path $root "bobguard\reports\policy-summary-final.json"
$testResults  = Join-Path $root "bobguard\test-results.json"
$incidentFile = Join-Path $root "incidents\INC-001\incident.md"
$verdictFile  = Join-Path $root "bobguard\reports\release-verdict.json"
$logFile      = Join-Path $root "bobguard\reports\run-log.txt"

New-Item -ItemType Directory -Force -Path (Join-Path $root "bobguard\reports") | Out-Null

$log = [System.Collections.Generic.List[string]]::new()
function Log {
    param([string]$msg)
    $ts   = Get-Date -Format "HH:mm:ss"
    $line = "[$ts] $msg"
    $log.Add($line)
    Write-Host $line
}

function Run-PS {
    param([string]$file, [string[]]$extraArgs = @())
    $argList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $file) + $extraArgs
    $proc = Start-Process powershell.exe `
        -ArgumentList $argList `
        -Wait -PassThru -NoNewWindow
    return $proc.ExitCode
}

Log "===== BobGuard MVP - End-to-End Run ====="

# Detect whether fix is already applied
$appContent = Get-Content $appFile -Raw
$bugPresent = $appContent -match '\[int\]\(\$Count / \$PageSize\)'
$fixPresent = $appContent -match '\[Math\]::Ceiling'

if ($fixPresent -and -not $bugPresent) {
    Log "INFO: Fix already applied. Creating temporary buggy copy for pre-fix phases."
    $tempApp = Join-Path $root "app\Invoke-Calculator-buggy-temp.ps1"
    $buggyContent = $appContent -replace '\[Math\]::Ceiling\(\$Count / \$PageSize\)', '[int]($Count / $PageSize)'
    Set-Content -Path $tempApp -Value $buggyContent -Encoding UTF8
    $usingTemp = $true
} else {
    $tempApp   = $appFile
    $usingTemp = $false
}

# Phase 1: Unit tests with bug present (pass expected)
Log ">> Phase 1: Unit tests (bug present)"
if ($DryRun) { Log "   [DRY-RUN]"; $p1 = 0 } else {
    if ($usingTemp) {
        $origContent = Get-Content $appFile -Raw
        Set-Content -Path $appFile -Value $buggyContent -Encoding UTF8
        $p1 = Run-PS $testScript @("-Suite", "Unit")
        Set-Content -Path $appFile -Value $origContent -Encoding UTF8
    } else {
        $p1 = Run-PS $testScript @("-Suite", "Unit")
    }
}
Log "   Phase 1 result: exit=$p1 (expected 0)"

# Phase 2: Regression test with bug present (fail expected)
Log ">> Phase 2: Regression test (bug present - expected FAIL)"
if ($DryRun) { Log "   [DRY-RUN]"; $p2 = 1 } else {
    if ($usingTemp) {
        $origContent = Get-Content $appFile -Raw
        Set-Content -Path $appFile -Value $buggyContent -Encoding UTF8
        $p2 = Run-PS $testScript @("-Suite", "Regression")
        Set-Content -Path $appFile -Value $origContent -Encoding UTF8
    } else {
        $p2 = Run-PS $testScript @("-Suite", "Regression")
    }
}
Log "   Phase 2 result: exit=$p2 (expected 1 - confirmed bug)"

# Phase 3: Ensure fix is applied
Log ">> Phase 3: Apply fix"
if ($DryRun) { Log "   [DRY-RUN]"; $p3 = 0 } else {
    $current = Get-Content $appFile -Raw
    if ($current -match '\[int\]\(\$Count / \$PageSize\)') {
        $fixed = $current -replace '\[int\]\(\$Count / \$PageSize\)', '[Math]::Ceiling($Count / $PageSize)'
        Set-Content -Path $appFile -Value $fixed -Encoding UTF8
        Log "   Fix applied."
        $p3 = 0
    } elseif ($current -match '\[Math\]::Ceiling') {
        Log "   Fix already present - no change needed."
        $p3 = 0
    } else {
        Log "   [ERROR] Could not locate bug pattern."
        $p3 = 1
    }
}
Log "   Phase 3 result: exit=$p3 (expected 0)"

# Phase 4a: Regression after fix (must pass)
Log ">> Phase 4a: Regression test (after fix - must PASS)"
if ($DryRun) { Log "   [DRY-RUN]"; $p4a = 0 } else { $p4a = Run-PS $testScript @("-Suite", "Regression") }
Log "   Phase 4a result: exit=$p4a (expected 0)"

# Phase 4b: Full suite after fix (must pass)
Log ">> Phase 4b: Full test suite (after fix - must PASS)"
if ($DryRun) { Log "   [DRY-RUN]"; $p4b = 0 } else { $p4b = Run-PS $testScript @("-Suite", "All") }
Log "   Phase 4b result: exit=$p4b (expected 0)"

# Phase 5: Policy filter unit tests
Log ">> Phase 5: Policy filter unit tests"
if ($DryRun) { Log "   [DRY-RUN]"; $p5 = 0 } else { $p5 = Run-PS $filterTests @() }
Log "   Phase 5 result: exit=$p5 (expected 0)"

# Phase 6: Filter raw report
Log ">> Phase 6: Policy filter on raw-report.md"
if ($DryRun) { Log "   [DRY-RUN]"; $p6 = 2 } else {
    $p6 = Run-PS $filter @("-InputPath", $rawReport, "-OutputPath", $sanitized, "-SummaryPath", $policySummary)
    # Re-filter sanitized output -> final clean report
    Run-PS $filter @("-InputPath", $sanitized, "-OutputPath", $sanitizedFinal, "-SummaryPath", $policySummaryFinal) | Out-Null
}
Log "   Phase 6 result: exit=$p6 (0=clean, 2=redacted)"

# Phase 7: Release readiness check
Log ">> Phase 7: Release readiness check"
if ($DryRun) { Log "   [DRY-RUN]"; $p7 = 0 } else {
    $p7 = Run-PS $releaseCheck @("-SanitizedReportPath", $sanitizedFinal, "-PolicySummaryPath", $policySummaryFinal, "-TestResultsPath", $testResults, "-IncidentPath", $incidentFile, "-OutputPath", $verdictFile)
}
Log "   Phase 7 result: exit=$p7 (0=APPROVED, 1=BLOCKED)"

# Cleanup temp if used
if ($usingTemp -and (Test-Path $tempApp)) {
    Remove-Item $tempApp -ErrorAction SilentlyContinue
}

# Save run log
$log | Set-Content -Path $logFile -Encoding UTF8
Log "   Run log saved to: $logFile"

$allPass = ($p1 -eq 0) -and ($p2 -eq 1) -and ($p3 -eq 0) -and ($p4a -eq 0) -and ($p4b -eq 0) -and ($p5 -eq 0) -and ($p7 -eq 0)

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host " BobGuard MVP - Final Results" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
$c = { param($ok) if ($ok) {"Green"} else {"Red"} }
Write-Host (" Phase 1  - Unit tests with bug:             exit=$p1  (expected 0)") -ForegroundColor (& $c ($p1 -eq 0))
Write-Host (" Phase 2  - Regression test with bug:        exit=$p2  (expected 1)") -ForegroundColor (& $c ($p2 -eq 1))
Write-Host (" Phase 3  - Fix applied:                     exit=$p3  (expected 0)") -ForegroundColor (& $c ($p3 -eq 0))
Write-Host (" Phase 4a - Regression after fix:            exit=$p4a (expected 0)") -ForegroundColor (& $c ($p4a -eq 0))
Write-Host (" Phase 4b - Full suite after fix:            exit=$p4b (expected 0)") -ForegroundColor (& $c ($p4b -eq 0))
Write-Host (" Phase 5  - Policy filter tests:             exit=$p5  (expected 0)") -ForegroundColor (& $c ($p5 -eq 0))
Write-Host (" Phase 6  - Filter raw report:               exit=$p6  (0=clean, 2=redacted)") -ForegroundColor (& $c ($p6 -in 0,2))
Write-Host (" Phase 7  - Release readiness:               exit=$p7  (expected 0=APPROVED)") -ForegroundColor (& $c ($p7 -eq 0))
Write-Host ""
if ($allPass) {
    Write-Host " MVP VERIFIED" -ForegroundColor Green
} else {
    Write-Host " MVP BLOCKED - review phases with errors" -ForegroundColor Red
}
Write-Host "============================================================" -ForegroundColor Cyan
