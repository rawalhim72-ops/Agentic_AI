"""
Structured Logging Module.
Writes JSONL logs to disk for all agent executions, tool calls, and error events.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from config.settings import settings

logger = logging.getLogger("student_support.monitoring")

# Ensure logs directory
settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
JSONL_LOG_PATH = settings.LOGS_DIR / "agent_traces.jsonl"


def log_structured_event(event_type: str, payload: Dict[str, Any]) -> None:
    """Append a structured JSON line entry to the persistent logs."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }
    try:
        with open(JSONL_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except Exception as e:
        logger.error(f"Failed to write structured log: {e}")
