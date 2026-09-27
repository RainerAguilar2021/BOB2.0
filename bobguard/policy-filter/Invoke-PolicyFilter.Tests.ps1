<#
.SYNOPSIS
    BobGuard MVP - Policy Filter Unit Tests

.DESCRIPTION
    Tests:
      T1   Clean input -> exit 0, zero redactions
      T2   Synthetic API key -> exit 2, redacted
      T3   Synthetic DB password -> exit 2, redacted
      T4   Synthetic bearer token -> exit 2, redacted
      T5   Long code block -> exit 2, truncated
      T6   Short code block -> exit 0, not truncated
      T7a  Mixed input: API key -> exit 2, redacted
      T7b  Mixed input: long code block -> exit 2, truncated
      T8   Missing input file -> exit 1 (operational error)

    Exit codes:
        0  - all tests passed
        1  - one or more tests failed
#>
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$filterScript = Join-Path $PSScriptRoot "..\policy-filter\Invoke-PolicyFilter.ps1"
$tmpDir       = Join-Path $env:TEMP ("bobguard-filter-tests-" + [System.IO.Path]::GetRandomFileName())
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

$passed = 0; $failed = 0

function Assert-FilterTest {
    param(
        [string] $Name,
        [string] $InputContent,
        [int]    $ExpectedExit,
        [string] $MustContain    = "",
        [string] $MustNotContain = "",
        [int]    $ExpectedRedacted = -1
    )
    $inFile  = Join-Path $tmpDir "in-$Name.md"
    $outFile = Join-Path $tmpDir "out-$Name.md"
    $sumFile = Join-Path $tmpDir "sum-$Name.json"
    Set-Content -Path $inFile -Value $InputContent -Encoding UTF8

    $proc = Start-Process powershell.exe `
        -ArgumentList ("-NoProfile -ExecutionPolicy Bypass -File `"" + $filterScript + "`" -InputPath `"" + $inFile + "`" -OutputPath `"" + $outFile + "`" -SummaryPath `"" + $sumFile + "`"") `
        -Wait -PassThru -NoNewWindow
    $actualExit = $proc.ExitCode

    $issues = @()
    if ($actualExit -ne $ExpectedExit) {
        $issues += "Exit=$actualExit (expected $ExpectedExit)"
    }
    if ($MustContain -and (Test-Path $outFile)) {
        $out = Get-Content $outFile -Raw
        if ($out -notmatch [regex]::Escape($MustContain)) {
            $issues += "Output missing: '$MustContain'"
        }
    }
    if ($MustNotContain -and (Test-Path $outFile)) {
        $out = Get-Content $outFile -Raw
        if ($out -match [regex]::Escape($MustNotContain)) {
            $issues += "Output still contains: '$MustNotContain'"
        }
    }
    if ($ExpectedRedacted -ge 0 -and (Test-Path $sumFile)) {
        $sum = Get-Content $sumFile -Raw | ConvertFrom-Json
        if ($sum.RedactedCount -ne $ExpectedRedacted) {
            $issues += "RedactedCount=$($sum.RedactedCount) (expected $ExpectedRedacted)"
        }
    }

    if ($issues.Count -eq 0) {
        $script:passed++
        Write-Host "  [PASS] $Name" -ForegroundColor Green
    } else {
        $script:failed++
        Write-Host "  [FAIL] $Name -- $($issues -join '; ')" -ForegroundColor Red
    }
}

Write-Host "`n=== Policy Filter Unit Tests ===" -ForegroundColor Cyan

# T1 - Clean input
Assert-FilterTest `
    -Name "T1-clean" `
    -InputContent "# Report`nThis report has no secrets." `
    -ExpectedExit 0 `
    -ExpectedRedacted 0

# T2 - API key
Assert-FilterTest `
    -Name "T2-api-key" `
    -InputContent "Key: BOBGUARD-KEY-ABCDEF1234567890`nEnd." `
    -ExpectedExit 2 `
    -MustContain "[REDACTED:API-KEY]" `
    -MustNotContain "BOBGUARD-KEY-ABCDEF1234567890" `
    -ExpectedRedacted 1

# T3 - DB password
Assert-FilterTest `
    -Name "T3-db-password" `
    -InputContent "Config: db_password=SuperSecret99`nOther." `
    -ExpectedExit 2 `
    -MustContain "[REDACTED:PASSWORD]" `
    -MustNotContain "SuperSecret99" `
    -ExpectedRedacted 1

# T4 - Bearer token
Assert-FilterTest `
    -Name "T4-bearer-token" `
    -InputContent "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456" `
    -ExpectedExit 2 `
    -MustContain "Authorization:" `
    -MustNotContain "Bearer abcdefghijklmnopqrstuvwxyz123456" `
    -ExpectedRedacted 1

# T5 - Long code block (55 lines > 50 limit)
$longBlock  = "``````powershell`n" + ("Write-Host 'line'`n" * 55) + "``````"
Assert-FilterTest `
    -Name "T5-long-code-block" `
    -InputContent "# Report`n$longBlock`nDone." `
    -ExpectedExit 2 `
    -MustContain "[CODE BLOCK TRUNCATED:"

# T6 - Short code block (5 lines < 50 limit)
$shortBlock = "``````powershell`n" + ("echo hi`n" * 5) + "``````"
Assert-FilterTest `
    -Name "T6-short-code-block" `
    -InputContent "# Report`n$shortBlock`nDone." `
    -ExpectedExit 0

# T7a - Mixed: API key present and redacted
$mixedContent = "Key: BOBGUARD-KEY-MIXEDTEST12345678`n$longBlock"
Assert-FilterTest `
    -Name "T7a-mixed-key-redacted" `
    -InputContent $mixedContent `
    -ExpectedExit 2 `
    -MustContain "[REDACTED:API-KEY]" `
    -MustNotContain "BOBGUARD-KEY-MIXEDTEST12345678"

# T7b - Mixed: long block truncated
Assert-FilterTest `
    -Name "T7b-mixed-block-truncated" `
    -InputContent $mixedContent `
    -ExpectedExit 2 `
    -MustContain "[CODE BLOCK TRUNCATED:"

# T8 - Missing input file -> operational error (exit 1)
$badIn  = Join-Path $tmpDir "does-not-exist.md"
$badOut = Join-Path $tmpDir "out-T8.md"
$proc8  = Start-Process powershell.exe `
    -ArgumentList ("-NoProfile -ExecutionPolicy Bypass -File `"" + $filterScript + "`" -InputPath `"" + $badIn + "`" -OutputPath `"" + $badOut + "`"") `
    -Wait -PassThru -NoNewWindow
if ($proc8.ExitCode -eq 1) {
    $passed++
    Write-Host "  [PASS] T8-missing-input" -ForegroundColor Green
} else {
    $failed++
    Write-Host "  [FAIL] T8-missing-input -- exit=$($proc8.ExitCode) (expected 1)" -ForegroundColor Red
}

Write-Host "`n=== Filter Test Results ===" -ForegroundColor Cyan
Write-Host "  Passed : $passed" -ForegroundColor Green
$failColor = if ($failed -gt 0) { "Red" } else { "Green" }
Write-Host "  Failed : $failed" -ForegroundColor $failColor

Remove-Item -Recurse -Force $tmpDir -ErrorAction SilentlyContinue

if ($failed -gt 0) { exit 1 } else { exit 0 }
