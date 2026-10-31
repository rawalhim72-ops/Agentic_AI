"""
Tool 2: Fee Status Checker.
Retrieves tuition/fee details, payments made, outstanding balance, due dates, and status from SQLite.
"""

import time
import logging
from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from database.db import get_db_session
from database.models import FeeRecord, Student
from security.authz import check_student_owner_access

logger = logging.getLogger("tools.fee_checker")


class FeeCheckerInput(BaseModel):
    student_id: str = Field(..., description="Unique alphanumeric student ID, e.g., 'STU1001'")


def check_fee_status(student_id: str, caller_user: Any = None) -> Dict[str, Any]:
    """
    Core function to check student fee status in SQLite.
    Validates input format, enforces owner isolation, and returns structured fee calculations.
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
        authorized, reason = check_student_owner_access(caller_user, clean_id, action="READ_FEE", resource_type="fee")
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
            # Check student exists first
            student = session.query(Student).filter(Student.student_id == clean_id).first()
            if not student:
                return {
                    "status": "NOT_FOUND",
                    "error_type": "STUDENT_NOT_FOUND",
                    "message": f"Student ID '{clean_id}' does not exist in university records.",
                    "data": None,
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                }

            fee_record = session.query(FeeRecord).filter(FeeRecord.student_id == clean_id).first()
            if not fee_record:
                logger.warning(f"No fee ledger found for student '{clean_id}'.")
                return {
                    "status": "NOT_FOUND",
                    "error_type": "RECORD_NOT_FOUND",
                    "message": f"No active fee record or tuition invoice found for {student.name} ({clean_id}).",
                    "data": None,
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                }

            data = fee_record.to_dict()
            data["student_name"] = student.name
            data["programme"] = student.programme
            logger.info(f"Fee status checked for {clean_id}: Outstanding {data['outstanding_balance']}.")
            return {
                "status": "SUCCESS",
                "student_id": clean_id,
                "message": f"Fee status for {student.name}: Status is {data['payment_status']} with balance {data['currency']} {data['outstanding_balance']:,.2f}.",
                "data": data,
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }
    except Exception as e:
        logger.error(f"Database error checking fee status for '{clean_id}': {e}", exc_info=True)
        return {
            "status": "ERROR",
            "error_type": "DATABASE_ERROR",
            "message": f"Internal database error checking fee status: {str(e)}",
            "data": None,
            "latency_ms": round((time.time() - start_time) * 1000, 2),
        }


@tool("fee_status_checker", args_schema=FeeCheckerInput)
def fee_status_checker_tool(student_id: str) -> Dict[str, Any]:
    """Retrieve tuition fee records including total fees, amount paid, outstanding balance, payment status, and due date for a student."""
    return check_fee_status(student_id)
