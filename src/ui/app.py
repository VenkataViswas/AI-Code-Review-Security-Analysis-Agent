
import streamlit as st

st.set_page_config(
    page_title="CodeCheck",
    page_icon="⌘",
    layout="wide",
)

input_page = st.Page(
    "pages/input_page.py",
    title="Code Input",
    url_path="",
    default=True,
)

result_page = st.Page(
    "pages/result_page.py",
    title="Analysis Results",
    url_path="result",
)

pg = st.navigation([
    input_page,
    result_page,
])

pg.run()
