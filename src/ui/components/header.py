import streamlit as st


def render_header():
    st.markdown(
        """
        <div class="hero-banner-purple">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <span class="badge-pill-light badge-purple">
                            <span class="pulse-dot-green"></span> Multi-Agent Pipeline Active
                        </span>
                        <span class="badge-pill-light badge-cyan">LangGraph Orchestrated</span>
                        <span class="badge-pill-light badge-green">⚡ Real-Time Checking</span>
                    </div>
                    <h1 style="margin: 0; padding: 0; font-size: 2.1rem; font-weight: 800; color: #1e1b4b; letter-spacing: -0.03em;">
                        🛡️ CRSA-Agent <span style="font-size: 1.2rem; font-weight: 600; color: #7c3aed;">AI Code Review & Security Analysis</span>
                    </h1>
                    <p style="margin: 6px 0 0 0; color: #4b5563; font-size: 0.96rem; max-width: 860px; line-height: 1.5;">
                        Intelligent multi-agent platform analyzing Python & Java codebases for security vulnerabilities, architectural code smells, 
                        and compliance defects — generating actionable remediation patches, PR summaries, and RAG-guided security intelligence.
                    </p>
                </div>
                <div style="display: flex; flex-direction: column; align-items: flex-end; justify-content: center;">
                    <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                        <span class="badge-pill-light badge-purple">🐍 Python 3.x</span>
                        <span class="badge-pill-light badge-cyan">☕ Java</span>
                    </div>
                    <span style="font-size: 0.78rem; color: #6b7280; margin-top: 8px; font-weight: 600;">
                        Enterprise Multi-Agent Pipeline v1.0
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
