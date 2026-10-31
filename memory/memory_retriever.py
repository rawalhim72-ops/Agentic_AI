"""
Memory Retriever Module.
Selectively retrieves only relevant long-term memories for a student given their current query.
Avoids dumping all memories into LLM prompt.
"""

import logging
from typing import List, Dict, Any, Optional
from database.db import get_db_session
from database.models import LongTermMemory

logger = logging.getLogger("memory.memory_retriever")

# Mapping of query keywords to memory keys
KEYWORD_TO_MEMORY_KEYS = {
    "programme": ["programme", "degree", "course", "major", "field", "study", "studying"],
    "preferred_name": ["name", "who am i", "call me", "remember me", "identity"],
    "response_style": ["style", "format", "bullet", "concise", "brief", "detailed"],
    "academic_interest": ["interest", "career", "goal", "specialization", "focus", "research", "project"],
}


def retrieve_relevant_memories(student_id: str, query: str) -> Dict[str, Any]:
    """
    Selectively retrieves memories matching the student and the current question context.
    Does NOT return all memories indiscriminately.
    """
    if not student_id:
        return {
            "status": "EMPTY",
            "memories": [],
            "formatted_context": "",
            "message": "No student ID provided for memory lookup.",
        }

    clean_id = student_id.strip().upper()
    lower_query = query.lower() if query else ""

    with get_db_session() as session:
        all_student_memories = session.query(LongTermMemory).filter(
            LongTermMemory.student_id == clean_id
        ).all()

        if not all_student_memories:
            return {
                "status": "EMPTY",
                "memories": [],
                "formatted_context": "",
                "message": f"No long-term memories stored for student {clean_id}.",
            }

        # Filter strictly for relevance
        selected_memories = []

        # Check which memory keys match the query keywords
        relevant_keys = set()
        for mem_key, keywords in KEYWORD_TO_MEMORY_KEYS.items():
            if any(kw in lower_query for kw in keywords):
                relevant_keys.add(mem_key)

        for mem in all_student_memories:
            # If query directly asks about or references this memory key
            if mem.memory_key in relevant_keys:
                selected_memories.append(mem)
            # Always include preferred name if student asks a personal question or greeting
            elif mem.memory_key == "preferred_name" and any(k in lower_query for k in ["hello", "hi", "hey", "who", "i am", "my"]):
                if mem not in selected_memories:
                    selected_memories.append(mem)

        # If no specific keyword matched, but query is a personal query like "what do you know about me?", return all
        if not selected_memories and any(phrase in lower_query for phrase in ["know about me", "my profile", "my details", "remember about me"]):
            selected_memories = list(all_student_memories)

        if not selected_memories:
            return {
                "status": "NO_RELEVANT_MEMORY",
                "memories": [],
                "formatted_context": "",
                "message": "No memories were determined relevant to this specific query.",
            }

        memories_data = [m.to_dict() for m in selected_memories]
        formatted_context = "\n".join(
            f"- Student's {m['memory_key'].replace('_', ' ').title()}: {m['memory_value']} (stored from prior session)"
            for m in memories_data
        )

        logger.info(f"Retrieved {len(memories_data)} relevant memories for {clean_id} (keys: {[m['memory_key'] for m in memories_data]}).")

        return {
            "status": "SUCCESS",
            "memories": memories_data,
            "formatted_context": formatted_context,
            "message": f"Retrieved {len(memories_data)} relevant personal memory items.",
        }
