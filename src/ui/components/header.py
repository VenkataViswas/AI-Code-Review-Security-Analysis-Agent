import streamlit as st


def render_header():
    st.title("⌘  CodeCheck")
    st.markdown(
        '<p class="eyebrow">'
        'Paste your code or upload a file to check for errors '
        '· Python / Java'
        '</p>',
        unsafe_allow_html=True,
    )
    st.divider()
