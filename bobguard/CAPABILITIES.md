# BobGuard MVP — IBM Bob 2.0 Capability Inventory

Generated during Phase 0 inspection. Last updated: Phase 0.

## Confirmed Available

| Capability | Evidence |
|---|---|
| File read / write / search | Native Bob tools: `read_file`, `write_file`, `grep`, `glob`, `apply_diff` used successfully |
| Shell execution (PowerShell 5.1) | `execute_command` ran PowerShell cmdlets; workspace CWD responds |
| .NET 8 runtime | `dotnet --list-runtimes` returned `Microsoft.NETCore.App 8.0.24` |
| Bob subtask spawn | `spawn_subagent` tool is listed in available tools |
| Bob parallel subtask evidence | **NOT VERIFIED** — tool is available but no native Bob event log or task-state stream is exposed in this session to prove concurrent execution. Timestamps written by the agent alone are not proof. |

## Confirmed Unavailable

| Capability | Evidence |
|---|---|
| `git` CLI | `git` not found on PATH; `CommandNotFoundException` |
| `node` / `npm` | Not found on PATH |
| `python` / `python3` | Windows store stub only; no real interpreter |
| `dotnet` SDK | Runtime present but `No .NET SDKs were found` |
| `pip` | Not found on PATH |
| Remote / PR operations | No git CLI; no remote configured |

## Unverified / Not Probed

| Capability | Reason |
|---|---|
| Entra ID / MFA / AKS / Key Vault / RBAC | Enterprise features not present in this environment; moved to roadmap |
| Actual secret detection (non-pattern) | Policy filter is pattern-based only; see Phase 3 disclaimer |
| Source-code isolation / sandboxing | Not implemented; moved to roadmap |

## Chosen Stack for MVP

- **Language / runtime:** PowerShell 5.1 (guaranteed available)
- **Sample app:** `app/Invoke-Calculator.ps1` — a pure-function module
- **Test harness:** `tests/Invoke-Tests.ps1` — custom minimal runner (no external test framework)
- **Policy filter:** `bobguard/policy-filter/Invoke-PolicyFilter.ps1`
- **Release readiness:** `bobguard/release-check/Invoke-ReleaseCheck.ps1`
