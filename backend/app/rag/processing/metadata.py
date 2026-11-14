import hashlib

from app.rag.processing.chunking import chunk_text, clean_text


def compute_content_hash(text: str) -> str:
    """Create a SHA-256 hash of cleaned text to detect changes during sync."""
    normalized = clean_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_chunk_records(
    user_id: int,
    doc: dict,
    chunk_size: int = 850,
    overlap: int = 150,
) -> list[dict]:
    """Split one ingested document into chunk records with source metadata."""
    raw_text = doc.get("text", "")
    chunks = chunk_text(raw_text, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        return []

    content_hash = compute_content_hash(raw_text)

    # Preserve extra source-specific fields without losing anything
    extra_metadata = {
        "document_type": doc.get("document_type"),
        "category": doc.get("category"),
        "repo": doc.get("repo"),
        "modified_time": doc.get("modified_time"),
        "updated_at": doc.get("updated_at"),
    }
    # Remove None values so metadata JSON stays clean
    extra_metadata = {k: v for k, v in extra_metadata.items() if v is not None}

    total_chunks = len(chunks)
    records: list[dict] = []

    for index, chunk_content in enumerate(chunks):
        records.append(
            {
                "user_id": user_id,
                "source_type": doc["source_type"],
                "external_id": doc["external_id"],
                "title": doc["title"],
                "url": doc.get("url"),
                "chunk_index": index,
                "total_chunks": total_chunks,
                "content": chunk_content,
                "content_hash": content_hash,
                "metadata": extra_metadata,
            }
        )

    return records


def build_chunks_for_documents(
    user_id: int,
    documents: list[dict],
    chunk_size: int = 850,
    overlap: int = 150,
) -> list[dict]:
    """Process a list of ingested Drive and GitHub documents into chunk records."""
    all_records: list[dict] = []
    for doc in documents:
        all_records.extend(
            build_chunk_records(
                user_id=user_id,
                doc=doc,
                chunk_size=chunk_size,
                overlap=overlap,
            )
        )
    return all_records