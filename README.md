# BobGuard MVP — README

## Overview

BobGuard is described as a hackathon MVP demonstrating a debugging workflow
assisted by IBM Bob 2.0. The source README provided for this submission describes
a PowerShell prototype, the INC-001 pagination scenario, synthetic logs, tests, a
report-policy filter, and a release checker.

**Evidence status in this worktree:** the checkout available for this implementation
did not contain those prototype files. The structure, commands, and expected results
below preserve what the provided source README describes; they do not by themselves
prove that the files exist or that the commands were executed. INC-002 is not
described in that source README either. The web app distinguishes these documented
claims from artifacts actually found in the repository.

The Streamlit app is a visualization/replay, not a live IBM Bob execution. It does
not run PowerShell, call IBM Bob, watsonx.ai, or watsonx Orchestrate, or make network
requests. There is no direct integration with an IBM API. Demo incidents and logs
are synthetic.

## Structure described in the source README

The following paths and comments were described in the source README. They are not
present in the checkout used to build this app, except where explicitly indicated
in the table.

| Described path | Described purpose | Present in this checkout |
|---|---|---|
| `app/Invoke-Calculator.ps1` | Sample module, INC-001 bug | No |
| `tests/Invoke-Tests.ps1` | Unit + Regression test harness | No |
| `incidents/INC-001/incident.md` | Incident description | No |
| `incidents/INC-001/logs.md` | Synthetic logs | No |
| `docs/ADR-001-pagination.md` | Architecture decision | No |
| `docs/runbook-INC-001.md` | Incident runbook | No |
| `docs/release-policy.md` | Mechanical release conditions | No |
| `bobguard/CAPABILITIES.md` | Bob capabilities inventory | No |
| `bobguard/test-results.json` | Generated test results | No |
| `bobguard/policy-filter/Invoke-PolicyFilter.ps1` | Policy-filter CLI | No |
| `bobguard/policy-filter/Invoke-PolicyFilter.Tests.ps1` | Policy-filter tests | No |
| `bobguard/release-check/Invoke-ReleaseCheck.ps1` | Release-readiness CLI | No |
| `bobguard/reports/*` | Reports, summaries, verdict, and run log | No |
| `Invoke-BobGuardDemo.ps1` | Described demo orchestrator | No |
| `app.py`, `bobguard_demo.py` | Web demo and evidence reader | Yes |
| `tests/test_bobguard_demo.py` | Web demo tests | Yes |

## Prerequisites for the described prototype

The source README specifies PowerShell 5.1 (Windows 10/11) and says the prototype
requires no external dependencies, Node, Python, or the .NET SDK. These prerequisites
are part of the documentation for the missing prototype; the web demo does require
Python, as described below.

## INC-001: documented behavior, not reproduced here

The source README describes this command and its expected results:

```powershell
. .\app\Invoke-Calculator.ps1
Get-TotalPages -Count 25 -PageSize 10
# Result described with bug: 2
# Expected result: 3
```

The PowerShell module is not present in this worktree, so we cannot inspect the code,
confirm a fix, or reproduce that result.

### Documented commands and expectations

The source README says the unit tests should pass with the bug present (exit 0), the
regression suite should fail with the bug present (exit 1), and all tests should pass
after the fix (exit 0):

```powershell
.\tests\Invoke-Tests.ps1 -Suite Unit
.\tests\Invoke-Tests.ps1 -Suite Regression
.\tests\Invoke-Tests.ps1 -Suite All
```

These are documented expectations, not saved or rerun results. The PowerShell test
harness and its results are unavailable here. The web app has its own Python tests,
which do not validate the PowerShell prototype.

The source README also describes `Invoke-BobGuardDemo.ps1` as a workflow that applies
the fix and runs its phases. The script is not available in this checkout.

### INC-002

The provided source README does not describe INC-002, its cause, a fix, or test
results. The app does not infer this information from external summaries.

## Report policy and release

The source README describes a filter with these exit codes:

- `0`: no redactions
- `2`: content was redacted
- `1`: operational error

It also describes a release checker that consumes the sanitized report, policy
summary, test results, and incident description, and writes a JSON verdict. The
scripts, their outputs, and the dependency-audit gate are unavailable in this
checkout. Therefore, the app does not declare a global `APPROVED` status; a checker
result alone would not constitute a verified dependency audit either.

The filter is described as a demo limited to a documented list of synthetic/test
patterns in one report. It is not comprehensive secret detection, source-code
protection, process isolation, or a guarantee against data leakage. The web app's
display masking is also limited and is not a security control.

The following commands preserve the interface described in the source README. The
scripts at these paths are not included, so these commands cannot run in this
checkout:

```powershell
.\bobguard\policy-filter\Invoke-PolicyFilter.ps1 `
    -InputPath  .\bobguard\reports\raw-report.md `
    -OutputPath .\bobguard\reports\sanitized-report.md `
    -SummaryPath .\bobguard\reports\policy-summary.json

.\bobguard\policy-filter\Invoke-PolicyFilter.Tests.ps1

.\bobguard\release-check\Invoke-ReleaseCheck.ps1 `
    -SanitizedReportPath .\bobguard\reports\sanitized-report.md `
    -PolicySummaryPath   .\bobguard\reports\policy-summary.json `
    -TestResultsPath     .\bobguard\test-results.json `
    -IncidentPath        .\incidents\INC-001\incident.md `
    -OutputPath          .\bobguard\reports\release-verdict.json
```

## IBM Bob 2.0 usage and measurements

The source README declares file read/write, PowerShell execution, and code search as
capabilities verified in a session; it says concurrent subtasks were not verified.
The capabilities file and any transcript or log that could support that claim are
not present here. The app does not claim parallel execution.

The source README's table also marked Git, Node, Python, and the .NET SDK as
unavailable in that environment. Those statuses describe the referenced session,
not the current environment and not a check performed by this app.

The source README says no timed comparison was performed. Its measurements are
listed as pending:

| Documented metric | Manual | Bob-assisted | Status in README |
|---|---|---|---|
| Time to diagnosis | — | — | Pending |
| Time to passing regression test | — | — | Pending |
| Files inspected | — | 6 | Comparison pending |
| First successful fix | — | Yes | Comparison pending |
| Documents cited | — | 4 | Comparison pending |

These values and statuses are copied from the provided description, not independently
verified results. This app does not claim measured productivity improvements. The
source README does not document watsonx.ai or watsonx Orchestrate integration either.

## Roadmap described as not implemented

The source README lists Entra ID/MFA/RBAC, Azure Key Vault, an AKS pipeline, subtask
isolation, native evidence of parallel execution, dependency auditing, and metric
comparison as pending enterprise features. They are not presented as capabilities
of this app.

## Web demo: run locally

Requires Python 3.10 or later.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL shown by Streamlit in the terminal (usually
`http://localhost:8501`). To run the app's tests:

```powershell
python -m unittest discover -s tests -v
```

The app searches repository artifacts by incident ID and displays bounded excerpts
with masking for some common patterns. This masking is not comprehensive. The IDs
in the selector do not imply that their files are present.

## Deploy to Streamlit Community Cloud

1. Publish this repository to GitHub when you decide to do so.
2. In Streamlit Community Cloud, create an app and select the repository, the branch
   you want to deploy, and `app.py` as the entry point.
3. Streamlit will install the pinned dependency in `requirements.txt`. No secrets
   or environment variables are required.

**Status:** not deployed or published; there is no public URL.
