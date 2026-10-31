"""
Tests for Assignment 2: Authentication, Authorization, Approval Workflows, and Audit Logging.
==============================================================================================
Validates:
1. PBKDF2 Password Hashing and Authentication
2. Default-Deny Authorization and Cross-Student Access Blocking
3. Course Change Approval Workflow (Pending, Rejection Non-Execution, Approved Execution, Duplicate Guard)
4. Sensitive Credential Masking & Immutable Audit Logging
5. End-to-End Agent Session Identity Resolution
"""

import pytest
from database.db import get_db_session
from database.models import Student, UserCredential, ApprovalRequest, AuditLog
from security.authn import hash_password, verify_password, authenticate_user
from security.authz import check_student_owner_access, check_approval_permission, Role
from security.audit import mask_sensitive_text, log_audit_event, get_audit_trail
from approvals.approval_manager import (
    create_course_change_request,
    process_approval_decision,
    get_pending_approvals,
    get_all_approvals
)
from tools.fee_checker import check_fee_status
from tools.scholarship_checker import check_scholarship_status
from tools.student_lookup import lookup_student_record
from tools.course_change import request_course_change
from agent.orchestrator import run_agent


# ---------------------------------------------------------------------------
# 1. AUTHENTICATION & PASSWORD HASHING (PBKDF2)
# ---------------------------------------------------------------------------

def test_password_hashing_pbkdf2():
    """Verify PBKDF2-HMAC-SHA256 with salt is used (not plain SHA-256 alone)."""
    raw_pwd = "TestPassword#2026!"
    hashed = hash_password(raw_pwd)

    # Must contain PBKDF2 scheme identifier, iteration count, salt, and digest
    parts = hashed.split("$")
    assert len(parts) == 4, f"Hash format invalid: {hashed}"
    assert parts[0] == "pbkdf2_sha256"
    assert int(parts[1]) == 100000
    assert len(parts[2]) == 32  # 16 bytes hex salt

    # Verification must succeed with correct password and fail with wrong password
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_authentication_service():
    """Verify login authentication for Student, Support Staff, and Admin."""
    # Seeded student
    student_user = authenticate_user("stu1001", "Student#1001!")
    assert student_user is not None
    assert student_user["role"] == "STUDENT"
    assert student_user["student_id"] == "STU1001"
    assert student_user["username"] == "stu1001"

    # Seeded staff
    staff_user = authenticate_user("support1", "Staff#2026!")
    assert staff_user is not None
    assert staff_user["role"] == "SUPPORT_STAFF"
    assert staff_user["can_review_approvals"] is True

    # Seeded admin
    admin_user = authenticate_user("admin1", "Admin#2026!")
    assert admin_user is not None
    assert admin_user["role"] == "ADMINISTRATOR"
    assert admin_user["can_review_approvals"] is True

    # Invalid credentials
    assert authenticate_user("stu1001", "WrongPass#999") is None
    assert authenticate_user("nonexistent_user", "AnyPass") is None


# ---------------------------------------------------------------------------
# 2. AUTHORIZATION & OWNER DATA ISOLATION
# ---------------------------------------------------------------------------

def test_authorization_own_record_access():
    """Student can access only their own records."""
    caller_stu1001 = {
        "username": "stu1001",
        "role": Role.STUDENT.value,
        "student_id": "STU1001",
        "full_name": "Rahul Sharma"
    }

    # Own fee
    fee_res = check_fee_status(student_id="STU1001", caller_user=caller_stu1001)
    assert fee_res["status"] == "SUCCESS"
    assert fee_res["student_id"] == "STU1001"

    # Own scholarship
    schol_res = check_scholarship_status(student_id="STU1001", caller_user=caller_stu1001)
    assert schol_res["status"] == "SUCCESS"
    assert schol_res["student_id"] == "STU1001"

    # Own profile lookup
    lookup_res = lookup_student_record(student_id="STU1001", caller_user=caller_stu1001)
    assert lookup_res["status"] == "SUCCESS"
    assert lookup_res["student_id"] == "STU1001"


