# BobGuard Incident Report — INC-001 (FINAL)
# Produced by IBM Bob 2.0 BobGuard investigation (Prompt 2)
# Raw version — will be processed by policy filter before release evaluation

## Summary

| Field | Value |
|---|---|
| Incident | INC-001 — Billing Pagination: Last Page Silently Dropped |
| Severity | High |
| Status | RESOLVED |
| Component | `app/Invoke-Calculator.ps1` -> `Get-TotalPages` |
| Analyst | IBM Bob 2.0 (BobGuard MVP, Prompt 2) |
| Fix applied | Yes — `[Math]::Ceiling` replacing `[int]` cast |

## Root Cause (Verified)

**Primary cause:** `Get-TotalPages` in `app/Invoke-Calculator.ps1` (pre-fix line 40)
used `[int]($Count / $PageSize)`, which performs floating-point division followed by
truncation toward zero (equivalent to `floor` for positive values).

For `Count=25, PageSize=10`:
- Division result: 2.5
- After `[int]` cast: 2 (truncated)
- Correct value: 3 (ceiling)
- Effect: page index 2 never fetched; 5 records silently omitted

**ADR violation:** ADR-001 (`docs/ADR-001-pagination.md`, Status: Accepted, 2026-09-01)
explicitly mandates ceiling division. The pre-fix implementation directly contradicts
this accepted architectural decision.

## Supporting Evidence

| Evidence | Citation | Verified |
|---|---|---|
| Source bug | `app/Invoke-Calculator.ps1` pre-fix line 40: `[int]($Count / $PageSize)` | Yes — regression test confirmed |
| Log mismatch | `incidents/INC-001/logs.md` line 13: `Get-TotalPages result=2` (labeled SYNTHETIC) | Yes — consistent with source |
| Log integrity failure | `incidents/INC-001/logs.md` line 18: `export integrity check FAILED` | Yes — consistent with source |
| ADR violation | `docs/ADR-001-pagination.md`: "Use ceiling integer division" | Yes |
| Runbook match | `docs/runbook-INC-001.md`: symptoms, diagnosis steps, fix | Yes — all match |
| Deployment history | NOT APPLICABLE — local dev workspace, no CI/CD | N/A |

## Fix Applied

**File:** `app/Invoke-Calculator.ps1`
**Line:** 39 (post-fix)
**Change:**

```
Before: return [int]($Count / $PageSize)
After:  return [Math]::Ceiling($Count / $PageSize)
```

**Additional cleanup (external change):**
- Removed UTF-8 BOM added by external editor
- Updated stale comment ("INC-001 BUG:") to reflect resolved state
- Fixed mojibake `0â€"100` -> `0-100` in comment
- Removed 3 trailing blank lines

## Test Results

### Pre-fix regression (expected failure — confirms bug)

```
=== Regression Tests ===
  [FAIL] INC-001 regression: TotalPages(25,10)=2 (expected 3)
         -> BUG PRESENT: truncation discards last partial page
  [FAIL] INC-001 regression: TotalPages(1,10)=1  expected=1  actual=0
  [FAIL] INC-001 regression: TotalPages(11,10)=2  expected=2  actual=1
  [PASS] INC-001 regression: TotalPages(30,10)=3
  Passed: 1  Failed: 3  Exit: 1
```

Failure matches incident description exactly.
Full output preserved in: `incidents/INC-001/findings/regression-pre-fix.txt`

### Post-fix full suite (must pass — confirms fix)

```
=== Unit Tests ===   17/17 PASS
=== Regression Tests === 4/4 PASS
Total: Passed: 21  Failed: 0  Exit: 0
```

No warnings. Results in: `bobguard/test-results.json`

## Security Scope

- Pattern-based policy filter scanned this report for 3 documented synthetic patterns.
- One synthetic credential present in this raw report (see below) — will be redacted.
- Dependency audit: NOT VERIFIED (no package manager available).
- No real credentials are present; all secrets are synthetic test fixtures.

SYNTHETIC SECRET FOR POLICY FILTER DEMO (NONFUNCTIONAL):
  API access token: BOBGUARD-KEY-SYNTHETICTESTONLY9999

## Rollback Plan

1. Revert `app/Invoke-Calculator.ps1` to previous version (undo `[Math]::Ceiling` -> `[int]`).
2. Run `.\tests\Invoke-Tests.ps1 -Suite All` — regression tests must fail, unit tests pass.
3. Re-run billing export jobs for affected date range.
4. In a real pipeline: cancel in-flight export jobs before reverting.

## Remaining Risks

- No production deployment in this environment; actual production impact is synthetic.
- Dependency audit (R5) NOT VERIFIED.
- Pattern filter covers only 3 patterns; not comprehensive secret detection.
- Parallel investigation evidence: NOT VERIFIED (sequential execution used).

## Release Verdict

APPROVED (with one NOT VERIFIED condition)

R1 Unit tests:        PASS  — 17/17 unit tests pass (exit 0)
R2 Regression tests:  PASS  — 4/4 regression tests pass (exit 0)
R3 Sanitized report:  PASS  — Final clean report has 0 redactions, 0 truncated blocks
R4 Rollback plan:     PASS  — Rollback plan present with numbered steps
R5 Dependency audit:  NOT VERIFIED — no package manager available in this environment
R6 Release tool:      exit 0 — APPROVED

Synthetic credential in raw report was redacted by policy filter (exit 2, first pass).
Second filter pass on sanitized output: exit 0 (RedactedCount=0 confirmed).
Release readiness evaluated against the final clean sanitized report.

NOTE: This approval covers only the verifiable conditions. R5 (dependency audit)
remains NOT VERIFIED. This is NOT a guarantee against arbitrary credential leakage
or production readiness beyond the scope of this sample project.
