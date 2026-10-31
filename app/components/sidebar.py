"""
Enterprise Sidebar Component for Streamlit.
Provides student switcher, navigation controls, system status indicators,
and knowledge base health monitors.
"""

import streamlit as st
from config.settings import settings
from database.db import get_db_session
from database.models import Student


def render_sidebar():
    """Renders the persistent enterprise sidebar across all pages."""
    with st.sidebar:
        # App Branding Header
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                <div style="background: linear-gradient(135deg, #3B82F6, #1D4ED8); width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; font-weight: bold; color: white;">
                    ⚡
                </div>
                <div>
                    <div style="font-weight: 700; font-size: 1.05rem; color: #F8FAFC; line-height: 1.2;">APEX SUPPORT AI</div>
                    <div style="font-size: 0.72rem; color: #94A3B8; letter-spacing: 0.02em;">Intelligent Student Agent</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<hr style='margin: 10px 0; border-color: rgba(255,255,255,0.08);'/>", unsafe_allow_html=True)

        # 1. Navigation Menu
        st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; margin-bottom: 6px;'>NAVIGATION</div>", unsafe_allow_html=True)
        nav_options = [
            "💬 Support Chat",
            "📊 Monitoring & Telemetry",
            "🧠 Long-Term Memory",
            "📚 Policy Knowledge Base",
            "🔐 Login / Profile",
            "⚖️ Approval Center",
            "🛡️ Audit Logs",
        ]
        if "selected_page" not in st.session_state:
            st.session_state.selected_page = nav_options[0]

        selected_nav = st.radio(
            "Go to",
            nav_options,
            index=nav_options.index(st.session_state.selected_page) if st.session_state.selected_page in nav_options else 0,
            label_visibility="collapsed",
        )
        st.session_state.selected_page = selected_nav

        # Authenticated Session Indicator
        auth_user = st.session_state.get("authenticated_user")
        if auth_user:
            role_badge = auth_user.get("role", "STUDENT")
            st.markdown(
                f"""
                <div style="background: rgba(59, 130, 246, 0.12); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 6px; padding: 6px 10px; margin-top: 6px;">
                    <div style="font-size: 0.7rem; color: #94A3B8;">Authenticated As:</div>
                    <div style="font-size: 0.82rem; font-weight: 700; color: #F8FAFC;">{auth_user.get('display_name', auth_user.get('username'))}</div>
                    <div style="font-size: 0.68rem; color: #38BDF8; font-weight: 600;">● {role_badge}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<hr style='margin: 12px 0; border-color: rgba(255,255,255,0.08);'/>", unsafe_allow_html=True)

        # 2. Student Persona Switcher
        st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; margin-bottom: 6px;'>ACTIVE STUDENT PROFILE</div>", unsafe_allow_html=True)

        # Fetch student list from SQLite
        students_map = {}
        try:
            with get_db_session() as session:
                students = session.query(Student).all()
                for s in students:
                    students_map[f"{s.name} ({s.student_id})"] = s.to_dict()
        except Exception:
            students_map["Rahul Sharma (STU1001)"] = {
                "student_id": "STU1001",
                "name": "Rahul Sharma",
                "programme": "MBA",
                "department": "School of Business",
                "academic_year": "Year 2",
                "status": "Active",
            }

        selected_label = st.selectbox(
            "Select Student Profile",
            options=list(students_map.keys()),
            index=0,
            label_visibility="collapsed",
        )
        current_student = students_map.get(selected_label, {})
        st.session_state.active_student = current_student
        st.session_state.student_id = current_student.get("student_id", "STU1001")

        # Active Student Card
        st.markdown(
            f"""
            <div style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 10px; margin-top: 4px;">
                <div style="font-weight: 600; font-size: 0.85rem; color: #F1F5F9;">{current_student.get('name')}</div>
                <div style="font-size: 0.75rem; color: #60A5FA;">{current_student.get('programme')} • {current_student.get('academic_year')}</div>
                <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 2px;">Dept: {current_student.get('department')}</div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px;">
                    <span style="font-size: 0.68rem; background: rgba(16, 185, 129, 0.2); color: #34D399; padding: 1px 6px; border-radius: 4px;">{current_student.get('status')}</span>
                    <span style="font-size: 0.7rem; color: #94A3B8; font-family: monospace;">{current_student.get('student_id')}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<hr style='margin: 12px 0; border-color: rgba(255,255,255,0.08);'/>", unsafe_allow_html=True)

        # 3. New Session / Reset
        if st.button("🔄 New Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = f"sess_{id(object())}"
            st.rerun()

        st.markdown("<hr style='margin: 12px 0; border-color: rgba(255,255,255,0.08);'/>", unsafe_allow_html=True)

        # 4. Knowledge Base & System Status
        st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; margin-bottom: 6px;'>SYSTEM HEALTH</div>", unsafe_allow_html=True)

        faiss_ready = (settings.VECTOR_STORE_DIR / "faiss_index").exists()
        db_ready = settings.DATABASE_PATH.exists()
        has_llm = settings.has_llm_key
        provider_name = settings.LLM_PROVIDER.upper()

        status_html = f"""
        <div style="font-size: 0.75rem; color: #CBD5E1; line-height: 1.6;">
            <div>Vector Store: <span style="color: {'#34D399' if faiss_ready else '#F87171'};">● {'Indexed (FAISS)' if faiss_ready else 'Not Indexed'}</span></div>
            <div>Database: <span style="color: {'#34D399' if db_ready else '#F87171'};">● {'Online (SQLite)' if db_ready else 'Offline'}</span></div>
            <div>LLM Provider: <span style="color: {'#34D399' if has_llm else '#FBBF24'};">● {provider_name} {'(API Active)' if has_llm else '(Grounded Fallback)'}</span></div>
            <div>Model: <span style="color: #93C5FD;">{settings.LLM_MODEL}</span></div>
            <div>Embeddings: <span style="color: #93C5FD;">{settings.EMBEDDING_MODEL}</span></div>
        </div>
        """
        st.markdown(status_html, unsafe_allow_html=True)

        # 5. Groq / LLM API Key Settings
        with st.expander("⚡ LLM & Groq API Key", expanded=not has_llm):
            st.caption("Enter your Groq API key to power real-time LLM response synthesis:")
            active_provider = st.selectbox(
                "Provider",
                options=["Groq", "OpenAI"],
                index=0 if settings.LLM_PROVIDER == "groq" else 1,
                key="sidebar_llm_provider",
            )

            if active_provider == "Groq":
                groq_models = [
                    "llama-3.3-70b-versatile",
                    "llama-3.1-8b-instant",
                    "mixtral-8x7b-32768",
                    "gemma2-9b-it",
                ]
                selected_model = st.selectbox(
                    "Model",
                    options=groq_models,
                    index=groq_models.index(settings.LLM_MODEL) if settings.LLM_MODEL in groq_models else 0,
                    key="sidebar_groq_model",
                )
                curr_key = settings.GROQ_API_KEY or (settings.LLM_API_KEY if settings.LLM_API_KEY.startswith("gsk_") else "")
                entered_key = st.text_input(
                    "Groq API Key",
                    value=curr_key,
                    type="password",
                    placeholder="gsk_...",
                    key="sidebar_groq_api_key_input",
                )
                if st.button("💾 Apply Groq Key", use_container_width=True):
                    if entered_key.strip():
                        settings.update_llm_config("groq", entered_key.strip(), selected_model)
                        # Persist to .env
                        env_file = settings.BASE_DIR / ".env"
                        env_file.write_text(
                            f"LLM_PROVIDER=groq\nGROQ_API_KEY={entered_key.strip()}\nLLM_MODEL={selected_model}\n",
                            encoding="utf-8",
                        )
                        st.success(f"Groq API key activated with {selected_model}!")
                        st.rerun()
                    else:
                        st.warning("Please enter a valid Groq API key (starts with gsk_).")
            else:
                openai_models = ["gpt-4o-mini", "gpt-4o"]
                selected_model = st.selectbox(
                    "Model",
                    options=openai_models,
                    index=openai_models.index(settings.LLM_MODEL) if settings.LLM_MODEL in openai_models else 0,
                    key="sidebar_openai_model",
                )
                entered_key = st.text_input(
                    "OpenAI API Key",
                    value=settings.LLM_API_KEY if not settings.LLM_API_KEY.startswith("gsk_") else "",
                    type="password",
                    placeholder="sk-...",
                    key="sidebar_openai_key_input",
                )
                if st.button("💾 Apply OpenAI Key", use_container_width=True):
                    if entered_key.strip():
                        settings.update_llm_config("openai", entered_key.strip(), selected_model)
                        env_file = settings.BASE_DIR / ".env"
                        env_file.write_text(
                            f"LLM_PROVIDER=openai\nLLM_API_KEY={entered_key.strip()}\nLLM_MODEL={selected_model}\n",
                            encoding="utf-8",
                        )
                        st.success(f"OpenAI API key activated with {selected_model}!")
                        st.rerun()
                    else:
                        st.warning("Please enter a valid OpenAI API key.")

        # Assignment Footer
        st.markdown(
            """
            <div style="margin-top: 25px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.06); font-size: 0.7rem; color: #64748B; text-align: center;">
                Agentic AI Engineering • Assignment 1<br/>
                Senior AI Architecture Demo
            </div>
            """,
            unsafe_allow_html=True,
        )

    return st.session_state.selected_page
