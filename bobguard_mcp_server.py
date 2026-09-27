#!/usr/bin/env python3
"""
BobGuard MCP Server
Exposes BobGuard tools to IBM Bob 2.0 via the Model Context Protocol (stdio).

Tools provided:
  - run_tests           Run the PowerShell test suite and return results.
  - get_incident        Read incident metadata and description.
  - get_release_verdict Read the latest release-readiness verdict from JSON.
  - run_policy_filter   Run the policy filter on a report file.
  - get_capabilities    Return the verified IBM Bob capability inventory.

Usage (stdio, spawned by Bob):
  python bobguard_mcp_server.py

Log output goes to stderr only — stdout is the MCP protocol channel.
"""

import json
import subprocess
import sys
from pathlib import Path

from mcp.server.mcpserver import MCPServer

# ── Repo root ──────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent

server = MCPServer(
    name="bobguard",
    version="0.1.0",
    instructions=(
        "BobGuard tools expose the local BobGuard MVP repository. "
        "Use run_tests to execute the PowerShell test suite, "
        "get_incident to read incident details, "
        "get_release_verdict to check release readiness, "
        "run_policy_filter to sanitize a report, "
        "and get_capabilities to see what IBM Bob 2.0 capabilities are verified."
    ),
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _repo(rel: str) -> Path:
    return REPO_ROOT / rel


def _read(rel: str) -> str | None:
    p = _repo(rel)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else None


def _load_json(rel: str):
    p = _repo(rel)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"error": str(exc)}


