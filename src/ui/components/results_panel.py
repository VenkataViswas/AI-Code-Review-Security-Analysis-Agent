
from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape

import streamlit as st
import pandas as pd
import plotly.express as px

from ui.components.assistant import render_code_assistant

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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
    Image as PDFImage,
    KeepTogether,
)


# =========================================================
# CONSTANTS
# =========================================================

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]

SEVERITY_COLORS = {
    "CRITICAL": "#DC2626",
    "HIGH": "#EA580C",
    "MEDIUM": "#D97706",
    "LOW": "#2563EB",
    "INFORMATIONAL": "#64748B",
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


def safe_int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def get_summary(analysis):
    raw = analysis.get("pr_summary")

    if raw is None:
        return {}

    outer = to_dict(raw)
    nested = outer.get("summary")

    return to_dict(nested) if nested is not None else outer


def get_findings(analysis):
    unified = get_list(analysis.get("unified_findings"))

    if unified:
        return [to_dict(item) for item in unified]

    code_findings = get_list(analysis.get("code_findings"))
    security_findings = get_list(analysis.get("security_findings"))

    return [
        to_dict(item)
        for item in code_findings + security_findings
    ]


def get_remediations(analysis):
    raw = analysis.get("remediation_findings")

    if raw is None:
        raw = analysis.get("remediation")

    if raw is None:
        return []

    data = to_dict(raw)

    if data:
        return [
            to_dict(item)
            for item in get_list(data.get("remediations"))
        ]

    return [to_dict(item) for item in get_list(raw)]


def get_severity_breakdown(summary, findings):

    breakdown = to_dict(summary.get("severity_breakdown"))

    keys = {
        "INFORMATIONAL": "informational",
        "LOW": "low",
        "MEDIUM": "medium",
        "HIGH": "high",
        "CRITICAL": "critical",
    }

    if any(field in breakdown for field in keys.values()):
        return {
            severity: safe_int(breakdown.get(field))
            for severity, field in keys.items()
        }

    counts = {severity: 0 for severity in keys}

    for finding in findings:
        severity = clean_text(
            finding.get("severity"), ""
        ).upper()

        if severity in counts:
            counts[severity] += 1

    return counts


def get_total_findings(summary, findings):
    value = summary.get("total_findings")
    return value if value is not None else len(findings)


def build_findings_df(findings):

    rows = []

    for finding in findings:
        rows.append({
            "Category": clean_text(finding.get("category")),
            "Issue": clean_text(finding.get("issue")),
            "Severity": clean_text(
                finding.get("severity")
            ).upper(),
            "Line": clean_text(finding.get("line_number")),
            "Description": clean_text(finding.get("description")),
        })

    return pd.DataFrame(
        rows,
        columns=[
            "Category",
            "Issue",
            "Severity",
            "Line",
            "Description",
        ],
    )


# =========================================================
# DASHBOARD CHARTS
# =========================================================

def render_dashboard_charts(severity_breakdown, findings_df):

    st.markdown("**Visual Analytics**")

    chart_col1, chart_col2 = st.columns(2)

    # Severity distribution
    with chart_col1:

        sev_df = pd.DataFrame([
            {
                "Severity": severity.title(),
                "Count": safe_int(
                    severity_breakdown.get(severity, 0)
                ),
                "SeverityKey": severity,
            }
            for severity in SEVERITY_ORDER
        ])

        fig_sev = px.bar(
            sev_df,
            x="Severity",
            y="Count",
            color="SeverityKey",
            color_discrete_map=SEVERITY_COLORS,
            text="Count",
            title="Findings by Severity",
        )

        fig_sev.update_traces(
            textposition="outside",
            cliponaxis=False,
        )

        fig_sev.update_layout(
            showlegend=False,
            xaxis_title=None,
            yaxis_title="Number of Findings",
            margin=dict(t=55, b=20, l=20, r=20),
            height=330,
        )

        st.plotly_chart(
            fig_sev,
            use_container_width=True,
        )

    # Category distribution
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
                hole=0.48,
                title="Findings by Category",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )

            fig_cat.update_traces(
                textinfo="percent+label"
            )

            fig_cat.update_layout(
                margin=dict(t=55, b=20, l=20, r=20),
                height=330,
            )

            st.plotly_chart(
                fig_cat,
                use_container_width=True,
            )

        else:
            st.info("No category data available.")

    # Severity by category
    if not findings_df.empty:

        grouped = (
            findings_df.groupby(
                ["Category", "Severity"]
            )
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
            category_orders={
                "Severity": SEVERITY_ORDER
            },
            title="Severity Breakdown Across Categories",
        )

        fig_stack.update_layout(
            xaxis_title=None,
            yaxis_title="Number of Findings",
            legend_title="Severity",
            margin=dict(t=55, b=20, l=20, r=20),
            height=320,
        )

        st.plotly_chart(
            fig_stack,
            use_container_width=True,
        )


