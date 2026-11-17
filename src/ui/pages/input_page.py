import streamlit as st

from ui.components.styles import load_styles
from ui.components.header import render_header
from ui.components.input_panel import render_input_panel
from ui.components.session import initialize_session_state
from ui.components.validation import validate_and_analyze


load_styles()
initialize_session_state()
render_header()

code, language, check = render_input_panel()

if check:
    if not code.strip():
        st.session_state["syntax_error"] = {
            "language": language or "Code",
            "title": "Empty Code Submission",
            "line_number": 1,
            "message": "Please enter or upload source code before initiating analysis.",
            "code_line": "",
            "snippet": "No source code provided in editor.",
            "suggestion": "Paste Python or Java code in the editor, or choose one of the benchmark presets above.",
        }
        st.rerun()
    else:
        validate_and_analyze(code, language)
