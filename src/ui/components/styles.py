import streamlit as st


def configure_page():
    st.set_page_config(
        page_title="CodeCheck",
        page_icon="⌘",
        layout="wide",
    )


def load_styles():
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
