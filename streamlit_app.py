"""
BobGuard MVP — Streamlit Demo
Visualizes the evidence available in this repository.
No live IBM Bob integration. No external services.
"""

import json
import os
from pathlib import Path

import streamlit as st

# ── Constants ─────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent

# Evidence status labels
VERIFIED = "✅ Verified"
DOCUMENTED_UNVERIFIED = "📄 Documented / not verified here"
PENDING = "🔲 Pending"
OPEN = "🔴 Open"
BLOCKED = "🔴 BLOCKED"
NOT_VERIFIED = "⚠️ NOT VERIFIED"
APPROVED = "✅ APPROVED"
PASS_LABEL = "✅ PASS"
FAIL_LABEL = "❌ FAIL"

# ── Data loaders (never fabricate — return None / empty on missing) ────────────

def load_json(rel_path: str):
    """Load a JSON file relative to repo root. Returns None if missing."""
    p = REPO_ROOT / rel_path
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def file_exists(rel_path: str) -> bool:
    return (REPO_ROOT / rel_path).exists()


def read_text(rel_path: str) -> str | None:
    p = REPO_ROOT / rel_path
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8", errors="replace")


def check_fix_applied() -> bool:
    """Return True if INC-001 fix is present in the source file."""
    src = read_text("app/Invoke-Calculator.ps1")
    if src is None:
        return False
    return "[Math]::Ceiling($Count / $PageSize)" in src


def check_inc002_bug_present() -> bool:
    """Return True if INC-002 bug is still present (no AwayFromZero)."""
    src = read_text("app/Invoke-Calculator.ps1")
    if src is None:
        return False
    return "AwayFromZero" not in src


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="BobGuard MVP",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🛡️ BobGuard MVP")
    st.caption("Local evidence demo — no live IBM Bob integration")
    st.divider()

    page = st.radio(
        "Navigate to:",
        [
            "Home",
            "INC-001: Pagination",
            "INC-002: Rounding",
            "Policy filter",
            "Release check",
            "IBM Bob 2.0",
            "Limitations and roadmap",
        ],
        index=0,
    )

    st.divider()
    st.caption(
        "⚠️ This app displays evidence from the local repository. "
        "It is not publicly deployed and does not run IBM Bob live."
    )

# ── Helper widgets ────────────────────────────────────────────────────────────

def badge(label: str) -> str:
    """Return colored Markdown badge text."""
    if label.startswith("✅"):
        return f":green[{label}]"
    if label.startswith("❌") or label.startswith("🔴"):
        return f":red[{label}]"
    if label.startswith("⚠️"):
        return f":orange[{label}]"
    if label.startswith("📄"):
        return f":blue[{label}]"
    return label


def evidence_row(label: str, value: str, status: str, path: str = ""):
    cols = st.columns([3, 4, 2, 3])
    cols[0].write(f"**{label}**")
    cols[1].write(value)
    cols[2].markdown(badge(status))
    if path:
        cols[3].code(path, language=None)
    else:
        cols[3].write("")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: HOME
# ══════════════════════════════════════════════════════════════════════════════

if page == "Home":
    st.title("🛡️ BobGuard MVP")
    st.subheader("AI-assisted debugging and incident investigation workflow demo")

    st.info(
        "**About this app**  \n"
        "This app displays the evidence available in this repository. "
        "It clearly distinguishes between code-verified artifacts, "
        "results described in documentation, and pending capabilities. "
        "It is not publicly deployed and does not run IBM Bob live.",
        icon="ℹ️",
    )

    st.divider()

    # ── Problem ──
    st.header("The debugging problem")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**Without AI assistance:**
- Engineers review logs manually.
- They investigate multiple files and functions.
- They run tests one at a time.
- They write reports without automation.
- Release review is a manual checklist.

Triage can take longer than the actual fix.
        """)
    with col2:
        st.markdown("""
**With BobGuard + IBM Bob 2.0 (proposed):**
- The agent reads logs, code, and docs in parallel*.
- It identifies the affected function and root cause.
- It runs the test suite and confirms the fix.
- It applies a policy filter to reports.
- It produces a structured release verdict.

