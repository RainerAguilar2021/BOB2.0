<#
.SYNOPSIS
    Minimal test runner for BobGuard MVP.
    Usage:
        .\tests\Invoke-Tests.ps1              # run all tests
        .\tests\Invoke-Tests.ps1 -Suite Unit  # unit tests only
        .\tests\Invoke-Tests.ps1 -Suite Regression  # regression test only

    Exit codes:
        0  — all executed tests passed
        1  — one or more tests failed
        2  — runner error (bad parameter, missing module, etc.)

.NOTES
    No external test framework required. Pure PowerShell 5.1.
#>
param(
    [ValidateSet("All","Unit","Regression")]
    [string] $Suite = "All"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Load module under test ────────────────────────────────────────────────────
$modulePath = Join-Path $PSScriptRoot "..\app\Invoke-Calculator.ps1"
if (-not (Test-Path $modulePath)) {
    Write-Error "Module not found: $modulePath"
    exit 2
}
. $modulePath

# ── Tiny assertion helpers ────────────────────────────────────────────────────
$script:passed = 0
$script:failed = 0
$script:results = [System.Collections.Generic.List[PSCustomObject]]::new()

function Assert-Equal {
    param([string]$Name, $Expected, $Actual)
    if ($Expected -eq $Actual) {
        $script:passed++
        $script:results.Add([PSCustomObject]@{ Name=$Name; Status="PASS"; Expected=$Expected; Actual=$Actual; Note="" })
        Write-Host "  [PASS] $Name" -ForegroundColor Green
    } else {
        $script:failed++
        $script:results.Add([PSCustomObject]@{ Name=$Name; Status="FAIL"; Expected=$Expected; Actual=$Actual; Note="" })
        Write-Host "  [FAIL] $Name  expected=$Expected  actual=$Actual" -ForegroundColor Red
    }
}

function Assert-Throws {
    param([string]$Name, [scriptblock]$Block)
    try {
        & $Block | Out-Null
        $script:failed++
        $script:results.Add([PSCustomObject]@{ Name=$Name; Status="FAIL"; Expected="exception"; Actual="no exception"; Note="" })
        Write-Host "  [FAIL] $Name  (expected exception, none thrown)" -ForegroundColor Red
    } catch {
        $script:passed++
        $script:results.Add([PSCustomObject]@{ Name=$Name; Status="PASS"; Expected="exception"; Actual="thrown: $($_.Exception.Message)"; Note="" })
        Write-Host "  [PASS] $Name" -ForegroundColor Green
    }
}

# ── Unit tests ────────────────────────────────────────────────────────────────
function Invoke-UnitTests {
    Write-Host "`n=== Unit Tests ===" -ForegroundColor Cyan

    # Get-PagedItems
    $items = 1..25
    [object[]]$page0 = @(Get-PagedItems -Items $items -PageIndex 0 -PageSize 10)
    Assert-Equal "PagedItems: page 0 length"   10  $page0.Count
    Assert-Equal "PagedItems: page 0 first"     1  $page0[0]
    Assert-Equal "PagedItems: page 0 last"     10  $page0[-1]

    [object[]]$page2 = @(Get-PagedItems -Items $items -PageIndex 2 -PageSize 10)
    Assert-Equal "PagedItems: page 2 length"    5  $page2.Count
    Assert-Equal "PagedItems: page 2 first"    21  $page2[0]
    Assert-Equal "PagedItems: page 2 last"     25  $page2[-1]

    [object[]]$empty = @(Get-PagedItems -Items $items -PageIndex 99 -PageSize 10)
    Assert-Equal "PagedItems: beyond end is empty" 0 $empty.Count

    Assert-Throws "PagedItems: PageSize 0 throws" { Get-PagedItems -Items $items -PageIndex 0 -PageSize 0 }

    # ConvertTo-DiscountedPrice
    Assert-Equal "Discount: 10% of 100"  90.00  (ConvertTo-DiscountedPrice -UnitPrice 100 -DiscountPct 10)
    Assert-Equal "Discount: 0% of 50"   50.00  (ConvertTo-DiscountedPrice -UnitPrice 50  -DiscountPct 0)
    Assert-Equal "Discount: 100% of 75"  0.00  (ConvertTo-DiscountedPrice -UnitPrice 75  -DiscountPct 100)
    Assert-Equal "Discount: 33.33% of 99.99" 66.66 (ConvertTo-DiscountedPrice -UnitPrice 99.99 -DiscountPct 33.33)
    Assert-Throws "Discount: negative pct throws"   { ConvertTo-DiscountedPrice -UnitPrice 10 -DiscountPct -1 }
    Assert-Throws "Discount: pct > 100 throws"      { ConvertTo-DiscountedPrice -UnitPrice 10 -DiscountPct 101 }

    # Get-TotalPages — exact multiples (pass even with buggy code)
    Assert-Equal "TotalPages: 20/10=2 (exact)" 2 (Get-TotalPages -Count 20 -PageSize 10)
    Assert-Equal "TotalPages: 0 items = 0 pages" 0 (Get-TotalPages -Count 0 -PageSize 10)
    Assert-Throws "TotalPages: PageSize 0 throws" { Get-TotalPages -Count 10 -PageSize 0 }
}

# ── Regression test ───────────────────────────────────────────────────────────
function Invoke-RegressionTests {
    Write-Host "`n=== Regression Tests ===" -ForegroundColor Cyan
    Write-Host "  INC-001: Get-TotalPages must use ceiling division" -ForegroundColor Yellow
    # ---- INC-001 block (unchanged) ----

    # This is the key regression: 25 items / 10 per page = 3 pages (not 2)
    $actual   = Get-TotalPages -Count 25 -PageSize 10
    $expected = 3

    if ($actual -eq $expected) {
        $script:passed++
        $script:results.Add([PSCustomObject]@{
            Name="INC-001 regression: TotalPages(25,10)=3"
            Status="PASS"; Expected=$expected; Actual=$actual
            Note="Fix verified: ceiling division returns correct page count"
        })
        Write-Host "  [PASS] INC-001 regression: TotalPages(25,10)=$actual (expected $expected)" -ForegroundColor Green
    } else {
        $script:failed++
        $script:results.Add([PSCustomObject]@{
            Name="INC-001 regression: TotalPages(25,10)=3"
            Status="FAIL"; Expected=$expected; Actual=$actual
            Note="BUG PRESENT: integer truncation drops last partial page"
        })
        Write-Host "  [FAIL] INC-001 regression: TotalPages(25,10)=$actual (expected $expected)" -ForegroundColor Red
        Write-Host "         -> BUG PRESENT: truncation discards last partial page" -ForegroundColor Red
    }

    # Additional regression cases
    Assert-Equal "INC-001 regression: TotalPages(1,10)=1"   1  (Get-TotalPages -Count 1  -PageSize 10)
    Assert-Equal "INC-001 regression: TotalPages(11,10)=2"  2  (Get-TotalPages -Count 11 -PageSize 10)
    Assert-Equal "INC-001 regression: TotalPages(30,10)=3"  3  (Get-TotalPages -Count 30 -PageSize 10)

    # ---- INC-002 block ----
    Write-Host "  INC-002: ConvertTo-DiscountedPrice must use AwayFromZero rounding" -ForegroundColor Yellow

    # Midpoint case 1: $0.25 @ 10% -> $0.225 -> AwayFromZero = $0.23, ToEven = $0.22
    $r1 = ConvertTo-DiscountedPrice -UnitPrice 0.25 -DiscountPct 10
    if ($r1 -eq 0.23) {
        $script:passed++
        $script:results.Add([PSCustomObject]@{
            Name="INC-002 regression: Discount(0.25,10)=0.23"
            Status="PASS"; Expected=0.23; Actual=$r1
            Note="AwayFromZero rounding verified"
        })
        Write-Host "  [PASS] INC-002 regression: Discount(0.25,10)=$r1 (expected 0.23)" -ForegroundColor Green
    } else {
        $script:failed++
        $script:results.Add([PSCustomObject]@{
            Name="INC-002 regression: Discount(0.25,10)=0.23"
            Status="FAIL"; Expected=0.23; Actual=$r1
            Note="BUG PRESENT: Banker's rounding (ToEven) instead of AwayFromZero"
        })
        Write-Host "  [FAIL] INC-002 regression: Discount(0.25,10)=$r1 (expected 0.23)" -ForegroundColor Red
        Write-Host "         -> BUG PRESENT: MidpointRounding.ToEven rounds 0.225 down to 0.22" -ForegroundColor Red
    }

    # Midpoint case 2: $0.05 @ 50% -> $0.025 -> AwayFromZero = $0.03, ToEven = $0.02
    $r2 = ConvertTo-DiscountedPrice -UnitPrice 0.05 -DiscountPct 50
    if ($r2 -eq 0.03) {
        $script:passed++
        $script:results.Add([PSCustomObject]@{
            Name="INC-002 regression: Discount(0.05,50)=0.03"
            Status="PASS"; Expected=0.03; Actual=$r2
            Note="AwayFromZero rounding verified"
        })
        Write-Host "  [PASS] INC-002 regression: Discount(0.05,50)=$r2 (expected 0.03)" -ForegroundColor Green
    } else {
        $script:failed++
        $script:results.Add([PSCustomObject]@{
            Name="INC-002 regression: Discount(0.05,50)=0.03"
            Status="FAIL"; Expected=0.03; Actual=$r2
            Note="BUG PRESENT: MidpointRounding.ToEven rounds 0.025 down to 0.02"
        })
        Write-Host "  [FAIL] INC-002 regression: Discount(0.05,50)=$r2 (expected 0.03)" -ForegroundColor Red
        Write-Host "         -> BUG PRESENT: MidpointRounding.ToEven rounds 0.025 down to 0.02" -ForegroundColor Red
    }

    # Non-midpoint case (must pass with either rounding mode -- confirms test is not over-broad)
    Assert-Equal "INC-002 regression: Discount(1.00,10)=0.90"    0.90  (ConvertTo-DiscountedPrice -UnitPrice 1.00 -DiscountPct 10)
    Assert-Equal "INC-002 regression: Discount(99.99,33.33)=66.66" 66.66 (ConvertTo-DiscountedPrice -UnitPrice 99.99 -DiscountPct 33.33)
}

# ── Run selected suite ────────────────────────────────────────────────────────
switch ($Suite) {
    "Unit"       { Invoke-UnitTests }
    "Regression" { Invoke-RegressionTests }
    "All"        { Invoke-UnitTests; Invoke-RegressionTests }
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host "`n=== Results ===" -ForegroundColor Cyan
Write-Host "  Passed : $($script:passed)" -ForegroundColor Green
Write-Host "  Failed : $($script:failed)" -ForegroundColor $(if ($script:failed -gt 0) { "Red" } else { "Green" })

# Write machine-readable JSON results
$jsonPath = Join-Path $PSScriptRoot "..\bobguard\test-results.json"
$script:results | ConvertTo-Json | Set-Content -Path $jsonPath -Encoding UTF8
Write-Host "  Results written to: $jsonPath"

if ($script:failed -gt 0) { exit 1 } else { exit 0 }
