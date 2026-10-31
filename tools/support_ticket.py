"""
Tool 4: Create Support Ticket.
Creates a persistent support ticket in SQLite with unique ticket ID, priority, category, and audit timestamps.
"""

import time
import random
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from database.db import get_db_session
from database.models import SupportTicket, Student
from security.authz import check_student_owner_access

logger = logging.getLogger("tools.support_ticket")

ALLOWED_CATEGORIES = [
    "Fee Payment",
    "Scholarship",
    "Course Registration",
    "Academic Policy",
    "Portal / Technical Issue",
    "Hostel / Campus Facilities",
    "General Support",
]


class SupportTicketInput(BaseModel):
    student_id: str = Field(..., description="Unique student ID, e.g., 'STU1001'")
    issue_category: str = Field(..., description="Category: 'Fee Payment', 'Scholarship', 'Course Registration', 'Academic Policy', 'Portal / Technical Issue', 'General Support'")
    description: str = Field(..., description="Detailed description of the problem or request")
    priority: Optional[str] = Field("Medium", description="Priority level: 'Low', 'Medium', 'High', 'Urgent'")


def create_support_ticket(student_id: str, issue_category: str, description: str, priority: str = "Medium", caller_user: Any = None) -> Dict[str, Any]:
    """
    Core function to insert a real support ticket into SQLite.
    Generates a unique reference ID, enforces owner isolation, and verifies student record.
    """
    start_time = time.time()

    if not student_id or not isinstance(student_id, str):
        return {
            "status": "ERROR",
            "error_type": "VALIDATION_ERROR",
            "message": "Student ID is required.",
            "data": None,
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }

    clean_id = student_id.strip().upper()

    # Backend Authorization Check (Assignment 2)
    if caller_user:
        authorized, reason = check_student_owner_access(caller_user, clean_id, action="CREATE_TICKET", resource_type="ticket")
        if not authorized:
            return {
                "status": "DENIED",
                "error_type": "ACCESS_DENIED",
                "message": f"Access Denied: {reason}",
                "data": None,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }

    if not description or len(description.strip()) < 5:
        return {
            "status": "ERROR",
            "error_type": "VALIDATION_ERROR",
            "message": "A meaningful description (at least 5 characters) must be provided to create a support ticket.",
            "data": None,
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }

    clean_id = student_id.strip().upper()
    clean_category = issue_category.strip() if issue_category else "General Support"
    clean_priority = priority.capitalize() if priority in ["Low", "Medium", "High", "Urgent"] else "Medium"

    # Match category approximately if user phrased it slightly differently
    matched_cat = clean_category
    for cat in ALLOWED_CATEGORIES:
        if cat.lower() in clean_category.lower() or clean_category.lower() in cat.lower():
            matched_cat = cat
            break

    try:
        with get_db_session() as session:
            student = session.query(Student).filter(Student.student_id == clean_id).first()
            if not student:
                return {
                    "status": "NOT_FOUND",
                    "error_type": "STUDENT_NOT_FOUND",
                    "message": f"Cannot create ticket: Student ID '{clean_id}' does not exist.",
                    "data": None,
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                }

            # Generate unique ticket ID: TICK-YYYY-XXXX
            year = datetime.now().year
            rand_suffix = random.randint(1000, 9999)
            ticket_id = f"TICK-{year}-{rand_suffix}"

            # Ensure uniqueness
            while session.query(SupportTicket).filter(SupportTicket.ticket_id == ticket_id).first():
                rand_suffix = random.randint(1000, 9999)
                ticket_id = f"TICK-{year}-{rand_suffix}"

            new_ticket = SupportTicket(
                ticket_id=ticket_id,
                student_id=clean_id,
                issue_category=matched_cat,
                description=description.strip(),
                status="Open",
                priority=clean_priority,
                created_at=datetime.now(timezone.utc),
            )
            session.add(new_ticket)
            session.flush()

            data = new_ticket.to_dict()
            data["student_name"] = student.name
            logger.info(f"Created Support Ticket {ticket_id} for student {clean_id} [{matched_cat}].")

            return {
                "status": "SUCCESS",
                "message": f"Support ticket #{ticket_id} has been created successfully for {student.name}. The Student Support team will review it under '{clean_priority}' priority.",
                "data": data,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }
    except Exception as e:
        logger.error(f"Failed to create support ticket for '{clean_id}': {e}", exc_info=True)
        return {
            "status": "ERROR",
            "error_type": "DATABASE_ERROR",
            "message": f"Internal database error while creating support ticket: {str(e)}",
            "data": None,
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }


@tool("create_support_ticket", args_schema=SupportTicketInput)
def create_support_ticket_tool(student_id: str, issue_category: str, description: str, priority: str = "Medium") -> Dict[str, Any]:
    """Create a formal student support ticket for unresolved fee discrepancies, technical failures, grade disputes, or academic grievances."""
    return create_support_ticket(student_id, issue_category, description, priority)
