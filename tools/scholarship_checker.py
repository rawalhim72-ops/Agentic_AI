"""
Tool 3: Scholarship Status Checker.
Retrieves scholarship applications, awards, review statuses, and requirements from SQLite.
"""

import time
import logging
from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from database.db import get_db_session
from database.models import Scholarship, Student
from security.authz import check_student_owner_access

logger = logging.getLogger("tools.scholarship_checker")


class ScholarshipCheckerInput(BaseModel):
    student_id: str = Field(..., description="Unique alphanumeric student ID, e.g., 'STU1001'")


def check_scholarship_status(student_id: str, caller_user: Any = None) -> Dict[str, Any]:
    """
    Core function to retrieve scholarship information for a student.
    Validates input, enforces owner-based isolation, and checks SQLite records.
    """
    start_time = time.time()
    if not student_id or not isinstance(student_id, str):
        return {
            "status": "ERROR",
            "error_type": "VALIDATION_ERROR",
            "message": "Student ID must be a non-empty string.",
            "data": None,
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }

    clean_id = student_id.strip().upper()

    # Backend Authorization Check (Assignment 2)
    if caller_user:
        authorized, reason = check_student_owner_access(caller_user, clean_id, action="READ_SCHOLARSHIP", resource_type="scholarship")
        if not authorized:
            return {
                "status": "DENIED",
                "error_type": "ACCESS_DENIED",
                "message": f"Access Denied: {reason}",
                "data": None,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }

    try:
        with get_db_session() as session:
            student = session.query(Student).filter(Student.student_id == clean_id).first()
            if not student:
                return {
                    "status": "NOT_FOUND",
                    "error_type": "STUDENT_NOT_FOUND",
                    "message": f"Student ID '{clean_id}' does not exist in university records.",
                    "data": None,
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                }

            scholarship = session.query(Scholarship).filter(Scholarship.student_id == clean_id).first()
            if not scholarship:
                logger.info(f"No scholarship on file for student {clean_id}.")
                return {
                    "status": "NO_SCHOLARSHIP",
                    "message": f"No active scholarship or financial grant found on record for {student.name} ({clean_id}).",
                    "data": {
                        "student_id": clean_id,
                        "student_name": student.name,
                        "scholarship_name": "None",
                        "application_status": "No Active Application",
                        "award_amount": 0.0,
                        "details": "Student may apply through the Student Aid & Fellowship portal during the open window.",
                    },
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                }

            data = scholarship.to_dict()
            data["student_name"] = student.name
            logger.info(f"Scholarship status checked for {clean_id}: {data['scholarship_name']} ({data['application_status']}).")
            return {
                "status": "SUCCESS",
                "student_id": clean_id,
                "message": f"Scholarship '{data['scholarship_name']}' is currently {data['application_status']}.",
                "data": data,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }
    except Exception as e:
        logger.error(f"Database error checking scholarship for '{clean_id}': {e}", exc_info=True)
        return {
            "status": "ERROR",
            "error_type": "DATABASE_ERROR",
            "message": f"Internal database error checking scholarship records: {str(e)}",
            "data": None,
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }


@tool("scholarship_status_checker", args_schema=ScholarshipCheckerInput)
def scholarship_status_checker_tool(student_id: str) -> Dict[str, Any]:
    """Retrieve scholarship application status, grant name, awarded funding, and compliance details for a student."""
    return check_scholarship_status(student_id)
