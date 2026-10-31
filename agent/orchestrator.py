"""
LangGraph Agent Orchestration Engine.
Assembles StateGraph with intent routing, tool execution, RAG, memory,
context selection, grounded generation, and telemetry logging.
"""

import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END

from agent.state import AgentState
from agent.nodes import (
    intent_analyzer_node,
    tool_executor_node,
    rag_retrieval_node,
    memory_retrieval_node,
    context_selector_node,
    llm_generator_node,
    trace_logger_node,
)

logger = logging.getLogger("agent.orchestrator")


def route_by_intent(state: AgentState) -> str:
    """Conditional router based on intent analysis."""
    intent = state.get("intent", "DIRECT_ANSWER")
    if intent in ["TOOL_CALL", "COMPOSITE"]:
        return "tool_executor"
    elif intent in ["RAG_RETRIEVAL", "POLICY_QUERY"]:
        return "rag_retriever"
    else:
        return "memory_retriever"


def route_after_tool_execution(state: AgentState) -> str:
    """Conditional router following tool execution."""
    if state.get("intent") == "COMPOSITE":
        return "rag_retriever"
    return "memory_retriever"


def build_agent_graph():
    """Build and compile the LangGraph agent workflow."""
    workflow = StateGraph(AgentState)

    # 1. Register Nodes
    workflow.add_node("intent_analyzer", intent_analyzer_node)
    workflow.add_node("tool_executor", tool_executor_node)
    workflow.add_node("rag_retriever", rag_retrieval_node)
    workflow.add_node("memory_retriever", memory_retrieval_node)
    workflow.add_node("context_selector", context_selector_node)
    workflow.add_node("llm_generator", llm_generator_node)
    workflow.add_node("trace_logger", trace_logger_node)

    # 2. Set Entry Point
    workflow.set_entry_point("intent_analyzer")

    # 3. Add Edges & Conditional Branches
    workflow.add_conditional_edges(
        "intent_analyzer",
        route_by_intent,
        {
            "tool_executor": "tool_executor",
            "rag_retriever": "rag_retriever",
            "memory_retriever": "memory_retriever",
        },
    )

    workflow.add_conditional_edges(
        "tool_executor",
        route_after_tool_execution,
        {
            "rag_retriever": "rag_retriever",
            "memory_retriever": "memory_retriever",
        },
    )

    workflow.add_edge("rag_retriever", "memory_retriever")
    workflow.add_edge("memory_retriever", "context_selector")
    workflow.add_edge("context_selector", "llm_generator")
    workflow.add_edge("llm_generator", "trace_logger")
    workflow.add_edge("trace_logger", END)

    return workflow.compile()


# Singleton compiled graph instance
agent_app = build_agent_graph()


def run_agent(
    query: Optional[str] = None,
    student_id: Optional[str] = "STU1001",
    session_id: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    caller_user: Optional[Dict[str, Any]] = None,
    user_message: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main execution interface for Streamlit and automated evaluation.
    Invokes the compiled LangGraph workflow and returns complete execution state.
    Binds authenticated caller_user for owner-based isolation and auditing.
    """
    active_query = query or user_message or ""
    start_total_time = time.time()
    trace_id = str(uuid.uuid4())
    s_id = session_id or f"sess_{str(uuid.uuid4())[:8]}"

    resolved_student_id = (
        caller_user.get("student_id")
        if (caller_user and caller_user.get("role") == "STUDENT" and caller_user.get("student_id"))
        else (student_id or "STU1001")
    )

    initial_state: AgentState = {
        "trace_id": trace_id,
        "session_id": s_id,
        "student_id": resolved_student_id,
        "caller_user": caller_user,
        "query": active_query,
        "conversation_history": conversation_history or [],
        "intent": "DIRECT_ANSWER",
        "decision_reasoning": "",
        "tools_to_call": [],
        "tool_results": [],
        "rag_chunks": [],
        "memories": [],
        "memory_storage_logs": [],
        "selected_context": {},
        "final_response": "",
        "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        "latency_ms": 0.0,
        "status": "SUCCESS",
        "error_message": None,
    }

    try:
        logger.info(f"Invoking Agent for query: '{active_query}' (student: {student_id})")
        final_state = agent_app.invoke(initial_state)
        total_latency = round((time.time() - start_total_time) * 1000, 2)
        final_state["latency_ms"] = total_latency
        tool_results = final_state.get("tool_results", [])
        final_state["tool_called"] = tool_results[0].get("tool_name") if tool_results else None
        return final_state
    except Exception as e:
        logger.error(f"Agent orchestration failed: {e}", exc_info=True)
        return {
            "trace_id": trace_id,
            "session_id": s_id,
            "student_id": student_id,
            "query": query,
            "intent": "ERROR",
            "decision_reasoning": "Uncaught exception in agent workflow.",
            "tools_to_call": [],
            "tool_results": [],
            "rag_chunks": [],
            "memories": [],
            "selected_context": {},
            "final_response": f"An unexpected system error occurred: {str(e)}",
            "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "latency_ms": round((time.time() - start_total_time) * 1000, 2),
            "status": "ERROR",
            "error_message": str(e),
        }
