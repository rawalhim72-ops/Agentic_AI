"""
Agent Tracing and Telemetry Module.
Persists execution traces to SQLite, JSONL log files, and optionally Langfuse.
Records query, decisions, tools executed, retrieved evidence, latency, and token usage.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from config.settings import settings
from database.db import get_db_session
from database.models import ConversationLog
from monitoring.logger import log_structured_event

logger = logging.getLogger("monitoring.tracing")

# Initialize Langfuse client if configured
_langfuse_client = None
if settings.has_langfuse:
    try:
        from langfuse import Langfuse
        _langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
        logger.info("Langfuse tracing client successfully initialized.")
    except Exception as e:
        logger.warning(f"Could not initialize Langfuse ({e}). Falling back to local SQLite/JSON logging.")


def record_agent_trace(trace_data: Dict[str, Any]) -> str:
    """
    Persist complete agent execution trace into SQLite and local JSONL.
    Sends to Langfuse if configured.
    """
    trace_id = trace_data.get("trace_id") or str(uuid.uuid4())
    session_id = trace_data.get("session_id", "default_session")
    student_id = trace_data.get("student_id")
    query = trace_data.get("query", "")
    decision = trace_data.get("intent_decision", "DIRECT_ANSWER")
    tools_called = trace_data.get("tools_called", [])
    tool_results = trace_data.get("tool_results", [])
    rag_evidence = trace_data.get("retrieved_evidence", [])
    memories_used = trace_data.get("memory_retrieved", [])
    context_selected = trace_data.get("context_selected", {})
    response = trace_data.get("response", "")
    latency_ms = float(trace_data.get("latency_ms", 0.0))
    token_usage = trace_data.get("token_usage", {})
    in_tok = token_usage.get("input_tokens", 0)
    out_tok = token_usage.get("output_tokens", 0)
    tot_tok = token_usage.get("total_tokens", in_tok + out_tok)
    status = trace_data.get("status", "SUCCESS")
    err_msg = trace_data.get("error_message")

    # 1. SQLite Persistence
    try:
        with get_db_session() as session:
            log_entry = ConversationLog(
                trace_id=trace_id,
                session_id=session_id,
                student_id=student_id,
                query=query,
                intent_decision=decision,
                tools_called=json.dumps(tools_called, default=str),
                tool_results=json.dumps(tool_results, default=str),
                retrieved_evidence=json.dumps(rag_evidence, default=str),
                memory_retrieved=json.dumps(memories_used, default=str),
                context_selected=json.dumps(context_selected, default=str),
                response=response,
                latency_ms=latency_ms,
                input_tokens=in_tok,
                output_tokens=out_tok,
                total_tokens=tot_tok,
                status=status,
                error_message=err_msg,
                created_at=datetime.now(timezone.utc),
            )
            session.add(log_entry)
            session.flush()
    except Exception as e:
        logger.error(f"Error persisting trace to SQLite: {e}", exc_info=True)

    # 2. Local JSONL Structured Log
    log_structured_event("AGENT_EXECUTION_TRACE", {
        "trace_id": trace_id,
        "session_id": session_id,
        "student_id": student_id,
        "query": query,
        "decision": decision,
        "tools_called": tools_called,
        "retrieved_evidence_count": len(rag_evidence),
        "memories_count": len(memories_used),
        "latency_ms": latency_ms,
        "token_usage": {"input": in_tok, "output": out_tok, "total": tot_tok},
        "status": status,
        "error": err_msg,
    })

    # 3. Optional Langfuse Tracing
    if _langfuse_client:
        try:
            lf_trace = _langfuse_client.trace(
                id=trace_id,
                name="student_support_agent_query",
                session_id=session_id,
                user_id=student_id,
                input={"query": query},
                output={"response": response},
                metadata={
                    "intent": decision,
                    "tools": tools_called,
                    "evidence_count": len(rag_evidence),
                    "memories_count": len(memories_used),
                },
            )
            lf_trace.generation(
                name="agent_response_generation",
                model=settings.LLM_MODEL,
                usage={"input": in_tok, "output": out_tok, "total": tot_tok},
                output=response,
            )
        except Exception as e:
            logger.warning(f"Langfuse export skipped due to error: {e}")

    return trace_id


def get_recent_traces(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch recent execution traces from SQLite database."""
    with get_db_session() as session:
        logs = (
            session.query(ConversationLog)
            .order_by(ConversationLog.created_at.desc())
            .limit(limit)
            .all()
        )
        return [l.to_dict() for l in logs]
