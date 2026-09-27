# Release Policy — BobGuard MVP

Version: 1.0 | Effective: 2026-09-27

## Mechanically Checkable Conditions

A release is **APPROVED** only when ALL of the following conditions are met.
Any condition that cannot be evaluated must be reported as **BLOCKED** or
**NOT VERIFIED** — never silently treated as passing.

Run `.\tests\Invoke-Tests.ps1 -Suite All` before the release check so the
results file contains the complete set of unit and regression results. The
checker blocks missing test evidence. INC-002 is intentionally unresolved in
this demo; its two midpoint regression cases currently fail, so a release
verdict must remain **BLOCKED**.

| # | Condition | Check method |
|---|---|---|
| R1 | All 17 unit tests pass | `test-results.json` contains all 17 unit results and no failures |
| R2 | All 8 regression tests pass | `test-results.json` contains all 8 regression results and no failures |
| R3 | Final sanitized report contains no unredacted synthetic-secret patterns | `Invoke-PolicyFilter.ps1` exits 0 or 2 (not an operational error); redaction count must be 0 on the final report |
| R4 | Rollback plan present and project-specific | `incidents/INC-001/incident.md` contains "Rollback Plan" section with step-by-step instructions |
| R5 | Dependency audit: no critical/high findings | Run the checks in [`dependency-audit.md`](dependency-audit.md); the PowerShell release checker does not consume their results and reports **NOT VERIFIED** |
| R6 | Release-readiness tool produces a non-BLOCKED verdict | `Invoke-ReleaseCheck.ps1` exits 0 |

## Secret Patterns Covered by Policy Filter

The policy filter redacts the following **synthetic / test-only** patterns.
This list is explicitly bounded. It is **not** comprehensive secret detection
and does **not** protect against arbitrary credential leakage.

| Pattern name | Regex |
|---|---|
| Synthetic API key | `BOBGUARD-KEY-[A-Za-z0-9]{16,}` |
| Synthetic DB password | `db_password\s*=\s*\S+` |
| Synthetic bearer token | `Bearer\s+[A-Za-z0-9\-._~+/]{20,}` |

## Code Block Size Limit

Fenced code blocks longer than **50 lines** will be replaced with a
`[CODE BLOCK TRUNCATED: N lines]` placeholder in sanitized reports.

## Disclaimer

This policy filter is a demonstration tool. It redacts a documented,
bounded list of synthetic test patterns from a single text report.
It is **not**:
- comprehensive secret detection
- source-code protection
- process isolation or sandboxing
- a guarantee against data leakage
