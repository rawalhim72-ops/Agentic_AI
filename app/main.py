"""
Main Streamlit Application Entrypoint.
Orchestrates enterprise styling, persistent sidebar, and modular view routing.
"""

import sys
from pathlib import Path

# Add root directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import streamlit as st

# Set Streamlit page config
st.set_page_config(
    page_title="Apex Support AI | Student Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.components.custom_styles import apply_enterprise_styles
from app.components.sidebar import render_sidebar
from app.views.chat_view import render_chat_view
from app.views.monitoring_view import render_monitoring_view
from app.views.memory_view import render_memory_view
from app.views.knowledge_view import render_knowledge_view
from app.views.login_view import render_login_view
from app.views.approval_view import render_approval_view
from app.views.audit_view import render_audit_view
from database.seed import seed_database
from rag.retriever import build_or_load_vector_store

# Ensure DB seeded and FAISS index loaded on initial app boot
if "app_initialized" not in st.session_state:
    try:
        seed_database()
        build_or_load_vector_store()
        st.session_state.app_initialized = True
    except Exception as e:
        print(f"Startup initialization notice: {e}")
        st.session_state.app_initialized = True

# Apply Enterprise Dark Styling
apply_enterprise_styles()

# Render Persistent Sidebar
selected_nav = render_sidebar()

# Route to active view
if "Support Chat" in selected_nav:
    render_chat_view()
elif "Monitoring" in selected_nav:
    render_monitoring_view()
elif "Memory" in selected_nav:
    render_memory_view()
elif "Knowledge" in selected_nav:
    render_knowledge_view()
elif "Login" in selected_nav or "Profile" in selected_nav:
    render_login_view()
elif "Approval" in selected_nav:
    render_approval_view()
elif "Audit" in selected_nav:
    render_audit_view()
else:
    render_chat_view()