def test_authorization_cross_student_access_denied():
    """Student STU1001 attempting to access STU1002 records is strictly blocked."""
    caller_stu1001 = {
        "username": "stu1001",
        "role": Role.STUDENT.value,
        "student_id": "STU1001",
        "full_name": "Rahul Sharma"
    }

    # Cross-student fee query
    fee_res = check_fee_status(student_id="STU1002", caller_user=caller_stu1001)
    assert fee_res["status"] == "DENIED"
    assert "Access Denied" in fee_res["message"]
    assert "STU1002" in fee_res["message"]

    # Cross-student scholarship query
    schol_res = check_scholarship_status(student_id="STU1002", caller_user=caller_stu1001)
    assert schol_res["status"] == "DENIED"
    assert "Access Denied" in schol_res["message"]

    # Cross-student profile lookup
    lookup_res = lookup_student_record(student_id="STU1002", caller_user=caller_stu1001)
    assert lookup_res["status"] == "DENIED"
    assert "Access Denied" in lookup_res["message"]


def test_staff_and_admin_cross_student_access():
    """Staff and Admin have authorized cross-student access."""
    staff_caller = {
        "username": "support1",
        "role": Role.SUPPORT_STAFF.value,
        "student_id": None,
        "full_name": "Support Staff Lead"
    }
    admin_caller = {
        "username": "admin1",
        "role": Role.ADMINISTRATOR.value,
        "student_id": None,
        "full_name": "System Administrator"
    }

    # Staff can check STU1002
    fee_staff = check_fee_status(student_id="STU1002", caller_user=staff_caller)
    assert fee_staff["status"] == "SUCCESS"
    assert fee_staff["student_id"] == "STU1002"

    # Admin can check STU1002
    fee_admin = check_fee_status(student_id="STU1002", caller_user=admin_caller)
    assert fee_admin["status"] == "SUCCESS"
    assert fee_admin["student_id"] == "STU1002"


# ---------------------------------------------------------------------------
# 3. APPROVAL WORKFLOW FOR COURSE CHANGE
# ---------------------------------------------------------------------------

def test_course_change_request_pending_state():
    """Course change requests enter PENDING state and do NOT immediately update student record."""
    caller_stu1003 = {
        "username": "stu1003",
        "role": Role.STUDENT.value,
        "student_id": "STU1003",
        "full_name": "Rohan Verma"
    }

    # Fetch original programme
    with get_db_session() as session:
        stu = session.query(Student).filter(Student.student_id == "STU1003").first()
        orig_programme = stu.programme

    # Submit course change request via tool
    res = request_course_change(
        target_programme="Master of Science in Artificial Intelligence",
        reason="Career pivot to AI research",
        caller_user=caller_stu1003
    )

    assert res["status"] == "PENDING_APPROVAL"
    assert res["request_id"].startswith("REQ-")

    # Verify student record has NOT changed
    with get_db_session() as session:
        stu_after = session.query(Student).filter(Student.student_id == "STU1003").first()
        assert stu_after.programme == orig_programme, "Student record was prematurely modified before approval!"


def test_course_change_rejection_does_not_execute():
    """Rejected request is marked REJECTED and never modifies the student record."""
    # Create request
    caller_stu1004 = {
        "username": "stu1004",
        "role": Role.STUDENT.value,
        "student_id": "STU1004",
        "full_name": "Ananya Patel"
    }
    with get_db_session() as session:
        orig_prog = session.query(Student).filter(Student.student_id == "STU1004").first().programme

    req = create_course_change_request(
        student_id="STU1004",
        target_programme="Cybersecurity Engineering",
        reason="Interest in security",
        requested_by="stu1004"
    )

    # Reviewer rejects
    staff_caller = {
        "username": "support1",
        "role": Role.SUPPORT_STAFF.value,
        "full_name": "Support Staff Lead"
    }
    dec_res = process_approval_decision(
        request_id=req["request_id"],
        decision="REJECTED",
        reviewer_user=staff_caller,
        reviewer_notes="Prerequisites not met."
    )

    assert dec_res["status"] == "REJECTED"
    assert dec_res["executed"] is False

    # Check database
    with get_db_session() as session:
        stu = session.query(Student).filter(Student.student_id == "STU1004").first()
        assert stu.programme == orig_prog, "Rejected change was executed in database!"


