import re

MINIMUM_JD_CHAR_COUNT = 50
MINIMUM_JD_WORD_COUNT = 10


def clean_and_normalize_jd(raw_text: str) -> str:
    """Clean and normalize pasted job description text.

    This function removes messy formatting, standardizes bullets,
    collapses extra whitespace, and strips non-printable characters.
    """
    if not raw_text or not raw_text.strip():
        return ""

    # 1. Remove NUL bytes and invisible zero-width unicode characters
    cleaned = raw_text.replace("\x00", "").replace("\u200b", "").replace("\ufeff", "")

    # 2. Standardize all line breaks to \n
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    # 3. Standardize common bullet point symbols to a simple dash '-'
    # e.g., '• Python' or '▪ React' becomes '- Python' or '- React'
    cleaned = re.sub(r"^[ \t]*[•▪►*\–—✔][ \t]*", "- ", cleaned, flags=re.MULTILINE)

    # 4. Collapse multiple horizontal spaces and tabs within lines into a single space
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    # 5. Fix spacing after our standardized dash bullets (e.g., "-Python" -> "- Python")
    cleaned = re.sub(r"^-([^\s-])", r"- \1", cleaned, flags=re.MULTILINE)

    # 6. Trim trailing whitespace from each line so empty lines are truly empty
    cleaned = "\n".join(line.strip() for line in cleaned.split("\n"))

    # 7. Collapse three or more consecutive newlines into two newlines (clean paragraphs)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # 8. Strip whitespace at the very start and end
    return cleaned.strip()


def validate_jd_text(text: str) -> tuple[bool, str]:
    """Check if the provided job description has enough content to be useful.

    Returns:
        (is_valid, error_message)
    """
    cleaned = clean_and_normalize_jd(text)

    if not cleaned:
        return False, "Job description cannot be empty."

    if len(cleaned) < MINIMUM_JD_CHAR_COUNT:
        return False, f"Job description is too short ({len(cleaned)} characters). Please paste at least {MINIMUM_JD_CHAR_COUNT} characters."

    word_count = len(cleaned.split())
    if word_count < MINIMUM_JD_WORD_COUNT:
        return False, f"Job description contains only {word_count} words. Please provide a more detailed job posting."

    return True, ""
