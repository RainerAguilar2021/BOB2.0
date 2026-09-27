# INC-001 — Billing Pagination: Last Page Silently Dropped

| Field | Value |
|---|---|
| **ID** | INC-001 |
| **Severity** | High |
| **Status** | RESOLVED — fix verified, 21/21 tests pass |
| **Component** | `app/Invoke-Calculator.ps1` → `Get-TotalPages` |
| **Reporter** | BobGuard MVP demo |
| **Environment** | PowerShell 5.1, local dev (synthetic — no production deployment) |

## Summary

When a billing export contains a number of records that is not an exact multiple
of the page size, `Get-TotalPages` returns one fewer page than expected.
The last partial page of records is never fetched, so those records are silently
omitted from the export.

## Reproduction

```powershell
# From workspace root
. .\app\Invoke-Calculator.ps1
Get-TotalPages -Count 25 -PageSize 10
# Expected: 3   (pages 0, 1, 2 — last page has 5 items)
# Actual:   2   (page 2 is never returned)
```

## Stack Trace (synthetic — matches source at app/Invoke-Calculator.ps1 line 40)

```
Get-TotalPages: return [int]($Count / $PageSize)  <- line 40
  Called from: billing-export pipeline, step "Paginate records"
  Count=25, PageSize=10
  Result=2 (expected 3)
  Effect: 5 records on page index 2 never fetched → silent data loss
```

> **Note:** Stack trace is synthetic and constructed to match the implemented source.
> No production deployment or real data loss occurred.

## Root Cause

`[int]($Count / $PageSize)` performs a cast of a floating-point division result to
integer, which truncates toward zero. The correct operation is
`[Math]::Ceiling($Count / $PageSize)`.

## Fix

In `app/Invoke-Calculator.ps1`, line 40:

```powershell
# Before (bug)
return [int]($Count / $PageSize)

# After (fix)
return [Math]::Ceiling($Count / $PageSize)
```

## Deployment History

> **SYNTHETIC / NOT APPLICABLE** — this is a local dev workspace with no CI/CD
> pipeline or production deployment. Deployment history section is intentionally
> absent to avoid presenting fabricated data.

## Rollback Plan

1. Revert `app/Invoke-Calculator.ps1` to the previous version (undo the one-line
   change in `Get-TotalPages`).
2. Re-run `.\tests\Invoke-Tests.ps1` to confirm the regression test fails and
   the unit tests pass (confirming revert is correct).
3. Re-run billing export jobs for the affected date range.

> Rollback is specific to this sample project. In a real pipeline, also cancel
> any in-flight export jobs before reverting.