*Parallel subagent execution is available as a tool, but **has not been natively verified** in this environment — see the IBM Bob 2.0 section.
        """)

    st.divider()

    # ── Incidents ──
    st.header("Incidents in this repository")
    col_a, col_b = st.columns(2)

    inc001_fix = check_fix_applied()
    with col_a:
        st.markdown("### INC-001 — Pagination")
        st.markdown(f"**Status:** {'✅ RESOLVED' if inc001_fix else '🔴 FIX NOT DETECTED'}")
        st.markdown(
            "The `Get-TotalPages` function used integer truncation instead of `Ceiling`. "
            "The last partial page of records was silently dropped."
        )
        st.markdown(f"**Source file:** `app/Invoke-Calculator.ps1` — {'fix present' if inc001_fix else 'fix not found'}")

    with col_b:
        st.markdown("### INC-002 — Rounding")
        inc002_bug = check_inc002_bug_present()
        st.markdown(f"**Status:** {'🔴 OPEN (bug present)' if inc002_bug else '✅ FIX DETECTED'}")
        st.markdown(
            "`ConvertTo-DiscountedPrice` usa `[Math]::Round` sin `AwayFromZero`. "
            "Midpoint values are rounded incorrectly (Banker's rounding)."
        )
        st.markdown(f"**Source file:** `app/Invoke-Calculator.ps1` — {'no fix' if inc002_bug else 'fix applied'}")

    st.divider()

    # ── Evidence summary ──
    st.header("Evidence summary by category")
    test_results = load_json("bobguard/test-results.json")
    total = len(test_results) if test_results else 0
    passed = sum(1 for t in test_results if t.get("Status") == "PASS") if test_results else 0

    verdict_v2 = load_json("bobguard/reports/final-release-verdict-v2.json")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tests in JSON", total, help="From bobguard/test-results.json")
    col2.metric("Passing tests", passed)
    col3.metric(
        "Release verdict",
        verdict_v2.get("Verdict", "N/A") if verdict_v2 else "N/A",
        help="From final-release-verdict-v2.json",
    )
    col4.metric(
        "Incident files",
        sum(1 for p in ["incidents/INC-001/incident.md", "incidents/INC-002/incident.md"] if file_exists(p)),
    )

    st.caption(
        "The values above are read from repository files at runtime. "
        "They are not results from a live execution."
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: INC-001
# ══════════════════════════════════════════════════════════════════════════════

elif page == "INC-001: Pagination":
    st.title("INC-001 — Billing Pagination: Last Page Silently Dropped")

    inc001_fix = check_fix_applied()
    if inc001_fix:
        st.success("✅ Fix verified in `app/Invoke-Calculator.ps1` (current line: `[Math]::Ceiling`)")
    else:
        st.error("❌ Fix not detected in the current source code.")

    st.divider()

    # ── Metadata ──
    st.subheader("Incident metadata")
    col1, col2 = st.columns(2)
    with col1:
        evidence_row("ID", "INC-001", VERIFIED, "incidents/INC-001/incident.md")
        evidence_row("Severity", "High", VERIFIED, "incidents/INC-001/incident.md")
        evidence_row("Status", "RESOLVED", VERIFIED, "incidents/INC-001/incident.md")
    with col2:
        evidence_row("Componente", "Get-TotalPages", VERIFIED, "app/Invoke-Calculator.ps1")
        evidence_row("Fix applied", "Ceiling division", VERIFIED, "app/Invoke-Calculator.ps1:38")
        evidence_row("Violated ADR", "ADR-001 (2026-09-01)", VERIFIED, "docs/ADR-001-pagination.md")

    st.divider()

    # ── Root cause ──
    st.subheader("Root cause (verified in source code)")
    col_bug, col_fix = st.columns(2)
    with col_bug:
        st.markdown("**Before the fix (bug):**")
        st.code("return [int]($Count / $PageSize)", language="powershell")
        st.caption(
            "For Count=25, PageSize=10: `25/10 = 2.5` → `[int]` truncates → `2`. "
            "Page 2 (5 records) is never processed."
        )
    with col_fix:
        st.markdown("**After the fix (current):**")
        st.code("return [Math]::Ceiling($Count / $PageSize)", language="powershell")
        st.caption(
            "Para Count=25, PageSize=10: `Ceiling(2.5) = 3`. "
            "All 3 pages are processed. Fix verified on line 38 of the current file."
        )

    # Reproduce exact content
    src = read_text("app/Invoke-Calculator.ps1")
    if src:
        with st.expander("View current source code — `app/Invoke-Calculator.ps1`"):
            st.code(src, language="powershell")
    else:
        st.warning("`app/Invoke-Calculator.ps1` not found.")

    st.divider()

    # ── Synthetic logs ──
    st.subheader("Incident logs")
    st.warning(
        "The logs below are **synthetic and labeled** — constructed to match "
        "the source code. They are not from a production system.",
        icon="⚠️",
    )
    logs = read_text("incidents/INC-001/logs.md")
    if logs:
        with st.expander("View logs — `incidents/INC-001/logs.md`"):
            st.markdown(logs)
    else:
        st.error("Log file not found.")

    st.divider()

    # ── Investigation findings ──
    st.subheader("Investigation findings")
    tabs = st.tabs(["Developer", "Operations", "Security"])
    finding_files = {
        "Developer": "incidents/INC-001/findings/dev-investigation.md",
        "Operations": "incidents/INC-001/findings/ops-investigation.md",
        "Security": "incidents/INC-001/findings/security-investigation.md",
    }
    for tab, (name, path) in zip(tabs, finding_files.items()):
        with tab:
            content = read_text(path)
            if content:
                st.markdown(content)
                st.caption(f"Source: `{path}` — {VERIFIED}")
            else:
                st.error(f"File not found: `{path}`")

    st.divider()

    # ── Test results for INC-001 ──
    st.subheader("Test results related to INC-001")
    test_results = load_json("bobguard/test-results.json")
    if test_results:
        inc001_tests = [
            t for t in test_results
            if "TotalPages" in t.get("Name", "") or "PagedItems" in t.get("Name", "")
        ]
        for t in inc001_tests:
            status_icon = "✅" if t["Status"] == "PASS" else "❌"
            cols = st.columns([1, 4, 2, 2])
            cols[0].write(status_icon)
            cols[1].write(t["Name"])
            cols[2].write(f"Expected: `{t['Expected']}`")
            cols[3].write(f"Actual: `{t['Actual']}`")
        st.caption(f"Source: `bobguard/test-results.json` — {VERIFIED}")
    else:
        st.error("`bobguard/test-results.json` not found.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: INC-002
# ══════════════════════════════════════════════════════════════════════════════

elif page == "INC-002: Rounding":
    st.title("INC-002 — Billing Rounding: Midpoint Rounded to Even (Banker's Rounding)")

    inc002_bug = check_inc002_bug_present()
    if inc002_bug:
        st.error(
            "🔴 **OPEN** — Bug present in `app/Invoke-Calculator.ps1`. "
            "No fix has been applied."
        )
    else:
        st.success("✅ Fix detected in the source code.")

    st.info(
        "INC-002 is **independent** of INC-001 (different function, different root cause). "
        "It is intentionally left open for the demonstration.",
        icon="ℹ️",
    )

    st.divider()

    # ── Metadata ──
    st.subheader("Incident metadata")
    col1, col2 = st.columns(2)
    with col1:
        evidence_row("ID", "INC-002", VERIFIED, "incidents/INC-002/incident.md")
        evidence_row("Severity", "Medium", VERIFIED, "incidents/INC-002/incident.md")
        evidence_row("Status", "OPEN (no fix)", VERIFIED, "incidents/INC-002/incident.md")
    with col2:
        evidence_row("Componente", "ConvertTo-DiscountedPrice", VERIFIED, "app/Invoke-Calculator.ps1")
        evidence_row("Fix applied", "No", VERIFIED, "app/Invoke-Calculator.ps1:49")
        evidence_row("Additional evidence", "No fix artifacts", OPEN, "")

    st.divider()

    # ── Root cause ──
    st.subheader("Root cause (verified in source code)")
    col_bug, col_fix = st.columns(2)
    with col_bug:
        st.markdown("**Current code (bug present):**")
        st.code(
            "return [Math]::Round($UnitPrice * (1 - $DiscountPct / 100), 2)",
            language="powershell",
        )
        st.caption(
            "`[Math]::Round(value, 2)` uses `MidpointRounding.ToEven` by default. "
            "For 0.225: it rounds to the even digit → **0.22** (incorrect)."
        )
    with col_fix:
        st.markdown("**Proposed fix (NOT applied):**")
        st.code(
            "return [Math]::Round($UnitPrice * (1 - $DiscountPct / 100), 2,\n"
            "    [System.MidpointRounding]::AwayFromZero)",
            language="powershell",
        )
        st.caption(
            "For 0.225: `AwayFromZero` → **0.23** (correct). "
            "Fix documented in `incidents/INC-002/incident.md`, **not applied**."
        )

    st.divider()

    # ── Table of affected cases ──
    st.subheader("Cases affected by the bug")
    st.markdown(
        "Only exact midpoint values (`intermediate % 0.01 == 0.005`) differ. "
        "Non-midpoint values are identical in both modes."
    )
    import pandas as pd  # local import; streamlit bundles pandas
    df = pd.DataFrame(
        [
            ("$0.25", "10%", "$0.225", "$0.22 ❌", "$0.23 ✅", "-$0.01"),
            ("$0.05", "50%", "$0.025", "$0.02 ❌", "$0.03 ✅", "-$0.01"),
            ("$1.00", "10%", "$0.90",  "$0.90 ✅", "$0.90 ✅", "$0.00"),
            ("$99.99", "33.33%", "$66.66…", "$66.66 ✅", "$66.66 ✅", "$0.00"),
        ],
        columns=["Price", "Discount", "Intermediate", "ToEven (bug)", "AwayFromZero (expected)", "Delta"],
    )
    st.dataframe(df, width="stretch", hide_index=True)
    st.caption(f"Source: `incidents/INC-002/incident.md` — {VERIFIED}")

    st.divider()

    # ── Synthetic logs ──
    st.subheader("Incident logs")
    st.warning(
        "The logs below are **synthetic and labeled** — constructed to match "
        "the source code. They are not from a production system.",
        icon="⚠️",
    )
    logs = read_text("incidents/INC-002/logs.md")
    if logs:
        with st.expander("View logs — `incidents/INC-002/logs.md`"):
            st.markdown(logs)
    else:
        st.error("Log file not found.")

    st.divider()

    # ── Test results for INC-002 ──
    st.subheader("Test results related to INC-002")
    test_results = load_json("bobguard/test-results.json")
    if test_results:
        inc002_tests = [
            t for t in test_results
            if "Discount" in t.get("Name", "") or "INC-002" in t.get("Name", "")
        ]
        for t in inc002_tests:
            status_icon = "✅" if t["Status"] == "PASS" else "❌"
            cols = st.columns([1, 4, 2, 2])
            cols[0].write(status_icon)
            cols[1].write(t["Name"])
            note = t.get("Note", "")
            label = f"`{t['Expected']}`"
            cols[2].write(f"Expected: {label}")
            cols[3].write(f"Actual: `{t['Actual']}`")
        st.caption(f"Source: `bobguard/test-results.json` — {VERIFIED}")
        st.info(
            "The discount tests in the JSON use **non-midpoint** values "
            "(they pass with either rounding mode). "
            "INC-002 midpoint regression tests run with `tests/Invoke-Tests.ps1 -Suite Regression` "
            "and currently FAIL with the current code.",
            icon="ℹ️",
        )
    else:
        st.error("`bobguard/test-results.json` not found.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: POLICY FILTER
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Policy filter":
    st.title("Policy Filter — Report Sanitization")

    st.info(
        "The policy filter redacts a **bounded** set of synthetic secret patterns "
        "before reports are shared. "
        "**It is not comprehensive credential detection.** "
        "It covers exactly 3 documented patterns.",
        icon="ℹ️",
    )

    st.divider()

    # ── Covered patterns ──
    st.subheader("Covered patterns")
    import pandas as pd
    df_patterns = pd.DataFrame(
        [
            ("Synthetic API key", "`BOBGUARD-KEY-[A-Za-z0-9]{16,}`", VERIFIED),
            ("Synthetic DB password", "`db_password\\s*=\\s*\\S+`", VERIFIED),
            ("Synthetic bearer token", "`Bearer\\s+[A-Za-z0-9\\-._~+/]{20,}`", VERIFIED),
        ],
        columns=["Name", "Regex", "Status"],
    )
    st.dataframe(df_patterns, width="stretch", hide_index=True)
    st.caption(f"Source: `docs/release-policy.md` — {VERIFIED}")

    st.warning(
        "This filter is **not** arbitrary secret detection, source-code protection, "
        "process isolation, or a guarantee against data leakage. "
        "It demonstrates report sanitization for a synthetic set of patterns.",
        icon="⚠️",
    )

    st.divider()

    # ── Recorded runs ──
    st.subheader("Recorded runs")
    summary_v2 = load_json("bobguard/reports/final-report-policy-summary-v2.json")
    summary_final = load_json("bobguard/reports/policy-summary-final.json")
    summary_v1 = load_json("bobguard/reports/policy-summary.json")

    for label, data, path in [
        ("Run v2 (final-report-raw.md)", summary_v2, "bobguard/reports/final-report-policy-summary-v2.json"),
        ("Final run (sanitized→clean)", summary_final, "bobguard/reports/policy-summary-final.json"),
        ("Run v1 (raw-report.md)", summary_v1, "bobguard/reports/policy-summary.json"),
    ]:
        if data:
            with st.expander(f"📄 {label}"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Redactions", data.get("RedactedCount", "N/A"))
                c2.metric("Truncated blocks", data.get("TruncatedBlocks", "N/A"))
                c3.metric("Timestamp", data.get("Timestamp", "N/A")[:19] if data.get("Timestamp") else "N/A")
                redacted = data.get("RedactedItems", [])
                if redacted:
                    st.markdown("**Redacted items:**")
                    for item in redacted:
                        # Show type only — NEVER show key value
                        st.write(f"- Type: `{item.get('Type', '?')}` — preview: `[REDACTED]`")
                    st.caption("The exact value is not shown. It appeared in raw-report.md as synthetic data and was redacted.")
                st.caption(f"Source: `{path}` — {VERIFIED}")
        else:
            st.warning(f"File not found: `{path}`")

    st.divider()

    # ── Script ──
    st.subheader("Filter script")
    if file_exists("bobguard/policy-filter/Invoke-PolicyFilter.ps1"):
        src = read_text("bobguard/policy-filter/Invoke-PolicyFilter.ps1")
        with st.expander("View `bobguard/policy-filter/Invoke-PolicyFilter.ps1`"):
            st.code(src, language="powershell")
        st.caption(f"Source: `bobguard/policy-filter/Invoke-PolicyFilter.ps1` — {VERIFIED}")
    else:
        st.error("Script not found.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: RELEASE CHECK
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Release check":
    st.title("Release Readiness Check")

    st.info(
        "The release check evaluates the mechanical conditions in `docs/release-policy.md`. "
        "The verdict shown here comes from JSON files generated by "
        "`Invoke-ReleaseCheck.ps1` — not from a live execution.",
        icon="ℹ️",
    )

    stored_test_results = load_json("bobguard/test-results.json") or []
    regression_results = [
        result for result in stored_test_results
        if " regression:" in result.get("Name", "").lower()
    ]
    failed_regressions = [
        result for result in regression_results
        if result.get("Status") == "FAIL"
    ]
    if len(regression_results) < 8 or failed_regressions or check_inc002_bug_present():
        st.error(
            f"Current release readiness is BLOCKED: "
            f"{len(regression_results)}/8 regression results are recorded and "
            f"{len(failed_regressions)} recorded regression test(s) fail. "
            "INC-002 remains open. The saved verdict files are historical snapshots, "
            "not current release approval."
        )

    st.divider()

    # ── Verdicts ──
    verdict_v2 = load_json("bobguard/reports/final-release-verdict-v2.json")
    verdict_v1 = load_json("bobguard/reports/final-release-verdict.json")

    col1, col2 = st.columns(2)
    for col, verdict, label, path in [
        (col1, verdict_v2, "Verdict v2 (final)", "bobguard/reports/final-release-verdict-v2.json"),
        (col2, verdict_v1, "Verdict v1 (intermediate)", "bobguard/reports/final-release-verdict.json"),
    ]:
        with col:
            st.subheader(label)
            if verdict:
                v = verdict.get("Verdict", "N/A")
                if v == "APPROVED":
                    st.success(f"**Verdict: {v}**")
                elif v == "BLOCKED":
                    st.error(f"**Verdict: {v}**")
                else:
                    st.warning(f"**Verdict: {v}**")

                st.warning(
                    "⚠️ This verdict is the result of the local checker, "
                    "**not a production approval**. "
                    "R5 (dependency audit) is marked NOT VERIFIED in all cases.",
                    icon="⚠️",
                )

                checks = verdict.get("Checks", [])
                for c in checks:
                    s = c.get("Status", "")
                    icon = "✅" if s == "PASS" else ("❌" if s == "BLOCKED" else "⚠️")
                    detail = c.get("Detail", "")
                    st.write(f"{icon} **{c['Check']}** — {s}")
                    if detail:
                        st.caption(f"  {detail}")

                ts = verdict.get("Timestamp", "")
                if ts:
                    st.caption(f"Timestamp: {ts[:19]}")
                st.caption(f"Source: `{path}` — {VERIFIED}")
            else:
                st.error(f"File not found: `{path}`")

    st.divider()

    # ── Policy conditions ──
    st.subheader("Release policy conditions")
    import pandas as pd
    df_policy = pd.DataFrame(
        [
            ("R1", "Unit tests pass", "`Invoke-Tests.ps1 -Suite Unit` exits 0", VERIFIED),
            ("R2", "Regression tests pass", "`Invoke-Tests.ps1 -Suite Regression` exits 0", VERIFIED),
            ("R3", "Final report has no unredacted secrets", "Policy filter RedactedCount=0 in final report", VERIFIED),
            ("R4", "Rollback plan present", "`incidents/INC-001/incident.md` contains a Rollback Plan section", VERIFIED),
            ("R5", "Dependency audit", "Not verified — no package manager available", NOT_VERIFIED),
            ("R6", "Release tool is not BLOCKED", "`Invoke-ReleaseCheck.ps1` exits 0", VERIFIED),
        ],
        columns=["#", "Condition", "Verification method", "Status"],
    )
    st.dataframe(df_policy, width="stretch", hide_index=True)
    st.caption(f"Source: `docs/release-policy.md` — {VERIFIED}")

    st.divider()

    # ── Run log ──
    run_log = read_text("bobguard/reports/run-log.txt")
    if run_log:
        with st.expander("View run-log.txt — end-to-end execution log"):
            st.code(run_log, language="text")
            st.caption(f"Source: `bobguard/reports/run-log.txt` — {VERIFIED}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: IBM BOB 2.0
# ══════════════════════════════════════════════════════════════════════════════

elif page == "IBM Bob 2.0":
    st.title("IBM Bob 2.0 — Use in this project")

    st.warning(
        "This section explicitly distinguishes **evidence-backed facts** from "
        "**unverified claims in documentation**. "
        "The app does not run IBM Bob live and is not deployed.",
        icon="⚠️",
    )

    st.divider()

    st.subheader("Verified capabilities")
    st.success(
        "The following capabilities were confirmed through direct use "
        "during project development (source: `bobguard/CAPABILITIES.md`)."
    )
    import pandas as pd
    df_verified = pd.DataFrame(
        [
            ("File read / write / search", "Native tools: `read_file`, `write_file`, `grep`, `glob`, `apply_diff` — used successfully", VERIFIED),
            ("Shell execution (PowerShell 5.1)", "`execute_command` ran PowerShell cmdlets; workspace CWD responds", VERIFIED),
            (".NET 8 runtime", "`dotnet --list-runtimes` returned `Microsoft.NETCore.App 8.0.24`", VERIFIED),
            ("Subagent spawn (`spawn_subagent`)", "Tool listed among the tools available to Bob", VERIFIED),
        ],
        columns=["Capability", "Evidence", "Status"],
    )
    st.dataframe(df_verified, width="stretch", hide_index=True)

    st.divider()

    st.subheader("Unverified capabilities")
    st.warning(
        "The following capabilities **could not be verified** in this environment, "
        "although they are mentioned in documentation."
    )
    df_unverified = pd.DataFrame(
        [
            (
                "Parallel subagent execution",
                "The `spawn_subagent` tool is available, but there is no native Bob event log "
                "or task-state stream demonstrating actual concurrent execution. "
                "Timestamps written by the agent are not sufficient evidence.",
                DOCUMENTED_UNVERIFIED,
            ),
            (
                "Parallel investigation phases",
                "The findings files (dev, ops, security) are labeled 'SEQUENTIAL' "
                "— see each file's heading in `incidents/INC-001/findings/`.",
                DOCUMENTED_UNVERIFIED,
            ),
        ],
        columns=["Capability", "Reason", "Status"],
    )
    st.dataframe(df_unverified, width="stretch", hide_index=True)

    st.divider()

    st.subheader("Unavailable capabilities")
    st.error("The following tools are not available in this environment.")
    df_unavailable = pd.DataFrame(
        [
            ("`git` CLI", "`git` not found on PATH — `CommandNotFoundException`"),
            ("`node` / `npm`", "Not found on PATH"),
            ("`python` (original)", "Windows Store stub only; external Python 3.12.10 detected"),
            ("`dotnet` SDK", "Runtime present, but no SDK — `No .NET SDKs were found`"),
            ("`pip` (original)", "Not found on the original Bob environment PATH"),
            ("Remote / PR operations", "No git CLI; no remote configured"),
        ],
        columns=["Capability", "Evidence"],
    )
    st.dataframe(df_unavailable, width="stretch", hide_index=True)
    st.caption(f"Source: `bobguard/CAPABILITIES.md` — {VERIFIED}")

    st.divider()

    st.subheader("About IBM Bob integration in this app")
    st.info(
        "**This Streamlit app does NOT integrate IBM Bob live.** "
        "It displays static evidence from the local repository. "
        "There is no public deployment URL. "
        "This app makes no calls to watsonx or IBM Cloud APIs. "
        "Live IBM Bob integration would require an API key, MCP configuration, "
        "and an active server — none of which are present or configured here.",
        icon="ℹ️",
    )

    st.divider()

    # ── Full CAPABILITIES.md ──
    caps = read_text("bobguard/CAPABILITIES.md")
    if caps:
        with st.expander("View full `bobguard/CAPABILITIES.md`"):
            st.markdown(caps)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: LIMITATIONS AND ROADMAP
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Limitations and roadmap":
    st.title("Limitations and Roadmap")

    st.subheader("Current MVP limitations")
    import pandas as pd
    df_limits = pd.DataFrame(
        [
            ("Synthetic data", "No production deployment, real credentials, or real data loss.", VERIFIED),
            ("Bounded policy filter", "Covers only 3 documented synthetic patterns. Not comprehensive secret detection.", VERIFIED),
            ("No sandboxing or RBAC", "Process isolation and role-based access control are roadmap items.", VERIFIED),
            ("Dependency audit unverified", "No `npm`, `pip`, or `dotnet` SDK in the original environment. R5 is always NOT VERIFIED.", VERIFIED),
            ("Parallel execution not natively tested", "The `spawn_subagent` tool exists, but actual concurrency was not demonstrated.", VERIFIED),
            ("No live IBM Bob integration", "This app visualizes evidence; it is not an IBM Bob/watsonx client.", VERIFIED),
            ("No public URL", "The app is not deployed. No public URL currently exists.", VERIFIED),
        ],
        columns=["Limitation", "Details", "Limitation status"],
    )
    st.dataframe(df_limits, width="stretch", hide_index=True)

    st.divider()

    st.subheader("Roadmap — Enterprise features (not implemented)")
    df_roadmap = pd.DataFrame(
        [
            ("Entra ID / MFA / RBAC", PENDING),
            ("Azure Key Vault / real secrets management", PENDING),
            ("AKS deployment pipeline", PENDING),
            ("Real subtask isolation (sandboxing)", PENDING),
            ("Native parallel-execution evidence", PENDING),
            ("Dependency audit (`npm audit`, `pip audit`, etc.)", PENDING),
            ("Timed comparison: manual vs. Bob-assisted", PENDING),
            ("INC-002 fix applied and verified", PENDING),
        ],
        columns=["Item", "Status"],
    )
    st.dataframe(df_roadmap, width="stretch", hide_index=True)
    st.caption(f"Source: `README.md` — {VERIFIED}")

    st.divider()

    st.subheader("What is real, documented, and still pending")
    st.markdown("""
| Category | Examples |
|---|---|
| **Evidence (verified in repository)** | Source code with INC-001 fix, test-results JSON (17 tests PASS), incident and findings files, run-log.txt, verdict JSON files, PolicyFilter script |
| **Documented / not verified here** | Parallel subagent execution, dependency audit (R5), synthetic logs labeled as non-production |
| **Pending / roadmap** | All Enterprise items, INC-002 fix, public URL, live IBM Bob integration |
    """)
