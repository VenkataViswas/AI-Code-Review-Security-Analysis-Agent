import streamlit as st


def configure_page():
    st.set_page_config(
        page_title="CRSA-Agent | AI Code Review & Security Analysis",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def load_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

        /* Root CSS Variables - Purple Light Theme */
        :root {
            --primary-purple: #7c3aed;
            --primary-purple-hover: #6d28d9;
            --purple-50: #faf5ff;
            --purple-100: #f3e8ff;
            --purple-200: #e9d5ff;
            --purple-300: #d8b4fe;
            --purple-600: #9333ea;
            --purple-700: #7e22ce;
            --purple-900: #4c1d95;
            --bg-page: #fbf9fe;
            --bg-card: #ffffff;
            --bg-card-alt: #f5f3ff;
            --border-light: #ede9fe;
            --border-hover: #d8b4fe;
            --text-heading: #1e1b4b;
            --text-body: #312e81;
            --text-muted: #6b7280;
            --color-critical: #dc2626;
            --color-high: #ea580c;
            --color-medium: #d97706;
            --color-low: #7c3aed;
            --color-success: #16a34a;
            --font-sans: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
            --shadow-sm: 0 1px 3px 0 rgba(124, 58, 237, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(124, 58, 237, 0.07), 0 2px 4px -2px rgba(124, 58, 237, 0.04);
            --shadow-lg: 0 10px 15px -3px rgba(124, 58, 237, 0.09), 0 4px 6px -4px rgba(124, 58, 237, 0.04);
        }

        /* Canvas in Purple Light Theme */
        html, body, [class*="css"], .stApp {
            font-family: var(--font-sans) !important;
            color: var(--text-body);
            background-color: var(--bg-page) !important;
        }

        .block-container {
            padding-top: 1.8rem !important;
            padding-bottom: 3.5rem !important;
            max-width: 1480px !important;
        }

        /* Headings with Deep Violet Text */
        h1, h2, h3, h4, h5, h6 {
            font-family: var(--font-sans) !important;
            font-weight: 700 !important;
            color: var(--text-heading) !important;
            letter-spacing: -0.02em !important;
        }

        h1 {
            font-size: 2.2rem !important;
            color: var(--text-heading) !important;
        }

        h2 {
            font-size: 1.55rem !important;
            margin-top: 0.4rem !important;
            margin-bottom: 0.6rem !important;
        }

        h3 {
            font-size: 1.2rem !important;
            color: var(--text-heading) !important;
        }

        p, span, label, div {
            color: var(--text-body);
        }

        /* Streamlit Buttons in Purple Theme */
        div.stButton > button {
            border-radius: 8px !important;
            font-family: var(--font-sans) !important;
            font-weight: 600 !important;
            font-size: 0.92rem !important;
            padding: 0.5rem 1.1rem !important;
            border: 1px solid var(--border-light) !important;
            background: #ffffff !important;
            color: #1e1b4b !important;
            box-shadow: var(--shadow-sm) !important;
            transition: all 0.2s ease !important;
        }

        div.stButton > button:hover {
            border-color: var(--primary-purple) !important;
            color: var(--primary-purple) !important;
            background: #faf5ff !important;
            box-shadow: var(--shadow-md) !important;
            transform: translateY(-1px) !important;
        }

        /* Primary Purple Action Buttons */
div.stButton > button[kind="primary"],
div.stDownloadButton > button[kind="primary"],
div.stButton > button[data-testid="stBaseButton-primary"],
div.stDownloadButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: 1px solid #6d28d9 !important;
    box-shadow: 0 2px 10px rgba(124, 58, 237, 0.28) !important;
}

/* Force Primary Button Text to White */
div.stButton > button[kind="primary"] *,
div.stDownloadButton > button[kind="primary"] *,
div.stButton > button[data-testid="stBaseButton-primary"] *,
div.stDownloadButton > button[data-testid="stBaseButton-primary"] * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

div.stButton > button[kind="primary"]:hover,
div.stDownloadButton > button[kind="primary"]:hover,
div.stButton > button[data-testid="stBaseButton-primary"]:hover,
div.stDownloadButton > button[data-testid="stBaseButton-primary"]:hover {
    background: linear-gradient(135deg, #6d28d9 0%, #5b21b6 100%) !important;
    box-shadow: 0 4px 16px rgba(124, 58, 237, 0.45) !important;
    transform: translateY(-1.5px) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

/* Download Button */
div.stDownloadButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) {
    border-radius: 8px !important;
    font-family: var(--font-sans) !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    background: #ffffff !important;
    color: #7c3aed !important;
    -webkit-text-fill-color: #7c3aed !important;
    border: 1.5px solid #a855f7 !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all 0.2s ease !important;
}

/* Download Button Hover */
div.stDownloadButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover {
    background: #faf5ff !important;
    color: #6d28d9 !important;
    -webkit-text-fill-color: #6d28d9 !important;
    border-color: #7c3aed !important;
    box-shadow: var(--shadow-md) !important;
    transform: translateY(-1px) !important;
}

        /* File Uploader in Purple Theme */
        div[data-testid="stFileUploader"] {
            background: #ffffff !important;
            border: 1.5px dashed #d8b4fe !important;
            border-radius: 12px !important;
            padding: 16px 20px !important;
            box-shadow: var(--shadow-sm) !important;
            transition: all 0.25s ease !important;
        }

        div[data-testid="stFileUploader"]:hover {
            border-color: var(--primary-purple) !important;
            background: #faf5ff !important;
        }

        div[data-testid="stFileUploader"] button {
            background: #f5f3ff !important;
            color: #7c3aed !important;
            border: 1px solid #d8b4fe !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
        }

        div[data-testid="stFileUploader"] button:hover {
            background: #ede9fe !important;
            color: #6d28d9 !important;
            border-color: #c084fc !important;
        }

        /* Code Editor / Text Area in Purple Theme */
        textarea, div[data-baseweb="textarea"] textarea {
            font-family: var(--font-mono) !important;
            font-size: 0.92rem !important;
            line-height: 1.6 !important;
            background-color: #ffffff !important;
            color: #1e1b4b !important;
            border: 1.5px solid #e9d5ff !important;
            border-radius: 10px !important;
            padding: 14px 16px !important;
            box-shadow: inset 0 1px 2px rgba(124, 58, 237, 0.04) !important;
            transition: all 0.2s ease !important;
        }

        textarea:focus, div[data-baseweb="textarea"] textarea:focus {
            border-color: var(--primary-purple) !important;
            box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15) !important;
            outline: none !important;
        }

        /* Streamlit Metrics Default Styling */
        div[data-testid="stMetric"] {
            background: #ffffff !important;
            border: 1px solid var(--border-light) !important;
            border-radius: 12px !important;
            padding: 16px 18px !important;
            box-shadow: var(--shadow-sm) !important;
            transition: all 0.2s ease !important;
        }

        div[data-testid="stMetric"]:hover {
            border-color: var(--purple-300) !important;
            box-shadow: var(--shadow-md) !important;
            transform: translateY(-1.5px) !important;
        }

        div[data-testid="stMetricLabel"] > div {
            font-size: 0.78rem !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            color: #6b7280 !important;
        }

        div[data-testid="stMetricValue"] > div {
            font-size: 1.85rem !important;
            font-weight: 800 !important;
            color: var(--text-heading) !important;
            font-family: var(--font-sans) !important;
        }

        /* Purple Tabs */
        div[data-baseweb="tab-list"] {
            gap: 8px !important;
            background-color: #f5f3ff !important;
            padding: 5px !important;
            border-radius: 10px !important;
            border: 1px solid var(--border-light) !important;
        }

        button[data-baseweb="tab"] {
            font-family: var(--font-sans) !important;
            font-weight: 600 !important;
            font-size: 0.90rem !important;
            padding: 8px 18px !important;
            border-radius: 7px !important;
            color: #6b7280 !important;
            border: none !important;
            transition: all 0.15s ease !important;
            background: transparent !important;
        }

        button[data-baseweb="tab"]:hover {
            color: var(--primary-purple) !important;
            background: rgba(255, 255, 255, 0.6) !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--primary-purple) !important;
            background: #ffffff !important;
            box-shadow: 0 1px 4px rgba(124, 58, 237, 0.12) !important;
            border: 1px solid #ddd6fe !important;
        }

        div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] {
            display: none !important;
        }

        /* Expanders in Purple Theme */
        div[data-testid="stExpander"] {
            background: #ffffff !important;
            border: 1px solid var(--border-light) !important;
            border-radius: 10px !important;
            margin-bottom: 10px !important;
            box-shadow: var(--shadow-sm) !important;
            transition: border-color 0.2s ease !important;
        }

        div[data-testid="stExpander"]:hover {
            border-color: var(--purple-300) !important;
        }

        div[data-testid="stExpander"] summary {
            font-family: var(--font-sans) !important;
            font-weight: 600 !important;
            font-size: 0.92rem !important;
            color: var(--text-heading) !important;
            padding: 12px 16px !important;
        }

        /* Code Blocks */
        div[data-testid="stCodeBlock"] {
            border-radius: 10px !important;
            border: 1px solid var(--border-light) !important;
            box-shadow: var(--shadow-sm) !important;
        }

        /* Sidebar in Purple Light Theme */
        section[data-testid="stSidebar"] {
            background-color: #faf5ff !important;
            border-right: 1px solid var(--border-light) !important;
        }

        /* Multiselect Tags in Purple Theme */
        div[data-baseweb="tag"] {
            background-color: #f3e8ff !important;
            border: 1px solid #d8b4fe !important;
            border-radius: 6px !important;
        }

        div[data-baseweb="tag"] span {
            color: #6b21a8 !important;
            font-weight: 600 !important;
        }

        /* ================================================= */
        /* RESPONSIVE, SPACED KPI METRIC CARDS (NEW)         */
        /* ================================================= */

        .kpi-metric-card {
            background: #ffffff;
            border: 1px solid #ede9fe;
            border-radius: 12px;
            padding: 16px 18px;
            box-shadow: 0 1px 3px rgba(124, 58, 237, 0.05);
            transition: all 0.2s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .kpi-metric-card:hover {
            border-color: #d8b4fe;
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.08);
            transform: translateY(-2px);
        }

        .kpi-metric-label {
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #6b7280;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .kpi-metric-value {
            font-size: 1.85rem;
            font-weight: 800;
            font-family: var(--font-sans);
            line-height: 1.2;
        }

        .kpi-metric-subtext {
            font-size: 0.74rem;
            color: #9ca3af;
            margin-top: 6px;
            font-weight: 500;
        }

        /* ================================================= */
        /* PURPLE THEME CUSTOM CARDS & BADGES                */
        /* ================================================= */

        .hero-banner-purple {
            background: #ffffff;
            border: 1px solid #e9d5ff;
            border-radius: 14px;
            padding: 24px 28px;
            margin-bottom: 22px;
            box-shadow: var(--shadow-md);
            position: relative;
            overflow: hidden;
        }

        .hero-banner-purple::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #7c3aed, #9333ea, #c084fc, #a855f7);
        }

        /* Security Grade Card */
        .grade-card {
            background: #ffffff;
            border: 1px solid #e9d5ff;
            border-radius: 14px;
            padding: 22px 26px;
            box-shadow: var(--shadow-md);
            display: flex;
            align-items: center;
            gap: 22px;
            height: 100%;
        }

        .grade-badge-circle {
            width: 82px;
            height: 82px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.3rem;
            font-weight: 800;
            font-family: var(--font-sans);
            flex-shrink: 0;
            box-shadow: var(--shadow-md);
        }

        .grade-a {
            background: #f0fdf4;
            color: #16a34a;
            border: 4px solid #86efac;
        }

        .grade-b {
            background: #faf5ff;
            color: #7c3aed;
            border: 4px solid #c084fc;
        }

        .grade-c {
            background: #fffbeb;
            color: #d97706;
            border: 4px solid #fde68a;
        }

        .grade-d {
            background: #fff7ed;
            color: #ea580c;
            border: 4px solid #fdba74;
        }

        .grade-f {
            background: #fef2f2;
            color: #dc2626;
            border: 4px solid #fca5a5;
        }

        /* Pill Badges in Purple Theme */
        .badge-pill-light {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 11px;
            border-radius: 999px;
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }

        .badge-purple {
            background: #f5f3ff;
            color: #7c3aed;
            border: 1px solid #d8b4fe;
        }

        .badge-cyan {
            background: #ecfeff;
            color: #0891b2;
            border: 1px solid #a5f3fc;
        }

        .badge-green {
            background: #f0fdf4;
            color: #16a34a;
            border: 1px solid #bbf7d0;
        }

        .badge-amber {
            background: #fffbeb;
            color: #d97706;
            border: 1px solid #fde68a;
        }

        .badge-red {
            background: #fef2f2;
            color: #dc2626;
            border: 1px solid #fecaca;
        }

        /* Pulsing Dot */
        .pulse-dot-green {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            background-color: #16a34a;
            box-shadow: 0 0 0 0 rgba(22, 163, 74, 0.6);
            animation: pulse-green-light 2s infinite;
        }

        .pulse-dot-red {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            background-color: #dc2626;
            box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.6);
            animation: pulse-red-light 2s infinite;
        }

        @keyframes pulse-green-light {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(22, 163, 74, 0.6); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(22, 163, 74, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(22, 163, 74, 0); }
        }

        @keyframes pulse-red-light {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.6); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(220, 38, 38, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
        }

        /* Status Badge for PR */
        .status-badge-light {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 5px 14px;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            vertical-align: middle;
        }

        .status-pass-light {
            background-color: #f0fdf4;
            color: #15803d;
            border: 1px solid #86efac;
        }

        .status-warn-light {
            background-color: #fffbeb;
            color: #b45309;
            border: 1px solid #fde68a;
        }

        .status-fail-light {
            background-color: #fef2f2;
            color: #b91c1c;
            border: 1px solid #fca5a5;
        }

        /* Light Cards */
        .card-light {
            background: #ffffff;
            border: 1px solid #ede9fe;
            border-radius: 12px;
            padding: 18px 20px;
            box-shadow: var(--shadow-sm);
            transition: all 0.2s ease;
        }

        .card-light:hover {
            border-color: #d8b4fe;
            box-shadow: var(--shadow-md);
        }

        .card-light-title {
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #6b7280;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* Pipeline Step Cards */
        .pipeline-card-light {
            background: #ffffff;
            border: 1px solid #ede9fe;
            border-radius: 10px;
            padding: 14px 16px;
            box-shadow: var(--shadow-sm);
            transition: all 0.2s ease;
        }

        .pipeline-card-light:hover {
            border-color: #c084fc;
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        /* Action Checklist in Purple Theme */
        .action-item-light {
            background: #ffffff;
            border-left: 4px solid var(--primary-purple);
            border-top: 1px solid #ede9fe;
            border-right: 1px solid #ede9fe;
            border-bottom: 1px solid #ede9fe;
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 8px;
            font-size: 0.90rem;
            line-height: 1.5;
            box-shadow: var(--shadow-sm);
            transition: all 0.15s ease;
        }

        .action-item-light:hover {
            background: #faf5ff;
            border-left-color: var(--primary-purple-hover);
            transform: translateX(2px);
        }

        /* Severity Chips */
        .sev-pill-light {
            display: inline-block;
            padding: 3px 9px;
            border-radius: 6px;
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .sev-critical-light {
            background: #fef2f2;
            color: #dc2626;
            border: 1px solid #fecaca;
        }

        .sev-high-light {
            background: #fff7ed;
            color: #ea580c;
            border: 1px solid #ffedd5;
        }

        .sev-medium-light {
            background: #fffbeb;
            color: #d97706;
            border: 1px solid #fef3c7;
        }

        .sev-low-light {
            background: #f5f3ff;
            color: #7c3aed;
            border: 1px solid #ddd6fe;
        }

        .sev-info-light {
            background: #f8fafc;
            color: #64748b;
            border: 1px solid #e2e8f0;
        }

        .purple-divider {
            height: 1px;
            background: #ede9fe;
            margin: 20px 0;
            border: none;
        }

        /* ================================================= */
        /* PROMINENT SYNTAX ERROR DIAGNOSTIC CARD            */
        /* ================================================= */

        .syntax-error-banner {
            background: #fff5f5;
            border: 1.5px solid #fca5a5;
            border-left: 6px solid #dc2626;
            border-radius: 10px;
            padding: 16px 20px;
            margin: 14px 0 18px 0;
            box-shadow: 0 4px 12px rgba(220, 38, 38, 0.08);
            animation: fadeInError 0.25s ease-in-out;
        }

        @keyframes fadeInError {
            from { opacity: 0; transform: translateY(-4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .syntax-error-title {
            font-size: 1.02rem;
            font-weight: 800;
            color: #b91c1c;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }

        .syntax-error-msg {
            font-size: 0.90rem;
            color: #7f1d1d;
            font-weight: 600;
            margin-bottom: 10px;
        }

        .syntax-snippet-box {
            background: #ffffff;
            border: 1px solid #fecaca;
            border-radius: 8px;
            padding: 10px 14px;
            font-family: var(--font-mono);
            font-size: 0.86rem;
            color: #991b1b;
            line-height: 1.5;
            white-space: pre-wrap;
            margin-bottom: 8px;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.03);
        }

        .syntax-suggestion-box {
            font-size: 0.84rem;
            color: #9a3412;
            background: #fffbeb;
            border: 1px solid #fed7aa;
            border-radius: 6px;
            padding: 6px 12px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
