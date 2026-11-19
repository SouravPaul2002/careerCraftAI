"""
Prompt Injection Defense Guardrail.
Detects and neutralizes adversarial prompt injection, jailbreaks,
and delimiter smuggling in untrusted Job Descriptions or user inputs.
"""
import re
from typing import Tuple

# High-risk adversarial injection signatures
INJECTION_PATTERNS = [
    # Catches: "ignore all instructions", "ignore all instruction", "ignore instructions", "ignore previous instructions"
    r"(?i)\bignore\s+(all\s+|any\s+)?(previous\s+|prior\s+|above\s+|system\s+)?(instructions?|prompts?|rules?|commands?|guidelines?)\b",
    
    # Catches: "ignore everything", "ignore everything above", "ignore all above"
    r"(?i)\bignore\s+(everything|all)(\s+(above|before|previously))?\b",
    
    # Catches: "disregard all instructions", "disregard instructions", "disregard previous prompts"
    r"(?i)\bdisregard\s+(all\s+|any\s+)?(previous\s+|prior\s+|above\s+|system\s+)?(instructions?|prompts?|rules?|commands?)\b",
    
    # Catches: "forget all instructions", "forget previous instructions", "forget rules"
    r"(?i)\bforget\s+(all\s+|everything\s+)?(previous\s+|prior\s+|above\s+)?(instructions?|prompts?|rules?|constraints?)\b",
    
    # System and developer mode overrides
    r"(?i)\b(system\s+override|admin\s+override|developer\s+mode)\b",
    r"(?i)\byou\s+are\s+now\s+(in\s+developer\s+mode|unrestricted|DAN)\b",
    r"(?i)\bdo\s+not\s+follow\s+(the\s+)?(system|above|any)\s+(prompt|instructions?)\b",
    r"(?i)\b(bypass|disable)\s+(security|safety|ethical|content)\s+(filters|checks|guidelines)\b",
    r"(?i)\boutput\s+only\s+(json|approved|yes)\s+regardless\s+of\b",
    r"(?i)\bpretend\s+you\s+are\s+not\s+an\s+ai\b",
]

# Delimiter markers used internally by our agent templates
INTERNAL_DELIMITERS = [
    r"===\s*TARGET\s+JOB\s+ANALYSIS.*===",
    r"===\s*CANDIDATE\s+PROFILE.*===",
    r"===\s*SUPERVISOR\s+STRATEGY.*===",
    r"===\s*SYSTEM.*===",
    r"===\s*CRITIQUE\s+END.*===",
]


def detect_prompt_injection(text: str) -> Tuple[bool, str | None]:
    """Scan input text for prompt injection attempts or malicious overrides.

    Args:
        text: Raw text to scan (e.g. Job Description).

    Returns:
        (is_injection_detected, reason_message)
    """
    if not text or not text.strip():
        return False, None

    # 1. Check for known injection patterns
    for pattern in INJECTION_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return True, f"Potential prompt injection detected matching signature: '{match.group(0)}'"

    # 2. Check for delimiter hijacking attempts
    for delim in INTERNAL_DELIMITERS:
        if re.search(delim, text, re.IGNORECASE):
            return True, "Potential delimiter smuggling detected: unauthorized internal prompt markers."

    return False, None


def sanitize_prompt_input(text: str) -> str:
    """Sanitize input text by escaping or stripping delimiter hijacking attempts.

    Args:
        text: Raw input text.

    Returns:
        Sanitized safe string suitable for prompt inclusion.
    """
    if not text:
        return ""

    sanitized = text

    # Neutralize repeated triple-equals headers used as section boundaries
    sanitized = re.sub(r"={3,}", "---", sanitized)

    # Neutralize excessive markdown fences (avoid early prompt closing)
    sanitized = re.sub(r"`{4,}", "```", sanitized)

    # Strip HTML script or hidden injection comments
    sanitized = re.sub(r"<!--.*?-->", "", sanitized, flags=re.DOTALL)

    return sanitized.strip()