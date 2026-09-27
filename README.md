# BobGuard MVP

A hackathon MVP demonstrating an end-to-end AI-assisted debugging and release-readiness workflow powered by **IBM Bob 2.0**. The project diagnoses a real incident, verifies the fix, enforces a policy filter on reports, and produces a release verdict — all orchestrated by an AI agent.

**Demo application URL:** Not available — the app is not deployed.

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
│   ├── release-policy.md             # Mechanical release-gate conditions
│   └── dependency-audit.md            # Python dependency sets and audit record
├── bobguard/
│   ├── CAPABILITIES.md               # Verified IBM Bob 2.0 capability inventory
│   ├── test-results.json             # Test results (generated at runtime)
│   ├── policy-filter/
│   │   ├── Invoke-PolicyFilter.ps1         # Report sanitisation CLI
│   │   └── Invoke-PolicyFilter.Tests.ps1   # Policy filter tests
│   ├── release-check/
│   │   └── Invoke-ReleaseCheck.ps1         # Release readiness check CLI
│   └── reports/                       # Generated reports (raw, sanitized, verdicts)
├── streamlit_app.py                  # Evidence-based Streamlit web demo
├── bobguard_mcp_server.py             # Optional stdio MCP server
├── requirements.txt                  # Streamlit demo dependencies
├── requirements-mcp.txt              # Optional MCP server dependency
├── Invoke-BobGuardDemo.ps1            # Master end-to-end orchestration script
└── README.md
```

---

## Prerequisites

- **PowerShell 5.1** (included in Windows 10/11)
- **Python 3.11 or later** for the Streamlit demo and optional MCP server
- No Node.js or .NET SDK is required

### Run the Streamlit demo

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip==26.2.1
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

The demo displays static repository evidence. It is not publicly deployed and
does not make live calls to IBM Bob, watsonx, or IBM Cloud.

### Publish the Streamlit demo

To create a public demo, first push or merge the desired project branch to
GitHub, then:

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and select
   **Create app**.
2. Select repository `RainerAguilar2021/BOB2.0` and the branch containing the
   app.
3. Set **Main file path** to `streamlit_app.py`.
4. In **Advanced settings**, select Python 3.12. No secrets are required.
5. Select **Deploy**. The generated application URL will be shown by Streamlit
   Community Cloud after deployment.

The repository currently has no demo URL because deployment has not been
authorized or performed.

### Optional MCP server

Install this only if you use `bobguard_mcp_server.py`:

```powershell
python -m pip install --upgrade pip==26.2.1
python -m pip install -r requirements-mcp.txt
python bobguard_mcp_server.py
```

The server uses stdio as its MCP transport. It does not provide a live IBM Bob
or cloud-service integration.

### Dependency audit

The current direct dependency versions and audit record are documented in
[`docs/dependency-audit.md`](docs/dependency-audit.md). To install the pinned
local audit tool and run checks for both dependency sets:

```powershell
python -m pip install --upgrade pip==26.2.1
python -m pip install -r requirements-dev.txt
python -m pip_audit -r requirements.txt --progress-spinner off
python -m pip_audit -r requirements-mcp.txt --progress-spinner off
```

The recorded audit is date-scoped; rerun it before publishing or deploying.

---

## The Incident — INC-001

**Billing Pagination: Last Page Silently Dropped**

`Get-TotalPages` in [`app/Invoke-Calculator.ps1`](app/Invoke-Calculator.ps1) used integer truncation instead of ceiling division. For any record count not evenly divisible by the page size, it returned one fewer page than expected, silently dropping the trailing partial page of records.

| | Value |
|---|---|
| **Component** | `Get-TotalPages` in `app/Invoke-Calculator.ps1` |
| **Severity** | High |
| **Status** | ✅ INC-001 RESOLVED — 17 unit and 4 pagination regression checks pass; INC-002 remains open |

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

### Run all tests
```powershell
.\tests\Invoke-Tests.ps1 -Suite All
# Current result: exit 1 — INC-002 midpoint regression cases fail while that incident remains open
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
| `.\tests\Invoke-Tests.ps1 -Suite Regression` | `1` while INC-002 is open; `0` only when all regression cases pass | INC-001 pagination and INC-002 rounding regression checks |
| `.\tests\Invoke-Tests.ps1 -Suite All` | `1` currently (23 pass, 2 fail for open INC-002); `0` only when all tests pass | Full suite |

The regression failures for INC-002 are intentional evidence of its unresolved
rounding bug; its expected behavior and `OPEN` status are preserved. Each test
run overwrites `bobguard/test-results.json` with only the selected suite's
results. Run `-Suite All` to provide complete test evidence to the release
checker.

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
| R2 — All regression tests pass | Complete test results contain all 8 regression cases and they pass |
| R3 — No unredacted secrets in final report | Policy filter redaction count = 0 |
| R4 — Rollback plan present | `incident.md` contains a Rollback Plan section |
| R5 — Dependency audit | See [`docs/dependency-audit.md`](docs/dependency-audit.md); the PowerShell release checker does not consume this result and reports NOT VERIFIED |
| R6 — Release tool non-BLOCKED verdict | `Invoke-ReleaseCheck.ps1` exits 0 |

---

## IBM Bob 2.0 Capabilities

See [`bobguard/CAPABILITIES.md`](bobguard/CAPABILITIES.md) for the full verified inventory.
Statuses in that inventory describe the original IBM Bob inspection environment,
not the current local development environment.

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
- **PowerShell release checker does not verify Python dependencies.** A current,
  date-scoped `pip-audit` result is recorded in
  [`docs/dependency-audit.md`](docs/dependency-audit.md); rerun it before publishing.

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
