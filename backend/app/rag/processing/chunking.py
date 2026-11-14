import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
def clean_text(text: str) -> str:
    """Clean extracted PDF/GitHub text before chunking and saving to PostgreSQL."""
    if not text:
        return ""
    # PostgreSQL rejects NUL bytes (\x00), which sometimes appear in PDF extractions
    cleaned = text.replace("\x00", "")
    # Normalize Windows line endings and collapse extra spaces/blank lines
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def chunk_text(text: str, chunk_size: int = 850, overlap: int = 150) -> list[str]:
    """Preprocess text and split it into overlapping chunks."""

    cleaned= clean_text(text)
    if not cleaned:
        return []
    
    splitter= RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap= overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    return splitter.split_text(cleaned)