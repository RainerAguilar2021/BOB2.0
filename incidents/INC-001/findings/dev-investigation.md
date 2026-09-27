# INC-001 — Developer Investigation Findings

Investigation mode: SEQUENTIAL (parallel execution NOT VERIFIED per bobguard/CAPABILITIES.md)

## Source Location

File: `app/Invoke-Calculator.ps1`
Function: `Get-TotalPages`

```
Pre-fix line 40 (from incident.md):
  return [int]($Count / $PageSize)

Post-fix line 39 (current):
  return [Math]::Ceiling($Count / $PageSize)
```

## Verified Root Cause

`[int]($Count / $PageSize)` in PowerShell evaluates `$Count / $PageSize` as a
.NET Double (floating-point), then casts to `[int]` using **truncation toward zero**
(i.e., `floor` for positive values).

For Count=25, PageSize=10:
  - Floating-point division: 2.5
  - After `[int]` cast: 2  (truncated)
  - Correct value: 3  (ceiling of 2.5)

The trailing partial page (page index 2, containing 5 records) is therefore
never included in the page loop, causing those records to be silently omitted.

## ADR Violation

ADR-001 (`docs/ADR-001-pagination.md`, Status: Accepted, 2026-09-01) explicitly
mandates ceiling division:
> "Use ceiling integer division for total-page count: total_pages = ceil(count / page_size)"
> "Integer truncation — Silently drops the last partial page — root cause of INC-001"

The pre-fix implementation directly contradicts this accepted decision.

## Fix Verified

Minimal one-line change:
  `[int]($Count / $PageSize)` → `[Math]::Ceiling($Count / $PageSize)`

Fix is present in current `app/Invoke-Calculator.ps1` line 39.
Fix confirmed by: regression test passing (21/21, exit 0).

## External Change Observation

The file was externally modified after the fix was applied. Observed changes:
- UTF-8 BOM added (line 1: `\uFEFF`)
- Stale comment on lines 12-14 still references bug description ("INC-001 BUG:")
- Mojibake on line 45: `# 0â€"100` (should be `# 0-100`)
- Three trailing blank lines added (lines 53-55)

None of these changes revert the fix. The function logic on line 39 is unaffected.
The comment and encoding issues are cosmetic but should be cleaned up.

## Regression Test

Pre-fix failure (from run-log.txt, captured during Prompt 1 orchestration):
  Phase 2: exit=1 — [FAIL] INC-001 regression: TotalPages(25,10)=2 (expected 3)
  Phase 2: exit=1 — [FAIL] INC-001 regression: TotalPages(1,10)=1  actual=0
  Phase 2: exit=1 — [FAIL] INC-001 regression: TotalPages(11,10)=2  actual=1

Post-fix confirmation (current run):
  All 21 tests PASS, exit=0.
