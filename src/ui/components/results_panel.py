from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape

import streamlit as st
import pandas as pd
import plotly.express as px

from ui.components.assistant import render_code_assistant

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Preformatted,
)


# =========================================================
# CONSTANTS & STYLING
# =========================================================

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]

SEVERITY_COLORS = {
    "CRITICAL": "#DC2626",       # Red
    "HIGH": "#EA580C",           # Orange
    "MEDIUM": "#D97706",         # Amber
    "LOW": "#2563EB",            # Blue
    "INFORMATIONAL": "#64748B",  # Slate
}


# =========================================================
# DATA HELPERS
# =========================================================

def to_dict(value):
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return {}


def get_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def enum_value(value):
    return value.value if hasattr(value, "value") else value


def clean_text(value, default="Not available"):
    if value is None or value == "":
        return default
    return str(enum_value(value))


def pdf_text(value):
    return escape(clean_text(value)).replace("\n", "<br/>")


def get_summary(analysis):
    """Read the PRSummary object exactly as returned by the PR Summary Agent."""
    raw = analysis.get("pr_summary")
    if raw is None:
        return {}

    outer = to_dict(raw)
    nested = outer.get("summary")
    return to_dict(nested) if nested is not None else outer


def get_findings(analysis):
    """
    Prefer unified_findings when supplied.
    Otherwise use the two agent-specific finding lists.
    """
    unified = get_list(analysis.get("unified_findings"))
    if unified:
        return [to_dict(item) for item in unified]

    code_findings = get_list(analysis.get("code_findings"))
    security_findings = get_list(analysis.get("security_findings"))
    return [to_dict(item) for item in code_findings + security_findings]


def get_remediations(analysis):
    """Read RemediationResult.remediations without creating remediation data."""
    raw = analysis.get("remediation_findings")
    if raw is None:
        raw = analysis.get("remediation")
    if raw is None:
        return []

    data = to_dict(raw)
    if data:
        return [to_dict(item) for item in get_list(data.get("remediations"))]

    return [to_dict(item) for item in get_list(raw)]


def get_severity_breakdown(summary, findings):
    """
    Use the PRSummary.severity_breakdown values first.
    Count findings only when the schema field is absent.
    """
    raw = summary.get("severity_breakdown")
    breakdown = to_dict(raw)

    keys = {
        "INFORMATIONAL": "informational",
        "LOW": "low",
        "MEDIUM": "medium",
        "HIGH": "high",
        "CRITICAL": "critical",
    }

    if any(key in breakdown for key in keys.values()):
        return {
            severity: breakdown.get(field, 0)
            for severity, field in keys.items()
        }

    counts = {severity: 0 for severity in keys}
    for finding in findings:
        severity = clean_text(finding.get("severity"), "").upper()
        if severity in counts:
            counts[severity] += 1
    return counts


def get_total_findings(summary, findings):
    value = summary.get("total_findings")
    return value if value is not None else len(findings)


def build_findings_df(findings):
    """Map schema fields to table columns; do not calculate additional metrics."""
    rows = []
    for finding in findings:
        rows.append({
            "Category": clean_text(finding.get("category")),
            "Issue": clean_text(finding.get("issue")),
            "Severity": clean_text(finding.get("severity")).upper(),
            "Line": clean_text(finding.get("line_number")),
            "Description": clean_text(finding.get("description")),
        })
    return pd.DataFrame(
        rows,
        columns=["Category", "Issue", "Severity", "Line", "Description"],
    )


# =========================================================
# DASHBOARD CHARTS
# =========================================================