def _ps(script: str, args: list[str] | None = None, timeout: int = 30) -> dict:
    """Run a PowerShell script and return stdout, stderr, and exit_code."""
    cmd = ["powershell", "-NonInteractive", "-NoProfile", "-File", str(_repo(script))]
    if args:
        cmd.extend(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(REPO_ROOT),
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": "Timeout after 30s"}
    except FileNotFoundError:
        return {"exit_code": -1, "stdout": "", "stderr": "powershell not found on PATH"}


# ── Tool: run_tests ─────────────────────────────────────────────────────────

@server.tool(
    description=(
        "Run the BobGuard PowerShell test suite and return results. "
        "suite must be 'Unit', 'Regression', or 'All' (default: 'All'). "
        "Returns stdout output, exit_code (0=all pass, 1=failures), "
        "and the parsed test-results.json if available."
    ),
)
def run_tests(suite: str = "All") -> str:
    valid = {"Unit", "Regression", "All"}
    if suite not in valid:
        return json.dumps({
            "error": f"Invalid suite '{suite}'. Must be one of: {sorted(valid)}",
            "isError": True,
        })

    result = _ps("tests/Invoke-Tests.ps1", ["-Suite", suite])

    # Load the JSON results written by the test runner
    test_json = _load_json("bobguard/test-results.json")

    summary = {
        "suite": suite,
        "exit_code": result["exit_code"],
        "passed": result["exit_code"] == 0,
        "stdout": result["stdout"].strip(),
        "stderr": result["stderr"].strip() or None,
        "test_results_json": test_json,
    }
    return json.dumps(summary, indent=2, ensure_ascii=False)


# ── Tool: get_incident ──────────────────────────────────────────────────────

@server.tool(
    description=(
        "Read incident metadata and description from the repository. "
        "incident_id must be 'INC-001' or 'INC-002'. "
        "Returns the incident.md text, logs.md text, "
        "and a list of available finding files."
    ),
)
def get_incident(incident_id: str) -> str:
    valid = {"INC-001", "INC-002"}
    if incident_id not in valid:
        return json.dumps({
            "error": f"Unknown incident '{incident_id}'. Valid: {sorted(valid)}",
            "isError": True,
        })

    base = f"incidents/{incident_id}"
    incident_md = _read(f"{base}/incident.md")
    logs_md = _read(f"{base}/logs.md")

    findings: list[dict] = []
    findings_dir = _repo(f"{base}/findings")
    if findings_dir.exists():
        for f in sorted(findings_dir.iterdir()):
            if f.is_file():
                findings.append({
                    "file": f.name,
                    "path": str(f.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "content": f.read_text(encoding="utf-8", errors="replace"),
                })

    return json.dumps(
        {
            "incident_id": incident_id,
            "incident_md": incident_md or "(file not found)",
            "logs_md": logs_md or "(file not found)",
            "findings": findings,
        },
        indent=2,
        ensure_ascii=False,
    )


# ── Tool: get_release_verdict ───────────────────────────────────────────────

@server.tool(
    description=(
        "Return the latest release-readiness verdict for BobGuard. "
        "Reads the pre-generated JSON verdict files from bobguard/reports/. "
        "version must be 'v2' (final, APPROVED) or 'v1' (intermediate, BLOCKED). "
        "Default: 'v2'. "
        "IMPORTANT: R5 (dependency audit) is always NOT VERIFIED in this environment. "
        "The verdict is a local checker result — not a production approval."
    ),
)
def get_release_verdict(version: str = "v2") -> str:
    paths = {
        "v2": "bobguard/reports/final-release-verdict-v2.json",
        "v1": "bobguard/reports/final-release-verdict.json",
    }
    if version not in paths:
        return json.dumps({
            "error": f"Unknown version '{version}'. Use 'v1' or 'v2'.",
            "isError": True,
        })

    data = _load_json(paths[version])
    if data is None:
        return json.dumps({"error": f"File not found: {paths[version]}", "isError": True})

    # Attach a disclaimer so Bob always surfaces the correct context
    data["_disclaimer"] = (
        "This verdict is produced by the local Invoke-ReleaseCheck.ps1 script. "
        "R5 (dependency audit) is NOT VERIFIED — no package manager available. "
        "This is not a production approval."
    )
    return json.dumps(data, indent=2, ensure_ascii=False)


# ── Tool: run_policy_filter ─────────────────────────────────────────────────

@server.tool(
    description=(
        "Run the BobGuard policy filter to sanitize a report file. "
        "Redacts the 3 documented synthetic secret patterns. "
        "input_report is the path relative to the repo root (e.g. 'bobguard/reports/raw-report.md'). "
        "output_report is the output path (default: 'bobguard/reports/policy-filter-output.md'). "
        "summary_path is the JSON summary path (default: 'bobguard/reports/policy-filter-summary.json'). "
        "Returns exit_code (0=no redactions, 2=content redacted, 1=error) and the summary JSON. "
        "WARNING: This filter covers only 3 synthetic patterns and is NOT comprehensive secret detection."
    ),
)
def run_policy_filter(
    input_report: str = "bobguard/reports/raw-report.md",
    output_report: str = "bobguard/reports/policy-filter-output.md",
    summary_path: str = "bobguard/reports/policy-filter-summary.json",
) -> str:
    # Safety: only allow paths inside the repo, no traversal
    try:
        in_path = (_repo(input_report)).resolve()
        out_path = (_repo(output_report)).resolve()
        sum_path = (_repo(summary_path)).resolve()
        REPO_ROOT.resolve()
        for p in (in_path, out_path, sum_path):
            p.relative_to(REPO_ROOT.resolve())  # raises ValueError if outside
    except ValueError:
        return json.dumps({
            "error": "Path traversal detected — all paths must be inside the repo.",
            "isError": True,
        })

    if not in_path.exists():
        return json.dumps({
            "error": f"Input file not found: {input_report}",
            "isError": True,
        })

    result = _ps(
        "bobguard/policy-filter/Invoke-PolicyFilter.ps1",
        [
            "-InputPath", str(in_path),
            "-OutputPath", str(out_path),
            "-SummaryPath", str(sum_path),
        ],
    )

    summary = _load_json(str(sum_path.relative_to(REPO_ROOT)))

    return json.dumps(
        {
            "exit_code": result["exit_code"],
            "exit_meaning": {0: "no redactions", 2: "content redacted", 1: "operational error"}.get(
                result["exit_code"], "unknown"
            ),
            "stdout": result["stdout"].strip(),
            "stderr": result["stderr"].strip() or None,
            "summary": summary,
            "_disclaimer": (
                "This filter covers exactly 3 synthetic patterns. "
                "It is NOT comprehensive secret detection."
            ),
        },
        indent=2,
        ensure_ascii=False,
    )


# ── Tool: get_capabilities ──────────────────────────────────────────────────

@server.tool(
    description=(
        "Return the verified IBM Bob 2.0 capability inventory for this environment. "
        "Lists confirmed-available, confirmed-unavailable, and unverified capabilities. "
        "Source: bobguard/CAPABILITIES.md"
    ),
)
def get_capabilities() -> str:
    content = _read("bobguard/CAPABILITIES.md")
    if content is None:
        return json.dumps({"error": "bobguard/CAPABILITIES.md not found", "isError": True})

    # Return structured summary alongside the raw markdown
    return json.dumps(
        {
            "source": "bobguard/CAPABILITIES.md",
            "summary": {
                "confirmed_available": [
                    "File read/write/search (read_file, write_file, grep, glob, apply_diff)",
                    "Shell execution (PowerShell 5.1 via execute_command)",
                    ".NET 8 runtime (Microsoft.NETCore.App 8.0.24)",
                    "Subagent spawn (spawn_subagent tool listed)",
                ],
                "not_verified": [
                    "Parallel subagent execution (tool available, concurrency not natively proven)",
                ],
                "confirmed_unavailable": [
                    "git CLI",
                    "node / npm",
                    "python / python3 (Windows Store stub only — external Python 3.12 is available)",
                    "dotnet SDK (runtime present, no SDK)",
                    "pip (not on Bob PATH — external pip available)",
                    "Remote / PR operations",
                ],
            },
            "raw_markdown": content,
        },
        indent=2,
        ensure_ascii=False,
    )


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("BobGuard MCP server starting on stdio", file=sys.stderr)
    server.run(transport="stdio")
