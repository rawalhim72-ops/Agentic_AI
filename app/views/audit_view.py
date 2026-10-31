"""
Institutional Audit Trail View for Apex Support AI (Assignment 2).
Provides an immutable, tamper-resistant inspection console for all access decisions,
sensitive tool executions, approval workflows, and redacted credentials.
"""

import streamlit as st
import pandas as pd
from security.audit import get_audit_trail
from database.db import get_db_session
from database.models import AuditLog


def render_audit_view():
    """Renders the institutional audit trail view."""
    st.markdown('<div class="enterprise-badge">● Compliance & Immutable Audit Trail</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="margin-bottom: 1.2rem;">
            <h1 style="font-size: 1.85rem; font-weight: 800; margin: 0; color: #F8FAFC; letter-spacing: -0.02em;">
                Institutional Audit Trail & Security Logs
            </h1>
            <p style="font-size: 0.88rem; color: #94A3B8; margin: 4px 0 0 0;">
                Append-only institutional record of all access requests, cross-student denials, approval transitions, and secret redactions.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Fetch audit events
    events = get_audit_trail(limit=250)

    total_events = len(events)
    allow_count = sum(1 for e in events if e.get("decision") == "ALLOW")
    deny_count = sum(1 for e in events if e.get("decision") == "DENY")
    pending_count = sum(1 for e in events if e.get("decision") == "PENDING")

    # Top KPI Summary Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Total Audit Events</div>
                <div class="stat-value">{total_events}</div>
                <div class="stat-subtitle">Append-only SQLite logs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Authorized Operations</div>
                <div class="stat-value" style="color: #10B981;">{allow_count}</div>
                <div class="stat-subtitle">Decision: ALLOW</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Access Denials Blocked</div>
                <div class="stat-value" style="color: #EF4444;">{deny_count}</div>
                <div class="stat-subtitle">Default-Deny Enforced</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Approval Workflows</div>
                <div class="stat-value" style="color: #F59E0B;">{pending_count}</div>
                <div class="stat-subtitle">Course change states</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Filter Bar
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns([1, 1, 2, 0.5])
    with f1:
        decision_filter = st.selectbox("Filter by Decision", ["ALL", "ALLOW", "DENY", "PENDING"], index=0)
    with f2:
        role_filter = st.selectbox("Filter by Role", ["ALL", "STUDENT", "SUPPORT_STAFF", "ADMINISTRATOR", "ANONYMOUS"], index=0)
    with f3:
        search_query = st.text_input("Search Logs", placeholder="Search by action, user, or resource...").strip().lower()
    with f4:
        st.markdown("<div style='margin-top: 1.7rem;'></div>", unsafe_allow_html=True)
        if st.button("🔄", help="Refresh audit trail"):
            st.rerun()

    # Apply filters
    filtered_events = events
    if decision_filter != "ALL":
        filtered_events = [e for e in filtered_events if e.get("decision") == decision_filter]
    if role_filter != "ALL":
        filtered_events = [e for e in filtered_events if e.get("actor_role") == role_filter]
    if search_query:
        filtered_events = [
            e for e in filtered_events
            if (
                search_query in (e.get("action") or "").lower()
                or search_query in (e.get("actor_username") or "").lower()
                or search_query in (e.get("target_resource") or "").lower()
                or search_query in (e.get("reason") or "").lower()
                or search_query in (e.get("details") or "").lower()
            )
        ]

    st.markdown(f"<div style='font-size: 0.82rem; color: #94A3B8; margin-bottom: 0.6rem;'>Displaying {len(filtered_events)} matching security audit events.</div>", unsafe_allow_html=True)

    if not filtered_events:
        st.info("No audit events match the selected criteria.")
    else:
        display_rows = []
        for e in filtered_events:
            ts = (e.get("timestamp") or "")[:19].replace("T", " ")
            dec = e.get("decision", "ALLOW")
            dec_badge = f"🟢 ALLOW" if dec == "ALLOW" else (f"🔴 DENY" if dec == "DENY" else f"🟡 {dec}")
            display_rows.append({
                "Timestamp (UTC)": ts,
                "Event ID": e.get("event_id"),
                "Decision": dec_badge,
                "Actor User": e.get("actor_username"),
                "Role": e.get("actor_role"),
                "Action": e.get("action"),
                "Target Resource": e.get("target_resource"),
                "Reason / Outcome": e.get("reason") or "Standard authorized operation",
                "Sanitized Details": e.get("details") or "",
            })

        df = pd.DataFrame(display_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Institutional Compliance Notice
    st.markdown(
        """
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 8px; padding: 1rem; margin-top: 1.5rem; font-size: 0.8rem; color: #94A3B8;">
            <strong>Institutional Security & Compliance Notice:</strong><br>
            • Audit logs are stored in the SQLite <code>audit_logs</code> table and are append-only.<br>
            • Students cannot edit or delete audit trail records under any circumstance.<br>
            • Passwords, OTP codes, card numbers, and secret tokens are automatically sanitized and redacted before storage.
        </div>
        """,
        unsafe_allow_html=True,
    )
