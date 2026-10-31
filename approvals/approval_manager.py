"""
Approval Workflow Manager for Apex Support AI (Assignment 2).
Coordinates sensitive student change requests (e.g., Course Change),
review enforcement by authorized staff/admin, and exactly-once execution.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from database.db import get_db_session
from database.models import ApprovalRequest, Student
from security.authz import check_approval_permission
from security.audit import log_audit_event

logger = logging.getLogger("approvals.manager")


def create_course_change_request(
    student_id: str,
    requested_programme: Optional[str] = None,
    reason: str = "Student course change request via support agent",
    actor_username: Optional[str] = None,
    target_programme: Optional[str] = None,
    requested_by: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Submits a course/programme change request.
    The action is NOT executed immediately; it enters PENDING status until reviewed.
    """
    clean_id = (student_id or "").strip().upper()
    prog_value = requested_programme or target_programme or ""
    clean_prog = prog_value.strip()
    clean_actor = actor_username or requested_by or clean_id.lower()

    with get_db_session() as session:
        student = session.query(Student).filter(Student.student_id == clean_id).first()
        if not student:
            return {
                "status": "ERROR",
                "message": f"Student with ID {clean_id} does not exist in the database.",
            }

        current_programme = student.programme
        request_id = f"REQ-COURSE-{uuid.uuid4().hex[:8].upper()}"

        new_request = ApprovalRequest(
            request_id=request_id,
            student_id=clean_id,
            action_type="COURSE_CHANGE",
            current_value=current_programme,
            requested_value=clean_prog,
            reason=reason,
            status="PENDING",
            created_at=datetime.now(timezone.utc),
        )
        session.add(new_request)
        session.flush()

        # Audit the creation of the pending change request
        log_audit_event(
            actor_username=clean_actor,
            actor_role="STUDENT",
            action="REQUEST_COURSE_CHANGE",
            target_resource=f"student:{clean_id}:programme",
            decision="PENDING",
            reason=f"Requested change from '{current_programme}' to '{clean_prog}'",
            details={"request_id": request_id, "new_programme": clean_prog, "reason": reason},
        )

        return {
            "status": "PENDING_APPROVAL",
            "request_id": request_id,
            "student_id": clean_id,
            "current_programme": current_programme,
            "requested_programme": clean_prog,
            "message": (
                f"Your request to change programme from '{current_programme}' to '{clean_prog}' "
                f"has been submitted under Request ID `{request_id}`. "
                f"Per university academic policy, course changes require institutional human approval. "
                f"Your record remains unchanged until an authorized reviewer approves this request."
            ),
        }


def get_pending_approvals() -> List[Dict[str, Any]]:
    """Retrieve all pending approval requests for staff/admin review."""
    with get_db_session() as session:
        reqs = (
            session.query(ApprovalRequest)
            .filter(ApprovalRequest.status == "PENDING")
            .order_by(ApprovalRequest.created_at.asc())
            .all()
        )
        return [r.to_dict() for r in reqs]


def get_all_approvals(student_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve approval requests, optionally filtered by student ID."""
    with get_db_session() as session:
        query = session.query(ApprovalRequest)
        if student_id:
            query = query.filter(ApprovalRequest.student_id == student_id.strip().upper())
        reqs = query.order_by(ApprovalRequest.created_at.desc()).all()
        return [r.to_dict() for r in reqs]


def process_approval_decision(
    request_id: str,
    reviewer_user: Dict[str, Any],
    decision: str,  # "APPROVE" / "APPROVED" or "REJECT" / "REJECTED"
    reviewer_notes: str = "",
) -> Dict[str, Any]:
    """
    Processes an approval or rejection by an authorized reviewer.
    Guarantees exactly-once execution:
    - If APPROVED: mutates the target student's record and transitions to EXECUTED.
    - If REJECTED: transitions to REJECTED; student record is NEVER mutated.
    - If already processed: rejects duplicate execution with ValueError.
    - If unauthorized reviewer: blocks with PermissionError.
    """
    # 1. Authorize reviewer role
    authorized, auth_msg = check_approval_permission(reviewer_user, action="APPROVE_REJECT")
    if not authorized:
        log_audit_event(
            actor_username=reviewer_user.get("username", "anonymous"),
            actor_role=reviewer_user.get("role", "ANONYMOUS"),
            action="UNAUTHORIZED_APPROVAL_ATTEMPT",
            target_resource=f"approval_request:{request_id}",
            decision="DENY",
            reason=auth_msg,
        )
        raise PermissionError(f"User is not authorized to review requests: {auth_msg}")

    clean_decision = decision.strip().upper()
    is_approve = clean_decision in ["APPROVE", "APPROVED"]
    is_reject = clean_decision in ["REJECT", "REJECTED"]

    if not is_approve and not is_reject:
        raise ValueError(f"Invalid decision '{decision}'. Must be 'APPROVE' or 'REJECT'.")

    reviewer_name = reviewer_user.get("username", "reviewer")
    reviewer_role = reviewer_user.get("role", "SUPPORT_STAFF")

    with get_db_session() as session:
        req = session.query(ApprovalRequest).filter(ApprovalRequest.request_id == request_id).first()
        if not req:
            raise KeyError(f"Approval request '{request_id}' not found.")

        # 2. Check duplicate execution guard
        if req.status != "PENDING":
            reason = f"Duplicate decision blocked: Request '{request_id}' is already finalized in '{req.status}' state."
            log_audit_event(
                actor_username=reviewer_name,
                actor_role=reviewer_role,
                action=f"DUPLICATE_{clean_decision}",
                target_resource=f"approval_request:{request_id}",
                decision="DENY",
                reason=reason,
            )
            raise ValueError(reason)

        now = datetime.now(timezone.utc)
        req.reviewer_id = reviewer_name
        req.reviewer_notes = reviewer_notes
        req.reviewed_at = now

        # 3. Handle APPROVED vs REJECTED
        if is_approve:
            # Mutate target student record exactly once
            student = session.query(Student).filter(Student.student_id == req.student_id).first()
            if not student:
                raise ValueError(f"Target student '{req.student_id}' no longer exists.")

            old_prog = student.programme
            student.programme = req.requested_value
            req.status = "APPROVED"
            req.executed_at = now
            session.flush()

            msg = f"Request '{request_id}' APPROVED and EXECUTED. Student '{student.student_id}' programme updated from '{old_prog}' to '{student.programme}'."
            log_audit_event(
                actor_username=reviewer_name,
                actor_role=reviewer_role,
                action="APPROVE_COURSE_CHANGE",
                target_resource=f"student:{req.student_id}:programme",
                decision="ALLOW",
                reason=msg,
                details={"old": old_prog, "new": student.programme, "notes": reviewer_notes},
            )
            return {
                "success": True,
                "status": "APPROVED",
                "executed": True,
                "message": msg,
                "data": req.to_dict(),
            }

        else:
            # REJECT: Record is NEVER mutated
            req.status = "REJECTED"
            session.flush()

            msg = f"Request '{request_id}' REJECTED. Student '{req.student_id}' programme remains unchanged."
            log_audit_event(
                actor_username=reviewer_name,
                actor_role=reviewer_role,
                action="REJECT_COURSE_CHANGE",
                target_resource=f"student:{req.student_id}:programme",
                decision="DENY",
                reason=msg,
                details={"student_id": req.student_id, "rejected_programme": req.requested_value, "notes": reviewer_notes},
            )
            return {
                "success": True,
                "status": "REJECTED",
                "executed": False,
                "message": msg,
                "data": req.to_dict(),
            }