# =========================================================
# PDF CHART GENERATION
# =========================================================

def create_pdf_charts(severity_breakdown, findings_df):

    chart_images = []

    # Severity chart
    severities = SEVERITY_ORDER

    counts = [
        safe_int(severity_breakdown.get(item, 0))
        for item in severities
    ]

    fig, ax = plt.subplots(figsize=(7.2, 3.0))

    bars = ax.bar(
        [item.title() for item in severities],
        counts,
        color=[
            SEVERITY_COLORS[item]
            for item in severities
        ],
    )

    ax.set_title("Findings by Severity")
    ax.set_ylabel("Number of Findings")
    ax.grid(axis="y", alpha=0.2)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            str(count),
            ha="center",
            va="bottom",
            fontsize=8,
        )

    fig.tight_layout()

    severity_buffer = BytesIO()

    fig.savefig(
        severity_buffer,
        format="png",
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(fig)
    severity_buffer.seek(0)

    chart_images.append(severity_buffer)

    # Category donut chart
    if not findings_df.empty:

        category_counts = (
            findings_df["Category"].value_counts()
        )

        fig, ax = plt.subplots(figsize=(6.2, 3.0))

        ax.pie(
            category_counts.values,
            labels=category_counts.index,
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops={"width": 0.45},
        )

        ax.set_title("Findings by Category")
        fig.tight_layout()

        category_buffer = BytesIO()

        fig.savefig(
            category_buffer,
            format="png",
            dpi=160,
            bbox_inches="tight",
        )

        plt.close(fig)
        category_buffer.seek(0)

        chart_images.append(category_buffer)

    # Stacked chart
    if not findings_df.empty:

        grouped = (
            findings_df.groupby(
                ["Category", "Severity"]
            )
            .size()
            .unstack(fill_value=0)
            .reindex(
                columns=SEVERITY_ORDER,
                fill_value=0,
            )
        )

        fig, ax = plt.subplots(figsize=(7.2, 3.0))

        grouped.plot(
            kind="bar",
            stacked=True,
            ax=ax,
            color=[
                SEVERITY_COLORS[item]
                for item in SEVERITY_ORDER
            ],
        )

        ax.set_title(
            "Severity Breakdown Across Categories"
        )
        ax.set_xlabel("")
        ax.set_ylabel("Number of Findings")
        ax.legend(title="Severity", fontsize=7)
        ax.tick_params(axis="x", rotation=20)

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        fig.tight_layout()

        stacked_buffer = BytesIO()

        fig.savefig(
            stacked_buffer,
            format="png",
            dpi=160,
            bbox_inches="tight",
        )

        plt.close(fig)
        stacked_buffer.seek(0)

        chart_images.append(stacked_buffer)

    return chart_images


# =========================================================
# PDF EXPORT
# =========================================================

def generate_dashboard_pdf(data):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=13 * mm,
        leftMargin=13 * mm,
        topMargin=13 * mm,
        bottomMargin=13 * mm,
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="SectionCustom",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1D4ED8"),
        spaceBefore=9,
        spaceAfter=5,
    ))

    styles.add(ParagraphStyle(
        name="SmallCustom",
        parent=styles["BodyText"],
        fontSize=7.5,
        leading=10,
    ))

    styles.add(ParagraphStyle(
        name="CodeCustom",
        parent=styles["Code"],
        fontSize=6.5,
        leading=8,
    ))

    summary = data["summary"]
    findings = data["findings"]
    remediations = data["remediations"]
    breakdown = data["severity_breakdown"]

    findings_df = build_findings_df(findings)

    story = [
        Paragraph(
            "CodeCheck — PR Review Dashboard",
            styles["Title"],
        ),
        Paragraph(
            f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')} "
            f"| Language: {pdf_text(data['language'])}",
            styles["SmallCustom"],
        ),
        Spacer(1, 8),
    ]

    # KPI metrics
    kpi_rows = [
        [
            "Total Findings",
            "Critical",
            "High",
            "Medium",
            "Low",
            "Informational",
        ],
        [
            str(data["total_findings"]),
            str(safe_int(breakdown.get("CRITICAL"))),
            str(safe_int(breakdown.get("HIGH"))),
            str(safe_int(breakdown.get("MEDIUM"))),
            str(safe_int(breakdown.get("LOW"))),
            str(safe_int(breakdown.get("INFORMATIONAL"))),
        ],
    ]

    kpi_table = Table(
        kpi_rows,
        colWidths=[28 * mm] * 6,
    )

    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F1F5F9")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#0F172A")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, 0), 6.5),
        ("FONTSIZE", (0, 1), (-1, 1), 10),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))

    story.extend([
        kpi_table,
        Spacer(1, 10),
    ])

    # PR overview
    story.append(
        Paragraph(
            "PR Review Overview",
            styles["SectionCustom"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Executive Overview:</b> "
            f"{pdf_text(summary.get('overview'))}",
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Merge Recommendation:</b> "
            f"{pdf_text(summary.get('merge_recommendation'))}",
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            f"<b>Review Status:</b> "
            f"{pdf_text(summary.get('review_status'))}",
            styles["BodyText"],
        )
    )

    prioritized_fixes = get_list(
        summary.get("prioritized_fix_list")
    )

    if prioritized_fixes:

        story.append(Spacer(1, 5))

        story.append(
            Paragraph(
                "<b>Priority Actions</b>",
                styles["BodyText"],
            )
        )

        for index, fix in enumerate(prioritized_fixes, 1):
            story.append(
                Paragraph(
                    f"{index}. {pdf_text(fix)}",
                    styles["SmallCustom"],
                )
            )

    # Charts
    story.append(
        Paragraph(
            "Visual Analytics",
            styles["SectionCustom"],
        )
    )

    for chart_buffer in create_pdf_charts(
        breakdown,
        findings_df,
    ):

        chart = PDFImage(chart_buffer)
        chart.drawHeight = 60 * mm
        chart.drawWidth = 175 * mm
        chart.hAlign = "CENTER"

        story.append(chart)
        story.append(Spacer(1, 5))

    # Findings
    story.append(
        Paragraph(
            f"Review Details  ",
            styles["SectionCustom"],
        )
    )

    if findings:

        finding_rows = [[
            "Category",
            "Issue",
            "Severity",
            "Line",
            "Description",
        ]]

        for item in findings:

            finding_rows.append([
                Paragraph(
                    pdf_text(item.get("category")),
                    styles["SmallCustom"],
                ),
                Paragraph(
                    pdf_text(item.get("issue")),
                    styles["SmallCustom"],
                ),
                Paragraph(
                    pdf_text(item.get("severity")),
                    styles["SmallCustom"],
                ),
                Paragraph(
                    pdf_text(item.get("line_number")),
                    styles["SmallCustom"],
                ),
                Paragraph(
                    pdf_text(item.get("description")),
                    styles["SmallCustom"],
                ),
            ])

        finding_table = Table(
            finding_rows,
            colWidths=[
                27 * mm,
                34 * mm,
                21 * mm,
                13 * mm,
                80 * mm,
            ],
            repeatRows=1,
        )

        finding_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))

        story.append(finding_table)

    else:

        story.append(
            Paragraph(
                "No findings were returned.",
                styles["BodyText"],
            )
        )

    # Remediation details
    if remediations:

        story.append(
            Paragraph(
                "Recommended Fixes",
                styles["SectionCustom"],
            )
        )

        for index, item in enumerate(remediations, 1):

            block = [
                Paragraph(
                    f"<b>{index}. {pdf_text(item.get('issue'))}</b>",
                    styles["BodyText"],
                ),
                Paragraph(
                    f"<b>Severity:</b> {pdf_text(item.get('severity'))} "
                    f"| <b>Line:</b> {pdf_text(item.get('line_number'))}",
                    styles["SmallCustom"],
                ),
                Paragraph(
                    f"<b>Fix recommendation:</b> "
                    f"{pdf_text(item.get('fix_recommendation'))}",
                    styles["BodyText"],
                ),
                Paragraph(
                    f"<b>Best practice:</b> "
                    f"{pdf_text(item.get('best_practice'))}",
                    styles["BodyText"],
                ),
            ]

            corrected_code = item.get("corrected_code")

            if corrected_code:
                block.append(
                    Preformatted(
                        str(corrected_code),
                        styles["CodeCustom"],
                    )
                )

            block.append(Spacer(1, 7))
            story.append(KeepTogether(block))

    else:

        story.append(
            Paragraph(
                "No remediation items were returned.",
                styles["BodyText"],
            )
        )

    # Source code
    if data.get("code"):

        story.append(
            Paragraph(
                "Analyzed Source Code",
                styles["SectionCustom"],
            )
        )

        story.append(
            Preformatted(
                str(data["code"]),
                styles["CodeCustom"],
            )
        )

    doc.build(story)

    buffer.seek(0)
    return buffer


