from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ui.components.assistant import render_code_assistant
from ui.components.styles import load_styles

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
# CONSTANTS & PALETTES (PURPLE THEME)
# =========================================================

SEVERITY_ORDER = [
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW",
    "INFORMATIONAL",
]

SEVERITY_COLORS = {
    "CRITICAL": "#DC2626",
    "HIGH": "#EA580C",
    "MEDIUM": "#D97706",
    "LOW": "#7C3AED",
    "INFORMATIONAL": "#64748B",
}

SEVERITY_BG_COLORS = {
    "CRITICAL": "#FEF2F2",
    "HIGH": "#FFF7ED",
    "MEDIUM": "#FFFBEB",
    "LOW": "#F5F3FF",
    "INFORMATIONAL": "#F8FAFC",
}

SEVERITY_BORDER_COLORS = {
    "CRITICAL": "#FECACA",
    "HIGH": "#FFEDD5",
    "MEDIUM": "#FEF3C7",
    "LOW": "#DDD6FE",
    "INFORMATIONAL": "#E2E8F0",
}

SEVERITY_WEIGHTS = {
    "CRITICAL": 20,
    "HIGH": 10,
    "MEDIUM": 5,
    "LOW": 2,
    "INFORMATIONAL": 0,
}


# =========================================================
# GRADE & STATUS HELPERS (PURPLE THEME)
# =========================================================

def calculate_grade(score, severity_breakdown):
    """Compute Letter Grade based on health score and critical vulnerability policy."""
    critical = safe_int(severity_breakdown.get("CRITICAL", 0))
    high = safe_int(severity_breakdown.get("HIGH", 0))

    if critical > 0:
        if score >= 50:
            return "D", "grade-d", "Unsatisfactory", "Critical security vulnerability detected. PR is blocked."
        return "F", "grade-f", "Critical Failure", "Multiple severe security defects detected. Unacceptable risk."

    if score >= 90 and high == 0:
        return "A+", "grade-a", "Excellent", "Production ready. High security & architectural adherence."
    elif score >= 80:
        return "B", "grade-b", "Good Posture", "Acceptable code quality with minor suggestions."
    elif score >= 65:
        return "C", "grade-c", "Moderate Risk", "Technical debt and code smells should be refactored."
    elif score >= 50:
        return "D", "grade-d", "At Risk", "High severity issues require resolution before merge."
    return "F", "grade-f", "Failing", "Unacceptable code health. Comprehensive remediation required."


def render_status_badge(status_text):
    upper = str(status_text).upper()
    if any(k in upper for k in ["APPROV", "PASS", "READY", "CLEAN"]):
        css_class = "status-pass-light"
        dot = '<span class="pulse-dot-green"></span>'
    elif any(k in upper for k in ["REJECT", "BLOCK", "FAIL", "CRITICAL"]):
        css_class = "status-fail-light"
        dot = '<span class="pulse-dot-red"></span>'
    else:
        css_class = "status-warn-light"
        dot = '<span class="pulse-dot-green"></span>'

    return f'<span class="status-badge-light {css_class}">{dot} {escape(status_text)}</span>'


def render_severity_pill(severity):
    sev = str(severity).upper()
    pill_class = {
        "CRITICAL": "sev-critical-light",
        "HIGH": "sev-high-light",
        "MEDIUM": "sev-medium-light",
        "LOW": "sev-low-light",
        "INFORMATIONAL": "sev-info-light",
    }.get(sev, "sev-info-light")
    return f'<span class="sev-pill-light {pill_class}">● {escape(sev)}</span>'


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
    return [to_dict(item) for item in code_findings + security_findings]


def get_remediations(analysis):
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
        severity = clean_text(finding.get("severity"), "").upper()
        if severity in counts:
            counts[severity] += 1
    return counts


def get_total_findings(summary, findings):
    value = summary.get("total_findings")
    return safe_int(value) if value is not None else len(findings)


# =========================================================
# CODE HEALTH CALCULATION 
# =========================================================

