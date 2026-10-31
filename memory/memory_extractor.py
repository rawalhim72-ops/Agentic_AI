"""
Memory Extractor with Sensitive Information Filtering.
Extracts persistent profile attributes (preferred name, programme, academic interests, style)
while strictly blocking sensitive credentials (OTPs, passwords, financial account tokens).
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("memory.memory_extractor")

# Regex patterns for sensitive information that MUST be blocked
SENSITIVE_PATTERNS = [
    (r"\b(otp|one[\s-]?time[\s-]?password|pin|verification[\s-]?code)\b", "Contains OTP or one-time verification pattern"),
    (r"\b(password|passwd|secret|api[\s_-]?key|bearer\s+[a-zA-Z0-9_\-\.]+)\b", "Contains password, secret, or API token reference"),
    (r"\b\d{4,8}\b.*(otp|pin|verify|code)", "Contains numeric authentication code with verification term"),
    (r"(otp|pin|code)[\s:=]+(\d{4,8})", "Contains direct OTP / PIN assignment"),
    (r"\b(card\s*number|cvv|cvc|credit\s*card|debit\s*card)\b", "Contains payment card credential term"),
    (r"\b[3-6]\d{3}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "Contains credit/debit card number sequence"),
]

# Temporary conversational utterances that should NOT be stored as long-term memories
TRIVIAL_PATTERNS = [
    r"^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|howdy)\b",
    r"^(ok|okay|thanks|thank\s+you|got\s+it|bye|goodbye|see\s+you)\b",
    r"^(what\s+is\s+\d+\s*[\+\-\*\/]\s*\d+)",  # Math calculations like 2+2
    r"^test\b",
]


class ExtractionDecision:
    def __init__(self, accepted: bool, key: Optional[str] = None, value: Optional[str] = None, reason: str = ""):
        self.accepted = accepted
        self.key = key
        self.value = value
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accepted": self.accepted,
            "key": self.key,
            "value": self.value,
            "reason": self.reason,
        }


def analyze_and_extract_memory(text: str) -> List[ExtractionDecision]:
    """
    Analyzes input text to extract non-sensitive, persistent student preferences or academic facts.
    Returns list of decisions with reasons (logged without exposing sensitive content).
    """
    decisions = []
    if not text or not text.strip():
        return decisions

    clean_text = text.strip()
    lower_text = clean_text.lower()

    # 1. Check Sensitive Filter First
    for pattern, reason in SENSITIVE_PATTERNS:
        if re.search(pattern, lower_text, re.IGNORECASE):
            logger.warning(f"Memory extraction REJECTED: {reason} [Sensitive filter triggered]")
            decisions.append(ExtractionDecision(
                accepted=False,
                key="SENSITIVE_CONTENT_BLOCKED",
                value=None,
                reason=f"REJECTED: Security filter triggered ({reason})."
            ))
            return decisions  # Drop entire extraction for security

    # 2. Check Trivial Filter
    for pat in TRIVIAL_PATTERNS:
        if re.search(pat, lower_text, re.IGNORECASE):
            decisions.append(ExtractionDecision(
                accepted=False,
                key="TRIVIAL_MESSAGE",
                value=None,
                reason="REJECTED: Temporary greeting, courtesy remark, or transient query."
            ))
            return decisions

    # 3. Extract Preferred Name
    # Patterns: "my preferred name is Rahul", "call me Rahul", "my name is Rahul"
    name_match = re.search(r"(?:preferred\s+name\s+is|call\s+me|my\s+name\s+is)\s+([A-Za-z]+)", clean_text, re.IGNORECASE)
    if name_match:
        extracted_name = name_match.group(1).capitalize().strip(".,;:!? ")
        decisions.append(ExtractionDecision(
            accepted=True,
            key="preferred_name",
            value=extracted_name,
            reason="ACCEPTED: Identified student preferred name."
        ))
        logger.info(f"Memory accepted: preferred_name = {extracted_name}")

    # 4. Extract Programme / Degree Information
    # Patterns: "studying MBA", "enrolled in MBA", "programme is MBA", "doing B.Tech"
    prog_match = re.search(r"(?:studying|enrolled\s+in|pursuing|doing|programme\s+is|degree\s+is|course\s+is)\s+([A-Za-z\.\s]{2,25}(?:MBA|B\.?Tech|M\.?Sc|BBA|Ph\.?D|Engineering|Science|Management|Arts)?)", clean_text, re.IGNORECASE)
    if prog_match:
        prog_raw = prog_match.group(1).strip()
        # Clean trailing filler words like "and", "in", "at"
        prog_clean = re.sub(r"\s+(and|at|in|with).*$", "", prog_raw, flags=re.IGNORECASE).strip().strip(".,;:!? ")
        if len(prog_clean) >= 2:
            decisions.append(ExtractionDecision(
                accepted=True,
                key="programme",
                value=prog_clean,
                reason="ACCEPTED: Identified academic programme/degree."
            ))
            logger.info(f"Memory accepted: programme = {prog_clean}")

    # 5. Extract Communication / Response Style
    style_match = re.search(r"(?:prefer|like|want)\s+(?:responses?\s+in\s+|answers?\s+in\s+)?(bullet\s*points?|concise|detailed|brief|summary\s+format)", clean_text, re.IGNORECASE)
    if style_match:
        style_val = style_match.group(1).lower().strip(".,;:!? ")
        decisions.append(ExtractionDecision(
            accepted=True,
            key="response_style",
            value=style_val,
            reason="ACCEPTED: Identified preferred response communication style."
        ))
        logger.info(f"Memory accepted: response_style = {style_val}")

    # 6. Extract Academic Interest or Specialization
    interest_match = re.search(r"(?:interested\s+in|focusing\s+on|specializing\s+in)\s+([A-Za-z\s]{3,35})", clean_text, re.IGNORECASE)
    if interest_match:
        interest_val = interest_match.group(1).strip()
        # Filter out common stop phrase
        interest_clean = re.sub(r"\s+(and|at|in|my).*$", "", interest_val, flags=re.IGNORECASE).strip().strip(".,;:!? ")
        if len(interest_clean) >= 3 and interest_clean.lower() not in ["the", "this", "that"]:
            decisions.append(ExtractionDecision(
                accepted=True,
                key="academic_interest",
                value=interest_clean,
                reason="ACCEPTED: Identified non-sensitive academic interest."
            ))
            logger.info(f"Memory accepted: academic_interest = {interest_clean}")

    return decisions
