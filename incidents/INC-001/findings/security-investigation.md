# INC-001 — Security / Release Investigation Findings

Investigation mode: SEQUENTIAL (parallel execution NOT VERIFIED per bobguard/CAPABILITIES.md)

## Scope of Security Scan

Scanned files:
- `incidents/INC-001/incident.md`
- `incidents/INC-001/logs.md`
- `app/Invoke-Calculator.ps1`
- `bobguard/reports/raw-report.md`

Scan method: Pattern-based (policy filter patterns from `docs/release-policy.md`).
This is NOT comprehensive secret detection. See policy disclaimer.

## Secret Patterns Checked

| Pattern | Found in raw inputs? | Action |
|---|---|---|
| `BOBGUARD-KEY-[A-Za-z0-9]{16,}` | YES — in `raw-report.md` demo section | Redacted by policy filter (exit 2) |
| `db_password\s*=\s*\S+` | No | N/A |
| `Bearer\s+[A-Za-z0-9\-._~+/]{20,}` | No | N/A |

The synthetic credential `BOBGUARD-KEY-SYNTHETICTESTONLY9999` in `raw-report.md`
is explicitly labeled as "SYNTHETIC and NONFUNCTIONAL" and exists solely to
demonstrate the policy filter. It was correctly redacted in the sanitized report.

## Dependency Audit

NOT VERIFIED — no package manager (`npm`, `pip`, `dotnet` SDK) available in this
environment. Per `docs/release-policy.md` R5: this condition must be marked
NOT VERIFIED, not silently passed.

## Security Scope Limitations

- Pattern-based filter covers only 3 documented patterns. It does NOT detect
  arbitrary credentials, environment variables, or secrets in binary/non-text files.
- No source-code isolation, sandboxing, or RBAC implemented (roadmap).
- No network access or external service scan performed.
- Real production credentials: none present in this workspace (all data is synthetic).

## Release Policy Conditions (Security-relevant)

| Condition | Status | Evidence |
|---|---|---|
| R3: Final sanitized report has 0 unredacted patterns | PASS | policy-summary-final.json: RedactedCount=0 |
| R5: Dependency audit | NOT VERIFIED | No package manager available |
