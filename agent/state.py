"""
Agent State Definition for LangGraph StateGraph.
Tracks all data flowing through orchestrator, nodes, tool executions, RAG, and telemetry.
"""

from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    # Session & Identity
    trace_id: str
    session_id: str
    student_id: Optional[str]
    caller_user: Optional[Dict[str, Any]]
    query: str
    conversation_history: List[Dict[str, str]]

    # Agent Decision & Reasoning
    intent: str  # DIRECT_ANSWER, TOOL_CALL, RAG_RETRIEVAL, COMPOSITE, CLARIFICATION_NEEDED
    decision_reasoning: str
    tools_to_call: List[Dict[str, Any]]
    
    # Executed Evidence & Results
    tool_results: List[Dict[str, Any]]
    rag_chunks: List[Dict[str, Any]]
    memories: List[Dict[str, Any]]
    memory_storage_logs: List[Dict[str, Any]]
    
    # Context Selection (audit of selected components)
    selected_context: Dict[str, Any]
    
    # Response Generation
    final_response: str
    token_usage: Dict[str, int]
    latency_ms: float
    status: str  # SUCCESS, ERROR
    error_message: Optional[str]
