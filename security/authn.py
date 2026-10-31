"""
Authentication Module for Apex Support AI (Assignment 2).
Implements secure PBKDF2-HMAC-SHA256 password hashing, salt generation,
and session user credential validation.
"""

import hashlib
import secrets
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone

from database.db import get_db_session
from database.models import UserCredential, Student

logger = logging.getLogger("security.authn")


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with 100,000 iterations.
    Never uses plain SHA-256 alone.
    Returns standard formatted string: pbkdf2_sha256$100000$<salt>$<hash>
    """
    if not salt:
        salt = secrets.token_hex(16)
    
    pwd_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")
    pwd_hash = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=pwd_bytes,
        salt=salt_bytes,
        iterations=100_000,
    ).hex()
    return f"pbkdf2_sha256$100000${salt}${pwd_hash}"


def verify_password(password: str, password_hash: str, salt: Optional[str] = None) -> bool:
    """Verifies a password against the stored hash and salt in constant time."""
    try:
        if not password or not password_hash:
            return False
            
        if "$" in password_hash:
            parts = password_hash.split("$")
            if len(parts) == 4:
                _, _, salt_val, _ = parts
                computed = hash_password(password, salt=salt_val)
                return secrets.compare_digest(computed, password_hash)
        
        # Legacy/direct hex hash fallback with explicit salt
        if salt:
            pwd_bytes = password.encode("utf-8")
            salt_bytes = salt.encode("utf-8")
            digest = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100_000).hex()
            return secrets.compare_digest(digest, password_hash)
            
        return False
    except Exception as e:
        logger.error(f"Error during password verification: {e}")
        return False


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticates a user against database credentials.
    Returns safe user dict upon success, or None on failure.
    """
    clean_username = username.strip().lower()
    if not clean_username or not password:
        return None

    with get_db_session() as session:
        user = session.query(UserCredential).filter(
            UserCredential.username == clean_username,
            UserCredential.is_active == True,
        ).first()

        if not user:
            return None

        if verify_password(password, user.password_hash, user.salt):
            student_data = None
            if user.student_id:
                stu = session.query(Student).filter(Student.student_id == user.student_id).first()
                if stu:
                    student_data = stu.to_dict()

            return {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "student_id": user.student_id,
                "display_name": user.display_name,
                "can_review_approvals": user.role in ("SUPPORT_STAFF", "ADMINISTRATOR"),
                "student_data": student_data,
                "authenticated_at": datetime.now(timezone.utc).isoformat(),
            }
        
        return None


def register_or_update_credential(
    username: str,
    password: str,
    role: str,
    display_name: str,
    student_id: Optional[str] = None,
) -> UserCredential:
    """Helper to create or update user credentials with PBKDF2 hashing."""
    clean_user = username.strip().lower()
    full_hash = hash_password(password)
    salt = full_hash.split("$")[2]

    with get_db_session() as session:
        existing = session.query(UserCredential).filter(UserCredential.username == clean_user).first()
        if existing:
            existing.password_hash = full_hash
            existing.salt = salt
            existing.role = role
            existing.display_name = display_name
            existing.student_id = student_id
            session.flush()
            return existing
        else:
            new_cred = UserCredential(
                username=clean_user,
                password_hash=full_hash,
                salt=salt,
                role=role,
                display_name=display_name,
                student_id=student_id,
                created_at=datetime.now(timezone.utc),
            )
            session.add(new_cred)
            session.flush()
            return new_cred
