"""
Chat View Component for Streamlit.
Provides rich chat bubbles, quick prompt suggestions, interactive agent activity inspection,
real-time execution status tracking, and observable telemetry.
"""

import time
import json
import streamlit as st
from agent.orchestrator import run_agent


def execute_agent_with_live_status(prompt_text: str, student_id: str):
    """
    Executes the agent while displaying real-time observable execution steps.
    Satisfies Requirement 3 (Real-time agent execution status) and Requirement 9 (Clear states).
    """
    st.session_state.messages.append({"role": "user", "content": prompt_text})

    with st.status("🤖 Agent Orchestrating Workflow...", expanded=True) as status_box:
        st.write("🔍 **Step 1:** Analyzing student query intent & academic context...")
        time.sleep(0.08)

        # Resolve caller_user from authenticated session or active profile
        caller_user = st.session_state.get("authenticated_user")
        if not caller_user:
            active_s = st.session_state.get("active_student", {})
            caller_user = {
                "username": (student_id or "stu1001").lower(),
                "role": "STUDENT",
                "student_id": student_id or "STU1001",
                "display_name": active_s.get("name", "Student"),
            }

        # Run the full LangGraph orchestrator
        agent_result = run_agent(
            query=prompt_text,
            student_id=student_id,
            session_id=st.session_state.session_id,
            conversation_history=st.session_state.messages[:-1],
            caller_user=caller_user,
        )

        intent = agent_result.get("intent", "DIRECT_ANSWER")
        reasoning = agent_result.get("decision_reasoning", "")
        st.write(f"⚙️ **Step 2: Routing Decision** → `{intent}` (*{reasoning}*)")

        # Tool execution details
        tool_results = agent_result.get("tool_results", [])
        if tool_results:
            for tr in tool_results:
                t_name = tr.get("tool_name")
                exec_res = tr.get("execution_result", {})
                t_status = exec_res.get("status", "SUCCESS")
                st.write(f"🛠️ **Step 3: Tool Invoked** → `{t_name}` | Status: **{t_status}**")
        elif intent == "RAG_RETRIEVAL":
            chunks = agent_result.get("rag_chunks", [])
            st.write(f"📚 **Step 3: Policy RAG** → Retrieved **{len(chunks)} grounded chunks** from `student_handbook.pdf`")

        # Memory check
        memories = agent_result.get("memories", [])
        storage_logs = agent_result.get("memory_storage_logs", [])
        if memories:
            mem_summary = ", ".join([f"{m.get('memory_key')}='{m.get('memory_value')}'" for m in memories])
            st.write(f"🧠 **Step 4: Persistent Memory Retrieved** → `{mem_summary}`")
        if storage_logs:
            for log in storage_logs:
                if log.get("action") == "ACCEPTED_AND_STORED":
                    st.write(f"💾 **Step 4: Persistent Memory Saved** → Stored `{log.get('key')}` = `{log.get('value')}` in SQLite")
                elif "SENSITIVE" in str(log.get("key", "")):
                    st.write(f"🛡️ **Step 4: Privacy Shield Activated** → Blocked sensitive credential ({log.get('reason')})")

        latency = agent_result.get("latency_ms", 0.0)
        tokens = agent_result.get("token_usage", {}).get("total_tokens", 0)
        st.write(f"✍️ **Step 5: Response Grounded & Synthesized** (Completed in **{latency:.1f}ms**, **{tokens} tokens**)")

        status_box.update(
            label=f"✅ Agent Response Ready ({intent} • {latency:.0f}ms)",
            state="complete",
            expanded=False,
        )

    # Append Assistant Message
    st.session_state.messages.append({
        "role": "assistant",
        "content": agent_result["final_response"],
        "trace": agent_result,
    })
    st.rerun()


