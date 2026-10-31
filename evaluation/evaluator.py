"""
Automated Evaluation Suite for Intelligent Student Support Agent.
Executes all 9 required assignment scenarios, benchmarks latency, token usage,
evaluates decision appropriateness and factual grounding, and exports evaluation_report.csv.
"""

import sys
import os
import json
import time
import csv
from pathlib import Path
from typing import Dict, Any, List

# Ensure project root in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import settings
from agent.orchestrator import run_agent
from memory.memory_manager import MemoryManager
from database.db import get_db_session
from database.models import LongTermMemory


def run_evaluation() -> Dict[str, Any]:
    """Execute complete test suite against the live agent."""
    test_cases_path = BASE_DIR / "evaluation" / "test_cases.json"
    if not test_cases_path.exists():
        raise FileNotFoundError(f"Test cases file not found at {test_cases_path}")

    with open(test_cases_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    results = []
    total_tests = len(test_cases)
    passed_tests = 0

    print("================================================================================")
    print("      INTELLIGENT STUDENT SUPPORT AGENT - AUTOMATED EVALUATION SUITE           ")
    print("================================================================================")

    # For Test 4 and Test 5 session simulation:
    session_id_turn1 = "eval_session_alpha"
    session_id_turn2 = "eval_session_beta_isolated"

    for idx, tc in enumerate(test_cases, start=1):
        t_id = tc["test_id"]
        t_name = tc["name"]
        query = tc["query"]
        student_id = tc["student_id"]
        expected_intent = tc["expected_intent"]
        expected_tool = tc["expected_tool"]
        keywords = tc["expected_content_keywords"]

        print(f"\n[{t_id}] Running: {t_name}")
        print(f"       Query: \"{query}\"")

        # Determine session ID (turn 1 vs turn 2 for session isolation)
        if t_id == "TEST_4":
            MemoryManager.clear_student_memories(student_id)
            current_sess = session_id_turn1
        elif t_id == "TEST_5":
            current_sess = session_id_turn2  # Fresh session with ZERO prior conversation history
        else:
            current_sess = f"eval_sess_{idx}"

        start_time = time.time()
        agent_output = run_agent(
            query=query,
            student_id=student_id,
            session_id=current_sess,
            conversation_history=[] if t_id == "TEST_5" else None,
        )
        duration_ms = round((time.time() - start_time) * 1000, 2)

        actual_intent = agent_output.get("intent", "UNKNOWN")
        tools_called = [t.get("name") for t in agent_output.get("tools_to_call", [])]
        final_resp = agent_output.get("final_response", "")
        tokens = agent_output.get("token_usage", {})
        rag_chunks = agent_output.get("rag_chunks", [])
        evidence_ids = [c.get("chunk_id") for c in rag_chunks]

        # Validation Logic
        passed = True
        failure_reasons = []

        # 1. Intent check
        if actual_intent != expected_intent:
            passed = False
            failure_reasons.append(f"Intent mismatch: Expected {expected_intent}, got {actual_intent}")

        # 2. Tool check
        if expected_tool:
            if expected_tool not in tools_called:
                passed = False
                failure_reasons.append(f"Tool mismatch: Expected '{expected_tool}', called {tools_called}")
        else:
            if tools_called and expected_intent == "DIRECT_ANSWER":
                passed = False
                failure_reasons.append(f"Unnecessary tool executed: {tools_called}")

        # 3. Content grounding check
        lower_resp = final_resp.lower()
        keyword_matches = [kw for kw in keywords if kw.lower() in lower_resp]
        if not keyword_matches:
            passed = False
            failure_reasons.append(f"Response missing expected keywords {keywords}. Got: '{final_resp[:100]}...'")

        # 4. Special Security Check for TEST_9: Verify OTP was NOT saved to SQLite
        if t_id == "TEST_9":
            with get_db_session() as session:
                mems = session.query(LongTermMemory).filter(LongTermMemory.student_id == student_id).all()
                for m in mems:
                    if "123456" in m.memory_value:
                        passed = False
                        failure_reasons.append("SECURITY FAILURE: OTP was stored in SQLite long_term_memories table!")

        # 5. Special Session Check for TEST_5: Confirm info was retrieved from memory
        if t_id == "TEST_5":
            if not agent_output.get("memories"):
                passed = False
                failure_reasons.append("Memory was not retrieved in isolated session!")

        status_str = "PASS" if passed else "FAIL"
        if passed:
            passed_tests += 1
            print(f"       Result: [PASS] (Intent: {actual_intent}, Tools: {tools_called}, Latency: {duration_ms}ms, Tokens: {tokens.get('total_tokens', 0)})")
        else:
            print(f"       Result: [FAIL] - Reasons: {'; '.join(failure_reasons)}")

        results.append({
            "test_id": t_id,
            "test_name": t_name,
            "query": query,
            "expected_intent": expected_intent,
            "actual_intent": actual_intent,
            "expected_tool": expected_tool or "None",
            "actual_tools": ", ".join(tools_called) if tools_called else "None",
            "tool_selection_appropriate": "Yes" if (expected_tool in tools_called if expected_tool else not tools_called) else "No",
            "evidence_chunk_ids": ", ".join(evidence_ids) if evidence_ids else "None",
            "latency_ms": duration_ms,
            "input_tokens": tokens.get("input_tokens", 0),
            "output_tokens": tokens.get("output_tokens", 0),
            "total_tokens": tokens.get("total_tokens", 0),
            "status": status_str,
            "failure_reason": "; ".join(failure_reasons) if failure_reasons else "None",
            "response_preview": final_resp.replace("\n", " ")[:140],
        })

    # Save to CSV
    settings.EVALUATION_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_file = settings.EVALUATION_RESULTS_DIR / "evaluation_report.csv"

    fieldnames = [
        "test_id", "test_name", "query", "expected_intent", "actual_intent",
        "expected_tool", "actual_tools", "tool_selection_appropriate",
        "evidence_chunk_ids", "latency_ms", "input_tokens", "output_tokens",
        "total_tokens", "status", "failure_reason", "response_preview"
    ]

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    success_rate = round((passed_tests / total_tests) * 100, 1)

    print("\n================================================================================")
    print(f"   EVALUATION SUMMARY: {passed_tests}/{total_tests} Tests Passed ({success_rate}%)")
    print(f"   Detailed CSV report written to: {csv_file}")
    print("================================================================================")

    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": success_rate,
        "csv_path": str(csv_file),
    }


if __name__ == "__main__":
    res = run_evaluation()
    if res["passed_tests"] < res["total_tests"]:
        sys.exit(1)
