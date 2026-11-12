import streamlit as st

from crsa_agent.initial_code_check_utils import detect_language


def render_input_panel():
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
            uploaded_bytes = uploaded.getvalue()
            uploaded_code = uploaded_bytes.decode("utf-8")

            # Update editor content only when a new file is selected.
            if (
                st.session_state.get("uploaded_name") != uploaded.name
                or st.session_state.get("uploaded_bytes") != uploaded_bytes
            ):
                st.session_state.code_text = uploaded_code
                st.session_state.uploaded_name = uploaded.name
                st.session_state.uploaded_bytes = uploaded_bytes

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

    return code, language, check
