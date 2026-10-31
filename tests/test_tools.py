"""
Unit tests for student support tools.
Validates input checking, error handling, database persistence, and return schemas.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.student_lookup import lookup_student_record
from tools.fee_checker import check_fee_status
from tools.scholarship_checker import check_scholarship_status
from tools.support_ticket import create_support_ticket
from database.db import get_db_session
from database.models import SupportTicket


def test_student_lookup_valid():
    res = lookup_student_record("STU1001")
    assert res["status"] == "SUCCESS", f"Expected SUCCESS but got {res}"
    assert res["data"]["name"] == "Rahul Sharma"
    assert res["data"]["programme"] == "MBA"
    assert res["data"]["department"] == "School of Business"


def test_student_lookup_invalid():
    res = lookup_student_record("INVALID_999")
    assert res["status"] == "NOT_FOUND"
    assert res["data"] is None


def test_fee_checker_valid():
    res = check_fee_status("STU1001")
    assert res["status"] == "SUCCESS"
    assert res["data"]["total_fees"] == 450000.0
    assert res["data"]["outstanding_balance"] == 150000.0
    assert res["data"]["payment_status"] == "Partial"


def test_scholarship_checker_valid():
    res = check_scholarship_status("STU1001")
    assert res["status"] == "SUCCESS"
    assert "Merit Excellence" in res["data"]["scholarship_name"]
    assert res["data"]["application_status"] == "Approved"


def test_scholarship_checker_none():
    res = check_scholarship_status("STU1004")
    assert res["status"] == "NO_SCHOLARSHIP"
    assert res["data"]["award_amount"] == 0.0


def test_create_support_ticket():
    res = create_support_ticket(
        student_id="STU1001",
        issue_category="Fee Payment",
        description="Payment of 150000 INR made via UPI not showing in portal ledger.",
        priority="High",
    )
    assert res["status"] == "SUCCESS"
    ticket_id = res["data"]["ticket_id"]
    assert ticket_id.startswith("TICK-")

    # Verify actual persistence in SQLite
    with get_db_session() as session:
        t = session.query(SupportTicket).filter(SupportTicket.ticket_id == ticket_id).first()
        assert t is not None
        assert t.student_id == "STU1001"
        assert t.priority == "High"


def test_create_ticket_validation():
    # Empty description should fail
    res = create_support_ticket(student_id="STU1001", issue_category="Fee Payment", description="")
    assert res["status"] == "ERROR"
    assert res["error_type"] == "VALIDATION_ERROR"


if __name__ == "__main__":
    print("Running tools tests...")
    test_student_lookup_valid()
    print("PASS: test_student_lookup_valid")
    test_student_lookup_invalid()
    print("PASS: test_student_lookup_invalid")
    test_fee_checker_valid()
    print("PASS: test_fee_checker_valid")
    test_scholarship_checker_valid()
    print("PASS: test_scholarship_checker_valid")
    test_scholarship_checker_none()
    print("PASS: test_scholarship_checker_none")
    test_create_support_ticket()
    print("PASS: test_create_support_ticket")
    test_create_ticket_validation()
    print("PASS: test_create_ticket_validation")
    print("ALL TOOLS TESTS PASSED!")
