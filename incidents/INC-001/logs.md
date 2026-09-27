# INC-001 — Synthetic Application Log (pre-fix)

> **SYNTHETIC / LABELED** — These log lines were constructed to match the
> implemented source at `app/Invoke-Calculator.ps1`. They are not from a
> running production system.

```
2026-09-27T08:14:02Z [INFO]  billing-export: starting nightly run  job_id=NR-20260927
2026-09-27T08:14:03Z [INFO]  billing-export: fetching records  filter=ACTIVE date=2026-09-26
2026-09-27T08:14:03Z [INFO]  billing-export: record count resolved  count=25
2026-09-27T08:14:03Z [INFO]  billing-export: pagination config  page_size=10
2026-09-27T08:14:03Z [DEBUG] Get-TotalPages called  count=25 page_size=10
2026-09-27T08:14:03Z [DEBUG] Get-TotalPages result=2  <-- INCORRECT (should be 3)
2026-09-27T08:14:03Z [INFO]  billing-export: processing page 0  items=10
2026-09-27T08:14:04Z [INFO]  billing-export: processing page 1  items=10
2026-09-27T08:14:04Z [INFO]  billing-export: all pages processed  total_exported=20
2026-09-27T08:14:04Z [WARN]  billing-export: expected 25 records, exported 20  MISMATCH delta=5
2026-09-27T08:14:04Z [ERROR] billing-export: export integrity check FAILED  job_id=NR-20260927
```

## Analysis

- `Get-TotalPages(25, 10)` returned `2` instead of `3`.
- Pages 0 and 1 (10 records each) were exported; page 2 (5 records) was never fetched.
- The integrity check at the end detected the mismatch (exported=20, expected=25).
- Root cause: integer truncation in `Get-TotalPages` — see `incident.md`.
