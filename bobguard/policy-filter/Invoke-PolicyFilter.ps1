<#
.SYNOPSIS
    BobGuard MVP — Report Policy Filter
    Redacts a documented, bounded list of synthetic-secret patterns from a
    text report and replaces oversized fenced code blocks.

.DESCRIPTION
    INPUT:  plain-text report file (--InputPath)
    OUTPUT: sanitized report file (--OutputPath)
            machine-readable summary JSON (--SummaryPath, optional)

    Exit codes:
        0  — completed; no redactions needed
        2  — completed; one or more items were redacted / blocked
        1  — operational failure (bad args, unreadable input, unwritable output)

    DISCLAIMER: This filter redacts a bounded list of synthetic/test patterns.
    It is NOT comprehensive secret detection, source-code protection, isolation,
    or a guarantee against data leakage.

.EXAMPLE
    .\bobguard\policy-filter\Invoke-PolicyFilter.ps1 `
        -InputPath  .\bobguard\reports\raw-report.md `
        -OutputPath .\bobguard\reports\sanitized-report.md `
        -SummaryPath .\bobguard\reports\policy-summary.json
#>
param(
    [Parameter(Mandatory)][string] $InputPath,
    [Parameter(Mandatory)][string] $OutputPath,
    [string] $SummaryPath,
    [int]    $MaxCodeBlockLines = 50
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Err([string]$msg) { Write-Host "[PolicyFilter ERROR] $msg" -ForegroundColor Red }
function Write-Info([string]$msg) { Write-Host "[PolicyFilter] $msg" }

# ── Validate inputs ───────────────────────────────────────────────────────────
if (-not (Test-Path $InputPath)) {
    Write-Err "Input file not found: $InputPath"
    exit 1
}
try { $content = Get-Content -Path $InputPath -Raw -Encoding UTF8 }
catch { Write-Err "Cannot read input: $_"; exit 1 }

$outputDir = Split-Path $OutputPath -Parent
if ($outputDir -and -not (Test-Path $outputDir)) {
    try { New-Item -ItemType Directory -Force -Path $outputDir | Out-Null }
    catch { Write-Err "Cannot create output directory: $_"; exit 1 }
}

# ── Secret patterns (synthetic/test only — explicitly bounded) ────────────────
$patterns = @(
    @{ Name="Synthetic API key";      Regex='BOBGUARD-KEY-[A-Za-z0-9]{16,}';          Replacement='[REDACTED:API-KEY]'  }
    @{ Name="Synthetic DB password";  Regex='db_password\s*=\s*\S+';                   Replacement='db_password=[REDACTED:PASSWORD]' }
    @{ Name="Synthetic bearer token"; Regex='Bearer\s+[A-Za-z0-9\-._~+/]{20,}';        Replacement='Bearer [REDACTED:TOKEN]' }
)

$redactedItems   = [System.Collections.Generic.List[PSCustomObject]]::new()
$sanitized = $content

# ── Apply secret redaction ────────────────────────────────────────────────────
foreach ($p in $patterns) {
    $matches = [regex]::Matches($sanitized, $p.Regex)
    if ($matches.Count -gt 0) {
        foreach ($m in $matches) {
            $redactedItems.Add([PSCustomObject]@{
                Type    = $p.Name
                Preview = $m.Value.Substring(0, [Math]::Min(30, $m.Value.Length)) + "..."
            })
        }
        $sanitized = [regex]::Replace($sanitized, $p.Regex, $p.Replacement)
        Write-Info "Redacted $($matches.Count) match(es) of pattern '$($p.Name)'"
    }
}

# ── Truncate oversized code blocks ────────────────────────────────────────────
$codeBlockPattern = '(?s)```[^\n]*\n(.*?)```'
$blocksReplaced   = 0
$sanitized = [regex]::Replace($sanitized, $codeBlockPattern, {
    param($m)
    $inner = $m.Groups[1].Value
    $lines = ($inner -split "`n").Count
    if ($lines -gt $MaxCodeBlockLines) {
        $script:blocksReplaced++
        Write-Info "Truncated code block: $lines lines > $MaxCodeBlockLines limit"
        return "``````" + "`n[CODE BLOCK TRUNCATED: $lines lines]`n" + "``````"
    }
    return $m.Value
})

# ── Write output ──────────────────────────────────────────────────────────────
try { Set-Content -Path $OutputPath -Value $sanitized -Encoding UTF8 -NoNewline }
catch { Write-Err "Cannot write output: $_"; exit 1 }

# ── Write summary ─────────────────────────────────────────────────────────────
$summary = [PSCustomObject]@{
    InputPath        = $InputPath
    OutputPath       = $OutputPath
    RedactedCount    = $redactedItems.Count
    TruncatedBlocks  = $blocksReplaced
    RedactedItems    = $redactedItems
    Timestamp        = (Get-Date -Format "o")
}

if ($SummaryPath) {
    try { $summary | ConvertTo-Json -Depth 5 | Set-Content -Path $SummaryPath -Encoding UTF8 }
    catch { Write-Err "Cannot write summary: $_"; exit 1 }
    Write-Info "Summary written to: $SummaryPath"
}

$summary | ConvertTo-Json -Depth 5 | Write-Host

if ($redactedItems.Count -gt 0 -or $blocksReplaced -gt 0) {
    Write-Info "Exit 2: content was redacted/truncated."
    exit 2
} else {
    Write-Info "Exit 0: no redactions needed."
    exit 0
}
