"""Security module for Apex Support AI (Authentication, Authorization, Auditing)."""
from security.authn import hash_password, verify_password, authenticate_user, register_or_update_credential
from security.authz import Role, check_student_owner_access, check_approval_permission
from security.audit import log_audit_event, get_audit_trail, mask_sensitive_text
