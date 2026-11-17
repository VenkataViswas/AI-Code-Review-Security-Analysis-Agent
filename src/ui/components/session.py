import streamlit as st


def initialize_session_state():
    if "code_text" not in st.session_state:
        st.session_state.code_text = (
            '"""Security issue: hardcoded credential."""\n\n'
            'API_TOKEN = "sk_test_EXAMPLE_DO_NOT_USE_123456"\n\n\n'
            'def call_service(client):\n'
            '    return client.get("/profile", headers={"Authorization": f"Bearer {API_TOKEN}"})\n'
        )

    if "result" not in st.session_state:
        st.session_state.result = None

    if "cca_messages" not in st.session_state:
        st.session_state.cca_messages = []