# =========================================================
# UNIFIED RESULTS DASHBOARD
# =========================================================

def render_results_panel(code="", language="python"):

    st.title("CodeCheck PR Audit & Security Dashboard")

    st.caption(
        f"Language: **{str(language).upper()}** "
        f"| Reviewed: **{datetime.now().strftime('%d %b %Y, %I:%M %p')}**"
    )

    analysis = st.session_state.get("analysis_result")

    if not analysis:
        st.warning(
            "No analysis results found. Please run an analysis first."
        )
        return

    analysis = to_dict(analysis)

    # Retrieve agent outputs
    summary = get_summary(analysis)
    findings = get_findings(analysis)
    remediations = get_remediations(analysis)

    total_findings = get_total_findings(
        summary,
        findings,
    )

    severity = get_severity_breakdown(
        summary,
        findings,
    )

    review_status = clean_text(
        summary.get("review_status")
    )

    overview = clean_text(
        summary.get("overview")
    )

    merge_recommendation = clean_text(
        summary.get("merge_recommendation")
    )

    prioritized_fixes = get_list(
        summary.get("prioritized_fix_list")
    )

    findings_df = build_findings_df(findings)

    # PDF export data
    export_data = {
        "language": str(language).capitalize(),
        "summary": summary,
        "total_findings": total_findings,
        "severity_breakdown": severity,
        "findings": findings,
        "remediations": remediations,
        "code": code,
    }

    # Header and export
    header_col, export_col = st.columns([3, 1])

    with header_col:
        st.markdown(
            f"### Review Status: `{review_status}`"
        )

    with export_col:

        pdf_bytes = generate_dashboard_pdf(export_data)

        st.download_button(
            "Download PDF Report",
            data=pdf_bytes,
            file_name="CodeCheck_PR_Review.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    # KPI metrics
    k1, k2, k3, k4, k5, k6 = st.columns(6)

    k1.metric("Total Findings", total_findings)
    k2.metric("Critical", severity["CRITICAL"])
    k3.metric("High", severity["HIGH"])
    k4.metric("Medium", severity["MEDIUM"])
    k5.metric("Low", severity["LOW"])
    k6.metric("Informational", severity["INFORMATIONAL"])

    st.divider()

    # Overview and recommendation
    st.subheader("PR Review Overview")

    overview_col, recommendation_col = st.columns(2)

    with overview_col:
        st.markdown("**Executive Overview**")
        st.write(overview)

    with recommendation_col:
        st.markdown("**Merge Recommendation**")
        st.info(merge_recommendation)

    if prioritized_fixes:

        st.markdown("**Priority Actions**")

        for index, fix in enumerate(prioritized_fixes, 1):
            st.markdown(f"{index}. {fix}")

    # Charts
    render_dashboard_charts(
        severity,
        findings_df,
    )

    st.divider()

    # Findings and remediations
    st.subheader(
        f"Review Details "
    )

    if findings_df.empty:

        st.success(
            "No findings were returned by the analysis agents."
        )

    else:

        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:

            severity_options = (
                findings_df["Severity"]
                .dropna()
                .unique()
                .tolist()
            )

            selected_severities = st.multiselect(
                "Filter by Severity",
                options=severity_options,
                default=severity_options,
            )

        with filter_col2:

            category_options = (
                findings_df["Category"]
                .dropna()
                .unique()
                .tolist()
            )

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

    # Remediation guidance
    if remediations:

        st.markdown("**Recommended Fixes**")

        for index, item in enumerate(remediations, 1):

            issue = clean_text(
                item.get("issue"),
                f"Remediation #{index}",
            )

            severity_value = clean_text(
                item.get("severity")
            )

            line_number = item.get("line_number")

            line_label = (
                f"Line {line_number}"
                if line_number is not None
                else "Not specified"
            )

            with st.expander(
                f"{index}. [{severity_value}] {issue} — {line_label}",
                expanded=(index == 1),
            ):

                st.markdown(
                    f"**Severity:** `{severity_value}` | "
                    f"**Affected line:** `{line_label}`"
                )

                st.markdown("**Fix Recommendation**")

                st.write(
                    clean_text(
                        item.get("fix_recommendation")
                    )
                )

                st.markdown("**Best Practice**")

                st.write(
                    clean_text(
                        item.get("best_practice")
                    )
                )

                corrected_code = item.get("corrected_code")

                if corrected_code:

                    st.markdown("**Suggested Corrected Code**")

                    st.code(
                        str(corrected_code),
                        language=str(language).lower(),
                    )

                else:

                    st.caption(
                        "No corrected code was provided for this item."
                    )

    # Source code: expandable, not a separate dashboard section
    if code:

        with st.expander("View Analyzed Source Code"):

            st.code(
                code,
                language=str(language).lower(),
                line_numbers=True,
            )

    else:

        st.caption(
            "No source code snippet was provided for this review."
        )

    # Code assistant
    st.divider()

    render_code_assistant(
        language=language,
        code=code,
        analysis=analysis,
    )
