"""
Approval Center View for Apex Support AI (Assignment 2).
Coordinates human review of sensitive change workflows (e.g., Course Change requests).
Enforces reviewer role verification, exactly-once execution, and rejected non-execution.
"""

import streamlit as st
from approvals.approval_manager import (
    get_pending_approvals,
    get_all_approvals,
    process_approval_decision,
)


def render_approval_view():
    """Renders the human approval management interface."""
    st.markdown('<div class="enterprise-badge">● Sensitive Workflow & Human-in-the-Loop</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="margin-bottom: 1.2rem;">
            <h1 style="font-size: 1.85rem; font-weight: 800; margin: 0; color: #F8FAFC; letter-spacing: -0.02em;">
                Institutional Approval Center
            </h1>
            <p style="font-size: 0.88rem; color: #94A3B8; margin: 4px 0 0 0;">
                Review and govern high-risk student mutations. Requests remain pending until an authorized reviewer decides.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    current_user = st.session_state.get("authenticated_user")
    is_authorized_reviewer = bool(
        current_user and current_user.get("role") in ["SUPPORT_STAFF", "ADMINISTRATOR"]
    )

    all_requests = get_all_approvals()
    pending_requests = [r for r in all_requests if r.get("status") == "PENDING"]
    approved_requests = [r for r in all_requests if r.get("status") == "APPROVED"]
    rejected_requests = [r for r in all_requests if r.get("status") == "REJECTED"]

    # Top KPI Metrics
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Pending Action</div>
                <div class="stat-value" style="color: #F59E0B;">{len(pending_requests)}</div>
                <div class="stat-subtitle">Awaiting Human Review</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Total Approved</div>
                <div class="stat-value" style="color: #10B981;">{len(approved_requests)}</div>
                <div class="stat-subtitle">Successfully Executed</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Total Rejected</div>
                <div class="stat-value" style="color: #EF4444;">{len(rejected_requests)}</div>
                <div class="stat-subtitle">Non-executed Records</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k4:
        reviewer_status_badge = (
            "<span style='color: #10B981;'>● Reviewer Authorized</span>"
            if is_authorized_reviewer
            else "<span style='color: #EF4444;'>● Read-Only Clearance</span>"
        )
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Active Clearance</div>
                <div class="stat-value" style="font-size: 1.15rem;">{current_user.get('role', 'STUDENT') if current_user else 'GUEST'}</div>
                <div class="stat-subtitle">{reviewer_status_badge}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Permission check notice
    if not is_authorized_reviewer:
        st.markdown(
            """
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 10px; padding: 1rem; margin: 1.2rem 0;">
                <div style="font-weight: 700; color: #EF4444; font-size: 0.95rem;">🔒 Reviewer Permission Required</div>
                <div style="color: #CBD5E1; font-size: 0.85rem; margin-top: 4px;">
                    Course-change approval decisions are restricted to Support Staff (<code>support1</code>) and Academic Dean Administrators (<code>admin1</code>).
                    Students may monitor the status of their submitted requests below.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    tab_pending, tab_history = st.tabs(["⏳ Pending Approvals", "📜 Request History"])

    with tab_pending:
        if not pending_requests:
            st.markdown(
                """
                <div style="text-align: center; padding: 3rem 1rem; color: #64748B;">
                    <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">✅</div>
                    <div style="font-weight: 600; color: #94A3B8;">No Pending Course-Change Requests</div>
                    <div style="font-size: 0.82rem; margin-top: 4px;">All student mutation requests have been reviewed and executed.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for req in pending_requests:
                req_id = req["request_id"]
                stu_id = req["student_id"]
                curr_prog = req.get("current_value")
                new_prog = req.get("requested_value")
                reason = req.get("reason", "Student course change request")
                created_at = req.get("created_at", "")[:19].replace("T", " ")

                with st.expander(f"📌 Request #{req_id} — {stu_id}: {curr_prog} ➜ {new_prog}", expanded=True):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(
                            f"""
                            <div style="font-size: 0.85rem; color: #CBD5E1; line-height: 1.8;">
                                <div><strong>Target Student:</strong> <code>{stu_id}</code></div>
                                <div><strong>Current Enrolled Programme:</strong> <span style="color: #94A3B8;">{curr_prog}</span></div>
                                <div><strong>Requested Programme:</strong> <span style="color: #38BDF8; font-weight: 700;">{new_prog}</span></div>
                                <div><strong>Student Reason:</strong> <em>"{reason}"</em></div>
                                <div><strong>Submitted At:</strong> {created_at} UTC</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    with c2:
                        st.markdown(
                            """
                            <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 8px; padding: 0.8rem; font-size: 0.78rem; color: #94A3B8;">
                                <strong>Workflow Guard:</strong><br>
                                • Approval executes exactly once.<br>
                                • Rejection preserves current record.<br>
                                • Decision logged to immutable audit trail.
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    if is_authorized_reviewer:
                        notes_key = f"notes_{req_id}"
                        notes = st.text_input("Reviewer Notes (Optional)", key=notes_key, placeholder="e.g. Prerequisites verified, academic standing good.")
                        
                        btn_col1, btn_col2, _ = st.columns([1, 1, 2])
                        with btn_col1:
                            if st.button(f"✅ Approve & Execute", key=f"app_{req_id}", type="primary", use_container_width=True):
                                try:
                                    res = process_approval_decision(
                                        request_id=req_id,
                                        reviewer_user=current_user,
                                        decision="APPROVED",
                                        reviewer_notes=notes,
                                    )
                                    st.success(f"Request {req_id} approved! Student record updated to '{new_prog}'.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Approval failed: {e}")

                        with btn_col2:
                            if st.button(f"❌ Reject Request", key=f"rej_{req_id}", type="secondary", use_container_width=True):
                                try:
                                    res = process_approval_decision(
                                        request_id=req_id,
                                        reviewer_user=current_user,
                                        decision="REJECTED",
                                        reviewer_notes=notes or "Application declined.",
                                    )
                                    st.warning(f"Request {req_id} rejected. Student record was not mutated.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Rejection failed: {e}")
                    else:
                        st.info("Log in as Support Staff (`support1`) or Admin Dean (`admin1`) in the Login tab to approve or reject this request.")

    with tab_history:
        if not all_requests:
            st.info("No approval requests have been submitted yet.")
        else:
            history_rows = []
            for r in all_requests:
                status_color = "#F59E0B" if r["status"] == "PENDING" else ("#10B981" if r["status"] == "APPROVED" else "#EF4444")
                history_rows.append({
                    "Request ID": r["request_id"],
                    "Student": r["student_id"],
                    "Current Programme": r.get("current_value"),
                    "Requested Programme": r.get("requested_value"),
                    "Status": r["status"],
                    "Reviewer": r.get("reviewer_id") or "Unreviewed",
                    "Notes": r.get("reviewer_notes") or "",
                    "Created": r.get("created_at", "")[:19].replace("T", " "),
                })
            
            import pandas as pd
            df = pd.DataFrame(history_rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
