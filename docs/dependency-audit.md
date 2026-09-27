# Python Dependencies and Audit

Last checked: 2026-09-27

## Install sets

- `requirements.txt` contains the Streamlit demo's direct runtime dependencies.
- `requirements-mcp.txt` contains the optional MCP server dependency. The Streamlit
  demo does not require the MCP server.
- `requirements-dev.txt` combines both sets and pins `pip-audit` for local
  dependency checks and pip 26.2.1 for the installer.

The direct dependencies are pinned to the latest versions available from the
configured package index on the date above. Install the intended set in a
virtual environment; do not install the optional MCP dependency unless you use
`bobguard_mcp_server.py`.

## Audit

The declared runtime and optional MCP dependency sets were checked with
`pip-audit` on 2026-09-27:

```powershell
python -m pip_audit -r requirements.txt --progress-spinner off
python -m pip_audit -r requirements-mcp.txt --progress-spinner off
```

Both checks reported `No known vulnerabilities found`. The audit reflects the
dependency metadata and vulnerability database available at check time; rerun
it before publishing or deploying.

Audit the development tool together with both dependency sets by installing
`requirements-dev.txt` and running:

```powershell
python -m pip_audit --progress-spinner off
```

The combined development audit also reported `No known vulnerabilities found`.
Pinning pip is important in environments that bootstrap with an older,
vulnerable installer; for example, the original Python 3.12 venv's pip 25.0.1
reported 12 advisories and was upgraded to 26.2.1 before the clean audit.

This local audit does not alter the historical release-verdict artifacts.
Release check R5 remains `NOT VERIFIED` in those artifacts because the
repository's release checker does not consume a dependency-audit result.
