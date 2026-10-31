"""
Tool 1: Student Record Lookup.
Retrieves student demographic, academic, and department records from SQLite.
"""

import time
import logging
from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from database.db import get_db_session
from database.models import Student
from security.authz import check_student_owner_access

logger = logging.getLogger("tools.student_lookup")


class StudentLookupInput(BaseModel):
    student_id: str = Field(..., description="Unique alphanumeric student ID, e.g., 'STU1001'")


def lookup_student_record(student_id: str, caller_user: Any = None) -> Dict[str, Any]:
    """
    Core function to look up student record in SQLite.
    Validates input format, enforces owner-based isolation if caller is authenticated,
    and returns structured student details.
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
        authorized, reason = check_student_owner_access(caller_user, clean_id, action="READ_RECORD", resource_type="student")
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
                logger.warning(f"Student lookup failed: ID '{clean_id}' not found.")
                return {
                    "status": "NOT_FOUND",
                    "error_type": "RECORD_NOT_FOUND",
                    "message": f"No student record found for Student ID: {clean_id}.",
                    "data": None,
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                }

            data = student.to_dict()
            logger.info(f"Student lookup succeeded for {clean_id} ({data['name']}).")
            return {
                "status": "SUCCESS",
                "student_id": clean_id,
                "message": f"Successfully retrieved profile for {data['name']}.",
                "data": data,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }
    except Exception as e:
        logger.error(f"Database error during student lookup for '{clean_id}': {e}", exc_info=True)
        return {
            "status": "ERROR",
            "error_type": "DATABASE_ERROR",
            "message": f"Internal database error while accessing student records: {str(e)}",
            "data": None,
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }


@tool("student_record_lookup", args_schema=StudentLookupInput)
def student_record_lookup_tool(student_id: str) -> Dict[str, Any]:
    """Look up a student's official record including programme, department, academic year, and enrollment status using their student ID."""
    return lookup_student_record(student_id)
