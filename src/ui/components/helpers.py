import json
from collections.abc import Mapping

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
    """Render one finding with available details."""

    issue = finding.get(
        "issue",
        finding.get("title", f"Finding {index}"),
    )

    severity = str(finding.get("severity", "Unknown")).upper()
    category = finding.get("category", "General")
    line_number = finding.get("line_number", "N/A")

    with st.expander(
        f"{index}. [{severity}] {issue}",
        expanded=(index == 1),
    ):
        st.write(f"**Category:** {category}")
        st.write(f"**Severity:** {severity}")
        st.write(f"**Line number:** {line_number}")

        if finding.get("description"):
            st.markdown("**Description**")
            st.write(finding["description"])

        if finding.get("recommendation"):
            st.markdown("**Recommendation**")
            st.write(finding["recommendation"])

        if finding.get("code_snippet"):
            st.markdown("**Affected code**")
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
            st.markdown("**Additional details**")
            st.json(extra_fields)
