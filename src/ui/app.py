import html
import json
from collections.abc import Mapping

import streamlit as st

from crsa_agent.initial_code_check_utils import (
    detect_language,
    check_java,
    check_python,
)
from crsa_agent.graph import graph


# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="CodeCheck",
    page_icon="⌘",
    layout="wide",
)


# --------------------------------------------------
# Custom CSS - Existing UI Theme
# --------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Patrick+Hand&family=Fira+Code:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Patrick Hand', cursive;
    }

    .stApp {
        background: #f7f9fc;
        color: #17233f;
    }

    .block-container {
        padding-top: 1.6rem;
        max-width: 1450px;
    }

    h1, h2, h3 {
        font-family: 'Patrick Hand', cursive !important;
        color: #14213d;
    }

    h1 {
        font-size: 2.7rem !important;
    }

    .eyebrow {
        color: #5d7194;
        font-size: 1.05rem;
    }

    div.stButton > button {
        border-radius: 10px;
        border: 1.5px solid #6da0f5;
        font-family: 'Patrick Hand', cursive;
        font-size: 1.15rem;
        min-height: 2.8rem;
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4388f4 0%, #2b6cb0 100%);
        color: white;
        border: none;
    }

    div[data-testid="stFileUploader"] {
        background: #ffffff;
        border: 1.5px dashed #a5c2eb;
        border-radius: 12px;
        padding: 12px;
    }

    div[data-testid="stFileUploader"] button {
        background: #ffffff !important;
        color: #2b6cb0 !important;
        border: 1.5px solid #2b6cb0 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: all 0.25s ease-in-out !important;
    }

    div[data-testid="stFileUploader"] button:hover,
    div[data-testid="stFileUploader"] button:focus,
    div[data-testid="stFileUploader"] button:active {
        background: linear-gradient(135deg, #4388f4 0%, #1a56db 100%) !important;
        color: #ffffff !important;
        border: 1.5px solid transparent !important;
        box-shadow: 0 4px 12px rgba(67, 136, 244, 0.3) !important;
    }

    div[data-testid="stFileUploader"] label,
    div[data-testid="stFileUploader"] span,
    div[data-testid="stFileUploader"] small {
        color: #17233f !important;
    }

    textarea {
        font-family: 'Fira Code', monospace !important;
        background-color: #ffffff !important;
        color: #17233f !important;
        border: 1.5px solid #c5d5eb !important;
        border-radius: 10px !important;
    }

    .status-ok {
        background: #eafaf1;
        border: 1.5px solid #65d69a;
        color: #086b40;
        padding: 1rem;
        border-radius: 12px;
    }

    .status-bad {
        background: #fff0ef;
        border: 1.5px solid #ffaaa3;
        color: #a32620;
        padding: 1rem;
        border-radius: 12px;
    }

    .small {
        color: #637797;
        font-size: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Session State
# --------------------------------------------------

if "code_text" not in st.session_state:
    st.session_state.code_text = (
        "def add(a, b):\n"
        "    return a + b\n\n"
        "print(add(5, 3))"
    )

if "result" not in st.session_state:
    st.session_state.result = None


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------

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


def invoke_analysis_graph(code, language):
    """
    Invoke the complete LangGraph workflow.

    Expected workflow:
    Code Analysis Agent + Security Agent (parallel)
        -> Merge Findings
        -> Remediation Agent
        -> END
    """

    initial_state = {
        "messages": [],
        "code": code,
        "language": language,
        "code_findings": [],
        "security_findings": [],
        "unified_findings": [],
        "remediation_findings": [],
    }

    return graph.invoke(initial_state)


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


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("⌘  CodeCheck")

st.markdown(
    '<p class="eyebrow">'
    'Paste your code or upload a file to check for errors '
    '· Python / Java'
    '</p>',
    unsafe_allow_html=True,
)

st.divider()


# --------------------------------------------------
# Main App Layout
# --------------------------------------------------

left, right = st.columns([1.05, 1], gap="large")


# --------------------------------------------------
# Left Panel: Input
# --------------------------------------------------

with left:
    st.subheader("1. Choose input")

    uploaded = st.file_uploader(
        "Upload a source file",
        type=["py", "java"],
        help="Supported extensions: .py and .java",
    )

    upload_name = ""

    if uploaded is not None:
        upload_name = uploaded.name

        try:
            uploaded_code = uploaded.getvalue().decode("utf-8")

            # Update editor content only when a new file is selected.
            if (
                st.session_state.get("uploaded_name") != uploaded.name
                or st.session_state.get("uploaded_bytes") != uploaded.getvalue()
            ):
                st.session_state.code_text = uploaded_code
                st.session_state.uploaded_name = uploaded.name
                st.session_state.uploaded_bytes = uploaded.getvalue()

        except UnicodeDecodeError:
            st.error("This file could not be read as UTF-8 text.")

    else:
        st.caption("Or paste code in the editor below.")

        # Clear upload tracking when the uploaded file is removed.
        st.session_state.pop("uploaded_name", None)
        st.session_state.pop("uploaded_bytes", None)

    st.write("")
    st.subheader("2. Code editor")

    code = st.text_area(
        "Paste or edit code",
        key="code_text",
        height=380,
        label_visibility="collapsed",
        placeholder="Paste your Python or Java code here...",
    )

    language = detect_language(code, upload_name)

    st.caption(f"Detected language: {language}")

    check = st.button(
        "⌕  Check code",
        type="primary",
        use_container_width=True,
    )

    st.markdown(
        '<p class="small">'
        'Validates syntax or compilation before running the AI analysis graph. '
        'Your code is not executed.'
        '</p>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# Validation + Graph Execution
# --------------------------------------------------

if check:
    if not code.strip():
        st.session_state.result = {
            "stage": "validation",
            "validation": {
                "ok": False,
                "title": "No code provided",
                "details": "Paste code or upload a source file first.",
                "items": [],
            },
            "analysis": None,
        }

    elif language not in ("Python", "Java"):
        st.session_state.result = {
            "stage": "validation",
            "validation": {
                "ok": False,
                "title": "Unsupported language",
                "details": (
                    f"Detected language: {language}. "
                    "Please provide Python or Java code."
                ),
                "items": [],
            },
            "analysis": None,
        }

    else:
        try:
            # Step 1: Syntax / compilation validation.
            with st.spinner("Checking syntax and compilation..."):
                if language == "Python":
                    validation = check_python(code)
                else:
                    validation = check_java(code)

            # Step 2: Do not invoke the graph for invalid code.
            if not validation.get("ok", False):
                st.session_state.result = {
                    "stage": "validation",
                    "validation": validation,
                    "analysis": None,
                }

            else:
                # Step 3: Valid code -> run the entire LangGraph.
                with st.spinner(
                    "Running code quality, security, and remediation agents..."
                ):
                    analysis = invoke_analysis_graph(code, language)

                st.session_state.result = {
                    "stage": "analysis",
                    "validation": validation,
                    "analysis": analysis,
                }

        except Exception as exc:
            st.session_state.result = {
                "stage": "execution_error",
                "validation": {
                    "ok": False,
                    "title": "Analysis failed",
                    "details": (
                        "An error occurred while validating the code "
                        "or running the analysis workflow."
                    ),
                    "items": [],
                },
                "analysis": None,
                "error": str(exc),
            }


# --------------------------------------------------
# Right Panel: Results
# --------------------------------------------------

with right:
    st.subheader("3. Analysis result")

    result = st.session_state.result

    if result is None:
        st.info(
            "Your result will appear here after you click **Check code**."
        )

        st.markdown("**Analysis workflow**")

        st.markdown(
            """
            - **Syntax validation:** Detect Python syntax errors or Java compilation errors.
            - **Code quality:** Identify code smells and design issues.
            - **Security analysis:** Detect potential vulnerabilities.
            - **Unified findings:** Combine findings from both agents.
            - **Remediation:** Provide suggested fixes and best practices.
            - **PR summary:** Display the summary if returned by the graph.
            """
        )

    else:
        validation = result["validation"]

        # ------------------------------------------
        # Syntax / compilation status
        # ------------------------------------------

        st.markdown("#### Syntax and compilation")

        if validation.get("ok", False):
            st.markdown(
                f"""
                <div class="status-ok">
                    <b>✓ {html.escape(str(validation.get("title", "Validation passed")))}</b><br>
                    {html.escape(str(validation.get("details", "Code is valid.")))}
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            st.markdown(
                f"""
                <div class="status-bad">
                    <b>✕ {html.escape(str(validation.get("title", "Validation failed")))}</b><br>
                    {html.escape(str(validation.get("details", "Validation failed.")))}
                </div>
                """,
                unsafe_allow_html=True,
            )

            for item in validation.get("items", []):
                st.code(str(item), language="text")

        # ------------------------------------------
        # Validation failure
        # ------------------------------------------

        if result["stage"] == "validation":
            st.warning(
                "Fix the syntax or compilation errors before running "
                "the AI analysis agents."
            )

        # ------------------------------------------
        # Graph / execution failure
        # ------------------------------------------

        elif result["stage"] == "execution_error":
            st.error("The validation or analysis workflow failed.")

            if result.get("error"):
                st.code(result["error"], language="text")

        # ------------------------------------------
        # Successful graph execution
        # ------------------------------------------

        elif result["stage"] == "analysis":
            analysis = result["analysis"]

            st.divider()
            st.markdown("### AI Code Analysis Report")

            code_findings = get_list(analysis, "code_findings")
            security_findings = get_list(analysis, "security_findings")
            unified_findings = get_list(analysis, "unified_findings")
            remediation_findings = get_list(
                analysis,
                "remediation_findings",
            )

            # --------------------------------------
            # Summary metrics
            # --------------------------------------

            col1, col2, col3 = st.columns(3)

            col1.metric("Code Quality", len(code_findings))
            col2.metric("Security Issues", len(security_findings))
            col3.metric("Total Findings", len(unified_findings))

            # --------------------------------------
            # Unified findings
            # --------------------------------------

            st.markdown("#### Unified Findings")

            if unified_findings:
                for index, finding in enumerate(
                    unified_findings,
                    start=1,
                ):
                    render_finding(finding, index, language)

            elif code_findings or security_findings:
                st.warning(
                    "The graph returned agent findings, but the unified "
                    "findings list is empty. Check the merge node."
                )

            else:
                st.success(
                    "No findings were returned by the analysis graph."
                )

            # --------------------------------------
            # Remediation
            # --------------------------------------

            st.divider()
            st.markdown("#### Remediation and Suggested Fixes")

            if remediation_findings:
                for index, fix in enumerate(
                    remediation_findings,
                    start=1,
                ):
                    issue = fix.get(
                        "issue",
                        fix.get("title", f"Remediation {index}"),
                    )

                    with st.expander(
                        f"{index}. {issue}",
                        expanded=(index == 1),
                    ):
                        st.write(
                            f"**Severity:** "
                            f"{fix.get('severity', 'Unknown')}"
                        )

                        st.write(
                            f"**Line number:** "
                            f"{fix.get('line_number', 'N/A')}"
                        )

                        if fix.get("description"):
                            st.markdown("**Description**")
                            st.write(fix["description"])

                        if fix.get("fix_recommendation"):
                            st.markdown("**Recommended fix**")
                            st.write(fix["fix_recommendation"])

                        if fix.get("corrected_code"):
                            st.markdown("**Corrected code**")
                            st.code(
                                str(fix["corrected_code"]),
                                language=language.lower(),
                            )

                        if fix.get("best_practice"):
                            st.markdown("**Best practice**")
                            st.write(fix["best_practice"])

                        # Preserve any additional model fields.
                        st.json(fix)

            else:
                st.info(
                    "No remediation findings were returned by the graph."
                )

            # --------------------------------------
            # Code Quality Agent output
            # --------------------------------------

            with st.expander("View Code Quality Agent Findings"):
                if code_findings:
                    for index, finding in enumerate(
                        code_findings,
                        start=1,
                    ):
                        render_finding(finding, index, language)
                else:
                    st.info(
                        "No separate code quality findings were returned."
                    )

            # --------------------------------------
            # Security Agent output
            # --------------------------------------

            with st.expander("View Security Agent Findings"):
                if security_findings:
                    for index, finding in enumerate(
                        security_findings,
                        start=1,
                    ):
                        render_finding(finding, index, language)
                else:
                    st.info(
                        "No separate security findings were returned."
                    )

            # --------------------------------------
            # Final PR Summary
            # --------------------------------------

            st.divider()
            st.markdown("#### Final PR Summary")

            pr_summary = analysis.get("pr_summary")

            if pr_summary:
                if isinstance(pr_summary, str):
                    st.markdown(pr_summary)
                else:
                    st.json(to_dict(pr_summary))

            else:
                # Check messages for a summary if the graph stores
                # its final output as a message instead of a state key.
                messages = analysis.get("messages", [])
                summary_found = False

                for message in messages:
                    if isinstance(message, Mapping):
                        content = message.get("content", "")
                        role = message.get(
                            "role",
                            message.get("type", "Agent"),
                        )
                    else:
                        content = getattr(message, "content", "")
                        role = getattr(
                            message,
                            "type",
                            message.__class__.__name__,
                        )

                    if not content:
                        continue

                    role_text = str(role).lower()

                    if "summary" in role_text or "pr" in role_text:
                        st.markdown(f"**{role}**")
                        st.markdown(format_value(content))
                        summary_found = True

                if not summary_found:
                    st.info(
                        "No explicit PR summary was found in the graph output. "
                        "The current workflow must return a summary field or "
                        "a summary message for this section to display one."
                    )

            # --------------------------------------
            # Complete graph output
            # --------------------------------------

            with st.expander("Inspect Complete Graph Output"):
                st.json(analysis)

            # --------------------------------------
            # Download report
            # --------------------------------------

            st.divider()

            st.download_button(
                label="Download Full Analysis (JSON)",
                data=json.dumps(
                    analysis,
                    indent=2,
                    default=str,
                ),
                file_name="codecheck_analysis.json",
                mime="application/json",
                use_container_width=True,
            )


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.divider()

st.caption(
    "CodeCheck · AI-powered code quality analysis, "
    "security vulnerability detection, and remediation for Python and Java"
)
