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
    """Extract unique findings from canonical analysis keys."""
    data = _to_dict(data)
    if not data:
        return []

    raw_items = data.get("unified_findings")
    if not raw_items:
        code_items = data.get("code_findings") or []
        sec_items = data.get("security_findings") or []
        raw_items = list(code_items) + list(sec_items)

    if not raw_items:
        raw_items = []
        finding_fields = {"title", "issue", "vulnerability", "finding", "rule_id"}

        def _walk(node):
            node = _to_dict(node) if not isinstance(node, (dict, list)) else node
            if isinstance(node, dict):
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
        f"{index + 1}. [{severity}] {title}"
        if severity
        else f"{index + 1}. {title}"
    )


def render_code_assistant(language, code, analysis):
    st.markdown(
        """
        <div style="background: #ffffff; border: 1.5px solid #e9d5ff; border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(124, 58, 237, 0.05);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 1.6rem;">🤖</span>
                    <div>
                        <div style="font-weight: 700; font-size: 1.05rem; color: #1e1b4b;">
                            RAG-Powered Conversational Code Assistant
                        </div>
                        <div style="font-size: 0.84rem; color: #6b7280;">
                            Grounded in OWASP Top 10, CWE security standards, and your active scan findings.
                        </div>
                    </div>
                </div>
                <span class="badge-pill-light badge-purple">
                    <span class="pulse-dot-green"></span> Knowledge Base Indexed
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "cca_messages" not in st.session_state:
        st.session_state.cca_messages = []

    findings = collect_findings(analysis)
    finding_labels = [
        get_finding_label(finding, index)
        for index, finding in enumerate(findings)
    ]
    options = ["All Audit Findings"] + finding_labels

    # --------------------------------------------------
    # Quick Prompt Suggestions Bar (Purple Theme)
    # --------------------------------------------------
    st.markdown("<span style='font-size: 0.80rem; font-weight: 700; text-transform: uppercase; color: #6b7280;'>Suggested Prompt Starters:</span>", unsafe_allow_html=True)
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)

    prompt_to_send = None
    with q_col1:
        if st.button("💡 Explain Critical Findings", use_container_width=True):
            prompt_to_send = "Can you explain the most critical findings in my code and why they represent a high risk?"
    with q_col2:
        if st.button("🔒 How to Store Secrets", use_container_width=True):
            prompt_to_send = "What is the industry best practice to store and inject API credentials safely without hardcoding?"
    with q_col3:
        if st.button("🛡️ Prevent SQL Injection", use_container_width=True):
            prompt_to_send = "How do parameterized queries or prepared statements eliminate SQL injection vulnerabilities?"
    with q_col4:
        if st.button("🧪 Generate Unit Tests", use_container_width=True):
            prompt_to_send = "Can you write a unit test demonstrating that the proposed remediation works correctly?"

    # --------------------------------------------------
    # Display Chat Messages
    # --------------------------------------------------
    chat_container = st.container()
    with chat_container:
        if not st.session_state.cca_messages:
            st.markdown(
                """
                <div style="text-align: center; padding: 32px 20px; color: #6b7280; background: #ffffff; border-radius: 12px; border: 1.5px dashed #d8b4fe; margin: 16px 0; box-shadow: 0 1px 2px rgba(124, 58, 237, 0.04);">
                    <div style="font-size: 2rem; margin-bottom: 8px;">💬</div>
                    <div style="font-weight: 700; color: #1e1b4b; font-size: 1rem;">No conversation yet</div>
                    <div style="font-size: 0.86rem; color: #6b7280; margin-top: 4px;">Choose a starter prompt above or type your question below to consult the AI Security Specialist.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for message in st.session_state.cca_messages:
                role = message["role"]
                avatar = "🧑‍💻" if role == "user" else "🛡️"
                with st.chat_message(role, avatar=avatar):
                    st.markdown(message["content"])

    # --------------------------------------------------
    # Chat Input Form
    # --------------------------------------------------
    st.write("")
    with st.form("cca_chat_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([5.5, 2.5, 1])

        with col1:
            question = st.text_input(
                "Question",
                placeholder="Ask about vulnerabilities, remediation, design patterns, or secure coding...",
                label_visibility="collapsed",
            )

        with col2:
            selected_context = st.multiselect(
                "Context",
                options=options,
                default=["All Audit Findings"],
                label_visibility="collapsed",
                placeholder="Select focus findings",
            )

        with col3:
            submitted = st.form_submit_button(
                "Send ➔",
                use_container_width=True,
                type="primary",
            )

    # Allow clearing chat history
    if st.session_state.cca_messages:
        if st.button("🗑️ Clear Chat History", help="Reset this conversation"):
            st.session_state.cca_messages = []
            st.rerun()

    active_question = prompt_to_send if prompt_to_send else (question if submitted else None)

    # --------------------------------------------------
    # Process Question
    # --------------------------------------------------
    if active_question:
        if not active_question.strip():
            st.warning("Please enter a question.")
            return

        if not selected_context:
            selected_context = ["All Audit Findings"]

        if "All Audit Findings" in selected_context:
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

        st.session_state.cca_messages.append(
            {
                "role": "user",
                "content": active_question,
            }
        )

        previous_messages = st.session_state.cca_messages[:-1]
        conversation_history = "\n".join(
            f'{msg["role"].upper()}: {msg["content"]}'
            for msg in previous_messages
        )

        contextual_question = (
            f"Previous conversation:\n{conversation_history}\n\n"
            f"Current question:\n{active_question}"
            if conversation_history
            else active_question
        )

        try:
            with st.spinner("🤖 Consulting RAG Knowledge Base and preparing answer..."):
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
                    "content": f"⚠️ The assistant encountered an error retrieving knowledge: {exc}",
                }
            )

        st.rerun()
