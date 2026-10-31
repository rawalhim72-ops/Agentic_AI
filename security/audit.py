"""
Audit Logging Module for Apex Support AI (Assignment 2).
Provides an append-only institutional audit trail for every sensitive inquiry,
access decision, approval action, and sensitive data redaction.
"""

import re
import json
import uuid
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from database.db import get_db_session
from database.models import AuditLog

logger = logging.getLogger("security.audit")

# Sensitive patterns that must never appear in raw audit logs
SENSITIVE_PATTERNS = [
    (r"\b\d{6}\b", "[REDACTED_OTP]"),
    (r"(?i)(?:password|passwd|pwd)\s*[=:]\s*(\S+)", r"password: [REDACTED_PASSWORD]"),
    (r"(?i)\b(gsk_[A-Za-z0-9_-]{20,})\b", "[REDACTED_GROQ_KEY]"),
    (r"(?i)\b(sk-[A-Za-z0-9_-]{20,})\b", "[REDACTED_OPENAI_KEY]"),
    (r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[REDACTED_CARD]"),
]


def mask_sensitive_text(text: str) -> str:
    """Masks OTPs, passwords, API keys, and credentials from audit strings."""
    if not text:
        return ""
    masked = str(text)
    for pattern, replacement in SENSITIVE_PATTERNS:
        masked = re.sub(pattern, replacement, masked)
    return masked


def log_audit_event(
    actor_username: Optional[str] = None,
    actor_role: Optional[str] = None,
    action: str = "SYSTEM_ACTION",
    target_resource: Optional[str] = None,
    decision: str = "ALLOW",
    reason: Optional[str] = None,
    details: Optional[Any] = None,
    ip_address: str = "127.0.0.1",
    user_id: Optional[str] = None,
    role: Optional[str] = None,
    resource: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Appends an immutable audit event to the SQLite audit_logs table.
    Enforces automatic redaction of sensitive credentials.
    """
    username = actor_username or user_id or "anonymous"
    user_role = actor_role or role or "ANONYMOUS"
    resource_key = target_resource or resource or "system:general"
    event_id = f"AUD-{uuid.uuid4().hex[:12].upper()}"
    
    # Sanitize and serialize details
    clean_details = ""
    if details is not None:
        if isinstance(details, (dict, list)):
            try:
                raw_json = json.dumps(details)
                clean_details = mask_sensitive_text(raw_json)
            except Exception:
                clean_details = mask_sensitive_text(str(details))
        else:
            clean_details = mask_sensitive_text(str(details))

    clean_reason = mask_sensitive_text(reason or "")

    with get_db_session() as session:
        log_entry = AuditLog(
            event_id=event_id,
            actor_username=actor_username or "anonymous",
            actor_role=actor_role or "UNAUTHENTICATED",
            action=action.upper(),
            target_resource=target_resource,
            decision=decision.upper(),
            reason=clean_reason,
            details=clean_details,
            ip_address=ip_address,
            created_at=datetime.now(timezone.utc),
        )
        session.add(log_entry)
        session.flush()
        record_dict = log_entry.to_dict()

    logger.info(f"AUDIT [{decision.upper()}] {actor_username} ({actor_role}) -> {action} on {target_resource}: {clean_reason}")
    return record_dict


def get_audit_trail(
    limit: int = 100,
    action_filter: Optional[str] = None,
    decision_filter: Optional[str] = None,
    actor_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieves audit logs ordered chronologically descending."""
    with get_db_session() as session:
        query = session.query(AuditLog)
        if action_filter and action_filter != "ALL":
            query = query.filter(AuditLog.action == action_filter.upper())
        if decision_filter and decision_filter != "ALL":
            query = query.filter(AuditLog.decision == decision_filter.upper())
        if actor_filter:
            query = query.filter(AuditLog.actor_username.ilike(f"%{actor_filter.strip()}%"))
        
        logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
        return [l.to_dict() for l in logs]
