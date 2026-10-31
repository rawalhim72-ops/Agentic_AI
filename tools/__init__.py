"""
Tools package registry for Intelligent Student Support Agent.
"""

from tools.student_lookup import student_record_lookup_tool, lookup_student_record
from tools.fee_checker import fee_status_checker_tool, check_fee_status
from tools.scholarship_checker import scholarship_status_checker_tool, check_scholarship_status
from tools.support_ticket import create_support_ticket_tool, create_support_ticket
from tools.course_change import request_course_change_tool, request_course_change

ALL_TOOLS = [
    student_record_lookup_tool,
    fee_status_checker_tool,
    scholarship_status_checker_tool,
    create_support_ticket_tool,
    request_course_change_tool,
]

TOOL_MAP = {
    "student_record_lookup": student_record_lookup_tool,
    "fee_status_checker": fee_status_checker_tool,
    "scholarship_status_checker": scholarship_status_checker_tool,
    "create_support_ticket": create_support_ticket_tool,
    "request_course_change": request_course_change_tool,
}

__all__ = [
    "ALL_TOOLS",
    "TOOL_MAP",
    "student_record_lookup_tool",
    "fee_status_checker_tool",
    "scholarship_status_checker_tool",
    "create_support_ticket_tool",
    "request_course_change_tool",
    "lookup_student_record",
    "check_fee_status",
    "check_scholarship_status",
    "create_support_ticket",
    "request_course_change",
]

