from pathlib import Path

import streamlit as st

from bobguard_demo import (
    INCIDENT_IDS,
    incident_artifact_label,
    incident_evidence_paths,
    incident_test_output_paths,
    inspect_release_evidence,
    list_repository_files,
    read_safe_excerpt,
)


ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="BobGuard | Evidence Viewer",
    page_icon="🛡️",
    layout="wide",
)
st.markdown(
    """
    <style>
      .block-container {max-width: 1180px; padding-top: 2.1rem; padding-bottom: 3rem;}
      .hero {padding: 1.5rem 1.7rem; border-radius: 18px; background: linear-gradient(120deg, #102a43, #176b87); color: white; margin-bottom: 1rem;}
      .hero p {color: #d9f0f4; font-size: 1.05rem; margin-bottom: 0;}
      .notice {padding: .9rem 1rem; border: 1px solid #e5a93d; border-radius: 12px; background: #fff8e8; color: #593c09;}
      .muted {color: #61758a; font-size: .92rem;}
      @media (max-width: 700px) {
        .block-container {padding-left: 1rem; padding-right: 1rem; padding-top: 1rem;}
        .hero {padding: 1rem;}
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>BobGuard</h1>
      <p>Evidence viewer for project incidents and checks.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="notice"><strong>Visualization/replay, not live execution.</strong> '
    "This app does not run IBM Bob or PowerShell, and does not connect to IBM Bob, "
    "watsonx.ai, or watsonx Orchestrate. INC-001 and INC-002 are selector options only: "
    "this checkout contains no evidence from which to reconstruct their results. "
    "Treat any demo incident/log artifacts as synthetic. No network requests are made."
    "</div>",
    unsafe_allow_html=True,
)

repository_files = list_repository_files(ROOT)
release_evidence = inspect_release_evidence(ROOT)
incident_files_by_id = {
    incident_id: incident_evidence_paths(ROOT, incident_id)
    for incident_id in INCIDENT_IDS
}
test_outputs_by_id = {
    incident_id: incident_test_output_paths(ROOT, incident_id)
    for incident_id in INCIDENT_IDS
}

st.header("Project")
st.write(
    "The project description provided for the README documents a PowerShell MVP with "
    "an assisted debugging workflow. It describes files and expected results, but "
    "this checkout does not contain the prototype. This app distinguishes those "
    "documented claims from verifiable evidence or executions."
)

project_col, evidence_col, run_col = st.columns(3)
with project_col:
    st.metric("Incident IDs in selector", len(INCIDENT_IDS))
    st.caption("Requested contexts; this does not imply evidence is available.")
with evidence_col:
    st.metric(
        "Incident evidence files",
        len({path for paths in incident_files_by_id.values() for path in paths}),
    )
    st.caption("Count observed in this checkout when the app loaded.")
with run_col:
    st.metric("Bob execution", "Unavailable")
    st.caption("No new result is executed or simulated.")

st.header("Incidents")
selected_incident = st.selectbox("Select an incident", INCIDENT_IDS)
incident_files = incident_files_by_id[selected_incident]
st.subheader(selected_incident)
st.write(
    "This ID does not confirm that the incident exists in this checkout. No behavior, "
    "cause, fix, test count, or result is attributed to it unless corresponding "
    "evidence is present in the repository."
)

if selected_incident == "INC-001":
    st.markdown("**What the provided README documents — not verified in code**")
    st.caption(
        "The documentation describes pagination returning 2 pages for 25 items at "
        "a page size of 10, instead of the expected 3. It cites "
        "`app/Invoke-Calculator.ps1` and `Get-TotalPages -Count 25 -PageSize 10`. "
        "The source file is not in this checkout, so the fix cannot be inspected or "
        "reproduced here."
    )
    st.markdown("**Test expectations in the README — not saved test results**")
    st.code(
        ".\\tests\\Invoke-Tests.ps1 -Suite Unit       # expected exit: 0 (bug present)\n"
        ".\\tests\\Invoke-Tests.ps1 -Suite Regression # expected exit: 1 (expected failure)\n"
        ".\\tests\\Invoke-Tests.ps1 -Suite All        # expected exit: 0 (after the fix)",
        language="powershell",
    )
    st.caption(
        "The README also describes an end-to-end demo that applies the fix automatically. "
        "No script or transcript is available to verify that it ran."
    )
elif selected_incident == "INC-002":
    st.info(
        "The provided README does not describe INC-002. No cause, fix, or test results "
        "are inferred from external summaries; this checkout contains no INC-002 artifacts."
    )

if incident_files:
    st.markdown("**Files found**")
    for relative_path in incident_files:
        st.markdown(f"- `{relative_path}` — {incident_artifact_label(relative_path)}")
    st.markdown("**Source/evidence excerpts**")
    for relative_path in incident_files:
        suffix = Path(relative_path).suffix.lstrip(".") or "text"
        with st.expander(relative_path):
            st.code(read_safe_excerpt(ROOT, relative_path), language=suffix)
else:
    st.info(
        f"No files cite {selected_incident} in their path or content. Excerpts, "
        "reproduction, test results, and artifact citations cannot be verified "
        "for this incident."
    )

st.markdown("**Reproduction and test results**")
test_outputs = test_outputs_by_id[selected_incident]
if test_outputs:
    st.write(
        "Artifacts named like test outputs were found. Their contents are shown as "
        "evidence without counting PASS/FAIL or inferring suite status."
    )
    for path in test_outputs:
        st.markdown(f"- `{path}` — {incident_artifact_label(path)}")
        st.code(
            read_safe_excerpt(ROOT, path),
            language=Path(path).suffix.lstrip(".") or "text",
        )
else:
    st.write(
        "No file identifiable by name as a run output was found for this incident. "
        "This web app's tests do not validate the reported PowerShell run results."
    )

st.header("Reports, policies, and release")
st.caption(
    "The provided README lists a policy-filter CLI, filter tests, and a release-check "
    "CLI with JSON outputs. The scripts and outputs are absent from this checkout, "
    "so the documented interface does not prove that the filter or checker ran."
)
policy_col, checker_col, audit_col = st.columns(3)
with policy_col:
    st.markdown("**Report policy filter**")
    if release_evidence.policy_files:
        st.write("Files found:")
        for path in release_evidence.policy_files:
            st.code(path)
    else:
        st.write("Unverified: no identifiable file was found.")
with checker_col:
    st.markdown("**Release checker**")
    st.write(release_evidence.checker_status)
    for path in release_evidence.checker_files:
        st.code(path)
    if release_evidence.checker_output_files:
        st.caption("Outputs found (approval is not inferred):")
        for path in release_evidence.checker_output_files:
            st.code(path)
with audit_col:
    st.markdown("**Dependency audit gate**")
    st.warning(release_evidence.audit_status)
st.info(
    "No global release verdict is issued. A checker output and dependency-audit status "
    "are separate evidence; neither is interpreted as approval."
)

st.header("IBM Bob 2.0 usage and evidence")
st.write(
    "The provided README claims that file read/write, PowerShell shell execution, and "
    "code search were verified; it says subtask concurrency was not verified. This "
    "checkout contains no capability inventory, prompts, transcripts, run logs, or "
    "versioned artifacts to corroborate those claims. The README leaves comparative "
    "measurements pending; this app makes no productivity-improvement claims. There "
    "is no direct integration with Bob or watsonx."
)
with st.expander("Checkout README: documentation, not an execution transcript"):
    if (ROOT / "README.md").is_file():
        st.code(read_safe_excerpt(ROOT, "README.md"), language="markdown")
    else:
        st.info("README.md is not available in this checkout.")

with st.expander("Checkout files"):
    st.caption(
        "Observed inventory; it shows available files, not proof that a run was executed."
    )
    st.code("\n".join(repository_files) or "(no files)", language="text")

st.caption(
    "Display masking covers only common credential patterns; it is not comprehensive "
    "redaction or a security control."
)
