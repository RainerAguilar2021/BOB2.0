# BobGuard MVP

A hackathon MVP demonstrating an end-to-end AI-assisted debugging and release-readiness workflow powered by **IBM Bob 2.0**. The project diagnoses a real incident, verifies the fix, enforces a policy filter on reports, and produces a release verdict — all orchestrated by an AI agent.

---

## Project Structure

```
.
├── app/
│   └── Invoke-Calculator.ps1          # Sample billing module (site of INC-001 bug)
├── tests/
│   └── Invoke-Tests.ps1               # Minimal test harness (Unit + Regression suites)
├── incidents/
│   ├── INC-001/
│   │   ├── incident.md                # Incident description & rollback plan
│   │   ├── logs.md                    # Synthetic incident logs
│   │   └── findings/
│   │       ├── dev-investigation.md
│   │       ├── ops-investigation.md
│   │       ├── security-investigation.md
│   │       └── regression-pre-fix.txt
│   └── INC-002/
│       ├── incident.md
│       └── logs.md
├── docs/
│   ├── ADR-001-pagination.md          # Architecture decision: pagination strategy
│   ├── runbook-INC-001.md             # Incident response runbook
│   └── release-policy.md             # Mechanical release-gate conditions
├── bobguard/
│   ├── CAPABILITIES.md               # Verified IBM Bob 2.0 capability inventory
│   ├── test-results.json             # Test results (generated at runtime)
│   ├── policy-filter/
│   │   ├── Invoke-PolicyFilter.ps1         # Report sanitisation CLI
│   │   └── Invoke-PolicyFilter.Tests.ps1   # Policy filter tests
│   ├── release-check/
│   │   └── Invoke-ReleaseCheck.ps1         # Release readiness check CLI
│   └── reports/                       # Generated reports (raw, sanitized, verdicts)
├── Invoke-BobGuardDemo.ps1            # Master end-to-end orchestration script
└── README.md
```

---

## Prerequisites

- **PowerShell 5.1** (included in Windows 10/11)
- No external dependencies — no Node.js, Python, or .NET SDK required

---

## The Incident — INC-001

**Billing Pagination: Last Page Silently Dropped**

`Get-TotalPages` in [`app/Invoke-Calculator.ps1`](app/Invoke-Calculator.ps1) used integer truncation instead of ceiling division. For any record count not evenly divisible by the page size, it returned one fewer page than expected, silently dropping the trailing partial page of records.

| | Value |
|---|---|
| **Component** | `Get-TotalPages` in `app/Invoke-Calculator.ps1` |
| **Severity** | High |
| **Status** | ✅ RESOLVED — 21/21 tests pass |

**Root cause:**
```powershell
# Bug — truncates toward zero
return [int]($Count / $PageSize)

# Fix — ceiling division includes the trailing partial page
return [Math]::Ceiling($Count / $PageSize)
```

---

## Quick Start

### Reproduce the bug (before fix)
```powershell
. .\app\Invoke-Calculator.ps1
Get-TotalPages -Count 25 -PageSize 10
# Bug:      2
# Expected: 3
```

### Run all tests (after fix is applied)
```powershell
.\tests\Invoke-Tests.ps1 -Suite All
# Expected exit code: 0  (21/21 pass)
```

### Full end-to-end demo
```powershell
.\Invoke-BobGuardDemo.ps1
# Applies fix, runs all phases, produces reports and release verdict
```

---

## Test Suites

| Command | Expected exit | Purpose |
|---|---|---|
| `.\tests\Invoke-Tests.ps1 -Suite Unit` | `0` | Unit tests — pass with or without fix |
| `.\tests\Invoke-Tests.ps1 -Suite Regression` | `1` (pre-fix) / `0` (post-fix) | Regression gate for INC-001 |
| `.\tests\Invoke-Tests.ps1 -Suite All` | `0` (post-fix only) | Full suite |

---

## Policy Filter

Sanitises report files by redacting a bounded set of synthetic secret patterns before any report is shared or used for a release decision.

```powershell
.\bobguard\policy-filter\Invoke-PolicyFilter.ps1 `
    -InputPath   .\bobguard\reports\raw-report.md `
    -OutputPath  .\bobguard\reports\sanitized-report.md `
    -SummaryPath .\bobguard\reports\policy-summary.json
```

**Exit codes:** `0` = no redactions | `2` = content redacted | `1` = operational error

**Patterns covered** (synthetic/test-only — not comprehensive secret detection):

| Pattern | Regex |
|---|---|
| Synthetic API key | `BOBGUARD-KEY-[A-Za-z0-9]{16,}` |
| Synthetic DB password | `db_password\s*=\s*\S+` |
| Synthetic bearer token | `Bearer\s+[A-Za-z0-9\-._~+/]{20,}` |

Run the filter's own tests:
```powershell
.\bobguard\policy-filter\Invoke-PolicyFilter.Tests.ps1
```

---

## Release Readiness Check

Evaluates all mechanical release-gate conditions from [`docs/release-policy.md`](docs/release-policy.md) and writes a structured verdict.

```powershell
.\bobguard\release-check\Invoke-ReleaseCheck.ps1 `
    -SanitizedReportPath .\bobguard\reports\sanitized-report.md `
    -PolicySummaryPath   .\bobguard\reports\policy-summary.json `
    -TestResultsPath     .\bobguard\test-results.json `
    -IncidentPath        .\incidents\INC-001\incident.md `
    -OutputPath          .\bobguard\reports\release-verdict.json
```

| Condition | Check |
|---|---|
| R1 — Unit tests pass | `Invoke-Tests.ps1 -Suite Unit` exits 0 |
| R2 — Regression tests pass | `Invoke-Tests.ps1 -Suite Regression` exits 0 |
| R3 — No unredacted secrets in final report | Policy filter redaction count = 0 |
| R4 — Rollback plan present | `incident.md` contains a Rollback Plan section |
| R5 — Dependency audit | ⚠️ NOT VERIFIED — no package manager in environment |
| R6 — Release tool non-BLOCKED verdict | `Invoke-ReleaseCheck.ps1` exits 0 |

---

## IBM Bob 2.0 Capabilities

See [`bobguard/CAPABILITIES.md`](bobguard/CAPABILITIES.md) for the full verified inventory.

| Capability | Status |
|---|---|
| File read / write / search | ✅ VERIFIED |
| Shell execution (PowerShell 5.1) | ✅ VERIFIED |
| Code search (grep / glob) | ✅ VERIFIED |
| .NET 8 runtime | ✅ VERIFIED |
| Subagent spawn | ⚠️ Tool available — concurrent execution not natively verified |
| git / node / python / dotnet SDK | ❌ Not available in this environment |

---

## Scope & Limitations

- **Synthetic data only.** No production deployment, no real credentials, no real data loss.
- **Policy filter is pattern-based.** It covers 3 documented synthetic patterns. It is not comprehensive secret detection and does not protect against arbitrary credential leakage.
- **No sandboxing or RBAC.** Process isolation and role-based access are roadmap items.
- **Dependency audit unverified.** No `npm`, `pip`, or `dotnet` SDK available in this environment.

---

## Roadmap (Enterprise features — not implemented)

- Entra ID / MFA / RBAC
- Azure Key Vault / real secrets management
- AKS deployment pipeline
- Real subtask isolation (sandboxing)
- Native parallel-execution evidence
- Dependency audit (`npm audit`, `pip audit`, etc.)
- Timed comparison: manual vs. Bob-assisted incident resolution

---

## License

This repository is a hackathon demo. All data, credentials, and incidents are synthetic and non-functional.
