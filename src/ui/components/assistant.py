import json
import streamlit as st

from crsa_agent.agent.cca import ask_cca


def _to_dict(item):
    """Convert Pydantic models or objects into plain dictionaries."""
    if item is None:
        return {}
    if isinstance(item, dict):
        return item
    if hasattr(item, "model_dump"):
        return item.model_dump()
    if hasattr(item, "dict"):
        return item.dict()
    return {}


def collect_findings(data):
    """Extract unique findings from canonical analysis keys (excluding duplicate remediation copies)."""
    data = _to_dict(data)
    if not data:
        return []

    # 1. Prefer unified_findings; otherwise combine code_findings + security_findings
    raw_items = data.get("unified_findings")
    if not raw_items:
        code_items = data.get("code_findings") or []
        sec_items = data.get("security_findings") or []
        raw_items = list(code_items) + list(sec_items)

    # Fallback only if none of the standard keys exist
    if not raw_items:
        raw_items = []
        finding_fields = {"title", "issue", "vulnerability", "finding", "rule_id"}

        def _walk(node):
            node = _to_dict(node) if not isinstance(node, (dict, list)) else node
            if isinstance(node, dict):
                # Skip remediation blocks so they don't duplicate findings
                if "fix_recommendation" in node or "corrected_code" in node:
                    return
                if finding_fields.intersection(node.keys()):
                    raw_items.append(node)
                    return
                for k, v in node.items():
                    if k not in ("remediation", "remediation_findings", "remediations", "pr_summary"):
                        _walk(v)
            elif isinstance(node, list):
                for elem in node:
                    _walk(elem)

        _walk(data)

    # 2. Deduplicate findings by normalized title + line + severity
    unique_findings = []
    seen = set()

    for raw in raw_items:
        finding = _to_dict(raw)
        if not finding:
            continue

        title = (
            finding.get("title")
            or finding.get("issue")
            or finding.get("vulnerability")
            or finding.get("finding")
            or finding.get("description")
            or finding.get("rule_id")
            or ""
        )
        line = finding.get("line_number") or finding.get("line") or finding.get("location") or ""
        severity = finding.get("severity") or finding.get("risk_level") or ""
        if hasattr(severity, "value"):
            severity = severity.value

        dedup_key = (
            str(title).strip().lower(),
            str(line).strip().lower(),
            str(severity).strip().lower(),
        )

        if dedup_key not in seen:
            seen.add(dedup_key)
            unique_findings.append(finding)

    return unique_findings


def get_finding_label(finding, index):
    title = (
        finding.get("title")
        or finding.get("issue")
        or finding.get("vulnerability")
        or finding.get("finding")
        or finding.get("description")
        or finding.get("rule_id")
        or f"Finding {index + 1}"
    )

    severity = finding.get("severity", "")
    if hasattr(severity, "value"):
        severity = severity.value

    if isinstance(title, (dict, list)):
        title = str(title)

    return (
        f"{index + 1}. {title} ({severity})"
        if severity
        else f"{index + 1}. {title}"
    )


def render_code_assistant(language, code, analysis):

    st.divider()

    st.markdown("### 💬 Conversational Code Assistant")

    st.caption(
        "Ask questions about your code review, security "
        "vulnerabilities, remediation, or secure coding practices."
    )

    if "cca_messages" not in st.session_state:
        st.session_state.cca_messages = []

    # Extract deduplicated findings
    findings = collect_findings(analysis)

    finding_labels = [
        get_finding_label(finding, index)
        for index, finding in enumerate(findings)
    ]

    options = ["All Results"] + finding_labels

    # Display conversation
    for message in st.session_state.cca_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --------------------------------------------------
    # Chat input + context selector + send button
    # --------------------------------------------------

    with st.form("cca_chat_form", clear_on_submit=True):

        col1, col2, col3 = st.columns([6, 2, 0.7])

        with col1:
            question = st.text_input(
                "Question",
                placeholder="Ask something about your code analysis...",
                label_visibility="collapsed",
            )

        with col2:
            selected_context = st.multiselect(
                "Context",
                options=options,
                default=["All Results"],
                label_visibility="collapsed",
                placeholder="Select results",
            )

        with col3:
            submitted = st.form_submit_button(
                "↑",
                use_container_width=True,
                type="primary",
            )

    # --------------------------------------------------
    # Process question
    # --------------------------------------------------

    if submitted:

        if not question.strip():
            st.warning("Please enter a question.")
            return

        if not selected_context:
            st.warning("Please select at least one analysis result.")
            return

        # Select all results or specific findings
        if "All Results" in selected_context:
            selected_analysis = analysis
        else:
            selected_analysis = [
                finding
                for label, finding in zip(finding_labels, findings)
                if label in selected_context
            ]

        review_context = json.dumps(
            {
                "language": language,
                "submitted_code": code,
                "selected_analysis": selected_analysis,
            },
            indent=2,
            default=str,
        )

        # Save user message
        st.session_state.cca_messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        # Build conversation history
        previous_messages = st.session_state.cca_messages[:-1]

        conversation_history = "\n".join(
            f'{msg["role"].upper()}: {msg["content"]}'
            for msg in previous_messages
        )

        contextual_question = (
            f"Previous conversation:\n{conversation_history}\n\n"
            f"Current question:\n{question}"
            if conversation_history
            else question
        )

        # Generate response
        try:
            with st.spinner(
                "CCA is retrieving knowledge and preparing an answer..."
            ):
                response = str(
                    ask_cca(
                        question=contextual_question,
                        review_context=review_context,
                    )
                )

            st.session_state.cca_messages.append(
                {
                    "role": "assistant",
                    "content": response,
                }
            )

        except Exception as exc:
            st.session_state.cca_messages.append(
                {
                    "role": "assistant",
                    "content": f"CCA could not generate a response: {exc}",
                }
            )

        st.rerun()