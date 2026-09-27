# Release Policy — BobGuard MVP

Version: 1.0 | Effective: 2026-09-27

## Mechanically Checkable Conditions

A release is **APPROVED** only when ALL of the following conditions are met.
Any condition that cannot be evaluated must be reported as **BLOCKED** or
**NOT VERIFIED** — never silently treated as passing.

| # | Condition | Check method |
|---|---|---|
| R1 | All unit tests pass | `.\tests\Invoke-Tests.ps1 -Suite Unit` exits 0 |
| R2 | All regression tests pass | `.\tests\Invoke-Tests.ps1 -Suite Regression` exits 0 |
| R3 | Final sanitized report contains no unredacted synthetic-secret patterns | `Invoke-PolicyFilter.ps1` exits 0 or 2 (not an operational error); redaction count must be 0 on the final report |
| R4 | Rollback plan present and project-specific | `incidents/INC-001/incident.md` contains "Rollback Plan" section with step-by-step instructions |
| R5 | Dependency audit: no critical/high findings | **NOT VERIFIED** — no package manager or audit command available in this environment |
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
