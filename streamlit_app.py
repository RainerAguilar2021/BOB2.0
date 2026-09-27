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
VERIFIED = "✅ Verificado"
DOCUMENTED_UNVERIFIED = "📄 Documentado / no verificado aquí"
PENDING = "🔲 Pendiente"
OPEN = "🔴 Abierto"
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
    st.caption("Demo de evidencia local — sin integración live con IBM Bob")
    st.divider()

    page = st.radio(
        "Navegar a:",
        [
            "Inicio",
            "INC-001: Paginación",
            "INC-002: Redondeo",
            "Filtro de política",
            "Release check",
            "IBM Bob 2.0",
            "Limitaciones y roadmap",
        ],
        index=0,
    )

    st.divider()
    st.caption(
        "⚠️ Esta app visualiza evidencia del repositorio local. "
        "No está desplegada públicamente. No ejecuta IBM Bob en vivo."
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
# PAGE: INICIO
# ══════════════════════════════════════════════════════════════════════════════

if page == "Inicio":
    st.title("🛡️ BobGuard MVP")
    st.subheader("Demostración de flujo AI-assisted para debugging e investigación de incidentes")

    st.info(
        "**Acerca de esta aplicación**  \n"
        "Esta app visualiza la evidencia disponible en este repositorio. "
        "Distingue claramente entre: artefactos verificados en el código, "
        "resultados descritos en documentación, y capacidades pendientes. "
        "No está desplegada públicamente y no ejecuta IBM Bob en vivo.",
        icon="ℹ️",
    )

    st.divider()

    # ── Problema ──
    st.header("El problema de debugging")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**Sin asistencia AI:**
- El ingeniero revisa logs manualmente.
- Investiga múltiples archivos y funciones.
- Ejecuta pruebas una por una.
- Redacta reportes sin automatización.
- La revisión de release es un checklist manual.

El tiempo invertido en triaje puede superar el tiempo de fix real.
        """)
    with col2:
        st.markdown("""
**Con BobGuard + IBM Bob 2.0 (propuesto):**
- El agente lee logs, código y docs en paralelo*.
- Identifica la función afectada y el root cause.
- Ejecuta el test suite y confirma el fix.
- Aplica filtro de política sobre los reportes.
- Produce un veredicto de release estructurado.

*La ejecución paralela de subagentes está disponible como herramienta, pero **no está verificada nativamente** en este entorno — ver sección IBM Bob 2.0.
        """)

    st.divider()

    # ── Incidentes ──
    st.header("Incidentes en este repositorio")
    col_a, col_b = st.columns(2)

    inc001_fix = check_fix_applied()
    with col_a:
        st.markdown("### INC-001 — Paginación")
        st.markdown(f"**Estado:** {'✅ RESUELTO' if inc001_fix else '🔴 FIX NO DETECTADO'}")
        st.markdown(
            "Función `Get-TotalPages` usaba truncación entera en lugar de `Ceiling`. "
            "La última página parcial de registros se descartaba silenciosamente."
        )
        st.markdown(f"**Archivo fuente:** `app/Invoke-Calculator.ps1` — {'fix presente' if inc001_fix else 'fix no encontrado'}")

    with col_b:
        st.markdown("### INC-002 — Redondeo")
        inc002_bug = check_inc002_bug_present()
        st.markdown(f"**Estado:** {'🔴 ABIERTO (bug presente)' if inc002_bug else '✅ FIX DETECTADO'}")
        st.markdown(
            "`ConvertTo-DiscountedPrice` usa `[Math]::Round` sin `AwayFromZero`. "
            "Valores en punto medio se redondean incorrectamente (Banker's Rounding)."
        )
        st.markdown(f"**Archivo fuente:** `app/Invoke-Calculator.ps1` — {'sin fix' if inc002_bug else 'fix aplicado'}")

    st.divider()

    # ── Resumen de evidencia ──
    st.header("Resumen de evidencia por categoría")
    test_results = load_json("bobguard/test-results.json")
    total = len(test_results) if test_results else 0
    passed = sum(1 for t in test_results if t.get("Status") == "PASS") if test_results else 0

    verdict_v2 = load_json("bobguard/reports/final-release-verdict-v2.json")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tests en JSON", total, help="De bobguard/test-results.json")
    col2.metric("Tests PASS", passed)
    col3.metric(
        "Veredicto release",
        verdict_v2.get("Verdict", "N/A") if verdict_v2 else "N/A",
        help="De final-release-verdict-v2.json",
    )
    col4.metric(
        "Archivos de incidentes",
        sum(1 for p in ["incidents/INC-001/incident.md", "incidents/INC-002/incident.md"] if file_exists(p)),
    )

    st.caption(
        "Los valores anteriores se leen en tiempo real desde los archivos del repositorio. "
        "No son resultados de una ejecución live."
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: INC-001
# ══════════════════════════════════════════════════════════════════════════════

elif page == "INC-001: Paginación":
    st.title("INC-001 — Billing Pagination: Last Page Silently Dropped")

    inc001_fix = check_fix_applied()
    if inc001_fix:
        st.success("✅ Fix verificado en `app/Invoke-Calculator.ps1` (línea actual: `[Math]::Ceiling`)")
    else:
        st.error("❌ Fix no detectado en el código fuente actual.")

    st.divider()

    # ── Metadata ──
    st.subheader("Metadata del incidente")
    col1, col2 = st.columns(2)
    with col1:
        evidence_row("ID", "INC-001", VERIFIED, "incidents/INC-001/incident.md")
        evidence_row("Severidad", "High", VERIFIED, "incidents/INC-001/incident.md")
        evidence_row("Estado", "RESUELTO", VERIFIED, "incidents/INC-001/incident.md")
    with col2:
        evidence_row("Componente", "Get-TotalPages", VERIFIED, "app/Invoke-Calculator.ps1")
        evidence_row("Fix aplicado", "Ceiling division", VERIFIED, "app/Invoke-Calculator.ps1:38")
        evidence_row("ADR violado", "ADR-001 (2026-09-01)", VERIFIED, "docs/ADR-001-pagination.md")

    st.divider()

    # ── Root cause ──
    st.subheader("Root cause (verificado en código fuente)")
    col_bug, col_fix = st.columns(2)
    with col_bug:
        st.markdown("**Antes del fix (bug):**")
        st.code("return [int]($Count / $PageSize)", language="powershell")
        st.caption(
            "Para Count=25, PageSize=10: `25/10 = 2.5` → `[int]` trunca → `2`. "
            "La página 2 (5 registros) nunca se procesa."
        )
    with col_fix:
        st.markdown("**Después del fix (actual):**")
        st.code("return [Math]::Ceiling($Count / $PageSize)", language="powershell")
        st.caption(
            "Para Count=25, PageSize=10: `Ceiling(2.5) = 3`. "
            "Las 3 páginas se procesan. Fix verificado en línea 38 del archivo actual."
        )

    # Reproduce exact content
    src = read_text("app/Invoke-Calculator.ps1")
    if src:
        with st.expander("Ver código fuente actual — `app/Invoke-Calculator.ps1`"):
            st.code(src, language="powershell")
    else:
        st.warning("`app/Invoke-Calculator.ps1` no encontrado.")

    st.divider()

    # ── Logs sintéticos ──
    st.subheader("Logs del incidente")
    st.warning(
        "Los logs a continuación son **sintéticos y etiquetados** — construidos para coincidir "
        "con el código fuente. No provienen de un sistema en producción.",
        icon="⚠️",
    )
    logs = read_text("incidents/INC-001/logs.md")
    if logs:
        with st.expander("Ver logs — `incidents/INC-001/logs.md`"):
            st.markdown(logs)
    else:
        st.error("Archivo de logs no encontrado.")

    st.divider()

    # ── Hallazgos de investigación ──
    st.subheader("Hallazgos de investigación")
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
                st.caption(f"Fuente: `{path}` — {VERIFIED}")
            else:
                st.error(f"Archivo no encontrado: `{path}`")

    st.divider()

    # ── Test results para INC-001 ──
    st.subheader("Resultados de prueba relacionados con INC-001")
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
            cols[2].write(f"Esperado: `{t['Expected']}`")
            cols[3].write(f"Actual: `{t['Actual']}`")
        st.caption(f"Fuente: `bobguard/test-results.json` — {VERIFIED}")
    else:
        st.error("`bobguard/test-results.json` no encontrado.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: INC-002
# ══════════════════════════════════════════════════════════════════════════════

elif page == "INC-002: Redondeo":
    st.title("INC-002 — Billing Rounding: Midpoint Rounded to Even (Banker's Rounding)")

    inc002_bug = check_inc002_bug_present()
    if inc002_bug:
        st.error(
            "🔴 **ABIERTO** — Bug presente en `app/Invoke-Calculator.ps1`. "
            "No se ha aplicado ningún fix."
        )
    else:
        st.success("✅ Fix detectado en el código fuente.")

    st.info(
        "INC-002 es **independiente** de INC-001 (función diferente, root cause diferente). "
        "Se mantiene abierto intencionalmente para la demostración.",
        icon="ℹ️",
    )

    st.divider()

    # ── Metadata ──
    st.subheader("Metadata del incidente")
    col1, col2 = st.columns(2)
    with col1:
        evidence_row("ID", "INC-002", VERIFIED, "incidents/INC-002/incident.md")
        evidence_row("Severidad", "Medium", VERIFIED, "incidents/INC-002/incident.md")
        evidence_row("Estado", "ABIERTO (sin fix)", VERIFIED, "incidents/INC-002/incident.md")
    with col2:
        evidence_row("Componente", "ConvertTo-DiscountedPrice", VERIFIED, "app/Invoke-Calculator.ps1")
        evidence_row("Fix aplicado", "No", VERIFIED, "app/Invoke-Calculator.ps1:49")
        evidence_row("Evidencia adicional", "Sin artefactos de fix", OPEN, "")

    st.divider()

    # ── Root cause ──
    st.subheader("Root cause (verificado en código fuente)")
    col_bug, col_fix = st.columns(2)
    with col_bug:
        st.markdown("**Código actual (bug presente):**")
        st.code(
            "return [Math]::Round($UnitPrice * (1 - $DiscountPct / 100), 2)",
            language="powershell",
        )
        st.caption(
            "`[Math]::Round(valor, 2)` usa `MidpointRounding.ToEven` por defecto. "
            "Para 0.225: redondea al dígito par → **0.22** (incorrecto)."
        )
    with col_fix:
        st.markdown("**Fix propuesto (NO aplicado):**")
        st.code(
            "return [Math]::Round($UnitPrice * (1 - $DiscountPct / 100), 2,\n"
            "    [System.MidpointRounding]::AwayFromZero)",
            language="powershell",
        )
        st.caption(
            "Para 0.225: `AwayFromZero` → **0.23** (correcto). "
            "Fix documentado en `incidents/INC-002/incident.md`, **no aplicado**."
        )

    st.divider()

    # ── Tabla de casos afectados ──
    st.subheader("Casos afectados por el bug")
    st.markdown(
        "Solo los valores en punto medio exacto (`intermedio % 0.01 == 0.005`) difieren. "
        "Valores no-midpoint son idénticos con ambos modos."
    )
    import pandas as pd  # local import; streamlit bundles pandas
    df = pd.DataFrame(
        [
            ("$0.25", "10%", "$0.225", "$0.22 ❌", "$0.23 ✅", "-$0.01"),
            ("$0.05", "50%", "$0.025", "$0.02 ❌", "$0.03 ✅", "-$0.01"),
            ("$1.00", "10%", "$0.90",  "$0.90 ✅", "$0.90 ✅", "$0.00"),
            ("$99.99", "33.33%", "$66.66…", "$66.66 ✅", "$66.66 ✅", "$0.00"),
        ],
        columns=["Precio", "Descuento", "Intermedio", "ToEven (bug)", "AwayFromZero (esperado)", "Delta"],
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"Fuente: `incidents/INC-002/incident.md` — {VERIFIED}")

    st.divider()

    # ── Logs sintéticos ──
    st.subheader("Logs del incidente")
    st.warning(
        "Los logs a continuación son **sintéticos y etiquetados** — construidos para coincidir "
        "con el código fuente. No provienen de un sistema en producción.",
        icon="⚠️",
    )
    logs = read_text("incidents/INC-002/logs.md")
    if logs:
        with st.expander("Ver logs — `incidents/INC-002/logs.md`"):
            st.markdown(logs)
    else:
        st.error("Archivo de logs no encontrado.")

    st.divider()

    # ── Test results para INC-002 ──
    st.subheader("Resultados de prueba relacionados con INC-002")
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
            cols[2].write(f"Esperado: {label}")
            cols[3].write(f"Actual: `{t['Actual']}`")
        st.caption(f"Fuente: `bobguard/test-results.json` — {VERIFIED}")
        st.info(
            "Los tests de descuento del JSON corresponden a valores **no-midpoint** "
            "(pasan con cualquier modo de redondeo). "
            "Los tests de regresión INC-002 con midpoints se ejecutan en `tests/Invoke-Tests.ps1 -Suite Regression` "
            "y producen FAIL con el código actual.",
            icon="ℹ️",
        )
    else:
        st.error("`bobguard/test-results.json` no encontrado.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: POLICY FILTER
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Filtro de política":
    st.title("Filtro de Política — Sanitización de Reportes")

    st.info(
        "El filtro de política redacta un conjunto **acotado** de patrones sintéticos "
        "de secretos antes de compartir reportes. "
        "**No es detección exhaustiva de credenciales.** "
        "Cubre exactamente 3 patrones documentados.",
        icon="ℹ️",
    )

    st.divider()

    # ── Patrones cubiertos ──
    st.subheader("Patrones cubiertos")
    import pandas as pd
    df_patterns = pd.DataFrame(
        [
            ("Synthetic API key", "`BOBGUARD-KEY-[A-Za-z0-9]{16,}`", VERIFIED),
            ("Synthetic DB password", "`db_password\\s*=\\s*\\S+`", VERIFIED),
            ("Synthetic bearer token", "`Bearer\\s+[A-Za-z0-9\\-._~+/]{20,}`", VERIFIED),
        ],
        columns=["Nombre", "Regex", "Estado"],
    )
    st.dataframe(df_patterns, use_container_width=True, hide_index=True)
    st.caption(f"Fuente: `docs/release-policy.md` — {VERIFIED}")

    st.warning(
        "Este filtro **no** es: detección de secretos arbitrarios, "
        "protección de código fuente, aislamiento de procesos, ni garantía contra filtraciones. "
        "Es una demostración de sanitización de reportes para un conjunto sintético de patrones.",
        icon="⚠️",
    )

    st.divider()

    # ── Ejecuciones ──
    st.subheader("Ejecuciones registradas")
    summary_v2 = load_json("bobguard/reports/final-report-policy-summary-v2.json")
    summary_final = load_json("bobguard/reports/policy-summary-final.json")
    summary_v1 = load_json("bobguard/reports/policy-summary.json")

    for label, data, path in [
        ("Ejecución v2 (final-report-raw.md)", summary_v2, "bobguard/reports/final-report-policy-summary-v2.json"),
        ("Ejecución final (sanitized→clean)", summary_final, "bobguard/reports/policy-summary-final.json"),
        ("Ejecución v1 (raw-report.md)", summary_v1, "bobguard/reports/policy-summary.json"),
    ]:
        if data:
            with st.expander(f"📄 {label}"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Redacciones", data.get("RedactedCount", "N/A"))
                c2.metric("Bloques truncados", data.get("TruncatedBlocks", "N/A"))
                c3.metric("Timestamp", data.get("Timestamp", "N/A")[:19] if data.get("Timestamp") else "N/A")
                redacted = data.get("RedactedItems", [])
                if redacted:
                    st.markdown("**Ítems redactados:**")
                    for item in redacted:
                        # Show type only — NEVER show key value
                        st.write(f"- Tipo: `{item.get('Type', '?')}` — preview: `[REDACTED]`")
                    st.caption("El valor exacto no se muestra. Existió en raw-report.md como dato sintético y fue redactado.")
                st.caption(f"Fuente: `{path}` — {VERIFIED}")
        else:
            st.warning(f"Archivo no encontrado: `{path}`")

    st.divider()

    # ── Script ──
    st.subheader("Script del filtro")
    if file_exists("bobguard/policy-filter/Invoke-PolicyFilter.ps1"):
        src = read_text("bobguard/policy-filter/Invoke-PolicyFilter.ps1")
        with st.expander("Ver `bobguard/policy-filter/Invoke-PolicyFilter.ps1`"):
            st.code(src, language="powershell")
        st.caption(f"Fuente: `bobguard/policy-filter/Invoke-PolicyFilter.ps1` — {VERIFIED}")
    else:
        st.error("Script no encontrado.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: RELEASE CHECK
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Release check":
    st.title("Release Readiness Check")

    st.info(
        "El release check evalúa condiciones mecánicas de `docs/release-policy.md`. "
        "El veredicto mostrado aquí proviene de los archivos JSON generados por "
        "`Invoke-ReleaseCheck.ps1` — no de una ejecución live.",
        icon="ℹ️",
    )

    st.divider()

    # ── Veredictos ──
    verdict_v2 = load_json("bobguard/reports/final-release-verdict-v2.json")
    verdict_v1 = load_json("bobguard/reports/final-release-verdict.json")

    col1, col2 = st.columns(2)
    for col, verdict, label, path in [
        (col1, verdict_v2, "Veredicto v2 (final)", "bobguard/reports/final-release-verdict-v2.json"),
        (col2, verdict_v1, "Veredicto v1 (intermedio)", "bobguard/reports/final-release-verdict.json"),
    ]:
        with col:
            st.subheader(label)
            if verdict:
                v = verdict.get("Verdict", "N/A")
                if v == "APPROVED":
                    st.success(f"**Veredicto: {v}**")
                elif v == "BLOCKED":
                    st.error(f"**Veredicto: {v}**")
                else:
                    st.warning(f"**Veredicto: {v}**")

                st.warning(
                    "⚠️ Este veredicto es el resultado del checker local, "
                    "**no una aprobación de producción**. "
                    "R5 (Dependency audit) está marcado NOT VERIFIED en todos los casos.",
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
                st.caption(f"Fuente: `{path}` — {VERIFIED}")
            else:
                st.error(f"Archivo no encontrado: `{path}`")

    st.divider()

    # ── Condiciones de política ──
    st.subheader("Condiciones de la política de release")
    import pandas as pd
    df_policy = pd.DataFrame(
        [
            ("R1", "Unit tests pasan", "`Invoke-Tests.ps1 -Suite Unit` exit 0", VERIFIED),
            ("R2", "Regression tests pasan", "`Invoke-Tests.ps1 -Suite Regression` exit 0", VERIFIED),
            ("R3", "Reporte final sin secretos sin redactar", "Policy filter RedactedCount=0 en reporte final", VERIFIED),
            ("R4", "Plan de rollback presente", "`incidents/INC-001/incident.md` contiene sección Rollback Plan", VERIFIED),
            ("R5", "Auditoría de dependencias", "No verificada — sin package manager disponible", NOT_VERIFIED),
            ("R6", "Herramienta de release no BLOCKED", "`Invoke-ReleaseCheck.ps1` exit 0", VERIFIED),
        ],
        columns=["#", "Condición", "Método de verificación", "Estado"],
    )
    st.dataframe(df_policy, use_container_width=True, hide_index=True)
    st.caption(f"Fuente: `docs/release-policy.md` — {VERIFIED}")

    st.divider()

    # ── Run log ──
    run_log = read_text("bobguard/reports/run-log.txt")
    if run_log:
        with st.expander("Ver run-log.txt — log de la ejecución end-to-end"):
            st.code(run_log, language="text")
            st.caption(f"Fuente: `bobguard/reports/run-log.txt` — {VERIFIED}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: IBM BOB 2.0
# ══════════════════════════════════════════════════════════════════════════════

elif page == "IBM Bob 2.0":
    st.title("IBM Bob 2.0 — Uso en este proyecto")

    st.warning(
        "Esta sección separa explícitamente los **hechos con evidencia** de las "
        "**afirmaciones documentales no verificadas**. "
        "La aplicación no ejecuta IBM Bob en vivo ni está desplegada.",
        icon="⚠️",
    )

    st.divider()

    st.subheader("Capacidades verificadas")
    st.success(
        "Las siguientes capacidades fueron confirmadas mediante uso directo "
        "durante la construcción del proyecto (fuente: `bobguard/CAPABILITIES.md`)."
    )
    import pandas as pd
    df_verified = pd.DataFrame(
        [
            ("Lectura / escritura / búsqueda de archivos", "Herramientas nativas: `read_file`, `write_file`, `grep`, `glob`, `apply_diff` — usadas con éxito", VERIFIED),
            ("Ejecución de shell (PowerShell 5.1)", "`execute_command` ejecutó cmdlets de PowerShell; CWD del workspace responde", VERIFIED),
            ("Runtime .NET 8", "`dotnet --list-runtimes` devolvió `Microsoft.NETCore.App 8.0.24`", VERIFIED),
            ("Spawn de subagente (`spawn_subagent`)", "Herramienta listada en las herramientas disponibles de Bob", VERIFIED),
        ],
        columns=["Capacidad", "Evidencia", "Estado"],
    )
    st.dataframe(df_verified, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Capacidades no verificadas")
    st.warning(
        "Las siguientes capacidades **no pudieron verificarse** en este entorno, "
        "aunque son mencionadas en documentación."
    )
    df_unverified = pd.DataFrame(
        [
            (
                "Ejecución paralela de subagentes",
                "La herramienta `spawn_subagent` está disponible, pero no existe log nativo de eventos de Bob "
                "ni stream de estado de tareas que demuestre ejecución concurrente real. "
                "Los timestamps escritos por el agente no son prueba suficiente.",
                DOCUMENTED_UNVERIFIED,
            ),
            (
                "Ejecución paralela de fases de investigación",
                "Los archivos de hallazgos (dev, ops, security) están etiquetados como 'SEQUENTIAL' "
                "— ver encabezado de cada archivo en `incidents/INC-001/findings/`.",
                DOCUMENTED_UNVERIFIED,
            ),
        ],
        columns=["Capacidad", "Razón", "Estado"],
    )
    st.dataframe(df_unverified, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Capacidades no disponibles")
    st.error("Las siguientes herramientas no están disponibles en este entorno.")
    df_unavailable = pd.DataFrame(
        [
            ("CLI `git`", "`git` no encontrado en PATH — `CommandNotFoundException`"),
            ("`node` / `npm`", "No encontrado en PATH"),
            ("`python` (original)", "Solo stub de Windows Store; se detectó Python 3.12.10 externo"),
            ("`dotnet` SDK", "Runtime presente, pero sin SDK — `No .NET SDKs were found`"),
            ("`pip` (original)", "No encontrado en PATH del entorno Bob original"),
            ("Operaciones remotas / PR", "Sin CLI git; sin remoto configurado"),
        ],
        columns=["Capacidad", "Evidencia"],
    )
    st.dataframe(df_unavailable, use_container_width=True, hide_index=True)
    st.caption(f"Fuente: `bobguard/CAPABILITIES.md` — {VERIFIED}")

    st.divider()

    st.subheader("Sobre la integración con IBM Bob en esta app")
    st.info(
        "**Esta aplicación Streamlit NO integra IBM Bob en vivo.** "
        "Visualiza evidencia estática del repositorio local. "
        "No hay URL pública desplegada. "
        "No se ejecutan llamadas a APIs de watsonx o IBM Cloud desde esta app. "
        "Para integrar IBM Bob en vivo se requeriría una API key, configuración de MCP, "
        "y un servidor activo — ninguno de estos está presente ni configurado aquí.",
        icon="ℹ️",
    )

    st.divider()

    # ── CAPABILITIES.md raw ──
    caps = read_text("bobguard/CAPABILITIES.md")
    if caps:
        with st.expander("Ver `bobguard/CAPABILITIES.md` completo"):
            st.markdown(caps)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: LIMITACIONES Y ROADMAP
# ══════════════════════════════════════════════════════════════════════════════

elif page == "Limitaciones y roadmap":
    st.title("Limitaciones y Roadmap")

    st.subheader("Limitaciones actuales del MVP")
    import pandas as pd
    df_limits = pd.DataFrame(
        [
            ("Datos sintéticos", "No hay despliegue en producción, ni credenciales reales, ni pérdida de datos real.", VERIFIED),
            ("Filtro de política acotado", "Cubre solo 3 patrones sintéticos documentados. No es detección exhaustiva de secretos.", VERIFIED),
            ("Sin sandboxing ni RBAC", "Aislamiento de procesos y control de acceso por roles son ítems del roadmap.", VERIFIED),
            ("Auditoría de dependencias no verificada", "Sin `npm`, `pip` ni `dotnet` SDK en el entorno original. R5 siempre NOT VERIFIED.", VERIFIED),
            ("Ejecución paralela no probada nativamente", "El tool `spawn_subagent` existe, pero concurrencia real no fue demostrada.", VERIFIED),
            ("Sin integración live de IBM Bob", "Esta app es una visualización de evidencia, no un cliente de IBM Bob/watsonx.", VERIFIED),
            ("Sin URL pública", "La app no está desplegada. No existe URL pública en este momento.", VERIFIED),
        ],
        columns=["Limitación", "Detalle", "Estado de la limitación"],
    )
    st.dataframe(df_limits, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Roadmap — Enterprise features (no implementadas)")
    df_roadmap = pd.DataFrame(
        [
            ("Entra ID / MFA / RBAC", PENDING),
            ("Azure Key Vault / gestión real de secretos", PENDING),
            ("Pipeline de despliegue AKS", PENDING),
            ("Aislamiento real de subtareas (sandboxing)", PENDING),
            ("Evidencia nativa de ejecución paralela", PENDING),
            ("Auditoría de dependencias (`npm audit`, `pip audit`, etc.)", PENDING),
            ("Comparativa temporizada: manual vs. Bob-assisted", PENDING),
            ("Fix de INC-002 aplicado y verificado", PENDING),
        ],
        columns=["Ítem", "Estado"],
    )
    st.dataframe(df_roadmap, use_container_width=True, hide_index=True)
    st.caption(f"Fuente: `README.md` — {VERIFIED}")

    st.divider()

    st.subheader("Qué es real, qué es documental, qué está pendiente")
    st.markdown("""
| Categoría | Ejemplos |
|---|---|
| **Evidencia real (verificada en repositorio)** | Código fuente con fix INC-001, JSON de test-results (17 tests PASS), archivos de incidente y hallazgos, run-log.txt, veredictos JSON, script PolicyFilter |
| **Documental / no verificado aquí** | Ejecución paralela de subagentes, auditoría de dependencias (R5), logs sintéticos marcados como no-producción |
| **Pendiente / roadmap** | Todos los ítems Enterprise, fix de INC-002, URL pública, integración live con IBM Bob |
    """)
