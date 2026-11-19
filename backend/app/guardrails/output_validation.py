"""
Output Validation Guardrail.
Validates structural completeness and checks for prompt instruction leakage
in generated application packages.
"""
import re
from typing import Any, Dict, List, Tuple

# Patterns indicating potential system prompt or instruction leakage
LEAKAGE_PATTERNS = [
    r"(?i)\byou\s+are\s+an\s+elite\s+technical\b",
    r"(?i)\bcritical\s+guardrails\b",
    r"(?i)\bformat_instructions\b",
    r"(?i)\bas\s+an\s+ai\s+language\s+model\b",
    r"(?i)\bjson\s+schema\b",
]


def validate_generated_application(
    package: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """Validate that the generated application meets quality and security standards.

    Args:
        package: Dictionary representation of ApplicationPackageOutput.

    Returns:
        (is_valid, validation_errors)
    """
    errors: List[str] = []
    if not package or not isinstance(package, dict):
        return False, ["Application package is empty or not a valid dictionary."]

    resume = package.get("resume")
    cover_letter = package.get("cover_letter")

    if not resume or not isinstance(resume, dict):
        errors.append("Resume section is missing or invalid.")
    else:
        header = resume.get("header", {})
        if not header.get("full_name"):
            errors.append("Resume header is missing 'full_name'.")
        if not resume.get("professional_summary"):
            errors.append("Resume is missing 'professional_summary'.")

    if not cover_letter or not isinstance(cover_letter, dict):
        errors.append("Cover letter section is missing or invalid.")
    else:
        if not cover_letter.get("opening_paragraph"):
            errors.append("Cover letter is missing 'opening_paragraph'.")
        if not cover_letter.get("closing_paragraph"):
            errors.append("Cover letter is missing 'closing_paragraph'.")

    # Check for prompt leakage across text fields
    package_str = str(package)
    for pattern in LEAKAGE_PATTERNS:
        match = re.search(pattern, package_str)
        if match:
            errors.append(f"Potential prompt instruction leakage detected: '{match.group(0)}'")

    return len(errors) == 0, errors
