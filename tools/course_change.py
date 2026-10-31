"""
Tool 5: Course Change Request Tool (Assignment 2 Sensitive Workflow).
Submits a sensitive course change request that enters PENDING state for institutional approval.
Never mutates student programme without explicit authorized reviewer approval.
"""

import time
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from approvals.approval_manager import create_course_change_request
from security.authz import check_student_owner_access

logger = logging.getLogger("tools.course_change")


class CourseChangeInput(BaseModel):
    student_id: str = Field(..., description="Unique alphanumeric student ID, e.g., 'STU1001'")
    requested_programme: str = Field(..., description="New degree programme name, e.g. 'Business Analytics' or 'Data Science'")
    reason: Optional[str] = Field("Academic career alignment", description="Reason for course change")


def request_course_change(
    student_id: Optional[str] = None,
    requested_programme: Optional[str] = None,
    reason: str = "Student course change request",
    caller_user: Any = None,
    target_programme: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Core function to submit a course change request.
    Enforces student owner-based isolation and queues approval request.
    """
    start_time = time.time()
    
    # Auto-resolve student_id from caller_user session if omitted
    resolved_id = student_id
    if not resolved_id and caller_user and isinstance(caller_user, dict):
        resolved_id = caller_user.get("student_id")
        
    prog_value = requested_programme or target_programme or ""
    clean_id = (resolved_id or "").strip().upper()
    clean_prog = prog_value.strip()

    if not clean_id or not clean_prog:
        return {
            "status": "ERROR",
            "error_type": "VALIDATION_ERROR",
            "message": "Both student_id and requested_programme must be provided.",
            "data": None,
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }

    # Authorize caller
    if caller_user:
        authorized, auth_msg = check_student_owner_access(caller_user, clean_id, action="REQUEST_COURSE_CHANGE", resource_type="student")
        if not authorized:
            return {
                "status": "DENIED",
                "error_type": "ACCESS_DENIED",
                "message": f"Access Denied: {auth_msg}",
                "data": None,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }

    actor_username = caller_user.get("username") if caller_user else clean_id.lower()
    res = create_course_change_request(
        student_id=clean_id,
        requested_programme=clean_prog,
        reason=reason,
        actor_username=actor_username,
    )
    res["latency_ms"] = round((time.time() - start_time) * 1000, 2)
    return res


@tool("request_course_change", args_schema=CourseChangeInput)
def request_course_change_tool(student_id: str, requested_programme: str, reason: str = "Academic career alignment") -> str:
    """Submits a formal course change request requiring institutional approval."""
    res = request_course_change(student_id, requested_programme, reason)
    return str(res)
