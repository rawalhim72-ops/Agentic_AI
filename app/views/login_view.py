"""
User Authentication & Profile View for Apex Support AI (Assignment 2).
Provides secure login/logout with PBKDF2 password verification,
session profile status, and quick credential switcher for testing.
"""

import streamlit as st
from security.authn import authenticate_user
from database.db import get_db_session
from database.models import Student


def render_login_view():
    """Renders the authentication login form and active profile status."""
    st.markdown('<div class="enterprise-badge">● Identity & Access Control</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="margin-bottom: 1.2rem;">
            <h1 style="font-size: 1.85rem; font-weight: 800; margin: 0; color: #F8FAFC; letter-spacing: -0.02em;">
                Authentication & Profile Center
            </h1>
            <p style="font-size: 0.88rem; color: #94A3B8; margin: 4px 0 0 0;">
                Role-based session authentication with PBKDF2-HMAC-SHA256 salted password hashing and default-deny isolation.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_user = st.session_state.get("authenticated_user")

    if current_user:
        # Active authenticated session card
        role = current_user.get("role", "STUDENT")
        role_badge_color = "#3B82F6" if role == "STUDENT" else ("#10B981" if role == "SUPPORT_STAFF" else "#8B5CF6")
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(
                f"""
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                        <div>
                            <span style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: #94A3B8; font-weight: 700;">Active Authenticated Session</span>
                            <h2 style="font-size: 1.5rem; font-weight: 700; color: #F8FAFC; margin: 0.2rem 0 0 0;">{current_user.get('display_name', current_user.get('username'))}</h2>
                        </div>
                        <span style="background: {role_badge_color}22; color: {role_badge_color}; border: 1px solid {role_badge_color}55; padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 700;">
                            {role}
                        </span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1rem; border-top: 1px solid rgba(148, 163, 184, 0.15); padding-top: 1rem;">
                        <div>
                            <div style="font-size: 0.75rem; color: #94A3B8;">Username</div>
                            <div style="font-size: 0.95rem; font-weight: 600; color: #F8FAFC; font-family: monospace;">{current_user.get('username')}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: #94A3B8;">Student ID</div>
                            <div style="font-size: 0.95rem; font-weight: 600; color: #F8FAFC; font-family: monospace;">{current_user.get('student_id') or 'N/A (Staff/Admin)'}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.75rem; color: #94A3B8;">Security Level</div>
                            <div style="font-size: 0.95rem; font-weight: 600; color: #10B981;">● PBKDF2 Verified</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_btn1, col_btn2 = st.columns([1, 3])
            with col_btn1:
                if st.button("🚪 Log Out", use_container_width=True, type="secondary"):
                    # Revert to default guest / stu1001
                    st.session_state.authenticated_user = None
                    st.session_state.student_id = "STU1001"
                    st.toast("Logged out successfully.")
                    st.rerun()

        with c2:
            st.markdown(
                """
                <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 12px; padding: 1.2rem;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #F8FAFC; margin-bottom: 0.6rem;">🛡️ Security Guarantees</div>
                    <ul style="font-size: 0.8rem; color: #94A3B8; padding-left: 1.2rem; margin: 0; line-height: 1.6;">
                        <li><strong>Session Binding:</strong> Agent resolves identity from session, not chat text.</li>
                        <li><strong>Owner Isolation:</strong> Students blocked from accessing peer records.</li>
                        <li><strong>PBKDF2 Protection:</strong> 100,000 iterations + hex salt.</li>
                        <li><strong>Immutable Audit:</strong> Every sensitive query logged to audit trail.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:
        # Login Form
        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.markdown(
                """
                <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC; margin-bottom: 0.8rem;">
                    Sign in to your Apex Support AI Account
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("login_form"):
                username_input = st.text_input("Username", placeholder="e.g. stu1001, support1, admin1").strip()
                password_input = st.text_input("Password", type="password", placeholder="Enter your secure password")
                submitted = st.form_submit_button("Sign In 🔐", use_container_width=True, type="primary")

                if submitted:
                    if not username_input or not password_input:
                        st.error("Please provide both username and password.")
                    else:
                        user = authenticate_user(username_input, password_input)
                        if user:
                            st.session_state.authenticated_user = user
                            if user.get("student_id"):
                                st.session_state.student_id = user["student_id"]
                                # Update active_student object
                                with get_db_session() as session:
                                    stu = session.query(Student).filter(Student.student_id == user["student_id"]).first()
                                    if stu:
                                        st.session_state.active_student = stu.to_dict()
                            st.success(f"Welcome back, {user.get('display_name')}! Identity authenticated.")
                            st.rerun()
                        else:
                            st.error("Invalid username or password. Check demo credentials below.")

        with c2:
            st.markdown(
                """
                <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 12px; padding: 1.2rem;">
                    <div style="font-size: 0.9rem; font-weight: 700; color: #38BDF8; margin-bottom: 0.5rem;">📋 Demo Credentials (PBKDF2)</div>
                    <table style="width: 100%; font-size: 0.78rem; color: #CBD5E1; border-collapse: collapse;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: left;">
                                <th style="padding: 6px 4px;">Role</th>
                                <th style="padding: 6px 4px;">Username</th>
                                <th style="padding: 6px 4px;">Password</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid rgba(148, 163, 184, 0.1);">
                                <td style="padding: 6px 4px; color: #3B82F6;">Student 1</td>
                                <td style="padding: 6px 4px; font-family: monospace;">stu1001</td>
                                <td style="padding: 6px 4px; font-family: monospace;">Student#1001!</td>
                            </tr>
                            <tr style="border-bottom: 1px solid rgba(148, 163, 184, 0.1);">
                                <td style="padding: 6px 4px; color: #3B82F6;">Student 2</td>
                                <td style="padding: 6px 4px; font-family: monospace;">stu1002</td>
                                <td style="padding: 6px 4px; font-family: monospace;">Student#1002!</td>
                            </tr>
                            <tr style="border-bottom: 1px solid rgba(148, 163, 184, 0.1);">
                                <td style="padding: 6px 4px; color: #10B981;">Support Staff</td>
                                <td style="padding: 6px 4px; font-family: monospace;">support1</td>
                                <td style="padding: 6px 4px; font-family: monospace;">Staff#2026!</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 4px; color: #8B5CF6;">Admin Dean</td>
                                <td style="padding: 6px 4px; font-family: monospace;">admin1</td>
                                <td style="padding: 6px 4px; font-family: monospace;">Admin#2026!</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Quick Switcher for evaluation testing
    st.markdown("<hr style='border: none; border-top: 1px solid rgba(148, 163, 184, 0.15); margin: 1.5rem 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #94A3B8; margin-bottom: 0.6rem;'>⚡ Quick Persona Switch (1-Click Evaluation)</div>", unsafe_allow_html=True)
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("👤 Student: Rahul (STU1001)", use_container_width=True):
            user = authenticate_user("stu1001", "Student#1001!")
            st.session_state.authenticated_user = user
            st.session_state.student_id = "STU1001"
            st.rerun()
    with q2:
        if st.button("👤 Student: Priya (STU1002)", use_container_width=True):
            user = authenticate_user("stu1002", "Student#1002!")
            st.session_state.authenticated_user = user
            st.session_state.student_id = "STU1002"
            st.rerun()
    with q3:
        if st.button("🛡️ Staff: Anita Roy (Reviewer)", use_container_width=True):
            user = authenticate_user("support1", "Staff#2026!")
            st.session_state.authenticated_user = user
            st.rerun()
    with q4:
        if st.button("👑 Admin: Dr. Mehta (Dean)", use_container_width=True):
            user = authenticate_user("admin1", "Admin#2026!")
            st.session_state.authenticated_user = user
            st.rerun()
