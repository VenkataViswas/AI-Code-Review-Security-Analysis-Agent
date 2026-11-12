
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
        st.warning("Please enter or upload your code.")
    else:
        validate_and_analyze(code, language)
