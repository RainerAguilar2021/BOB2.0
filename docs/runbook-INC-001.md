# Runbook — Billing Export Pagination Failure

**Applies to:** INC-001 class of incidents (wrong page count → records dropped)

## Symptoms

- Export job logs `MISMATCH` or integrity check `FAILED`.
- `total_exported` < expected record count.
- `Get-TotalPages` debug log shows a value that is `floor(count/page_size)` rather
  than `ceil(count/page_size)`.

## Diagnosis Steps

1. Check the job log for `Get-TotalPages result=` — compare to `ceil(count/page_size)`.
2. Run the regression test to confirm the bug is present:
   ```powershell
   .\tests\Invoke-Tests.ps1 -Suite Regression
   # Expected: [FAIL] INC-001 regression: TotalPages(25,10)=3
   ```
3. Inspect `app/Invoke-Calculator.ps1` line ~40 for the truncating cast.

## Fix

Replace in `app/Invoke-Calculator.ps1`:

```powershell
# BUGGY
return [int]($Count / $PageSize)

# FIXED
return [Math]::Ceiling($Count / $PageSize)
```

## Verification

After applying the fix:

```powershell
.\tests\Invoke-Tests.ps1 -Suite All
# All tests must PASS (exit code 0)
```

## Rollback

See `incidents/INC-001/incident.md` → Rollback Plan.

## Escalation

If the regression test passes but export integrity checks still fail, escalate
to the data-pipeline team. The bug may have a second cause.
