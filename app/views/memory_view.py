"""
Long-Term Memory Management View for Streamlit.
Provides inspection, manual addition, deletion, and privacy filtering audit for persistent memories.
All operations persist in the SQLite long_term_memories table across sessions.
"""

import streamlit as st
import pandas as pd
from memory.memory_manager import MemoryManager
from memory.memory_extractor import analyze_and_extract_memory


def render_memory_view():
    """Renders the memory management interface."""
    st.markdown('<div class="enterprise-badge">● Persistent State & Privacy Filter</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="margin-bottom: 1.2rem;">
            <h1 style="font-size: 1.85rem; font-weight: 800; margin: 0; color: #F8FAFC; letter-spacing: -0.02em;">
                Long-Term Memory & Privacy Audit
            </h1>
            <p style="font-size: 0.88rem; color: #94A3B8; margin: 4px 0 0 0;">
                Persistent profile attributes stored in SQLite across sessions. Sensitive information (passwords, OTPs, PINs) is strictly filtered.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    student_id = st.session_state.get("student_id", "STU1001")
    active_student = st.session_state.get("active_student", {})

    memories = MemoryManager.get_all_memories(student_id=student_id)

    # Top KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Active Student</div>
                <div class="stat-value" style="font-size: 1.25rem;">{active_student.get('name', 'Student')}</div>
                <div class="stat-subtitle">ID: {student_id}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Stored Memories</div>
                <div class="stat-value">{len(memories)}</div>
                <div class="stat-subtitle">Persistent SQLite items</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class="stat-card">
                <div class="stat-label">Privacy Shield</div>
                <div class="stat-value" style="color: #10B981;">Active</div>
                <div class="stat-subtitle">OTPs, credentials blocked</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">Programme</div>
                <div class="stat-value" style="font-size: 1.2rem; color: #60A5FA;">{active_student.get('programme', 'Degree')}</div>
                <div class="stat-subtitle">{active_student.get('department', 'Academic Dept')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # Stored Memories Table & Actions
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader(f"🧠 Persistent Memories for {active_student.get('name', 'Selected Student')}")
    st.caption("These attributes persist after application restarts and are selectively injected into the agent's context when relevant.")

    if memories:
        df_mem = pd.DataFrame(memories)
        st.dataframe(
            df_mem[["id", "memory_key", "memory_value", "confidence", "source_query", "updated_at"]],
            use_container_width=True,
            hide_index=True,
        )

        col_del, col_clear = st.columns([2, 1])
        with col_del:
            del_id = st.selectbox(
                "Select Memory ID to Delete",
                [m["id"] for m in memories],
                format_func=lambda x: f"ID #{x} ({next(m['memory_key'] for m in memories if m['id'] == x)}: {next(m['memory_value'] for m in memories if m['id'] == x)})",
            )
            if st.button("🗑️ Delete Selected Memory", type="secondary"):
                with st.spinner("Deleting record from SQLite..."):
                    success = MemoryManager.delete_memory(del_id)
                if success:
                    st.success(f"Memory #{del_id} deleted successfully.")
                    st.rerun()
                else:
                    st.error("Failed to delete memory record.")

        with col_clear:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("⚠️ Clear All Memories for Student", type="secondary"):
                with st.spinner("Clearing student memories..."):
                    count = MemoryManager.clear_student_memories(student_id)
                st.warning(f"Cleared {count} persistent memories for {student_id}.")
                st.rerun()
    else:
        st.info(f"No persistent memories stored yet for {student_id}. Switch to Chat and tell the agent 'My preferred name is Rahul and I am studying MBA' or add one manually below!")

    # Manual Add Memory Form
    with st.expander("➕ Add New Persistent Memory Manually"):
        col_k, col_v = st.columns(2)
        with col_k:
            new_key = st.selectbox("Memory Attribute Key", ["preferred_name", "programme", "response_style", "academic_interest", "career_goal"])
        with col_v:
            new_val = st.text_input("Memory Attribute Value", placeholder="e.g. Rahul, MBA, concise bullet points, Machine Learning")

        if st.button("💾 Save Attribute to SQLite"):
            if new_val.strip():
                with st.spinner("Saving attribute to persistent SQLite..."):
                    saved = MemoryManager.save_or_update_memory(
                        student_id=student_id,
                        memory_key=new_key,
                        memory_value=new_val.strip(),
                        source_query="Manual entry via Memory Management UI",
                    )
                st.success(f"Saved memory: `{new_key}` = `{new_val.strip()}` (ID #{saved.get('id')})")
                st.rerun()
            else:
                st.error("Please enter a valid memory value.")

    st.markdown("</div>", unsafe_allow_html=True)

    # Privacy Filter Sandbox / Live Demonstration
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("🛡️ Memory Extraction & Sensitive Information Filter Test")
    st.caption("Test how the extraction engine safely accepts legitimate academic preferences while strictly blocking sensitive credentials (OTPs, passwords, tokens).")

    # Preset test buttons
    st.markdown("**Quick Preset Scenarios:**")
    preset_cols = st.columns(3)
    preset_input = None
    with preset_cols[0]:
        if st.button("📋 Test Valid Profile Statement"):
            preset_input = "My preferred name is Rahul and I am studying MBA."
    with preset_cols[1]:
        if st.button("🚨 Test Sensitive OTP Attempt"):
            preset_input = "My OTP is 123456."
    with preset_cols[2]:
        if st.button("🔒 Test Password Attempt"):
            preset_input = "My netbanking password is SecretPass123"

    test_input = st.text_input(
        "Enter text to test extraction & privacy filter:",
        value=preset_input or "My preferred name is Rahul and my OTP is 123456.",
        key="privacy_test_input_box",
    )

    if st.button("🧪 Analyze & Audit Extraction"):
        with st.spinner("Analyzing text against sensitive & entity patterns..."):
            decisions = analyze_and_extract_memory(test_input)

        if decisions:
            for d in decisions:
                if d.accepted:
                    st.success(f"✅ **ACCEPTED & SAFE:** Key: `{d.key}` | Value: `{d.value}`\n\n*Audit Reason:* {d.reason}")
                else:
                    st.error(f"🛑 **REJECTED (PRIVACY SHIELD ACTIVATED):** Key: `{d.key}`\n\n*Security Reason:* {d.reason}")
        else:
            st.warning("No extractable facts or entities found in this input.")
    st.markdown("</div>", unsafe_allow_html=True)
