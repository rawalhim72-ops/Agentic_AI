"""
Authorization and Access Control Module for Apex Support AI (Assignment 2).
Implements default-deny authorization, owner-based student data isolation,
role permission checks, and automatic audit event dispatching.
"""

from typing import Dict, Any, Tuple, Optional
from security.audit import log_audit_event


from enum import Enum


class Role(str, Enum):
    STUDENT = "STUDENT"
    SUPPORT_STAFF = "SUPPORT_STAFF"
    ADMINISTRATOR = "ADMINISTRATOR"


def check_student_owner_access(
    actor: Optional[Dict[str, Any]],
    target_student_id: str,
    action: str,
    resource_type: str = "record",
) -> Tuple[bool, str]:
    """
    Validates whether the actor is authorized to access the target student's data.
    Enforces strict owner-based data isolation:
    - Students can ONLY view/mutate their OWN records.
    - Support Staff and Administrators have authorized elevated access.
    - Default-Deny: Any unauthenticated or cross-student attempt is blocked.
    Logs an audit event for every access decision.
    """
    clean_target = (target_student_id or "").strip().upper()
    resource_key = f"{resource_type}:{clean_target}"

    if not actor:
        reason = "Unauthenticated access attempt blocked"
        log_audit_event(
            actor_username="anonymous",
            actor_role="ANONYMOUS",
            action=action,
            target_resource=resource_key,
            decision="DENY",
            reason=reason,
        )
        return False, reason

    username = actor.get("username", "unknown")
    role = actor.get("role", Role.STUDENT).upper()
    actor_student_id = (actor.get("student_id") or "").strip().upper()

    # Staff and Admin have permitted organizational access
    if role in [Role.SUPPORT_STAFF, Role.ADMINISTRATOR]:
        reason = f"Authorized institutional access granted to {role}"
        log_audit_event(
            actor_username=username,
            actor_role=role,
            action=action,
            target_resource=resource_key,
            decision="ALLOW",
            reason=reason,
        )
        return True, reason

    # Student role: strict owner isolation
    if role == Role.STUDENT:
        if not actor_student_id or actor_student_id != clean_target:
            reason = f"Access denied: Student {username} ({actor_student_id}) is not the owner of {clean_target}"
            log_audit_event(
                actor_username=username,
                actor_role=role,
                action=action,
                target_resource=resource_key,
                decision="DENY",
                reason=reason,
            )
            return False, reason

        # Owner confirmed
        reason = f"Owner access verified for {actor_student_id}"
        log_audit_event(
            actor_username=username,
            actor_role=role,
            action=action,
            target_resource=resource_key,
            decision="ALLOW",
            reason=reason,
        )
        return True, reason

    # Default-Deny fallback
    reason = f"Access denied: Unrecognized role {role}"
    log_audit_event(
        actor_username=username,
        actor_role=role,
        action=action,
        target_resource=resource_key,
        decision="DENY",
        reason=reason,
    )
    return False, reason


def check_approval_permission(actor: Optional[Dict[str, Any]], action: str = "APPROVE_REJECT") -> Tuple[bool, str]:
    """
    Checks if an actor is permitted to approve or reject pending change requests.
    Only SUPPORT_STAFF and ADMINISTRATOR roles are permitted.
    """
    if not actor:
        return False, "Unauthenticated access blocked"
    
    role = actor.get("role", "").upper()
    username = actor.get("username", "unknown")

    if role in [Role.SUPPORT_STAFF, Role.ADMINISTRATOR]:
        return True, f"Authorized reviewer ({role})"
    
    reason = f"Permission denied: {role} is not permitted to review approvals"
    log_audit_event(
        actor_username=username,
        actor_role=role,
        action=action,
        target_resource="approval_center",
        decision="DENY",
        reason=reason,
    )
    return False, reason
