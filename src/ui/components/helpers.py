import json
from collections.abc import Mapping
from xml.sax.saxutils import escape

import streamlit as st


def to_dict(item):
    """Convert a finding or Pydantic model to a dictionary."""

    if isinstance(item, Mapping):
        return dict(item)

    if hasattr(item, "model_dump"):
        return item.model_dump()

    if hasattr(item, "dict"):
        return item.dict()

    if hasattr(item, "__dict__"):
        return vars(item)

    return {"details": str(item)}


def format_value(value):
    """Format nested data for readable display."""

    if value is None:
        return "Not provided"

    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, indent=2, default=str)

    return str(value)


def get_list(state, key):
    """Safely retrieve a list of findings from graph output."""

    value = state.get(key, [])

    if value is None:
        return []

    if isinstance(value, list):
        return [to_dict(item) for item in value]

    return [to_dict(value)]


def render_finding(finding, index, language):
    """Render one finding with clean purple theme styling."""

    issue = finding.get(
        "issue",
        finding.get("title", f"Finding {index}"),
    )

    severity = str(finding.get("severity", "Unknown")).upper()
    category = finding.get("category", "General")
    line_number = finding.get("line_number", "N/A")

    pill_class = {
        "CRITICAL": "sev-critical-light",
        "HIGH": "sev-high-light",
        "MEDIUM": "sev-medium-light",
        "LOW": "sev-low-light",
        "INFORMATIONAL": "sev-info-light",
    }.get(severity, "sev-info-light")

    header_label = f"{index}. [{severity}] {issue}"

    with st.expander(header_label, expanded=(index == 1)):
        st.markdown(
            f"""
            <div style="display: flex; gap: 8px; margin-bottom: 12px; align-items: center; flex-wrap: wrap;">
                <span class="sev-pill-light {pill_class}">● {escape(severity)}</span>
                <span style="background: #f5f3ff; color: #7c3aed; border: 1px solid #d8b4fe; padding: 2px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 600;">
                    🏷️ {escape(category)}
                </span>
                <span style="background: #f8fafc; color: #4b5563; border: 1px solid #e2e8f0; padding: 2px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; font-family: var(--font-mono);">
                    📍 Line: {escape(str(line_number))}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if finding.get("description"):
            st.markdown("**Diagnostic Description**")
            st.markdown(
                f"<div style='color: #312e81; font-size: 0.90rem; line-height: 1.5; margin-bottom: 10px;'>{escape(str(finding['description']))}</div>",
                unsafe_allow_html=True,
            )

        if finding.get("recommendation"):
            st.markdown("**Remediation Guidance**")
            st.info(finding["recommendation"])

        if finding.get("code_snippet"):
            st.markdown("**Affected Code Snippet**")
            st.code(
                str(finding["code_snippet"]),
                language=language.lower(),
            )

        known_fields = {
            "issue",
            "title",
            "severity",
            "category",
            "line_number",
            "description",
            "recommendation",
            "code_snippet",
        }

        extra_fields = {
            key: value
            for key, value in finding.items()
            if key not in known_fields
        }

        if extra_fields:
            st.markdown("**Telemetry & Extended Metadata**")
            st.json(extra_fields)
