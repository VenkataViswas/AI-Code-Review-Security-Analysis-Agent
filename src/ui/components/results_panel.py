from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ui.components.assistant import render_code_assistant

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as PDFImage,
    PageBreak,
    Preformatted,
)


# =========================================================
# CUSTOM CSS STYLING
# =========================================================

def inject_dashboard_css():
    st.markdown(
        """
        <style>
        .kpi-card {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 16px 18px;
            color: #F8FAFC;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.18);
            margin-bottom: 10px;
        }
        .kpi-title {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #94A3B8;
            margin-bottom: 6px;
            font-weight: 700;
        }
        .kpi-value {
            font-size: 1.85rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 6px;
        }
        .kpi-sub {
            font-size: 0.78rem;
            color: #CBD5E1;
        }
        .gate-banner {
            padding: 14px 20px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 1.05rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        .gate-blocked {
            background-color: rgba(220, 38, 38, 0.16);
            border-left: 6px solid #DC2626;
            color: #FCA5A5;
        }
        .gate-warning {
            background-color: rgba(234, 88, 12, 0.16);
            border-left: 6px solid #EA580C;
            color: #FDBA74;
        }
        .gate-pass {
            background-color: rgba(22, 163, 74, 0.16);
            border-left: 6px solid #16A34A;
            color: #86EFAC;
        }
        .summary-box {
            background-color: rgba(30, 41, 59, 0.45);
            border: 1px solid rgba(148, 163, 184, 0.25);
            border-radius: 10px;
            padding: 16px 18px;
            line-height: 1.55;
            margin-bottom: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def get_value(data, *keys, default=""):
    data = to_dict(data)
    for key in keys:
        value = data.get(key)
        if value is not None and value != "":
            return value
    return default


def clean_text(value):
    if value is None:
        return "Not available"
    if isinstance(value, (dict, list)):
        return str(value)
    return str(value)


def pdf_text(value):
    return escape(clean_text(value)).replace("\n", "<br/>")


# =========================================================
# ANALYTICS & METRIC COMPUTATION
# =========================================================

def get_findings(analysis):
    unified = get_list(analysis.get("unified_findings"))
    if unified:
        return [to_dict(item) for item in unified]
    code_findings = get_list(analysis.get("code_findings"))
    security_findings = get_list(analysis.get("security_findings"))
    return [to_dict(item) for item in code_findings + security_findings]


def get_remediations(analysis):
    """Extract RemediationResult.remediations list accurately."""
    remediation = analysis.get("remediation_findings")
    if remediation is None:
        remediation = analysis.get("remediation")
    if remediation is None:
        return []

    remediation = (
        to_dict(remediation)
        if not isinstance(remediation, (dict, list, tuple))
        else remediation
    )

    if isinstance(remediation, dict):
        if "remediations" in remediation:
            return [to_dict(item) for item in get_list(remediation["remediations"])]
        for key in ("findings", "suggestions", "items"):
            if key in remediation:
                return [to_dict(item) for item in get_list(remediation[key])]
        return [remediation]

    return [to_dict(item) for item in get_list(remediation)]


def get_pr_summary(analysis):
    summary = analysis.get("pr_summary")
    if isinstance(summary, str):
        return summary
    summary_dict = to_dict(summary)
    for key in ("summary", "overall_summary", "description", "content"):
        if summary_dict.get(key):
            return str(summary_dict[key])
    return "No PR summary was returned by the PR Summary Agent."


def normalize_severity(raw_severity):
    if hasattr(raw_severity, "value"):
        raw_severity = raw_severity.value
    sev = str(raw_severity).strip().lower()
    if "critical" in sev or "blocker" in sev:
        return "Critical"
    if "high" in sev or "major" in sev:
        return "High"
    if "medium" in sev or "moderate" in sev:
        return "Medium"
    return "Low"


def get_severity_counts(findings):
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for finding in findings:
        raw = get_value(finding, "severity", "risk_level", default="Low")
        counts[normalize_severity(raw)] += 1
    return counts


def analyze_source_code(code):
    if not code or not str(code).strip():
        return {"total_loc": 0, "exec_loc": 0, "comments": 0, "blanks": 0, "functions": 0}
    lines = str(code).splitlines()
    total_loc = len(lines)
    blanks = sum(1 for l in lines if not l.strip())
    comments = sum(1 for l in lines if l.strip().startswith(("#", "//", "/*", "*")))
    functions = sum(
        1 for l in lines if l.strip().startswith(("def ", "async def ", "function ", "public ", "private "))
    )
    exec_loc = max(0, total_loc - blanks - comments)
    return {
        "total_loc": total_loc,
        "exec_loc": exec_loc,
        "comments": comments,
        "blanks": blanks,
        "functions": functions,
    }


def     compute_audit_scores(severity, total_findings, remediation_count, exec_loc):
    penalty = (
        severity["Critical"] * 28
        + severity["High"] * 14
        + severity["Medium"] * 6
        + severity["Low"] * 2
    )
    risk_score = min(100, penalty)
    health_score = max(0, 100 - risk_score)

    if health_score >= 90:
        grade = "A"
    elif health_score >= 75:
        grade = "B"
    elif health_score >= 60:
        grade = "C"
    elif health_score >= 40:
        grade = "D"
    else:
        grade = "F"

    if severity["Critical"] > 0:
        gate_label = "MERGE BLOCKED — Critical Vulnerabilities Detected"
        gate_css = "gate-blocked"
    elif severity["High"] > 0:
        gate_label = "MANUAL REVIEW REQUIRED — High Severity Issues Found"
        gate_css = "gate-warning"
    else:
        gate_label = "APPROVED FOR MERGE — Passed Automated Quality & Security Gates"
        gate_css = "gate-pass"

    fix_rate = min(100, round((remediation_count / total_findings) * 100)) if total_findings else 100
    density = round((total_findings / max(1, exec_loc)) * 100, 1) if exec_loc else 0.0
    est_fix_mins = (
        severity["Critical"] * 45
        + severity["High"] * 25
        + severity["Medium"] * 15
        + severity["Low"] * 5
    )

    return {
        "risk_score": risk_score,
        "health_score": health_score,
        "grade": grade,
        "gate_label": gate_label,
        "gate_css": gate_css,
        "fix_rate": fix_rate,
        "density": density,
        "est_fix_mins": est_fix_mins,
    }


def build_findings_df(code_findings, security_findings, unified_findings):
    rows = []

    def ingest(items, agent_name):
        for idx, raw in enumerate(items, start=1):
            item = to_dict(raw)
            sev = normalize_severity(get_value(item, "severity", "risk_level", default="Low"))
            title = get_value(item, "title", "issue", "vulnerability", "name", default=f"Issue #{idx}")
            cat = get_value(item, "category", "type", "rule_id", default=agent_name)
            loc = str(get_value(item, "line_number", "line", "location", default="N/A"))
            desc = get_value(item, "description", "explanation", "details", default="No description.")
            src = get_value(item, "source", "agent", default=agent_name)

            rows.append(
                {
                    "Severity": sev,
                    "Agent": str(src),
                    "Category": str(cat),
                    "Title": str(title),
                    "Line": loc,
                    "Description": str(desc),
                }
            )

    if code_findings or security_findings:
        ingest(code_findings, "Code Quality Agent")
        ingest(security_findings, "Security Agent")
    else:
        ingest(unified_findings, "Unified Audit")

    return pd.DataFrame(rows)


# =========================================================
# INTERACTIVE PLOTLY CHARTS (DASHBOARD UI)
# =========================================================

def plot_health_gauge(health_score):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=health_score,
            number={"suffix": "/100", "font": {"size": 32, "color": "#F8FAFC"}},
            title={"text": "Code Health Score", "font": {"size": 15, "color": "#CBD5E1"}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#94A3B8"},
                "bar": {"color": "#38BDF8"},
                "bgcolor": "#1E293B",
                "steps": [
                    {"range": [0, 40], "color": "rgba(220, 38, 38, 0.35)"},
                    {"range": [40, 75], "color": "rgba(234, 88, 12, 0.35)"},
                    {"range": [75, 100], "color": "rgba(22, 163, 74, 0.35)"},
                ],
            },
        )
    )
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=45, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#F8FAFC"},
    )
    return fig


def plot_severity_donut(severity):
    labels = ["Critical", "High", "Medium", "Low"]
    values = [severity[k] for k in labels]
    color_map = ["#EF4444", "#F97316", "#EAB308", "#22C55E"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.58,
                marker=dict(colors=color_map, line=dict(color="#0F172A", width=2)),
                textinfo="label+value",
                textfont=dict(size=12, color="#F8FAFC"),
            )
        ]
    )
    fig.update_layout(
        title=dict(text="Severity Breakdown", font=dict(size=15, color="#CBD5E1")),
        height=250,
        margin=dict(l=15, r=15, t=45, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        annotations=[
            dict(
                text=f"<b>{sum(values)}</b><br>Issues",
                x=0.5,
                y=0.5,
                font_size=15,
                font_color="#F8FAFC",
                showarrow=False,
            )
        ],
    )
    return fig


def plot_agent_category_bar(df):
    if df.empty:
        return None
    grouped = df.groupby(["Category", "Severity"]).size().reset_index(name="Count")
    fig = px.bar(
        grouped,
        x="Count",
        y="Category",
        color="Severity",
        orientation="h",
        title="Findings by Category & Severity",
        color_discrete_map={
            "Critical": "#EF4444",
            "High": "#F97316",
            "Medium": "#EAB308",
            "Low": "#22C55E",
        },
    )
    fig.update_layout(
        height=250,
        margin=dict(l=15, r=15, t=45, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1"),
        xaxis=dict(gridcolor="rgba(148,163,184,0.15)"),
        yaxis=dict(title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# =========================================================
# PDF CHARTS & COMPREHENSIVE EXECUTIVE PDF REPORT
# =========================================================

def create_pdf_charts(severity, code_count, security_count):
    """Create a side-by-side figure with Severity Distribution and Agent Split for the PDF."""
    buffer = BytesIO()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.8))

    # Subplot 1: Severity Bar Chart
    sev_labels = ["Critical", "High", "Medium", "Low"]
    sev_values = [severity.get(k, 0) for k in sev_labels]
    bars1 = ax1.bar(sev_labels, sev_values, width=0.5, color=["#DC2626", "#EA580C", "#D97706", "#16A34A"])
    ax1.set_title("Severity Distribution", fontsize=12, fontweight="bold", pad=12)
    ax1.set_ylabel("Findings Count")
    ax1.set_ylim(0, max(sev_values + [1]) + 1)
    ax1.grid(axis="y", linestyle="--", alpha=0.35)
    ax1.set_axisbelow(True)
    for bar, val in zip(bars1, sev_values):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.08, str(val), ha="center", fontweight="bold")

    # Subplot 2: Security Agent vs. Code Quality Agent Split
    agent_labels = ["Security Agent", "Code Quality Agent"]
    agent_values = [security_count, code_count]
    bars2 = ax2.bar(agent_labels, agent_values, width=0.45, color=["#7C3AED", "#0284C7"])
    ax2.set_title("Findings by Audit Agent", fontsize=12, fontweight="bold", pad=12)
    ax2.set_ylabel("Findings Count")
    ax2.set_ylim(0, max(agent_values + [1]) + 1)
    ax2.grid(axis="y", linestyle="--", alpha=0.35)
    ax2.set_axisbelow(True)
    for bar, val in zip(bars2, agent_values):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.08, str(val), ha="center", fontweight="bold")

    fig.tight_layout(pad=2.0)
    fig.savefig(buffer, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return buffer


def generate_dashboard_pdf(data):
    """Generate a comprehensive multi-section Executive PDF Report containing all dashboard details."""
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="DashboardTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=25,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Subtitle",
            parent=styles["BodyText"],
            fontSize=9.5,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"),
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1D4ED8"),
            spaceBefore=12,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubSection",
            parent=styles["Heading3"],
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=8,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyCustom",
            parent=styles["BodyText"],
            fontSize=9,
            leading=13.5,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["BodyText"],
            fontSize=8.2,
            leading=11.5,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=11.5,
            textColor=colors.white,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeCustom",
            parent=styles["Code"],
            fontSize=7.2,
            leading=9.5,
            backColor=colors.HexColor("#F8FAFC"),
            borderColor=colors.HexColor("#CBD5E1"),
            borderWidth=0.5,
            borderPadding=6,
        )
    )

    story = []
    scores = data.get("scores", {})
    code_stats = data.get("code_stats", {})
    severity = data.get("severity", {"Critical": 0, "High": 0, "Medium": 0, "Low": 0})

    # -----------------------------------------------------
    # 1. HEADER & MERGE GATE STATUS BANNER
    # -----------------------------------------------------
    story.append(Paragraph("CodeCheck — Executive PR Audit & Security Report", styles["DashboardTitle"]))
    story.append(
        Paragraph(
            f"Generated on {datetime.now().strftime('%d %B %Y, %I:%M %p')}  |  Language: {pdf_text(data['language']).upper()}",
            styles["Subtitle"],
        )
    )

    gate_label = scores.get("gate_label", "AUDIT COMPLETED")
    if severity["Critical"] > 0:
        gate_bg = colors.HexColor("#FEE2E2")
        gate_fg = colors.HexColor("#991B1B")
    elif severity["High"] > 0:
        gate_bg = colors.HexColor("#FFEDD5")
        gate_fg = colors.HexColor("#9A3412")
    else:
        gate_bg = colors.HexColor("#DCFCE7")
        gate_fg = colors.HexColor("#166534")

    gate_table = Table(
        [[Paragraph(f"<b>MERGE GATE STATUS: {pdf_text(gate_label)}</b>", ParagraphStyle("Gate", parent=styles["BodyCustom"], textColor=gate_fg, alignment=TA_CENTER))]],
        colWidths=[180 * mm],
    )
    gate_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), gate_bg),
            ("BOX", (0, 0), (-1, -1), 1, gate_fg),
            ("PADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(gate_table)
    story.append(Spacer(1, 10))

    # -----------------------------------------------------
    # 2. EXECUTIVE KPI SCORECARD & CODE FOOTPRINT TABLES
    # -----------------------------------------------------
    story.append(Paragraph("1. Executive Audit Scorecard & Codebase Footprint", styles["Section"]))

    kpi_rows = [
        [
            Paragraph("<b>Audit Metric</b>", styles["TableHeader"]),
            Paragraph("<b>Value / Score</b>", styles["TableHeader"]),
            Paragraph("<b>Codebase Metric</b>", styles["TableHeader"]),
            Paragraph("<b>Value</b>", styles["TableHeader"]),
        ],
        [
            Paragraph("<b>Overall Grade & Health</b>", styles["TableCell"]),
            Paragraph(f"Grade {scores.get('grade', 'N/A')} ({scores.get('health_score', 0)}/100)", styles["TableCell"]),
            Paragraph("<b>Total Source Lines</b>", styles["TableCell"]),
            Paragraph(str(code_stats.get("total_loc", 0)), styles["TableCell"]),
        ],
        [
            Paragraph("<b>Risk Index Score</b>", styles["TableCell"]),
            Paragraph(f"{scores.get('risk_score', 0)} / 100", styles["TableCell"]),
            Paragraph("<b>Executable Lines (LOC)</b>", styles["TableCell"]),
            Paragraph(str(code_stats.get("exec_loc", 0)), styles["TableCell"]),
        ],
        [
            Paragraph("<b>Total Findings</b>", styles["TableCell"]),
            Paragraph(f"{data['total_findings']} ({data['security_count']} Security, {data['code_count']} Quality)", styles["TableCell"]),
            Paragraph("<b>Comment Lines</b>", styles["TableCell"]),
            Paragraph(str(code_stats.get("comments", 0)), styles["TableCell"]),
        ],
        [
            Paragraph("<b>Severity Breakdown</b>", styles["TableCell"]),
            Paragraph(
                f"C: {severity['Critical']} | H: {severity['High']} | M: {severity['Medium']} | L: {severity['Low']}",
                styles["TableCell"],
            ),
            Paragraph("<b>Functions / Methods</b>", styles["TableCell"]),
            Paragraph(str(code_stats.get("functions", 0)), styles["TableCell"]),
        ],
        [
            Paragraph("<b>Auto-Remediation Rate</b>", styles["TableCell"]),
            Paragraph(f"{data['remediation_count']} Fixes ({scores.get('fix_rate', 100)}%)", styles["TableCell"]),
            Paragraph("<b>Defect Density</b>", styles["TableCell"]),
            Paragraph(f"{scores.get('density', 0.0)} per 100 LOC", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Est. Remediation Time</b>", styles["TableCell"]),
            Paragraph(f"~{scores.get('est_fix_mins', 0)} minutes", styles["TableCell"]),
            Paragraph("<b>Blank Lines</b>", styles["TableCell"]),
            Paragraph(str(code_stats.get("blanks", 0)), styles["TableCell"]),
        ],
    ]

    kpi_table = Table(kpi_rows, colWidths=[45 * mm, 48 * mm, 47 * mm, 40 * mm])
    kpi_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    # -----------------------------------------------------
    # 3. OVERALL PR SUMMARY
    # -----------------------------------------------------
    story.append(Paragraph("2. Overall PR Summary", styles["Section"]))
    summary_box = Table(
        [[Paragraph(pdf_text(data["pr_summary"]), styles["BodyCustom"])]],
        colWidths=[180 * mm],
    )
    summary_box.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#94A3B8")),
            ("PADDING", (0, 0), (-1, -1), 9),
        ])
    )
    story.append(summary_box)
    story.append(Spacer(1, 8))

    # -----------------------------------------------------
    # 4. VISUAL TELEMETRY CHARTS
    # -----------------------------------------------------
    story.append(Paragraph("3. Risk & Agent Telemetry Charts", styles["Section"]))
    charts_buf = create_pdf_charts(severity, data["code_count"], data["security_count"])
    story.append(PDFImage(charts_buf, width=180 * mm, height=68 * mm))
    story.append(Spacer(1, 8))

    # -----------------------------------------------------
    # 5. ALL DETECTED FINDINGS TABLE
    # -----------------------------------------------------
    story.append(Paragraph(f"4. Complete Detected Findings Log ({data['total_findings']})", styles["Section"]))
    findings_list = data.get("findings", [])

    if not findings_list:
        story.append(Paragraph("No code quality or security findings were reported during this audit.", styles["BodyCustom"]))
    else:
        finding_rows = [
            [
                Paragraph("<b>#</b>", styles["TableHeader"]),
                Paragraph("<b>Severity</b>", styles["TableHeader"]),
                Paragraph("<b>Agent / Category</b>", styles["TableHeader"]),
                Paragraph("<b>Line</b>", styles["TableHeader"]),
                Paragraph("<b>Issue & Description</b>", styles["TableHeader"]),
            ]
        ]
        for idx, f in enumerate(findings_list, start=1):
            f_dict = to_dict(f)
            f_sev = normalize_severity(get_value(f_dict, "severity", "risk_level", default="Low"))
            f_agent = get_value(f_dict, "source", "agent", default="Audit Agent")
            f_cat = get_value(f_dict, "category", "type", "rule_id", default="General")
            f_line = str(get_value(f_dict, "line_number", "line", "location", default="N/A"))
            f_title = get_value(f_dict, "title", "issue", "vulnerability", "name", default=f"Finding #{idx}")
            f_desc = get_value(f_dict, "description", "explanation", "details", default="")

            combined_text = f"<b>{pdf_text(f_title)}</b>"
            if f_desc:
                combined_text += f"<br/>{pdf_text(f_desc)}"

            finding_rows.append(
                [
                    Paragraph(str(idx), styles["TableCell"]),
                    Paragraph(f"<b>{pdf_text(f_sev)}</b>", styles["TableCell"]),
                    Paragraph(f"{pdf_text(f_agent)}<br/><i>({pdf_text(f_cat)})</i>", styles["TableCell"]),
                    Paragraph(pdf_text(f_line), styles["TableCell"]),
                    Paragraph(combined_text, styles["TableCell"]),
                ]
            )

        findings_table = Table(
            finding_rows,
            colWidths=[10 * mm, 20 * mm, 36 * mm, 16 * mm, 98 * mm],
            repeatRows=1,
        )
        findings_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        story.append(findings_table)

    # -----------------------------------------------------
    # 6. DETAILED REMEDIATIONS & CORRECTED CODE (SCHEMA-MATCHED)
    # -----------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph(f"5. Detailed Remediation Guidance & Corrected Code ({data['remediation_count']})", styles["Section"]))

    if not data["remediations"]:
        story.append(Paragraph("No remediation suggestions were returned by the Remediation Agent.", styles["BodyCustom"]))

    for index, item in enumerate(data["remediations"], start=1):
        issue = get_value(item, "issue", default=f"Remediation #{index}")
        sev = normalize_severity(get_value(item, "severity", default="Low"))
        line_num = get_value(item, "line_number", default=None)
        line_display = f"Line {line_num}" if line_num is not None else "Not specified"
        fix_rec = get_value(item, "fix_recommendation", default="No fix recommendation provided.")
        corrected_code = get_value(item, "corrected_code", default="")
        best_practice = get_value(item, "best_practice", default="")

        story.append(Paragraph(f"{index}. [{sev.upper()}] {pdf_text(issue)}", styles["SubSection"]))

        rows = [
            [Paragraph("<b>Severity</b>", styles["TableCell"]), Paragraph(pdf_text(sev), styles["TableCell"])],
            [Paragraph("<b>Affected Location</b>", styles["TableCell"]), Paragraph(pdf_text(line_display), styles["TableCell"])],
            [Paragraph("<b>Fix Recommendation</b>", styles["TableCell"]), Paragraph(pdf_text(fix_rec), styles["TableCell"])],
        ]
        if best_practice:
            rows.append([Paragraph("<b>Best Practice</b>", styles["TableCell"]), Paragraph(pdf_text(best_practice), styles["TableCell"])])

        detail_table = Table(rows, colWidths=[42 * mm, 138 * mm])
        detail_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EFF6FF")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        story.append(detail_table)

        if corrected_code:
            story.append(Spacer(1, 4))
            story.append(Paragraph("<b>Corrected Code:</b>", styles["BodyCustom"]))
            story.append(Preformatted(str(corrected_code), styles["CodeCustom"]))

        story.append(Spacer(1, 10))

    # -----------------------------------------------------
    # 7. APPENDIX: ANALYZED SOURCE CODE
    # -----------------------------------------------------
    raw_code = data.get("source_code", "")
    if raw_code and str(raw_code).strip():
        story.append(PageBreak())
        story.append(Paragraph("6. Appendix: Analyzed Source Code", styles["Section"]))
        numbered_lines = [
            f"{i:03d} | {line}" for i, line in enumerate(str(raw_code).splitlines(), start=1)
        ]
        story.append(Preformatted("\n".join(numbered_lines), styles["CodeCustom"]))

    document.build(story)
    buffer.seek(0)
    return buffer


# =========================================================
# MAIN SINGLE-VIEW DASHBOARD RENDERER
# =========================================================

def render_results_panel(code="", language="python"):
    """Render the complete PR Audit & Security Dashboard directly on one page."""
    inject_dashboard_css()

    analysis = st.session_state.get("analysis_result")
    if not analysis:
        st.warning("No analysis results found. Please run an analysis first.")
        return

    analysis = to_dict(analysis)
    findings = get_findings(analysis)
    remediations = get_remediations(analysis)
    code_findings = get_list(analysis.get("code_findings"))
    security_findings = get_list(analysis.get("security_findings"))
    unified_findings = get_list(analysis.get("unified_findings"))

    severity = get_severity_counts(findings)
    total_findings = len(findings)
    pr_summary = get_pr_summary(analysis)

    code_stats = analyze_source_code(code)
    scores = compute_audit_scores(severity, total_findings, len(remediations), code_stats["exec_loc"])
    findings_df = build_findings_df(code_findings, security_findings, unified_findings)

    # Tag findings with their agent source for complete PDF reporting
    enriched_findings = []
    if code_findings or security_findings:
        for item in code_findings:
            d = to_dict(item)
            d.setdefault("source", "Code Quality Agent")
            enriched_findings.append(d)
        for item in security_findings:
            d = to_dict(item)
            d.setdefault("source", "Security Agent")
            enriched_findings.append(d)
    else:
        enriched_findings = findings

    dashboard_data = {
        "language": str(language).capitalize(),
        "total_findings": total_findings,
        "code_count": len(code_findings),
        "security_count": len(security_findings),
        "remediation_count": len(remediations),
        "severity": severity,
        "pr_summary": pr_summary,
        "findings": enriched_findings,
        "remediations": remediations,
        "scores": scores,
        "code_stats": code_stats,
        "source_code": code,
    }

    # -----------------------------------------------------
    # 1. TOP TITLE BAR + INSTANT PDF EXPORT BUTTON
    # -----------------------------------------------------
    title_col, export_col = st.columns([3.2, 1])
    with title_col:
        st.title("CodeCheck PR Audit & Security Dashboard")
        st.caption(
            f"Multi-Agent Static & Security Analysis Telemetry  •  "
            f"Language: **{str(language).upper()}**  •  "
            f"Audited: **{datetime.now().strftime('%d %b %Y, %I:%M %p')}**"
        )
    with export_col:
        st.write("")
        pdf_bytes = generate_dashboard_pdf(dashboard_data)
        st.download_button(
            label="📥 Download Full PDF Report",
            data=pdf_bytes,
            file_name="CodeCheck_Executive_Audit.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    # -----------------------------------------------------
    # 2. MERGE GATE STATUS BANNER
    # -----------------------------------------------------
    st.markdown(
        f"""
        <div class="gate-banner {scores['gate_css']}">
            <span>🛡️ {scores['gate_label']}</span>
            <span>Overall Grade: {scores['grade']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # 3. 5 KPI SCORECARDS
    # -----------------------------------------------------
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Security & Quality Grade</div>
                <div class="kpi-value" style="color:#38BDF8;">{scores['grade']} ({scores['health_score']}%)</div>
                <div class="kpi-sub">Risk Index: {scores['risk_score']}/100</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Findings</div>
                <div class="kpi-value" style="color:#F87171;">{total_findings}</div>
                <div class="kpi-sub">{severity['Critical']} Critical • {severity['High']} High • {severity['Medium']} Med</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Agent Split</div>
                <div class="kpi-value" style="color:#FBBF24;">{len(security_findings)}S / {len(code_findings)}Q</div>
                <div class="kpi-sub">Security Agent vs. Code Quality</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Auto-Remediation</div>
                <div class="kpi-value" style="color:#4ADE80;">{scores['fix_rate']}%</div>
                <div class="kpi-sub">{len(remediations)} Fixes • ~{scores['est_fix_mins']}m Est. Fix</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c5:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Codebase Footprint</div>
                <div class="kpi-value" style="color:#C084FC;">{code_stats['exec_loc']} LOC</div>
                <div class="kpi-sub">{code_stats['functions']} Functions • {scores['density']} Defects/100L</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------
    # 4. PRIMARY VISUAL TELEMETRY (3 CHARTS SIDE-BY-SIDE)
    # -----------------------------------------------------
    st.subheader("📊 Risk & Vulnerability Telemetry")
    v1, v2, v3 = st.columns([1, 1, 1.4])

    with v1:
        st.plotly_chart(plot_health_gauge(scores["health_score"]), use_container_width=True)

    with v2:
        st.plotly_chart(plot_severity_donut(severity), use_container_width=True)

    with v3:
        cat_fig = plot_agent_category_bar(findings_df)
        if cat_fig:
            st.plotly_chart(cat_fig, use_container_width=True)
        else:
            st.success("Zero category issues detected across agents.")

    # -----------------------------------------------------
    # 5. EXECUTIVE PR SUMMARY & SEVERITY / CODE METRICS
    # -----------------------------------------------------
    s_col, m_col = st.columns([1.4, 1])

    with s_col:
        st.subheader("📝 Executive PR Summary")
        st.markdown(f'<div class="summary-box">{pr_summary}</div>', unsafe_allow_html=True)

    with m_col:
        st.subheader("📐 Codebase & Severity Metrics")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Lines", code_stats["total_loc"])
        m2.metric("Executable", code_stats["exec_loc"])
        m3.metric("Comments", code_stats["comments"])
        m4.metric("Functions", code_stats["functions"])

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("🔴 Critical", severity["Critical"])
        sc2.metric("🟠 High", severity["High"])
        sc3.metric("🟡 Medium", severity["Medium"])
        sc4.metric("🟢 Low", severity["Low"])

    st.divider()

    # -----------------------------------------------------
    # 6. ALL DETECTED FINDINGS TABLE
    # -----------------------------------------------------
    st.subheader(f"🔍 All Detected Findings ({total_findings})")

    if findings_df.empty:
        st.success("Clean audit! No code or security findings were reported.")
    else:
        fc1, fc2, fc3 = st.columns([1.2, 1.2, 2])
        with fc1:
            sev_sel = st.multiselect(
                "Filter Severity",
                ["Critical", "High", "Medium", "Low"],
                default=["Critical", "High", "Medium", "Low"],
            )
        with fc2:
            agent_sel = st.multiselect(
                "Filter Agent",
                sorted(findings_df["Agent"].unique().tolist()),
                default=sorted(findings_df["Agent"].unique().tolist()),
            )
        with fc3:
            kw = st.text_input("Search Issues", placeholder="Filter by title, rule, or line number...")

        view_df = findings_df[
            findings_df["Severity"].isin(sev_sel) & findings_df["Agent"].isin(agent_sel)
        ]
        if kw.strip():
            q = kw.strip().lower()
            view_df = view_df[
                view_df["Title"].str.lower().str.contains(q)
                | view_df["Description"].str.lower().str.contains(q)
                | view_df["Category"].str.lower().str.contains(q)
            ]

        st.dataframe(
            view_df[["Severity", "Agent", "Category", "Title", "Line", "Description"]],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # -----------------------------------------------------
    # 7. REMEDIATION GUIDANCE & CORRECTED CODE (SCHEMA-MATCHED)
    # -----------------------------------------------------
    st.subheader(f"🛠️ Suggested Remediations & Corrected Code ({len(remediations)})")

    if not remediations:
        st.info("No remediation suggestions were returned.")
    else:
        for idx, item in enumerate(remediations, start=1):
            issue = get_value(item, "issue", default=f"Issue #{idx}")
            sev = normalize_severity(get_value(item, "severity", default="Low"))
            line_num = get_value(item, "line_number", default=None)
            line_label = f"Line {line_num}" if line_num is not None else "Line N/A"
            fix_rec = get_value(item, "fix_recommendation", default="No fix recommendation provided.")
            corrected_code = get_value(item, "corrected_code", default="")
            best_practice = get_value(item, "best_practice", default="")

            with st.expander(f"[{sev.upper()}] {idx}. {issue} — {line_label}", expanded=True):
                left, right = st.columns([1, 1.2])
                with left:
                    st.markdown(f"**Severity:** `{sev}`  |  **Affected Location:** `{line_label}`")
                    st.markdown("**Fix Recommendation**")
                    st.info(fix_rec)
                    if best_practice:
                        st.markdown("**Best Practice**")
                        st.success(best_practice)
                with right:
                    st.markdown("**Corrected Code**")
                    if corrected_code:
                        st.code(str(corrected_code), language=language.lower())
                    else:
                        st.caption("No corrected code provided for this item.")

    st.divider()

    # -----------------------------------------------------
    # 8. SUBMITTED SOURCE CODE & CONVERSATIONAL CODE ASSISTANT
    # -----------------------------------------------------
    if code:
        st.subheader("💻 Analyzed Source Code")
        st.code(code, language=language.lower(), line_numbers=True)
        st.divider()

    render_code_assistant(
        language=language,
        code=code,
        analysis=analysis,
    )