def test_course_change_approval_executes_exactly_once():
    """Approved request updates record; duplicate approvals are rejected."""
    caller_stu1005 = {
        "username": "stu1005",
        "role": Role.STUDENT.value,
        "student_id": "STU1005",
        "full_name": "Vikram Malhotra"
    }
    req = create_course_change_request(
        student_id="STU1005",
        target_programme="Executive MBA in Technology Management",
        reason="Leadership track",
        requested_by="stu1005"
    )

    admin_caller = {
        "username": "admin1",
        "role": Role.ADMINISTRATOR.value,
        "full_name": "System Administrator"
    }

    # First approval -> must execute
    dec_res = process_approval_decision(
        request_id=req["request_id"],
        decision="APPROVED",
        reviewer_user=admin_caller,
        reviewer_notes="Approved by Dean."
    )
    assert dec_res["status"] == "APPROVED"
    assert dec_res["executed"] is True

    # Verify student record was updated
    with get_db_session() as session:
        stu = session.query(Student).filter(Student.student_id == "STU1005").first()
        assert stu.programme == "Executive MBA in Technology Management"

    # Second approval attempt -> duplicate execution guard
    with pytest.raises(ValueError, match="already finalized"):
        process_approval_decision(
            request_id=req["request_id"],
            decision="APPROVED",
            reviewer_user=admin_caller,
            reviewer_notes="Duplicate attempt"
        )


def test_student_cannot_approve_request():
    """Student attempting to approve a request is denied with PermissionError."""
    req = create_course_change_request(
        student_id="STU1001",
        target_programme="Any Course",
        reason="Testing",
        requested_by="stu1001"
    )

    student_caller = {
        "username": "stu1001",
        "role": Role.STUDENT.value,
        "student_id": "STU1001"
    }

    with pytest.raises(PermissionError, match="not authorized"):
        process_approval_decision(
            request_id=req["request_id"],
            decision="APPROVED",
            reviewer_user=student_caller
        )


# ---------------------------------------------------------------------------
# 4. SENSITIVE CREDENTIAL MASKING & AUDIT LOGGING
# ---------------------------------------------------------------------------

def test_sensitive_credential_masking():
    """Secrets, passwords, and OTPs must be masked in audit records."""
    raw = "User said password: MySecret#123 and OTP is 948210 with key sk-ant-12345678901234567890"
    masked = mask_sensitive_text(raw)

    assert "MySecret#123" not in masked
    assert "948210" not in masked
    assert "sk-ant-" not in masked
    assert "[REDACTED_PASSWORD]" in masked
    assert "[REDACTED_OTP]" in masked


def test_audit_trail_logging_and_query():
    """Audit events are recorded and queryable."""
    log_audit_event(
        user_id="stu1001",
        role="STUDENT",
        action="TEST_SENSITIVE_ACTION",
        resource="fee_records:STU1001",
        decision="ALLOW",
        reason="Authorized test action",
        details="Access with test details"
    )

    trail = get_audit_trail(limit=10)
    assert len(trail) > 0
    actions = [evt["action"] for evt in trail]
    assert "TEST_SENSITIVE_ACTION" in actions


# ---------------------------------------------------------------------------
# 5. END-TO-END AGENT SESSION IDENTITY & CROSS-STUDENT BLOCKING
# ---------------------------------------------------------------------------

def test_agent_e2e_own_fee_with_authenticated_session():
    """Agent answers own fee query using caller_user context."""
    caller_stu1001 = {
        "username": "stu1001",
        "role": Role.STUDENT.value,
        "student_id": "STU1001",
        "full_name": "Rahul Sharma"
    }

    result = run_agent(
        user_message="What is my fee status?",
        student_id="STU1001",
        caller_user=caller_stu1001
    )

    assert result["status"] == "SUCCESS"
    assert "Rahul Sharma" in result["final_response"] or "fee" in result["final_response"].lower()
    assert result["tool_called"] in ["fee_status_checker", "check_fee_status"]


def test_agent_e2e_cross_student_access_denial():
    """Agent blocks student STU1001 trying to query fee of STU1002."""
    caller_stu1001 = {
        "username": "stu1001",
        "role": Role.STUDENT.value,
        "student_id": "STU1001",
        "full_name": "Rahul Sharma"
    }

    result = run_agent(
        user_message="Show me the fee details of student STU1002",
        student_id="STU1001",
        caller_user=caller_stu1001
    )

    # Response must indicate Access Denied
    assert "Access Denied" in result["final_response"] or "denied" in result["final_response"].lower()
