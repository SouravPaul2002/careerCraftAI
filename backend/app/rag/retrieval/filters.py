VALID_SOURCE_TYPES = {"google_drive", "github_repo"}
VALID_DOCUMENT_TYPES = {"PDF", "DOCX"}
VALID_CATEGORIES = {"documentation", "manifest", "source"}


def build_metadata_filter(
    source_type: str | None = None,
    document_type: str | None = None,
    category: str | None = None,
    repo: str | None = None,
    external_id: str | None = None,
) -> dict[str, str] | None:
    """Validate and build optional metadata filters for ChromaDB queries."""
    filters: dict[str, str] = {}

    if source_type is not None:
        cleaned = source_type.strip()
        if cleaned not in VALID_SOURCE_TYPES:
            raise ValueError(f"source_type must be one of {sorted(VALID_SOURCE_TYPES)}")
        filters["source_type"] = cleaned

    if document_type is not None:
        cleaned = document_type.strip().upper()
        if cleaned not in VALID_DOCUMENT_TYPES:
            raise ValueError(f"document_type must be one of {sorted(VALID_DOCUMENT_TYPES)}")
        filters["document_type"] = cleaned

    if category is not None:
        cleaned = category.strip().lower()
        if cleaned not in VALID_CATEGORIES:
            raise ValueError(f"category must be one of {sorted(VALID_CATEGORIES)}")
        filters["category"] = cleaned

    if repo is not None and repo.strip():
        filters["repo"] = repo.strip()

    if external_id is not None and external_id.strip():
        filters["external_id"] = external_id.strip()

    return filters or None


def build_chroma_where(
    user_id: int,
    source_type: str | None = None,
    document_type: str | None = None,
    category: str | None = None,
    repo: str | None = None,
    external_id: str | None = None,
) -> dict:
    """Build a complete ChromaDB 'where' clause that always isolates by user_id."""
    conditions: list[dict] = [{"user_id": user_id}]
    extra = build_metadata_filter(
        source_type=source_type,
        document_type=document_type,
        category=category,
        repo=repo,
        external_id=external_id,
    )
    if extra:
        for key, value in extra.items():
            conditions.append({key: value})

    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}

