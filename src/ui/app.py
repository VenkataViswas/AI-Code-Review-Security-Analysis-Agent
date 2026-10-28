import html
from crsa_agent.initial_code_check_utils import detect_language, check_java, check_python
import streamlit as st

st.set_page_config(page_title="CodeCheck", page_icon="⌘", layout="wide")

# CSS for white file upload button transitioning to blue gradient, and light code editor
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Patrick+Hand&family=Fira+Code:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Patrick Hand', cursive; }
.stApp { background: #f7f9fc; color: #17233f; }
.block-container { padding-top: 1.6rem; max-width: 1450px; }
h1, h2, h3 { font-family: 'Patrick Hand', cursive !important; color: #14213d; }
h1 { font-size: 2.7rem !important; }

.eyebrow { color: #5d7194; font-size: 1.05rem; }

/* Primary Submit Button (Check Code) */
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

/* File Uploader styling */
div[data-testid="stFileUploader"] {
    background: #ffffff;
    border: 1.5px dashed #a5c2eb;
    border-radius: 12px;
    padding: 12px;
}

/* Upload Button: Starts White, changes to Blue Gradient on Submit/Hover/Active */
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

/* Light theme for Code Editor TextArea */
textarea {
    font-family: 'Fira Code', monospace !important;
    background-color: #ffffff !important;
    color: #17233f !important;
    border: 1.5px solid #c5d5eb !important;
    border-radius: 10px !important;
}

/* Status Cards */
.status-ok { background:#eafaf1; border:1.5px solid #65d69a; color:#086b40; padding:1rem; border-radius:12px; }
.status-bad { background:#fff0ef; border:1.5px solid #ffaaa3; color:#a32620; padding:1rem; border-radius:12px; }
.small { color:#637797; font-size:1rem; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "code_text" not in st.session_state:
    st.session_state.code_text = "def add(a, b):\n    return a + b\n\nprint(add(5, 3))"
if "result" not in st.session_state:
    st.session_state.result = None

# Header
st.title("⌘  CodeCheck")
st.markdown('<p class="eyebrow">Paste your code or upload a file to check for errors · Python / Java</p>', unsafe_allow_html=True)
st.divider()


# Main App Layout
left, right = st.columns([1.05, 1], gap="large")

with left:
    st.subheader("1. Choose input")
    uploaded = st.file_uploader("Upload a source file", type=["py", "java"], help="Supported extensions: .py and .java")
    
    upload_name = ""
    if uploaded:
        upload_name = uploaded.name
        try:
            st.session_state.code_text = uploaded.getvalue().decode("utf-8")
        except UnicodeDecodeError:
            st.error("This file could not be read as UTF-8 text.")
    else:
        st.caption("Or paste code in the editor below.")

    st.write("")
    st.subheader("2. Code editor")
    
    code = st.text_area(
        "Paste or edit code",
        key="code_text",
        height=380,
        label_visibility="collapsed",
        placeholder="Paste your Python or Java code here..."
    )
    
    language = detect_language(code, upload_name)
    
    check = st.button("⌕  Check code", type="primary", use_container_width=True)
    st.markdown('<p class="small">Checks syntax/compilation errors. It does not execute your code.</p>', unsafe_allow_html=True)

# Run Check Logic
if check:
    if not code.strip():
        st.session_state.result = {"ok": False, "title": "No code provided", "details": "Paste code or upload a source file first.", "items": []}
    elif language == "Python":
        st.session_state.result = check_python(code)
    else:
        st.session_state.result = check_java(code)

with right:
    st.subheader("3. Analysis result")
    result = st.session_state.result
    
    if result is None:
        st.info("Your result will appear here after you click **Check code**.")
        st.markdown("**What is checked?**")
        st.markdown("- **Python**: syntax parsing (`ast.parse`)")
        st.markdown("- **Java**: compilation (`javac`) with shutils")
    else:
        title_esc = html.escape(result["title"])
        details_esc = html.escape(result["details"])
        if result["ok"]:
            st.markdown(f'<div class="status-ok"><b>✓ {title_esc}</b><br>{details_esc}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-bad"><b>✕ {title_esc}</b><br>{details_esc}</div>', unsafe_allow_html=True)
            
        if result.get("items"):
            st.markdown("#### Details")
            for item in result["items"]:
                st.code(item, language="text")

st.divider()
st.caption("CodeCheck · Lightweight syntax checker for Python and Java")    