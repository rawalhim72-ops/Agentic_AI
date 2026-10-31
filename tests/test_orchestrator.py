"""
Unit and integration tests for LangGraph Agent Orchestrator.
Tests end-to-end routing, tool execution, RAG retrieval, memory, and telemetry.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.orchestrator import run_agent
from database.db import get_db_session
from database.models import ConversationLog, SupportTicket, LongTermMemory
from memory.memory_manager import MemoryManager


def test_scenario_direct_math():
    res = run_agent("What is 2 + 2?", student_id="STU1001")
    assert res["status"] == "SUCCESS"
    assert res["intent"] == "DIRECT_ANSWER"
    assert len(res["tools_to_call"]) == 0
    assert "4" in res["final_response"]
    print("PASS: test_scenario_direct_math")


def test_scenario_fee_tool():
    res = run_agent("What is my current fee status?", student_id="STU1001")
    assert res["status"] == "SUCCESS"
    assert res["intent"] == "TOOL_CALL"
    assert len(res["tool_results"]) == 1
    assert res["tool_results"][0]["tool_name"] == "fee_status_checker"
    assert "150,000" in res["final_response"] or "150000" in res["final_response"]
    print("PASS: test_scenario_fee_tool")


def test_scenario_scholarship_tool():
    res = run_agent("What is my scholarship application status?", student_id="STU1001")
    assert res["status"] == "SUCCESS"
    assert res["intent"] == "TOOL_CALL"
    assert res["tool_results"][0]["tool_name"] == "scholarship_status_checker"
    assert "Merit Excellence" in res["final_response"]
    print("PASS: test_scenario_scholarship_tool")


def test_scenario_portal_failure_rag():
    res = run_agent("The payment portal failed. Can I pay on the next working day?", student_id="STU1001")
    assert res["status"] == "SUCCESS"
    assert res["intent"] == "RAG_RETRIEVAL"
    assert len(res["rag_chunks"]) > 0
    assert "next working day" in res["final_response"].lower()
    print("PASS: test_scenario_portal_failure_rag")


def test_scenario_out_of_handbook():
    res = run_agent("Tell me the policy for international student hostel refunds.", student_id="STU1001")
    assert res["status"] == "SUCCESS"
    assert res["intent"] == "RAG_RETRIEVAL"
    resp_lower = res["final_response"].lower()
    assert "does not provide" in resp_lower or "not contained" in resp_lower or "global relations" in resp_lower or "unavailable" in resp_lower
    print("PASS: test_scenario_out_of_handbook")


def test_scenario_create_support_ticket():
    res = run_agent("I want to raise a support request because my payment is not reflected.", student_id="STU1001")
    assert res["status"] == "SUCCESS"
    assert res["intent"] == "TOOL_CALL"
    assert res["tool_results"][0]["tool_name"] == "create_support_ticket"
    assert "TICK-" in res["final_response"]
    print("PASS: test_scenario_create_support_ticket")


def test_scenario_memory_two_sessions():
    student_id = "STU1001"
    MemoryManager.clear_student_memories(student_id)

    # Session 1
    s1 = run_agent("My preferred name is Rahul and I am studying MBA.", student_id=student_id, session_id="sess_1")
    assert s1["status"] == "SUCCESS"
    assert "Rahul" in s1["final_response"]

    # Session 2 (completely new session_id, no conversation history)
    s2 = run_agent("What programme am I studying?", student_id=student_id, session_id="sess_2", conversation_history=[])
    assert s2["status"] == "SUCCESS"
    assert "MBA" in s2["final_response"]
    assert len(s2["memories"]) >= 1
    print("PASS: test_scenario_memory_two_sessions")


def test_scenario_otp_rejection():
    student_id = "STU1001"
    res = run_agent("My OTP is 123456.", student_id=student_id)
    assert res["status"] == "SUCCESS"

    # Verify 123456 is NOT in SQLite long-term memory
    with get_db_session() as session:
        mems = session.query(LongTermMemory).filter(LongTermMemory.student_id == student_id).all()
        for m in mems:
            assert "123456" not in m.memory_value, "SECURITY BREACH: OTP was stored in memory!"
    print("PASS: test_scenario_otp_rejection")


def test_trace_persisted():
    with get_db_session() as session:
        count = session.query(ConversationLog).count()
        assert count > 0, "No traces were persisted in SQLite."
    print("PASS: test_trace_persisted")


if __name__ == "__main__":
    print("Running Orchestrator test suite...")
    test_scenario_direct_math()
    test_scenario_fee_tool()
    test_scenario_scholarship_tool()
    test_scenario_portal_failure_rag()
    test_scenario_out_of_handbook()
    test_scenario_create_support_ticket()
    test_scenario_memory_two_sessions()
    test_scenario_otp_rejection()
    test_trace_persisted()
    print("ALL ORCHESTRATOR TESTS PASSED!")