def calculate_code_health(findings):
    code_quality_count = 0
    security_count = 0
    penalty = 0

    for finding in findings:
        category = clean_text(finding.get("category"), "").upper()
        finding_type = clean_text(finding.get("finding_type"), "").upper()
        severity = clean_text(finding.get("severity"), "").upper()

        category_text = f"{category} {finding_type}"
        if "CODE" in category_text or "DESIGN" in category_text or "DOCUMENT" in category_text:
            code_quality_count += 1
        elif "SECURITY" in category_text or "SECRET" in category_text or "INJECTION" in category_text:
            security_count += 1
        else:
            code_quality_count += 1

        penalty += SEVERITY_WEIGHTS.get(severity, 0)

    health_score = max(0, min(100, 100 - penalty))

    return {
        "code_quality_count": code_quality_count,
        "security_count": security_count,
        "total_score": health_score,
        "penalty": penalty,
    }


# =========================================================
# FINDINGS DATAFRAME
# =========================================================

def build_findings_df(findings):
    rows = []
    for finding in findings:
        rows.append({
            "Severity": clean_text(finding.get("severity")).upper(),
            "Category": clean_text(finding.get("category")),
            "Issue": clean_text(finding.get("issue")),
            "Line": clean_text(finding.get("line_number")),
            "Description": clean_text(finding.get("description")),
        })

    return pd.DataFrame(
        rows,
        columns=["Severity", "Category", "Issue", "Line", "Description"],
    )


def style_severity_cell(val):
    color = SEVERITY_COLORS.get(val, "#6B7280")
    bg = SEVERITY_BG_COLORS.get(val, "#FAF5FF")
    border = SEVERITY_BORDER_COLORS.get(val, "#EDE9FE")
    return f"color: {color}; background-color: {bg}; font-weight: 700; border: 1px solid {border}; border-radius: 4px;"


# =========================================================
# DASHBOARD CHARTS (PURPLE THEME)
# =========================================================

def render_health_gauge(score):
    if score >= 80:
        bar_color = "#16A34A"
        status_label = "HEALTHY / APPROVED"
    elif score >= 50:
        bar_color = "#D97706"
        status_label = "ACTION REQUIRED"
    else:
        bar_color = "#DC2626"
        status_label = "HIGH RISK / BLOCKED"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100", "font": {"size": 30, "weight": "bold", "color": "#1E1B4B"}},
            title={"text": f"<b>Health Score</b><br><span style='font-size:12px; color:#6B7280;'>{status_label}</span>", "font": {"size": 14, "color": "#1E1B4B"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#DDD6FE", "tickfont": {"color": "#6B7280", "size": 10}},
                "bar": {"color": bar_color, "thickness": 0.8},
                "bgcolor": "#F5F3FF",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 50], "color": "#FEE2E2"},
                    {"range": [50, 80], "color": "#FEF3C7"},
                    {"range": [80, 100], "color": "#DCFCE7"},
                ],
            },
        )
    )
    fig.update_layout(
        height=215,
        margin=dict(t=45, b=10, l=20, r=20),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Plus Jakarta Sans, sans-serif"),
    )
    return fig


def render_dashboard_charts(severity_breakdown, findings_df):
    plot_config = {"displayModeBar": False}
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        with st.container(border=True):
            sev_df = pd.DataFrame([
                {
                    "Severity": severity.title(),
                    "Count": safe_int(severity_breakdown.get(severity, 0)),
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
                title="<b>Findings by Severity</b>",
            )
            fig_sev.update_traces(
                textposition="outside",
                cliponaxis=False,
                marker_line_width=0,
                textfont=dict(color="#1E1B4B", size=12, family="Plus Jakarta Sans"),
            )
            fig_sev.update_layout(
                showlegend=False,
                xaxis_title=None,
                yaxis_title=None,
                yaxis=dict(showgrid=True, gridcolor="#F5F3FF", tickfont=dict(color="#6B7280")),
                xaxis=dict(tickfont=dict(color="#1E1B4B", size=11)),
                title_font=dict(size=14, color="#1E1B4B", family="Plus Jakarta Sans"),
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                margin=dict(t=45, b=15, l=15, r=15),
                height=290,
            )
            st.plotly_chart(fig_sev, use_container_width=True, config=plot_config)

    with chart_col2:
        with st.container(border=True):
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
                    hole=0.55,
                    title="<b>Findings by Category</b>",
                    color_discrete_sequence=["#7C3AED", "#0891B2", "#9333EA", "#D97706", "#16A34A"],
                )
                fig_cat.update_traces(
                    textposition="inside",
                    textinfo="percent+label",
                    textfont=dict(color="#FFFFFF", size=11, family="Plus Jakarta Sans"),
                    marker=dict(line=dict(color="#FFFFFF", width=2)),
                )
                fig_cat.update_layout(
                    showlegend=False,
                    title_font=dict(size=14, color="#1E1B4B", family="Plus Jakarta Sans"),
                    paper_bgcolor="#FFFFFF",
                    plot_bgcolor="#FFFFFF",
                    margin=dict(t=45, b=15, l=15, r=15),
                    height=290,
                )
                st.plotly_chart(fig_cat, use_container_width=True, config=plot_config)
            else:
                st.info("No category data available.")

    if not findings_df.empty and findings_df["Category"].nunique() > 1:
        with st.container(border=True):
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
                title="<b>Severity Distribution Across Defect Categories</b>",
            )
            fig_stack.update_layout(
                xaxis_title=None,
                yaxis_title="Count",
                title_font=dict(size=14, color="#1E1B4B", family="Plus Jakarta Sans"),
                legend_title=None,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#312E81")),
                yaxis=dict(showgrid=True, gridcolor="#F5F3FF", tickfont=dict(color="#6B7280")),
                xaxis=dict(tickfont=dict(color="#1E1B4B", size=11)),
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#FFFFFF",
                margin=dict(t=55, b=15, l=15, r=15),
                height=280,
            )
            st.plotly_chart(fig_stack, use_container_width=True, config=plot_config)