def render_chat_view():
    """Render the primary intelligent student support chat interface."""
    # Initialize session state for messages and session ID
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"sess_{int(time.time())}"

    active_student = st.session_state.get("active_student", {})
    student_id = st.session_state.get("student_id", "STU1001")
    student_name = active_student.get("name", "Student")
    student_prog = active_student.get("programme", "Degree Programme")
    student_dept = active_student.get("department", "Department")

    # Look up if student has an active preferred name in persistent memory
    preferred_name = ""
    try:
        from memory.memory_manager import retrieve_relevant_memories
        mem_lookup = retrieve_relevant_memories(student_id, "preferred name")
        for m in mem_lookup.get("memories", []):
            if m.get("memory_key") == "preferred_name":
                preferred_name = m.get("memory_value", "")
                break
    except Exception:
        pass

    display_name_html = f"<b>{student_name}</b>"
    if preferred_name and preferred_name.lower() != student_name.lower():
        display_name_html += f" (Preferred: <i>{preferred_name}</i>)"
    display_greeting = preferred_name if preferred_name else student_name.split()[0]

    # Header
    st.markdown('<div class="enterprise-badge">● Autonomous Multi-Tool Agent</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 1.2rem; flex-wrap: wrap; gap: 10px;">
            <div>
                <h1 style="font-size: 1.85rem; font-weight: 800; margin: 0; color: #F8FAFC; letter-spacing: -0.02em;">
                    Student Support Concierge
                </h1>
                <p style="font-size: 0.88rem; color: #94A3B8; margin: 4px 0 0 0;">
                    Connected for {display_name_html} ({student_id}) <span style="font-size: 0.72rem; background: rgba(59,130,246,0.2); color: #93C5FD; padding: 1px 6px; border-radius: 4px;">Demo Persona</span> • {student_prog} • {student_dept}
                </p>
            </div>
            <div>
                <span class="status-pill status-tool-success">● System Online</span>
                <span class="status-pill status-rag">● FAISS Vector Store</span>
                <span class="status-pill status-memory">● SQLite Memory</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Welcome Card if conversation is empty
    if not st.session_state.messages:
        st.markdown(
            f"""
            <div class="glass-card" style="border-left: 4px solid #3B82F6;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">
                    <div style="font-weight: 700; font-size: 1.15rem; color: #F1F5F9;">
                        Welcome back, {display_greeting}! How can I help you today?
                    </div>
                    <span style="font-size: 0.75rem; background: rgba(59, 130, 246, 0.15); color: #93C5FD; padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(59, 130, 246, 0.3);">
                        Student ID: {student_id} [Demo]
                    </span>
                </div>
                <div style="font-size: 0.88rem; color: #CBD5E1; line-height: 1.55; margin-bottom: 14px;">
                    I am your Intelligent Student Support Assistant. I autonomously coordinate between real-time university database records,
                    official student handbook policy documents, and your persistent academic profile to answer questions and resolve requests.
                </div>
                <div style="font-size: 0.78rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; margin-bottom: 8px;">
                    ⚡ Suggested Quick Actions (Click to Test):
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        suggestions = [
            ("💳 What is my current fee status?", "What is my current fee status?", "Queries real-time SQLite fee ledger for tuition, balance, and due date."),
            ("🎓 What is my scholarship application status?", "What is my scholarship application status?", "Queries scholarship registry for grant approval status and award amount."),
            ("⏳ Payment portal failed. Can I pay on next working day?", "The payment portal failed. Can I pay on the next working day?", "Retrieves Section 3 of Student Policy Handbook via FAISS RAG."),
            ("🔄 How can I change my course or programme?", "How can I change my course?", "Retrieves Add/Drop and transfer criteria from the student handbook."),
            ("🎫 Raise support ticket for payment discrepancy", "I want to raise a support request because my payment is not reflected.", "Executes ticket creation tool and persists ticket in SQLite."),
            ("🧠 Store my name and MBA programme in memory", "My preferred name is Rahul and I am studying MBA.", "Tests persistent memory extraction and SQLite storage across sessions."),
        ]

        for idx, (label, prompt_text, subdesc) in enumerate(suggestions):
            target_col = col1 if idx % 2 == 0 else col2
            with target_col:
                if st.button(label, key=f"quick_prompt_{idx}", use_container_width=True):
                    execute_agent_with_live_status(prompt_text, student_id)
                st.caption(f"ℹ️ *{subdesc}*")

    # Render Chat History
    for idx, msg in enumerate(st.session_state.messages):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        trace = msg.get("trace")

        with st.chat_message(role, avatar="🧑‍🎓" if role == "user" else "🤖"):
            st.markdown(content)

            # If assistant message has trace data, show operational status pills and expandable audit box
            if trace:
                intent = trace.get("intent", "DIRECT_ANSWER")
                tools_called = trace.get("tools_to_call", [])
                tool_results = trace.get("tool_results", [])
                rag_chunks = trace.get("rag_chunks", [])
                memories = trace.get("memories", [])
                storage_logs = trace.get("memory_storage_logs", [])
                context_audit = trace.get("selected_context", {}).get("audit", {})
                latency = trace.get("latency_ms", 0.0)
                tokens = trace.get("token_usage", {})

                # Render Visible Real-Time Status Pills (Requirements 4, 5, 6)
                status_pills_html = []

                # Tool Status (Requirement 4)
                if tool_results:
                    for tr in tool_results:
                        t_name = tr.get("tool_name", "tool")
                        exec_res = tr.get("execution_result", {})
                        t_status = exec_res.get("status", "SUCCESS")
                        if t_status == "SUCCESS":
                            status_pills_html.append(f'<span class="status-pill status-tool-success">🛠️ Tool: <b>{t_name}</b> (SUCCESS)</span>')
                        elif t_status == "NO_SCHOLARSHIP":
                            status_pills_html.append(f'<span class="status-pill status-rag">🛠️ Tool: <b>{t_name}</b> (NO RECORD)</span>')
                        else:
                            status_pills_html.append(f'<span class="status-pill status-tool-fail">⚠️ Tool: <b>{t_name}</b> ({t_status})</span>')
                elif intent == "DIRECT_ANSWER":
                    status_pills_html.append('<span class="status-pill status-rag">💬 Direct Synthesis (No Tools Needed)</span>')

                # RAG Retrieval Status (Requirement 5)
                if rag_chunks:
                    doc_name = rag_chunks[0].get("source", "student_handbook.pdf")
                    status_pills_html.append(f'<span class="status-pill status-rag">📚 Policy RAG: <b>{len(rag_chunks)} Chunks</b> from <code>{doc_name}</code></span>')

                # Memory Status (Requirement 6)
                if memories:
                    mem_keys = ", ".join([m.get("memory_key") for m in memories])
                    status_pills_html.append(f'<span class="status-pill status-memory">🧠 Memory Retrieved: <b>{mem_keys}</b></span>')
                if storage_logs:
                    for s_log in storage_logs:
                        if s_log.get("action") == "ACCEPTED_AND_STORED":
                            status_pills_html.append(f'<span class="status-pill status-memory">💾 Memory Saved: <b>{s_log.get("key")}</b></span>')
                        elif "SENSITIVE" in str(s_log.get("key", "")):
                            status_pills_html.append('<span class="status-pill status-tool-fail">🛡️ Sensitive OTP Shielded</span>')

                # Telemetry Pill
                status_pills_html.append(f'<span class="status-pill" style="background: rgba(255,255,255,0.08); color: #E2E8F0;">⏱️ {latency:.1f}ms • 🔤 {tokens.get("total_tokens", 0)} tokens</span>')

                st.markdown(f'<div style="margin-top: 8px; margin-bottom: 6px; display: flex; flex-wrap: wrap; gap: 4px;">{"".join(status_pills_html)}</div>', unsafe_allow_html=True)

                # Expandable Agent Activity Inspection Card
                with st.expander(f"🔍 Agent Activity & Observable Trace • Decision: {intent} • {latency:.0f}ms"):
                    st.markdown(f"**Intent Analysis Reasoning:** {trace.get('decision_reasoning', 'N/A')}")

                    tab_tool, tab_rag, tab_mem, tab_ctx = st.tabs([
                        f"🛠️ Tool Telemetry ({len(tool_results)})",
                        f"📚 Policy Evidence ({len(rag_chunks)})",
                        f"🧠 Memory Audit ({len(memories) + len(storage_logs)})",
                        "📦 Context Selection",
                    ])

                    with tab_tool:
                        if tool_results:
                            for tr in tool_results:
                                t_name = tr.get("tool_name")
                                res_obj = tr.get("execution_result", {})
                                st.markdown(f"**Tool:** `{t_name}` | **Status:** `{res_obj.get('status')}` | **Latency:** `{res_obj.get('latency_ms', 0)} ms`")
                                st.json(res_obj)
                        else:
                            st.info("No external tools were required. The agent determined direct answering or policy retrieval was appropriate.")

                    with tab_rag:
                        if rag_chunks:
                            st.markdown(f"**Source Document:** `{rag_chunks[0].get('source', 'student_handbook.pdf')}`")
                            for idx_c, c in enumerate(rag_chunks, start=1):
                                st.markdown(
                                    f"""
                                    <div class="trace-box" style="border-left: 3px solid #10B981; margin-bottom: 8px;">
                                        <b>Evidence #{idx_c}</b> | <b>Document:</b> <code>{c.get('source')}</code> | <b>Page:</b> {c.get('page_number')} | <b>Chunk ID:</b> <code>{c.get('chunk_id')}</code> | <b>Distance:</b> {c.get('distance_score', 0):.4f}<br/>
                                        <div style="margin-top: 5px; color: #F1F5F9; font-style: italic;">"{c.get('text')}"</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.info("No RAG policy chunks were retrieved for this inquiry.")

                    with tab_mem:
                        has_mem_activity = False
                        if memories:
                            has_mem_activity = True
                            st.markdown("**🧠 Retrieved Long-Term Memories (from prior interactions):**")
                            for m in memories:
                                st.markdown(f"- **{m.get('memory_key', '').replace('_', ' ').title()}:** `{m.get('memory_value')}` *(Source: {m.get('source_query')})*")

                        if storage_logs:
                            has_mem_activity = True
                            st.markdown("**💾 Memory Extraction & Privacy Filter Actions:**")
                            for s_log in storage_logs:
                                if s_log.get("action") == "ACCEPTED_AND_STORED":
                                    st.success(f"✅ **Saved:** `{s_log.get('key')}` = `{s_log.get('value')}` (*{s_log.get('reason')}*)")
                                else:
                                    st.warning(f"🛑 **Blocked:** `{s_log.get('key')}` (*{s_log.get('reason')}*)")

                        if not has_mem_activity:
                            st.info("No memory retrieval or updates were triggered for this query.")

                    with tab_ctx:
                        if context_audit:
                            st.markdown(f"**Context Sources Injected into Prompt:** `{', '.join(context_audit.get('sources_used', []))}`")
                            st.markdown(f"- Tools included: {context_audit.get('tool_count', 0)}")
                            st.markdown(f"- RAG chunks included: {context_audit.get('rag_chunk_count', 0)}")
                            st.markdown(f"- Memories included: {context_audit.get('memory_item_count', 0)}")
                            st.markdown(f"- Recent conversation turns: {context_audit.get('history_turns_count', 0)}")

    # Chat Input Box at Bottom
    user_prompt = st.chat_input("Ask about fee deadlines, scholarships, academic policies, or support tickets...")
    if user_prompt:
        execute_agent_with_live_status(user_prompt, student_id)
