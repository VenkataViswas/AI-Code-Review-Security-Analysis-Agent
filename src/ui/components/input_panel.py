from xml.sax.saxutils import escape

import streamlit as st

from crsa_agent.initial_code_check_utils import detect_language


# Curated benchmark presets for 1-click evaluation
PRESET_SAMPLES = {
    "secret_python": {
        "title": "🔴 Hardcoded Secret (Python)",
        "language": "Python",
        "filename": "auth_service.py",
        "code": (
            '"""Security issue: hardcoded credential."""\n\n'
            'API_TOKEN = "sk_test_EXAMPLE_DO_NOT_USE_123456"\n\n\n'
            'def call_service(client):\n'
            '    return client.get("/profile", headers={"Authorization": f"Bearer {API_TOKEN}"})\n'
        ),
    },
    "sqli_java": {
        "title": "🟠 SQL Injection (Java)",
        "language": "Java",
        "filename": "AccountLookup.java",
        "code": (
            '// Security issue: SQL injection via concatenated user input.\n'
            'import java.sql.Connection;\n'
            'import java.sql.ResultSet;\n'
            'import java.sql.SQLException;\n'
            'import java.sql.Statement;\n\n'
            'class AccountLookup {\n'
            '    public ResultSet findAccount(Connection connection, String name) throws SQLException {\n'
            '        Statement statement = connection.createStatement();\n'
            '        String sql = "SELECT * FROM accounts WHERE name = \'" + name + "\'";\n'
            '        return statement.executeQuery(sql);\n'
            '    }\n'
            '}\n'
        ),
    },
    "sqli_python": {
        "title": "🟠 SQL Injection (Python)",
        "language": "Python",
        "filename": "db_query.py",
        "code": (
            '"""Security issue: SQL injection via string concatenation."""\n\n'
            'def find_account(cursor, account_name):\n'
            '    query = "SELECT * FROM accounts WHERE name = \'" + account_name + "\'"\n'
            '    cursor.execute(query)\n'
            '    return cursor.fetchall()\n'
        ),
    },
    "syntax_error_py": {
        "title": "⚠️ Syntax Error Demo (Py)",
        "language": "Python",
        "filename": "broken_syntax.py",
        "code": (
            '# Intentional syntax error: missing colon and unclosed parenthesis\n'
            'def calculate_total(items)\n'
            '    total = sum(items\n'
            '    return total\n'
        ),
    },
    "clean_python": {
        "title": "🟢 Clean & Secure Code (Python)",
        "language": "Python",
        "filename": "math_utils.py",
        "code": (
            '"""Mathematical utility functions with secure input validation."""\n\n'
            'def calculate_factorial(n: int) -> int:\n'
            '    """Calculate factorial of a non-negative integer.\n\n'
            '    Args:\n'
            '        n: Non-negative integer value.\n\n'
            '    Returns:\n'
            '        Factorial of the given number.\n\n'
            '    Raises:\n'
            '        ValueError: If n is negative.\n'
            '    """\n'
            '    if not isinstance(n, int) or n < 0:\n'
            '        raise ValueError("Factorial is only defined for non-negative integers.")\n'
            '    result = 1\n'
            '    for i in range(2, n + 1):\n'
            '        result *= i\n'
            '    return result\n'
        ),
    },
}