# =========================================================
# PDF REPORT EXPORT
# =========================================================

def create_pdf_charts(severity_breakdown, findings_df):
    chart_images = []

    counts = [
        safe_int(severity_breakdown.get(item, 0))
        for item in SEVERITY_ORDER
    ]

    fig, ax = plt.subplots(figsize=(7.2, 3.0))

    bars = ax.bar(
        [item.title() for item in SEVERITY_ORDER],
        counts,
        color=[SEVERITY_COLORS[item] for item in SEVERITY_ORDER],
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
    fig.savefig(severity_buffer,format="png",dpi=300,bbox_inches="tight",pad_inches=0.15)

    plt.close(fig)
    severity_buffer.seek(0)
    chart_images.append(severity_buffer)

    if not findings_df.empty:
        category_counts = findings_df["Category"].value_counts()

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
        fig.savefig(category_buffer,format="png",dpi=300,bbox_inches="tight",pad_inches=0.15)
        plt.close(fig)
        category_buffer.seek(0)
        chart_images.append(category_buffer)

    return chart_images


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
        textColor=colors.HexColor("#7C3AED"),
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
    code_health = calculate_code_health(findings)
    grade, _, grade_label, _ = calculate_grade(code_health["total_score"], breakdown)

    story = [
        Paragraph("CRSA-Agent — Code Review & Security Analysis Report", styles["Title"]),
        Paragraph(
            f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')} "
            f"| Target Language: {pdf_text(data['language'])}",
            styles["SmallCustom"],
        ),
        Spacer(1, 8),
    ]

    # Health & Grade Table
    story.append(Paragraph("Security & Quality Posture", styles["SectionCustom"]))
    health_rows = [
        ["Security Grade", "Health Score", "Code Quality Smells", "Security Vulnerabilities"],
        [
            f"Grade {grade} ({grade_label})",
            f'{code_health["total_score"]}/100',
            str(code_health["code_quality_count"]),
            str(code_health["security_count"]),
        ],
    ]

    health_table = Table(health_rows, colWidths=[45 * mm, 40 * mm, 45 * mm, 45 * mm])
    health_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4C1D95")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FAF5FF")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#1E1B4B")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, 1), 10),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#DDD6FE")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    story.extend([health_table, Spacer(1, 10)])

    # Severity KPI metrics
    kpi_rows = [
        ["Total Findings", "Critical", "High", "Medium", "Low", "Informational"],
        [
            str(data["total_findings"]),
            str(safe_int(breakdown.get("CRITICAL"))),
            str(safe_int(breakdown.get("HIGH"))),
            str(safe_int(breakdown.get("MEDIUM"))),
            str(safe_int(breakdown.get("LOW"))),
            str(safe_int(breakdown.get("INFORMATIONAL"))),
        ],
    ]

    kpi_table = Table(kpi_rows, colWidths=[28 * mm] * 6)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4C1D95")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FAF5FF")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#1E1B4B")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, 0), 6.5),
        ("FONTSIZE", (0, 1), (-1, 1), 10),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#DDD6FE")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))

    story.extend([kpi_table, Spacer(1, 10)])

    # PR Overview
    story.append(Paragraph("Executive PR Review Overview", styles["SectionCustom"]))
    story.append(Paragraph(f"<b>Executive Summary:</b> {pdf_text(summary.get('overview'))}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Merge Verdict:</b> {pdf_text(summary.get('merge_recommendation'))}", styles["BodyText"]))
    story.append(Paragraph(f"<b>Review Decision:</b> {pdf_text(summary.get('review_status'))}", styles["BodyText"]))

    prioritized_fixes = get_list(summary.get("prioritized_fix_list"))
    if prioritized_fixes:
        story.append(Spacer(1, 5))
        story.append(Paragraph("<b>Required Remediation Roadmap:</b>", styles["BodyText"]))
        for index, fix in enumerate(prioritized_fixes, 1):
            story.append(Paragraph(f"{index}. {pdf_text(fix)}", styles["SmallCustom"]))

    # Visual Analytics
    story.append(Paragraph("Visual Analytics", styles["SectionCustom"]))
    for chart_buffer in create_pdf_charts(breakdown, findings_df):
        chart_buffer.seek(0)
        chart = PDFImage(
        chart_buffer,
        width=170 * mm,
        height=85 * mm,
        kind="proportional",
        )

        chart.hAlign = "CENTER"

        story.append(chart)
        story.append(Spacer(1, 5))

    # Findings
    story.append(Paragraph("Diagnostic Review Findings", styles["SectionCustom"]))
    if findings:
        finding_rows = [["Category", "Issue", "Severity", "Line", "Description"]]
        for item in findings:
            finding_rows.append([
                Paragraph(pdf_text(item.get("category")), styles["SmallCustom"]),
                Paragraph(pdf_text(item.get("issue")), styles["SmallCustom"]),
                Paragraph(pdf_text(item.get("severity")), styles["SmallCustom"]),
                Paragraph(pdf_text(item.get("line_number")), styles["SmallCustom"]),
                Paragraph(pdf_text(item.get("description")), styles["SmallCustom"]),
            ])

        finding_table = Table(
            finding_rows,
            colWidths=[27 * mm, 34 * mm, 21 * mm, 13 * mm, 80 * mm],
            repeatRows=1,
        )
        finding_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4C1D95")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#DDD6FE")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(finding_table)

    # Remediation
    story.append(Paragraph("Remediation Playbook & Suggested Patches", styles["SectionCustom"]))
    if remediations:
        for index, item in enumerate(remediations, 1):
            block = [
                Paragraph(f"<b>{index}. {pdf_text(item.get('issue'))}</b>", styles["BodyText"]),
                Paragraph(
                    f"<b>Severity:</b> {pdf_text(item.get('severity'))} | "
                    f"<b>Line:</b> {pdf_text(item.get('line_number'))}",
                    styles["SmallCustom"],
                ),
                Paragraph(f"<b>Fix Recommendation:</b> {pdf_text(item.get('fix_recommendation'))}", styles["BodyText"]),
                Paragraph(f"<b>Best Practice:</b> {pdf_text(item.get('best_practice'))}", styles["BodyText"]),
            ]

            corrected_code = item.get("corrected_code")
            if corrected_code:
                block.append(Preformatted(str(corrected_code), styles["CodeCustom"]))

            block.append(Spacer(1, 7))
            story.append(KeepTogether(block))

    doc.build(story)
    buffer.seek(0)
    return buffer


