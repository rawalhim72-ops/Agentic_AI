"""
Unit tests for Persistent Memory System.
Verifies extraction, sensitive data filtering (OTPs, passwords),
selective retrieval, and SQLite persistence.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from memory.memory_extractor import analyze_and_extract_memory
from memory.memory_manager import MemoryManager
from memory.memory_retriever import retrieve_relevant_memories
from database.db import get_db_session
from database.models import LongTermMemory


def test_extraction_name_and_programme():
    query = "My preferred name is Rahul and I am studying MBA."
    decisions = analyze_and_extract_memory(query)

    keys = [d.key for d in decisions if d.accepted]
    assert "preferred_name" in keys, "Failed to extract preferred name."
    assert "programme" in keys, "Failed to extract programme."

    # Verify extracted values
    for d in decisions:
        if d.key == "preferred_name":
            assert d.value == "Rahul"
        if d.key == "programme":
            assert d.value == "MBA"
    print("PASS: Extracted preferred_name and programme.")


def test_sensitive_otp_rejection():
    queries = [
        "My OTP is 123456.",
        "Here is my verification code 984321",
        "My net banking password is MySecretPass123",
    ]
    for q in queries:
        decisions = analyze_and_extract_memory(q)
        assert len(decisions) > 0
        assert not decisions[0].accepted, f"Expected rejection for sensitive query '{q}'"
        assert "Security filter" in decisions[0].reason or "sensitive" in decisions[0].reason.lower()
    print("PASS: Sensitive OTPs and passwords strictly rejected.")


def test_trivial_queries_rejected():
    queries = [
        "Hello!",
        "What is 2 + 2?",
        "Thank you very much",
    ]
    for q in queries:
        decisions = analyze_and_extract_memory(q)
        for d in decisions:
            assert not d.accepted, f"Trivial query should not be accepted: {q}"
    print("PASS: Trivial queries not stored.")


def test_persistent_memory_storage_and_retrieval():
    student_id = "STU1001"
    # Clear prior test memories for clean state
    MemoryManager.clear_student_memories(student_id)

    # Session 1: Student states name and programme
    s1_query = "My preferred name is Rahul and I am studying MBA."
    logs = MemoryManager.process_and_store_from_query(student_id, s1_query)
    assert len(logs) == 2, f"Expected 2 stored memories, got {logs}"

    # Verify in SQLite directly
    with get_db_session() as session:
        mems = session.query(LongTermMemory).filter(LongTermMemory.student_id == student_id).all()
        assert len(mems) == 2
        mem_map = {m.memory_key: m.memory_value for m in mems}
        assert mem_map["preferred_name"] == "Rahul"
        assert mem_map["programme"] == "MBA"

    # Session 2: New simulated session asks "What programme am I studying?"
    s2_query = "What programme am I studying?"
    retrieval = retrieve_relevant_memories(student_id, s2_query)
    assert retrieval["status"] == "SUCCESS"
    assert len(retrieval["memories"]) >= 1

    retrieved_keys = [m["memory_key"] for m in retrieval["memories"]]
    assert "programme" in retrieved_keys
    print(f"PASS: Session 2 retrieved programme '{retrieval['memories'][0]['memory_value']}' from persistent SQLite memory.")


def test_no_duplicate_memories():
    student_id = "STU1001"
    # Store updated preference
    MemoryManager.save_or_update_memory(student_id, "response_style", "concise")
    MemoryManager.save_or_update_memory(student_id, "response_style", "bullet points")

    with get_db_session() as session:
        count = session.query(LongTermMemory).filter(
            LongTermMemory.student_id == student_id,
            LongTermMemory.memory_key == "response_style",
        ).count()
        assert count == 1, f"Expected exactly 1 record for response_style, found {count}"
    print("PASS: No duplicate memories created on update.")


if __name__ == "__main__":
    print("Running Memory test suite...")
    test_extraction_name_and_programme()
    test_sensitive_otp_rejection()
    test_trivial_queries_rejected()
    test_persistent_memory_storage_and_retrieval()
    test_no_duplicate_memories()
    print("ALL MEMORY TESTS PASSED!")
