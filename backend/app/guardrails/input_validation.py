"""
Input Validation Guardrail.
Validates input lengths, enforces UTF-8 safety, and executes
prompt-injection detection before text reaches LLM agents.
"""
from typing import Tuple
from app.guardrails.prompt_injection import detect_prompt_injection, sanitize_prompt_input


def validate_and_sanitize_jd(raw_text: str) -> Tuple[bool, str, str | None]:
    """Validate and sanitize untrusted Job Description text.

    Args:
        raw_text: Raw JD text submitted by user.

    Returns:
        (is_valid, sanitized_text, error_message)
    """
    if not raw_text or not raw_text.strip():
        return False, "", "Job description text cannot be empty."

    cleaned = raw_text.strip()

    if len(cleaned) < 50:
        return (
            False,
            cleaned,
            f"Job description too short ({len(cleaned)} characters). Minimum 50 characters required.",
        )

    if len(cleaned) > 50000:
        return (
            False,
            cleaned,
            f"Job description exceeds maximum limit ({len(cleaned)}/50,000 characters).",
        )

    # Check for adversarial prompt injection signatures
    is_injection, reason = detect_prompt_injection(cleaned)
    if is_injection:
        return False, cleaned, f"Security Alert: {reason}"

    # Sanitize markdown and delimiter markers
    sanitized = sanitize_prompt_input(cleaned)

    return True, sanitized, None


def validate_human_feedback(feedback: str) -> Tuple[bool, str, str | None]:
    """Validate human-in-the-loop review feedback."""
    if not feedback or not feedback.strip():
        return False, "", "Feedback text cannot be empty when requesting revisions."

    cleaned = feedback.strip()
    if len(cleaned) > 2000:
        return False, cleaned, "Feedback text exceeds maximum limit (2,000 characters)."

    is_injection, reason = detect_prompt_injection(cleaned)
    if is_injection:
        return False, cleaned, f"Security Alert: {reason}"

    return True, sanitize_prompt_input(cleaned), None