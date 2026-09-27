# INC-001 — Operations Investigation Findings

Investigation mode: SEQUENTIAL (parallel execution NOT VERIFIED per bobguard/CAPABILITIES.md)

## Log Correlation

Source: `incidents/INC-001/logs.md` (SYNTHETIC / LABELED — constructed to match source)

Key log lines:
```
2026-09-27T08:14:03Z [DEBUG] Get-TotalPages called  count=25 page_size=10
2026-09-27T08:14:03Z [DEBUG] Get-TotalPages result=2  <-- INCORRECT (should be 3)
2026-09-27T08:14:04Z [INFO]  billing-export: all pages processed  total_exported=20
2026-09-27T08:14:04Z [WARN]  billing-export: expected 25 records, exported 20  MISMATCH delta=5
2026-09-27T08:14:04Z [ERROR] billing-export: export integrity check FAILED  job_id=NR-20260927
```

Correlation with source:
- `Get-TotalPages result=2` matches the pre-fix truncating cast in `app/Invoke-Calculator.ps1`.
- `total_exported=20` = pages 0+1 only (10 records each); page 2 (5 records) skipped.
- Integrity check detected the mismatch (expected 25, exported 20, delta=5).

## Deployment History

NOT APPLICABLE — this is a local dev workspace with no CI/CD pipeline or
production deployment. Per `incidents/INC-001/incident.md`:
> "SYNTHETIC / NOT APPLICABLE — this is a local dev workspace with no CI/CD
> pipeline or production deployment. Deployment history section is intentionally
> absent to avoid presenting fabricated data."

No deployment-linked change was identified. Root cause is a pre-existing
implementation error, not a recent deployment change.

## Rollback Plan (from incident.md)

1. Revert `app/Invoke-Calculator.ps1` (undo the one-line change in `Get-TotalPages`).
2. Re-run `.\tests\Invoke-Tests.ps1` to confirm regression test fails and unit tests pass.
3. Re-run billing export jobs for the affected date range.

Rollback is project-specific. In a real pipeline: cancel in-flight export jobs first.

## Runbook Match

Symptoms in `docs/runbook-INC-001.md` match observed log behavior:
- "Export job logs MISMATCH or integrity check FAILED" — confirmed in log line [ERROR]
- "total_exported < expected record count" — confirmed: 20 < 25
- "Get-TotalPages debug log shows floor(count/page_size)" — confirmed: result=2 = floor(2.5)

Runbook diagnosis steps verified: source inspection at line ~40 confirmed.
