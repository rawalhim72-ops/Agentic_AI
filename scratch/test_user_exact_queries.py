"""
Verification Script for User's Exact Test Queries.
Tests:
A. "Hello"
B. "What is the admission process?"
C. "What documents are required for admission?"
D. "What is my fee status?"
E. "What is my scholarship status?"
F. "What is the next working day payment policy?"
Plus the original bug queries:
G. "My name is Himanshu and I want to know the admission process."
H. "I want to know admission process."
"""

import sys
import json
import time
from pathlib import Path

# Add project root
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agent.orchestrator import run_agent
from memory.memory_manager import MemoryManager

def run_test_suite():
    # Clear test memories for clean run
    MemoryManager.clear_student_memories("STU1001")

    test_queries = [
        {"id": "A", "query": "Hello", "expected_intent": "DIRECT_ANSWER"},
        {"id": "B", "query": "What is the admission process?", "expected_intent": "RAG_RETRIEVAL"},
        {"id": "C", "query": "What documents are required for admission?", "expected_intent": "RAG_RETRIEVAL"},
        {"id": "D", "query": "What is my fee status?", "expected_intent": "TOOL_CALL"},
        {"id": "E", "query": "What is my scholarship status?", "expected_intent": "TOOL_CALL"},
        {"id": "F", "query": "What is the next working day payment policy?", "expected_intent": "RAG_RETRIEVAL"},
        {"id": "G", "query": "My name is Himanshu and I want to know the admission process.", "expected_intent": "RAG_RETRIEVAL"},
        {"id": "H", "query": "I want to know admission process.", "expected_intent": "RAG_RETRIEVAL"},
    ]

    results = []

    print("=" * 80)
    print("STARTING EXACT USER QUERIES VERIFICATION SUITE")
    print("=" * 80)

    for item in test_queries:
        t_id = item["id"]
        q = item["query"]
        exp_intent = item["expected_intent"]

        print(f"\n--- Running Test {t_id}: '{q}' ---")
        start = time.time()
        res = run_agent(query=q, student_id="STU1001", session_id=f"verify_{t_id}")
        dur = round((time.time() - start) * 1000, 2)

        intent = res.get("intent")
        tools_called = [t.get("name") for t in res.get("tools_to_call", [])]
        tool_results = res.get("tool_results", [])
        rag_chunks = res.get("rag_chunks", [])
        memories = res.get("memories", [])
        memory_logs = res.get("memory_storage_logs", [])
        final_resp = res.get("final_response", "")
        tokens = res.get("token_usage", {})
        latency = res.get("latency_ms", dur)

        # Determine retrieval or tool action summary
        action = "NONE"
        evidence_summary = []
        if tools_called:
            action = f"Tool Execution: {', '.join(tools_called)}"
            for tr in tool_results:
                evidence_summary.append(f"Tool {tr.get('tool_name')}: {json.dumps(tr.get('execution_result', {}))}")
        elif rag_chunks:
            action = f"RAG Retrieval ({len(rag_chunks)} chunks)"
            for rc in rag_chunks:
                evidence_summary.append(f"[{rc.get('chunk_id')} | Page {rc.get('page_number')}]: {rc.get('text')[:120]}...")
        elif intent == "DIRECT_ANSWER":
            action = "Direct Answer Generation (No DB/RAG needed)"

        # Check pass criteria
        passed = True
        notes = []

        if intent != exp_intent:
            passed = False
            notes.append(f"Intent mismatch: got {intent}, expected {exp_intent}")

        # Check for generic welcome response bug
        generic_welcome_signature = "Hello! I am your Intelligent Student Support Assistant. I can assist you with real-time fee balances"
        if q != "Hello" and generic_welcome_signature in final_resp:
            passed = False
            notes.append("FAILED: Substantive question returned generic welcome message!")

        # Check specific answers
        if t_id == "A":
            if "Hello!" not in final_resp:
                passed = False
                notes.append("Expected greeting response")
        elif t_id in ["B", "G", "H"]:
            if not ("online application" in final_resp.lower() or "entrance" in final_resp.lower() or "stage" in final_resp.lower() or "admissions" in final_resp.lower()):
                passed = False
                notes.append("Expected admission process content")
        elif t_id == "C":
            if not ("marksheet" in final_resp.lower() or "documents" in final_resp.lower() or "certificate" in final_resp.lower() or "verification" in final_resp.lower()):
                passed = False
                notes.append("Expected documents list")
        elif t_id == "D":
            if not ("fee status" in final_resp.lower() or "150,000" in final_resp or "balance" in final_resp.lower()):
                passed = False
                notes.append("Expected fee details")
        elif t_id == "E":
            if not ("scholarship" in final_resp.lower() or "merit" in final_resp.lower()):
                passed = False
                notes.append("Expected scholarship details")
        elif t_id == "F":
            if not ("next working day" in final_resp.lower() or "without penalty" in final_resp.lower()):
                passed = False
                notes.append("Expected next working day policy")

        status_str = "PASS" if passed else "FAIL"
        print(f"STATUS: {status_str}")
        print(f"Detected Intent: {intent}")
        print(f"Action: {action}")
        print(f"Evidence count: {len(evidence_summary)}")
        print(f"Final Answer: {final_resp[:180]}...")
        print(f"Latency: {latency} ms | Tokens: {tokens}")

        results.append({
            "test_id": t_id,
            "query": q,
            "status": status_str,
            "detected_intent": intent,
            "action": action,
            "evidence": evidence_summary,
            "final_answer": final_resp,
            "latency_ms": latency,
            "token_usage": tokens,
            "notes": notes,
        })

    # Save detailed JSON report
    out_file = BASE_DIR / "evaluation" / "results" / "bugfix_verification_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print(f"VERIFICATION COMPLETE. All results saved to {out_file}")
    all_passed = all(r["status"] == "PASS" for r in results)
    print(f"OVERALL RESULT: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 80)

if __name__ == "__main__":
    run_test_suite()
