import streamlit as st

st.set_page_config(
    page_title="CRSA-Agent | AI Code Review & Security Analysis",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

input_page = st.Page(
    "pages/input_page.py",
    title="Code Scanner & Presets",
    icon="🔍",
    url_path="",
    default=True,
)

result_page = st.Page(
    "pages/result_page.py",
    title="Security Audit Dashboard",
    icon="📊",
    url_path="result",
)

pg = st.navigation({
    "Multi-Agent Platform": [input_page, result_page],
})

# Sidebar branding & system health panel (Purple Theme)
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 10px 4px 14px 4px;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                <span style="font-size: 1.8rem;">🛡️</span>
                <div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #1e1b4b; letter-spacing: -0.02em;">
                        CRSA-Agent
                    </div>
                    <div style="font-size: 0.76rem; color: #7c3aed; font-weight: 700; text-transform: uppercase;">
                        Code Review & Security Analysis
                    </div>
                </div>
            </div>
            <div style="font-size: 0.82rem; color: #4b5563; line-height: 1.4; margin-top: 6px;">
                Autonomous multi-agent orchestration for vulnerability scanning, quality review, and remediation.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


    st.divider()

    st.caption("Active Target Languages:")
    st.markdown(
        """
        <div style="display: flex; gap: 6px; margin-bottom: 12px;">
            <span style="background: #f5f3ff; color: #7c3aed; border: 1px solid #d8b4fe; padding: 3px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">🐍 Python 3.x</span>
            <span style="background: #ecfeff; color: #0891b2; border: 1px solid #a5f3fc; padding: 3px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">☕ Java</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("© CRSA-Agent Multi-Agent Security Platform")

pg.run()
