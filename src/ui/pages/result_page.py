
import streamlit as st

from ui.components.results_panel import render_results_panel


# Retrieve submitted data.
analysis = st.session_state.get("analysis_result")
code = st.session_state.get("submitted_code", "")
language = st.session_state.get("submitted_language", "")

# Redirect if no result exists.
if analysis is None:
    st.warning(
        "No analysis results found. Please submit your code first."
    )
    st.switch_page("pages/input_page.py")
    st.stop()

# Display results.
# The Conversational Code Assistant is already rendered
# inside results_panel.py. Do not call it again here.
render_results_panel(code, language)