def render_input_panel():
    st.markdown("### 1. Ingestion & Benchmark Presets")
    st.caption("Select a benchmark sample to test vulnerabilities, or upload your own source file (.py, .java).")

    # ---------------------------------------------------------
    # Quick Preset Selector Bar (Purple Theme)
    # ---------------------------------------------------------
    p_col1, p_col2, p_col3, p_col4, p_col5, p_col6 = st.columns([1.2, 1.2, 1.2, 1.2, 1.2, 0.7])

    with p_col1:
        if st.button("🔴 Secret (Py)", use_container_width=True, help="Load Python hardcoded secret benchmark"):
            st.session_state.code_text = PRESET_SAMPLES["secret_python"]["code"]
            st.session_state.uploaded_name = PRESET_SAMPLES["secret_python"]["filename"]
            st.session_state.pop("syntax_error", None)
            st.rerun()

    with p_col2:
        if st.button("🟠 SQLi (Java)", use_container_width=True, help="Load Java SQL injection benchmark"):
            st.session_state.code_text = PRESET_SAMPLES["sqli_java"]["code"]
            st.session_state.uploaded_name = PRESET_SAMPLES["sqli_java"]["filename"]
            st.session_state.pop("syntax_error", None)
            st.rerun()

    with p_col3:
        if st.button("🟠 SQLi (Py)", use_container_width=True, help="Load Python SQL injection benchmark"):
            st.session_state.code_text = PRESET_SAMPLES["sqli_python"]["code"]
            st.session_state.uploaded_name = PRESET_SAMPLES["sqli_python"]["filename"]
            st.session_state.pop("syntax_error", None)
            st.rerun()

    with p_col4:
        if st.button("⚠️ Syntax Err (Py)", use_container_width=True, help="Test syntax error reporting with exact line and pointer"):
            st.session_state.code_text = PRESET_SAMPLES["syntax_error_py"]["code"]
            st.session_state.uploaded_name = PRESET_SAMPLES["syntax_error_py"]["filename"]
            st.session_state.pop("syntax_error", None)
            st.rerun()

    with p_col5:
        if st.button("🟢 Clean (Py)", use_container_width=True, help="Load clean secure Python code benchmark"):
            st.session_state.code_text = PRESET_SAMPLES["clean_python"]["code"]
            st.session_state.uploaded_name = PRESET_SAMPLES["clean_python"]["filename"]
            st.session_state.pop("syntax_error", None)
            st.rerun()

    with p_col6:
        if st.button("🧹 Clear", use_container_width=True, help="Reset the editor"):
            st.session_state.code_text = ""
            st.session_state.pop("uploaded_name", None)
            st.session_state.pop("uploaded_bytes", None)
            st.session_state.pop("syntax_error", None)
            st.rerun()

    st.write("")

    # ---------------------------------------------------------
    # Upload Zone
    # ---------------------------------------------------------
    uploaded = st.file_uploader(
        "Upload Source File (Python or Java)",
        type=["py", "java"],
        help="Supported extensions: .py, .java. Files are analyzed via AST static verification without execution.",
    )

    upload_name = st.session_state.get("uploaded_name", "")

    if uploaded is not None:
        upload_name = uploaded.name
        try:
            uploaded_bytes = uploaded.getvalue()
            uploaded_code = uploaded_bytes.decode("utf-8")

            if (
                st.session_state.get("uploaded_name") != uploaded.name
                or st.session_state.get("uploaded_bytes") != uploaded_bytes
            ):
                st.session_state.code_text = uploaded_code
                st.session_state.uploaded_name = uploaded.name
                st.session_state.uploaded_bytes = uploaded_bytes
                st.session_state.pop("syntax_error", None)

        except UnicodeDecodeError:
            st.error("Failed to decode uploaded file as UTF-8 text.")
    else:
        if "uploaded_name" in st.session_state and st.session_state.uploaded_name not in [
            p["filename"] for p in PRESET_SAMPLES.values()
        ]:
            st.session_state.pop("uploaded_name", None)
            st.session_state.pop("uploaded_bytes", None)

    # ---------------------------------------------------------
    # Editor Header Toolbar & Metadata Bar (Purple Theme)
    # ---------------------------------------------------------
    current_code = st.session_state.get("code_text", "")
    language = detect_language(current_code, upload_name)
    line_count = len(current_code.splitlines()) if current_code else 0
    char_count = len(current_code)
    file_label = upload_name if upload_name else ("scratchpad.py" if language == "Python" else "Scratchpad.java")

    lang_badge_class = "badge-purple" if language == "Python" else "badge-cyan"
    lang_icon = "🐍" if language == "Python" else "☕"

    st.write("")
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; background: #ffffff; padding: 10px 16px; border-radius: 10px 10px 0 0; border: 1.5px solid #e9d5ff; border-bottom: none; box-shadow: 0 1px 2px rgba(124, 58, 237, 0.04);">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-family: var(--font-mono); font-size: 0.88rem; font-weight: 600; color: #1e1b4b;">
                    📄 {file_label}
                </span>
                <span class="badge-pill-light {lang_badge_class}">
                    <span class="pulse-dot-green"></span> {lang_icon} {language}
                </span>
            </div>
            <div style="display: flex; align-items: center; gap: 14px; font-size: 0.82rem; color: #6b7280; font-family: var(--font-mono);">
                <span>Lines: <strong style="color: #1e1b4b;">{line_count}</strong></span>
                <span>Characters: <strong style="color: #1e1b4b;">{char_count}</strong></span>
                <span style="color: #7c3aed; font-weight: 600;">● Syntax Check Ready</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    code = st.text_area(
        "Code Editor",
        key="code_text",
        height=380,
        label_visibility="collapsed",
        placeholder="Paste your Python or Java code here, or choose a benchmark preset above...",
    )

    # ---------------------------------------------------------
    # PROMINENT SYNTAX ERROR CARD (Directly Below Editor!)
    # ---------------------------------------------------------
    syntax_err = st.session_state.get("syntax_error")
    if syntax_err:
        err_title = escape(str(syntax_err.get("title", "Syntax Error Detected")))
        err_msg = escape(str(syntax_err.get("message", "Syntax validation failed.")))
        err_snippet = escape(str(syntax_err.get("snippet", "")))
        err_sugg = escape(str(syntax_err.get("suggestion", "Review your syntax before proceeding.")))
        err_line = syntax_err.get("line_number", "N/A")

        st.markdown(
            f"""
            <div class="syntax-error-banner">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <div class="syntax-error-title">
                        <span>🚨</span> {err_title}
                    </div>
                    <span style="background: #fee2e2; color: #991b1b; padding: 2px 10px; border-radius: 999px; font-size: 0.76rem; font-weight: 700; border: 1px solid #fca5a5;">
                        Line {err_line}
                    </span>
                </div>
                <div class="syntax-error-msg">
                    {err_msg}
                </div>
                <div class="syntax-snippet-box">{err_snippet}</div>
                <div class="syntax-suggestion-box">
                    <span>💡</span> <strong>Correction Suggestion:</strong> {err_sugg}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("✕ Dismiss Syntax Error", key="dismiss_syntax_err"):
            st.session_state.pop("syntax_error", None)
            st.rerun()

    st.write("")

    # ---------------------------------------------------------
    # Launch Action Button
    # ---------------------------------------------------------
    action_col, note_col = st.columns([1.5, 2.5], vertical_alignment="center")

    with action_col:
        check = st.button(
            "⚡ Launch Multi-Agent Security Audit",
            type="primary",
            use_container_width=True,
        )

    with note_col:
        st.markdown(
            """
            <div style="font-size: 0.84rem; color: #6b7280; line-height: 1.4; padding-left: 10px;">
                🔒 <strong>Zero-Execution Sandbox:</strong> Code is statically verified using AST parsing and semantic rules. 
                Your code is never compiled with untrusted binaries or executed directly.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="purple-divider"></div>', unsafe_allow_html=True)

    # ---------------------------------------------------------
    # Multi-Agent Architecture Visualizer Cards (Purple Theme)
    # ---------------------------------------------------------
    st.markdown("### 🤖 Orchestrated Multi-Agent Pipeline Architecture")
    st.caption("How your source code is routed across the 4 specialized autonomous agents:")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        st.markdown(
            """
            <div class="pipeline-card-light">
                <div style="font-size: 1.3rem; margin-bottom: 6px;">🔍</div>
                <div style="font-weight: 700; font-size: 0.95rem; color: #1e1b4b;">1. Code Analysis</div>
                <div style="font-size: 0.76rem; color: #7c3aed; text-transform: uppercase; font-weight: 700; margin-bottom: 6px;">Quality & Complexity</div>
                <div style="font-size: 0.82rem; color: #4b5563; line-height: 1.4;">
                    Scans AST structure, cyclomatic complexity, code smells, anti-patterns, and maintainability.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_b:
        st.markdown(
            """
            <div class="pipeline-card-light">
                <div style="font-size: 1.3rem; margin-bottom: 6px;">🛡️</div>
                <div style="font-weight: 700; font-size: 0.95rem; color: #1e1b4b;">2. Security Agent</div>
                <div style="font-size: 0.76rem; color: #dc2626; text-transform: uppercase; font-weight: 700; margin-bottom: 6px;">OWASP Top 10 / CWE</div>
                <div style="font-size: 0.82rem; color: #4b5563; line-height: 1.4;">
                    Scans for SQLi, XSS, hardcoded credentials, token exposure, and broken access controls.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_c:
        st.markdown(
            """
            <div class="pipeline-card-light">
                <div style="font-size: 1.3rem; margin-bottom: 6px;">🛠️</div>
                <div style="font-weight: 700; font-size: 0.95rem; color: #1e1b4b;">3. Remediation Agent</div>
                <div style="font-size: 0.76rem; color: #16a34a; text-transform: uppercase; font-weight: 700; margin-bottom: 6px;">Patches & Diff Fixes</div>
                <div style="font-size: 0.82rem; color: #4b5563; line-height: 1.4;">
                    Generates production-grade corrected code patches and industry best practice standards.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_d:
        st.markdown(
            """
            <div class="pipeline-card-light">
                <div style="font-size: 1.3rem; margin-bottom: 6px;">📋</div>
                <div style="font-weight: 700; font-size: 0.95rem; color: #1e1b4b;">4. PR Summary & RAG</div>
                <div style="font-size: 0.76rem; color: #9333ea; text-transform: uppercase; font-weight: 700; margin-bottom: 6px;">Executive Reporting</div>
                <div style="font-size: 0.82rem; color: #4b5563; line-height: 1.4;">
                    Computes Security Letter Grade, generates PR review summaries, and powers the RAG Assistant.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return code, language, check
