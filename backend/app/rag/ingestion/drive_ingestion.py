import logging
import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import DiscoveredItem
from app.rag.ingestion.document_parser import parse_document
from app.services.google_drive_service import (
    GOOGLE_DRIVE_FILES_URL,
    _get_valid_access_token,
    get_google_connection,
)

logger = logging.getLogger(__name__)


def download_drive_file_bytes(file_id: str, user_id: int, db: Session) -> bytes:
    """Download the raw bytes of a Google Drive file using alt=media."""
    connection = get_google_connection(user_id, db)
    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google Drive is not connected",
        )

    access_token = _get_valid_access_token(connection, db)
    file_url = f"{GOOGLE_DRIVE_FILES_URL}/{file_id}"

    response = httpx.get(
        file_url,
        params={"alt": "media"},
        headers={"Authorization": f"Bearer {access_token}"},
        follow_redirects=True,
        timeout=30.0,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to download Drive file {file_id}: HTTP {response.status_code}",
        )

    return response.content


def ingest_selected_drive_documents(user_id: int, db: Session) -> list[dict]:
    """Download and extract text from all user-selected Google Drive files."""
    selected_items = (
        db.query(DiscoveredItem)
        .filter(
            DiscoveredItem.user_id == user_id,
            DiscoveredItem.source_type == "google_drive",
            DiscoveredItem.is_selected.is_(True),
        )
        .all()
    )

    documents: list[dict] = []

    for item in selected_items:
        file_type = str(item.subtitle or "").upper()
        if file_type not in ("PDF", "DOCX"):
            continue

        try:
            file_bytes = download_drive_file_bytes(str(item.external_id), user_id, db)
            extracted_text = parse_document(file_bytes, file_type)
        except Exception as err:
            logger.warning(f"Skipping Drive file '{item.title}' due to download/parse error: {err}")
            continue

        if not extracted_text.strip():
            continue

        details = item.details if isinstance(item.details, dict) else {}
        documents.append(
            {
                "external_id": str(item.external_id),
                "source_type": "google_drive",
                "title": str(item.title),
                "document_type": file_type,
                "url": str(item.url) if item.url else None,
                "modified_time": details.get("modified_time"),
                "text": extracted_text,
            }
        )

    return documents
