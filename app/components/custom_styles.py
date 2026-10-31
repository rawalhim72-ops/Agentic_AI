"""
Enterprise CSS Stylesheet for Streamlit Frontend.
Provides dark mode styling, glassmorphism cards, modern typography,
responsive layouts for laptop, tablet, and mobile, and clean sidebar controls.
"""

import streamlit as st


def apply_enterprise_styles():
    """Inject custom CSS into Streamlit application."""
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Completely hide Streamlit default page navigation to prevent duplicate menus */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    div[data-testid="stSidebarNavItems"] {
        display: none !important;
    }

    /* Main Container Responsiveness */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1280px;
    }

    /* Top Header Badge */
    .enterprise-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(59, 130, 246, 0.12);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 9999px;
        padding: 4px 14px;
        font-size: 0.78rem;
        font-weight: 600;
        color: #60A5FA;
        letter-spacing: 0.03em;
        margin-bottom: 10px;
        text-transform: uppercase;
    }

    /* Glassmorphism Cards */
    .glass-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
        margin-bottom: 1rem;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .glass-card:hover {
        border-color: rgba(96, 165, 250, 0.35);
    }

    /* Metric Stat Card */
    .stat-card {
        background: linear-gradient(145deg, #131B2E 0%, #0B1120 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 1rem 1.1rem;
        display: flex;
        flex-direction: column;
        gap: 3px;
        min-height: 85px;
    }
    .stat-label {
        font-size: 0.73rem;
        color: #94A3B8;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .stat-value {
        font-size: 1.55rem;
        font-weight: 700;
        color: #F8FAFC;
        line-height: 1.2;
    }
    .stat-subtitle {
        font-size: 0.73rem;
        color: #10B981;
    }

    /* Operational Status Pills */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 4px;
    }
    .status-tool-success {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.35);
        color: #34D399;
    }
    .status-tool-fail {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.35);
        color: #F87171;
    }
    .status-rag {
        background: rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.35);
        color: #60A5FA;
    }
    .status-memory {
        background: rgba(168, 85, 247, 0.15);
        border: 1px solid rgba(168, 85, 247, 0.35);
        color: #C084FC;
    }

    /* Quick Suggestion Action Chips */
    .quick-chip-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 8px;
        margin-top: 10px;
    }

    /* Trace Details Container */
    .trace-box {
        background: #090D16;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 0.82rem;
        line-height: 1.5;
        margin-top: 8px;
        color: #CBD5E1;
    }

    /* Sidebar Clean Styling */
    [data-testid="stSidebar"] {
        background-color: #080C14 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* Expander Styling */
    .streamlit-expanderHeader {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #94A3B8 !important;
        background: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 6px !important;
    }

    /* Chat Messages Enhancement */
    [data-testid="stChatMessage"] {
        background: rgba(15, 23, 42, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        margin-bottom: 0.75rem;
        padding: 0.9rem;
    }

    /* Tablet & Mobile Responsiveness */
    @media (max-width: 900px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        .stat-value {
            font-size: 1.3rem !important;
        }
        .quick-chip-container {
            grid-template-columns: 1fr;
        }
    }

    @media (max-width: 600px) {
        .stat-card {
            padding: 0.75rem;
            min-height: auto;
        }
        .enterprise-badge {
            font-size: 0.7rem;
            padding: 2px 10px;
        }
    }

    /* Custom Scrollbars */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0B0F19;
    }
    ::-webkit-scrollbar-thumb {
        background: #1E293B;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #334155;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
