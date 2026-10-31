"""
Memory Manager Module.
Coordinates persistence, extraction, updating, and CRUD operations for student long-term memories in SQLite.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from database.db import get_db_session
from database.models import LongTermMemory
from memory.memory_extractor import analyze_and_extract_memory, ExtractionDecision

logger = logging.getLogger("memory.memory_manager")


class MemoryManager:
    """Manages persistent long-term memories for students in SQLite."""

    @staticmethod
    def save_or_update_memory(
        student_id: str,
        memory_key: str,
        memory_value: str,
        source_query: str = "",
        confidence: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Save or update a memory attribute for a student.
        Prevents duplicate rows for the same key.
        """
        clean_id = student_id.strip().upper()
        clean_key = memory_key.strip().lower()
        clean_val = memory_value.strip()

        with get_db_session() as session:
            existing = session.query(LongTermMemory).filter(
                LongTermMemory.student_id == clean_id,
                LongTermMemory.memory_key == clean_key,
            ).first()

            if existing:
                existing.memory_value = clean_val
                existing.source_query = source_query
                existing.confidence = confidence
                existing.updated_at = datetime.now(timezone.utc)
                session.flush()
                res = existing.to_dict()
                logger.info(f"Updated memory [{clean_key}={clean_val}] for student {clean_id}")
            else:
                new_mem = LongTermMemory(
                    student_id=clean_id,
                    memory_key=clean_key,
                    memory_value=clean_val,
                    confidence=confidence,
                    source_query=source_query,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(new_mem)
                session.flush()
                res = new_mem.to_dict()
                logger.info(f"Inserted new memory [{clean_key}={clean_val}] for student {clean_id}")

            return res

    @staticmethod
    def process_and_store_from_query(student_id: str, query: str) -> List[Dict[str, Any]]:
        """
        Analyzes query for extractable memories, filters sensitive data,
        and saves accepted items to SQLite.
        Returns audit logs of decisions.
        """
        decisions: List[ExtractionDecision] = analyze_and_extract_memory(query)
        logs = []

        for dec in decisions:
            if dec.accepted and dec.key and dec.value:
                saved = MemoryManager.save_or_update_memory(
                    student_id=student_id,
                    memory_key=dec.key,
                    memory_value=dec.value,
                    source_query=query,
                )
                logs.append({
                    "action": "ACCEPTED_AND_STORED",
                    "key": dec.key,
                    "value": dec.value,
                    "reason": dec.reason,
                    "memory_id": saved.get("id"),
                })
            else:
                logs.append({
                    "action": "REJECTED",
                    "key": dec.key,
                    "value": None,
                    "reason": dec.reason,
                })
                # Audit log sensitive rejection
                if "SENSITIVE" in str(dec.key):
                    try:
                        from security.audit import log_audit_event
                        log_audit_event(
                            actor_username=student_id.lower(),
                            actor_role="STUDENT",
                            action="REDACT_SENSITIVE",
                            target_resource=f"memory:{student_id}",
                            decision="DENY",
                            reason=f"Sensitive input blocked from persistent storage: {dec.reason}",
                        )
                    except Exception:
                        pass

        return logs

    @staticmethod
    def get_all_memories(student_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all long-term memories or filter by student ID."""
        with get_db_session() as session:
            query = session.query(LongTermMemory)
            if student_id:
                query = query.filter(LongTermMemory.student_id == student_id.strip().upper())
            memories = query.order_by(LongTermMemory.updated_at.desc()).all()
            return [m.to_dict() for m in memories]

    @staticmethod
    def delete_memory(memory_id: int) -> bool:
        """Delete a memory record by ID."""
        with get_db_session() as session:
            mem = session.query(LongTermMemory).filter(LongTermMemory.id == memory_id).first()
            if mem:
                session.delete(mem)
                logger.info(f"Deleted memory ID {memory_id}")
                return True
            return False

    @staticmethod
    def clear_student_memories(student_id: str) -> int:
        """Clear all memories for a specific student."""
        clean_id = student_id.strip().upper()
        with get_db_session() as session:
            count = session.query(LongTermMemory).filter(LongTermMemory.student_id == clean_id).delete()
            logger.info(f"Cleared {count} memories for student {clean_id}")
            return count