# =========================================================
# REARRANGED EXECUTIVE DASHBOARD (PURPLE LIGHT THEME)
# =========================================================

def render_results_panel(code="", language="python"):
    load_styles()

    analysis = st.session_state.get("analysis_result")
    if not analysis:
        st.info("No active analysis session found. Please submit source code from the scanner panel.")
        if st.button("⬅️ Return to Code Scanner", type="primary"):
            st.switch_page("pages/input_page.py")
        return

    analysis = to_dict(analysis)
    summary = get_summary(analysis)
    findings = get_findings(analysis)
    remediations = get_remediations(analysis)
    total_findings = get_total_findings(summary, findings)
    severity = get_severity_breakdown(summary, findings)
    code_health = calculate_code_health(findings)

    # Compute Grade
    grade, grade_css, grade_title, grade_desc = calculate_grade(code_health["total_score"], severity)

    review_status = clean_text(summary.get("review_status"), "REVIEW_PENDING")
    overview = clean_text(summary.get("overview"), "No overview available.")
    merge_recommendation = clean_text(summary.get("merge_recommendation"), "No recommendation provided.")
    prioritized_fixes = get_list(summary.get("prioritized_fix_list"))
    findings_df = build_findings_df(findings)

    export_data = {
        "language": str(language).capitalize(),
        "summary": summary,
        "total_findings": total_findings,
        "severity_breakdown": severity,
        "findings": findings,
        "remediations": remediations,
        "code": code,
    }

    # -----------------------------------------------------
    # 1. TOP HEADER & ACTION BAR
    # -----------------------------------------------------
    title_col, action_col = st.columns([3.1, 1.4], vertical_alignment="center")

    with title_col:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <h2 style="margin: 0; padding: 0; color: #1e1b4b;">📊 Security Audit & PR Review Dashboard</h2>
                {render_status_badge(review_status)}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            f"Language: **{str(language).upper()}** • "
            f"Audit Timestamp: **{datetime.now().strftime('%d %b %Y, %I:%M %p')}** • "
            f"Analyzed Lines: **{len(code.splitlines()) if code else 'N/A'}**"
        )

    with action_col:
        btn_c1, btn_c2 = st.columns([1, 1.3])
        with btn_c1:
            if st.button("⬅️ New Scan", use_container_width=True, help="Scan another code snippet"):
                st.switch_page("pages/input_page.py")
        with btn_c2:
            pdf_bytes = generate_dashboard_pdf(export_data)
            st.download_button(
                "📥 Export PDF",
                data=pdf_bytes,
                file_name=f"CRSA_Audit_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )

    st.write("")

    # -----------------------------------------------------
    # 2. EXECUTIVE SCORECARD (GRADE & COMPLIANCE POSTURE)
    # -----------------------------------------------------
    scorecard_left, scorecard_right = st.columns([1.5, 1.5])

    with scorecard_left:
        st.markdown(
            f"""
            <div class="grade-card">
                <div class="grade-badge-circle {grade_css}">
                    {grade}
                </div>
                <div>
                    <div style="font-size: 0.76rem; font-weight: 700; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em;">
                        Security & Quality Posture
                    </div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: #1e1b4b; margin: 3px 0;">
                        Grade {grade} — {grade_title}
                    </div>
                    <div style="font-size: 0.84rem; color: #4b5563; line-height: 1.4;">
                        {grade_desc}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with scorecard_right:
        st.markdown(
            f"""
            <div class="card-light" style="height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div class="card-light-title">Automated Remediation & Standards</div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: #16a34a; margin-top: 2px;">
                        {len(remediations)} / {total_findings} Automated Patches Generated
                    </div>
                    <div style="font-size: 0.82rem; color: #6b7280; margin-top: 4px; line-height: 1.4;">
                        100% of detected vulnerabilities and code smells have verified remediation diffs ready to apply.
                    </div>
                </div>
                <div style="display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap;">
                    <span class="badge-pill-light badge-purple">OWASP Top 10</span>
                    <span class="badge-pill-light badge-cyan">CWE Indexed</span>
                    <span class="badge-pill-light badge-green">AST Verified</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # -----------------------------------------------------
    # 3. FULL-WIDTH SPACIOUS KPI METRIC STRIP (6 COLUMNS)
    # -----------------------------------------------------
    k1, k2, k3, k4, k5, k6 = st.columns(6)

    health_score_val = code_health["total_score"]
    health_accent = "#16A34A" if health_score_val >= 80 else ("#D97706" if health_score_val >= 50 else "#DC2626")

    with k1:
        st.markdown(
            f"""
            <div class="kpi-metric-card" style="border-top: 4px solid {health_accent};">
                <div class="kpi-metric-label">🛡️ Health Score</div>
                <div class="kpi-metric-value" style="color: {health_accent};">{health_score_val}/100</div>
                <div class="kpi-metric-subtext">Overall Code Health</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k2:
        st.markdown(
            f"""
            <div class="kpi-metric-card" style="border-top: 4px solid #7C3AED;">
                <div class="kpi-metric-label">📌 Total Issues</div>
                <div class="kpi-metric-value" style="color: #7C3AED;">{total_findings}</div>
                <div class="kpi-metric-subtext">Quality & Security</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k3:
        st.markdown(
            f"""
            <div class="kpi-metric-card" style="border-top: 4px solid #DC2626;">
                <div class="kpi-metric-label">🚨 Critical</div>
                <div class="kpi-metric-value" style="color: #DC2626;">{safe_int(severity["CRITICAL"])}</div>
                <div class="kpi-metric-subtext">Blocks PR Merge (P0)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k4:
        st.markdown(
            f"""
            <div class="kpi-metric-card" style="border-top: 4px solid #EA580C;">
                <div class="kpi-metric-label">🔥 High</div>
                <div class="kpi-metric-value" style="color: #EA580C;">{safe_int(severity["HIGH"])}</div>
                <div class="kpi-metric-subtext">Fix Before Merge (P1)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k5:
        st.markdown(
            f"""
            <div class="kpi-metric-card" style="border-top: 4px solid #D97706;">
                <div class="kpi-metric-label">⚡ Medium</div>
                <div class="kpi-metric-value" style="color: #D97706;">{safe_int(severity["MEDIUM"])}</div>
                <div class="kpi-metric-subtext">Design Anti-pattern</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with k6:
        low_info_count = safe_int(severity["LOW"]) + safe_int(severity["INFORMATIONAL"])
        st.markdown(
            f"""
            <div class="kpi-metric-card" style="border-top: 4px solid #9333EA;">
                <div class="kpi-metric-label">ℹ️ Low / Info</div>
                <div class="kpi-metric-value" style="color: #9333EA;">{low_info_count}</div>
                <div class="kpi-metric-subtext">Code Quality Smells</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")

    # -----------------------------------------------------
    # 4. WORKSPACE TABS (PURPLE THEME)
    # -----------------------------------------------------
    tab_overview, tab_findings, tab_remediation, tab_code, tab_chat = st.tabs([
        "📊 Executive Overview & Analytics",
        f"🔍 Findings Table ({total_findings})",
        f"🛠️ Remediation Playbook ({len(remediations)} Patches)",
        "📄 Analyzed Source",
        "💬 AI Code Assistant",
    ])

    # =====================================================
    # TAB 1: EXECUTIVE OVERVIEW & VISUAL ANALYTICS
    # =====================================================
    with tab_overview:
        c_left, c_right = st.columns([1.1, 2.2], vertical_alignment="top")

        with c_left:
            with st.container(border=True):
                st.plotly_chart(
                    render_health_gauge(code_health["total_score"]),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
                st.markdown(
                    f"""
                    <div style="background: #faf5ff; padding: 12px; border-radius: 8px; border: 1px solid #ede9fe; margin-top: 6px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">
                            <span style="color: #6b7280;">🔍 Code Quality Smells:</span>
                            <span style="font-weight: 700; color: #7c3aed;">{code_health['code_quality_count']}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
                            <span style="color: #6b7280;">🛡️ Security Vulnerabilities:</span>
                            <span style="font-weight: 700; color: #dc2626;">{code_health['security_count']}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with c_right:
            c_exec1, c_exec2 = st.columns(2)
            with c_exec1:
                st.markdown(
                    f"""
                    <div class="card-light" style="height: 100%;">
                        <div class="card-light-title">
                            <span>📝</span> Executive Review Summary
                        </div>
                        <div style="font-size: 0.90rem; color: #312e81; line-height: 1.55;">
                            {escape(overview)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c_exec2:
                st.markdown(
                    f"""
                    <div class="card-light" style="height: 100%;">
                        <div class="card-light-title">
                            <span>🔀</span> PR Merge Verdict
                        </div>
                        <div style="font-size: 0.90rem; color: #312e81; line-height: 1.55;">
                            {escape(merge_recommendation)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if prioritized_fixes:
                st.write("")
                st.markdown("#### ⚡ Priority Action Roadmap (Required Before Merge)")
                for idx, fix in enumerate(prioritized_fixes, 1):
                    st.markdown(
                        f"""
                        <div class="action-item-light">
                            <strong style="color: #7c3aed; margin-right: 6px;">#{idx}</strong> 
                            {escape(str(fix))}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        st.markdown('<div class="purple-divider"></div>', unsafe_allow_html=True)
        st.markdown("### 📈 Visual Vulnerability & Quality Distribution")
        render_dashboard_charts(severity, findings_df)

    # =====================================================
    # TAB 2: FINDINGS TABLE & DEEP DIVE
    # =====================================================
    with tab_findings:
        st.markdown("### 🔍 Diagnostic Review Findings")
        st.caption("Complete inventory of code quality defects, anti-patterns, and OWASP security vulnerabilities:")

        if findings_df.empty:
            st.success("🎉 Zero issues detected! Your code passed all quality, security, and architectural checks.")
        else:
            f_col1, f_col2, f_col3 = st.columns([1.2, 1.2, 1.6])

            with f_col1:
                severity_options = [s for s in SEVERITY_ORDER if s in findings_df["Severity"].unique()] or findings_df["Severity"].dropna().unique().tolist()
                selected_severities = st.multiselect(
                    "Severity Filter",
                    options=findings_df["Severity"].dropna().unique().tolist(),
                    default=findings_df["Severity"].dropna().unique().tolist(),
                )

            with f_col2:
                category_options = findings_df["Category"].dropna().unique().tolist()
                selected_categories = st.multiselect(
                    "Category Filter",
                    options=category_options,
                    default=category_options,
                )

            with f_col3:
                search_query = st.text_input(
                    "Search Findings",
                    placeholder="Search by issue title, line number, keyword...",
                )

            filtered_df = findings_df[
                findings_df["Severity"].isin(selected_severities)
                & findings_df["Category"].isin(selected_categories)
            ]

            if search_query.strip():
                q = search_query.strip().lower()
                filtered_df = filtered_df[
                    filtered_df.apply(
                        lambda r: q in str(r["Issue"]).lower()
                        or q in str(r["Description"]).lower()
                        or q in str(r["Line"]).lower(),
                        axis=1,
                    )
                ]

            st.caption(f"Displaying **{len(filtered_df)}** of **{len(findings_df)}** detected issues.")

            styled_df = filtered_df.style.map(
                style_severity_cell, subset=["Severity"]
            )

            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Severity": st.column_config.TextColumn("Severity", width="small"),
                    "Category": st.column_config.TextColumn("Category", width="medium"),
                    "Issue": st.column_config.TextColumn("Defect / Vulnerability", width="medium"),
                    "Line": st.column_config.TextColumn("Line", width="small"),
                    "Description": st.column_config.TextColumn("Diagnostic Description", width="large"),
                },
            )

    # =====================================================
    # TAB 3: REMEDIATION PLAYBOOK (PATCHES & DIFFS)
    # =====================================================
    with tab_remediation:
        st.markdown("### 🛠️ Automated Remediation Playbook")
        st.caption("AI-generated fix recommendations, industry best practices, and verified corrected code patches:")

        if remediations:
            for index, item in enumerate(remediations, 1):
                issue = clean_text(item.get("issue"), f"Remediation #{index}")
                sev_val = clean_text(item.get("severity")).upper()
                line_num = item.get("line_number")
                line_label = f"Line {line_num}" if line_num is not None else "Global"

                with st.expander(
                    f"{index}. [{sev_val}] {issue}  •  {line_label}",
                    expanded=(index <= 2),
                ):
                    rec_col, bp_col = st.columns(2)
                    with rec_col:
                        st.markdown("**🔧 Fix Recommendation**")
                        st.info(clean_text(item.get("fix_recommendation")))
                    with bp_col:
                        st.markdown("**🛡️ Secure Coding Standard / Best Practice**")
                        st.success(clean_text(item.get("best_practice")))

                    corrected_code = item.get("corrected_code")
                    if corrected_code:
                        st.markdown("**✨ Verified Corrected Patch (Remediation Diff)**")
                        st.code(str(corrected_code), language=str(language).lower())
        else:
            st.info("No specific remediation patches were generated for this run.")

    # =====================================================
    # TAB 4: ANALYZED SOURCE CODE
    # =====================================================
    with tab_code:
        st.markdown("### 📄 Submitted Source Code Under Audit")
        if code:
            st.caption(f"Language: **{str(language).upper()}** • Total Lines: **{len(code.splitlines())}**")
            st.code(code, language=str(language).lower(), line_numbers=True)
        else:
            st.info("No source code snippet was attached to this session.")

    # =====================================================
    # TAB 5: AI CODE ASSISTANT (RAG)
    # =====================================================
    with tab_chat:
        render_code_assistant(
            language=language,
            code=code,
            analysis=analysis,
        )
