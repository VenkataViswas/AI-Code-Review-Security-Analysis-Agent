import streamlit as st


def initialize_session_state():
    if "code_text" not in st.session_state:
        st.session_state.code_text = (
            "def add(a, b):\n"
            "    return a + b\n\n"
            "print(add(5, 3))"
        )

    if "result" not in st.session_state:
        st.session_state.result = None

    if "cca_messages" not in st.session_state:
        st.session_state.cca_messages = []