def render_dashboard_charts(severity_breakdown, findings_df):
    """Render interactive Plotly visualizations for the audit dashboard."""
    st.subheader("Visual Analytics")

    chart_col1, chart_col2 = st.columns(2)

    # 1. Severity Distribution Bar Chart
    with chart_col1:
        sev_df = pd.DataFrame([
            {"Severity": sev, "Count": severity_breakdown.get(sev, 0)}
            for sev in SEVERITY_ORDER
        ])
        fig_sev = px.bar(
            sev_df,
            x="Severity",
            y="Count",
            color="Severity",
            color_discrete_map=SEVERITY_COLORS,
            text="Count",
            title="Findings by Severity",
        )
        fig_sev.update_traces(textposition="outside", cliponaxis=False)
        fig_sev.update_layout(
            showlegend=False,
            xaxis_title=None,
            yaxis_title="Number of Findings",
            margin=dict(t=45, b=20, l=20, r=20),
            height=340,
        )
        st.plotly_chart(fig_sev, use_container_width=True)

    # 2. Findings by Category Donut Chart
    with chart_col2:
        if not findings_df.empty:
            cat_counts = (
                findings_df["Category"]
                .value_counts()
                .reset_index()
            )
            cat_counts.columns = ["Category", "Count"]

            fig_cat = px.pie(
                cat_counts,
                names="Category",
                values="Count",
                hole=0.45,
                title="Findings by Category",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_cat.update_traces(textinfo="percent+label")
            fig_cat.update_layout(
                margin=dict(t=45, b=20, l=20, r=20),
                height=340,
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("No category data available to chart.")

    # 3. Stacked Bar: Severity Breakdown per Category
    if not findings_df.empty:
        grouped = (
            findings_df.groupby(["Category", "Severity"])
            .size()
            .reset_index(name="Count")
        )
        fig_stack = px.bar(
            grouped,
            x="Category",
            y="Count",
            color="Severity",
            barmode="stack",
            color_discrete_map=SEVERITY_COLORS,
            category_orders={"Severity": SEVERITY_ORDER},
            title="Severity Breakdown Across Categories",
        )
        fig_stack.update_layout(
            xaxis_title=None,
            yaxis_title="Findings",
            legend_title="Severity",
            margin=dict(t=45, b=20, l=20, r=20),
            height=320,
        )
        st.plotly_chart(fig_stack, use_container_width=True)


# =========================================================
# PDF EXPORT
# =========================================================

def generate_dashboard_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="SectionCustom",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1D4ED8"),
        spaceBefore=10,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="SmallCustom",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
    ))
    styles.add(ParagraphStyle(
        name="CodeCustom",
        parent=styles["Code"],
        fontSize=7,
        leading=9,
    ))

    story = [
        Paragraph("CodeCheck — PR Review Report", styles["Title"]),
        Paragraph(
            f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')} "
            f"| Language: {pdf_text(data['language'])}",
            styles["SmallCustom"],
        ),
        Spacer(1, 10),
    ]

    summary = data["summary"]
    story.append(Paragraph("PR Summary", styles["SectionCustom"]))
    story.append(Paragraph(pdf_text(summary.get("overview")), styles["BodyText"]))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        f"<b>Review status:</b> {pdf_text(summary.get('review_status'))}",
        styles["BodyText"],
    ))
    story.append(Paragraph(
        f"<b>Merge recommendation:</b> {pdf_text(summary.get('merge_recommendation'))}",
        styles["BodyText"],
    ))

    story.append(Paragraph("Finding Counts", styles["SectionCustom"]))
    breakdown = data["severity_breakdown"]
    count_rows = [["Severity", "Count"]] + [
        [severity.title(), str(breakdown[severity])]
        for severity in ("INFORMATIONAL", "LOW", "MEDIUM", "HIGH", "CRITICAL")
    ]
    table = Table(count_rows, colWidths=[65 * mm, 35 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)

    story.append(Paragraph("Prioritized Fix List", styles["SectionCustom"]))
    fixes = summary.get("prioritized_fix_list") or []
    if fixes:
        for index, fix in enumerate(fixes, 1):
            story.append(Paragraph(f"{index}. {pdf_text(fix)}", styles["BodyText"]))
    else:
        story.append(Paragraph("No prioritized fixes were provided.", styles["BodyText"]))

    story.append(Paragraph(
        f"Findings ({data['total_findings']})",
        styles["SectionCustom"],
    ))
    if data["findings"]:
        rows = [["Category", "Issue", "Severity", "Line", "Description"]]
        for item in data["findings"]:
            rows.append([
                Paragraph(pdf_text(item.get("category")), styles["SmallCustom"]),
                Paragraph(pdf_text(item.get("issue")), styles["SmallCustom"]),
                Paragraph(pdf_text(item.get("severity")), styles["SmallCustom"]),
                Paragraph(pdf_text(item.get("line_number")), styles["SmallCustom"]),
                Paragraph(pdf_text(item.get("description")), styles["SmallCustom"]),
            ])
        finding_table = Table(
            rows,
            colWidths=[28 * mm, 35 * mm, 22 * mm, 15 * mm, 80 * mm],
            repeatRows=1,
        )
        finding_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(finding_table)
    else:
        story.append(Paragraph("No findings were returned.", styles["BodyText"]))

    story.append(Paragraph(
        f"Remediations ({len(data['remediations'])})",
        styles["SectionCustom"],
    ))
    if data["remediations"]:
        for index, item in enumerate(data["remediations"], 1):
            story.append(Paragraph(
                f"{index}. <b>{pdf_text(item.get('issue'))}</b>",
                styles["BodyText"],
            ))
            story.append(Paragraph(
                f"<b>Severity:</b> {pdf_text(item.get('severity'))} "
                f"| <b>Line:</b> {pdf_text(item.get('line_number'))}",
                styles["SmallCustom"],
            ))
            story.append(Paragraph(
                f"<b>Fix:</b> {pdf_text(item.get('fix_recommendation'))}",
                styles["BodyText"],
            ))
            story.append(Paragraph(
                f"<b>Best practice:</b> {pdf_text(item.get('best_practice'))}",
                styles["BodyText"],
            ))
            corrected = item.get("corrected_code")
            if corrected:
                story.append(Preformatted(str(corrected), styles["CodeCustom"]))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("No remediation items were returned.", styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)
    return buffer


# =========================================================
# RESULTS DASHBOARD PAGE
# =========================================================

def render_results_panel(code="", language="python"):
    st.title("CodeCheck PR Audit & Security Dashboard")
    st.caption(
        f"Language: **{str(language).upper()}** "
        f"| Reviewed: **{datetime.now().strftime('%d %b %Y, %I:%M %p')}**"
    )

    analysis = st.session_state.get("analysis_result")
    if not analysis:
        st.warning("No analysis results found. Please run an analysis first.")
        return

    analysis = to_dict(analysis)

    # Read values already returned by the agents/schema.
    summary = get_summary(analysis)
    findings = get_findings(analysis)
    remediations = get_remediations(analysis)

    total_findings = get_total_findings(summary, findings)
    severity = get_severity_breakdown(summary, findings)
    review_status = clean_text(summary.get("review_status"))
    overview = clean_text(summary.get("overview"))
    merge_recommendation = clean_text(summary.get("merge_recommendation"))
    prioritized_fixes = get_list(summary.get("prioritized_fix_list"))
    findings_df = build_findings_df(findings)

    # Export data uses the same values displayed in the UI.
    export_data = {
        "language": str(language).capitalize(),
        "summary": summary,
        "total_findings": total_findings,
        "severity_breakdown": severity,
        "findings": findings,
        "remediations": remediations,
    }

    # Top Header & Export Action
    header_col, export_col = st.columns([3, 1])
    with header_col:
        st.markdown(f"### Review Status: `{review_status}`")
    with export_col:
        pdf_bytes = generate_dashboard_pdf(export_data)
        st.download_button(
            "Download PDF Report",
            data=pdf_bytes,
            file_name="CodeCheck_PR_Review.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    # KPI Metric Row
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total Findings", total_findings)
    k2.metric("Critical", severity["CRITICAL"])
    k3.metric("High", severity["HIGH"])
    k4.metric("Medium", severity["MEDIUM"])
    k5.metric("Low", severity["LOW"])
    k6.metric("Informational", severity["INFORMATIONAL"])

    st.divider()

    # Organized Dashboard Tabs
    tab_overview, tab_details, tab_code = st.tabs([
        "Overview & Charts",
        f"Findings ({total_findings}) & Remediations ({len(remediations)})",
        "Analyzed Source Code",
    ])

    # --- TAB 1: OVERVIEW & GRAPHS ---
    with tab_overview:
        render_dashboard_charts(severity, findings_df)

        st.divider()

        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.subheader("PR Overview")
            st.write(overview)

            st.subheader("Merge Recommendation")
            st.info(merge_recommendation)

        with info_col2:
            st.subheader("Prioritized Fix List")
            if prioritized_fixes:
                for index, fix in enumerate(prioritized_fixes, 1):
                    st.markdown(f"{index}. {fix}")
            else:
                st.info("No prioritized fixes were provided by the PR Summary Agent.")

    # --- TAB 2: FINDINGS TABLE & REMEDIATION CARDS ---
    with tab_details:
        st.subheader(f"Findings ({total_findings})")
        if findings_df.empty:
            st.success("No findings were returned by the analysis agents.")
        else:
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                severity_options = findings_df["Severity"].dropna().unique().tolist()
                selected_severities = st.multiselect(
                    "Filter by Severity",
                    options=severity_options,
                    default=severity_options,
                )
            with filter_col2:
                category_options = findings_df["Category"].dropna().unique().tolist()
                selected_categories = st.multiselect(
                    "Filter by Category",
                    options=category_options,
                    default=category_options,
                )

            filtered_df = findings_df[
                findings_df["Severity"].isin(selected_severities)
                & findings_df["Category"].isin(selected_categories)
            ]
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
            )

        st.divider()

        st.subheader(f"Remediation Guidance ({len(remediations)})")
        if not remediations:
            st.info("No remediation items were returned by the Remediation Agent.")
        else:
            for index, item in enumerate(remediations, 1):
                issue = clean_text(item.get("issue"), f"Remediation #{index}")
                severity_value = clean_text(item.get("severity"))
                line_number = item.get("line_number")
                line_label = f"Line {line_number}" if line_number is not None else "Not specified"

                with st.expander(
                    f"[{severity_value}] {index}. {issue} — {line_label}",
                    expanded=(index == 1),
                ):
                    st.markdown(f"**Severity:** `{severity_value}` | **Affected line:** `{line_label}`")
                    st.markdown("**Fix recommendation**")
                    st.write(clean_text(item.get("fix_recommendation")))
                    st.markdown("**Best practice**")
                    st.write(clean_text(item.get("best_practice")))

                    corrected_code = item.get("corrected_code")
                    if corrected_code:
                        st.markdown("**Corrected code**")
                        st.code(str(corrected_code), language=str(language).lower())
                    else:
                        st.caption("No corrected code was provided for this item.")

    # --- TAB 3: SOURCE CODE ---
    with tab_code:
        if code:
            st.subheader("Analyzed Source Code")
            st.code(code, language=str(language).lower(), line_numbers=True)
        else:
            st.info("No source code snippet was provided for this review.")

    st.divider()
    render_code_assistant(
        language=language,
        code=code,
        analysis=analysis,
    )