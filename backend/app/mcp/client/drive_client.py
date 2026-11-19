"""
Google Drive MCP Client & Tools for CareerCraft AI.
Enables AI agents to search documents, retrieve metadata, and read document contents on demand.
"""
import io
import logging
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy.orm import Session

from app.database.connection import engine
from app.models.external_connection import ExternalConnection
from app.rag.ingestion.document_parser import extract_text_from_pdf
from app.services.google_drive_service import _get_valid_access_token

logger = logging.getLogger(__name__)

GOOGLE_DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"


def get_user_drive_token(user_id: int) -> Optional[str]:
    """Retrieve and validate the authenticated user's Google Drive OAuth token."""
    with Session(engine) as db:
        connection = (
            db.query(ExternalConnection)
            .filter(
                ExternalConnection.user_id == user_id,
                ExternalConnection.provider == "google_drive",
            )
            .first()
        )
        if not connection or not connection.encrypted_access_token:
            return None
        try:
            return _get_valid_access_token(connection, db)
        except Exception as e:
            logger.error(f"Failed to obtain valid Google Drive token for user {user_id}: {e}")
            return None


def _drive_headers(access_token: str) -> Dict[str, str]:
    """Construct standard headers for Google Drive API requests."""
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }


def search_drive_files(
    access_token: str,
    query: str = "",
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Search or list files in the user's Google Drive.

    Args:
        access_token: Valid Google OAuth access token.
        query: Optional search keyword or filename query.
        limit: Maximum number of files to return (up to 20).
    """
    url = f"{GOOGLE_DRIVE_API_BASE}/files"
    # Filter out trashed files
    q_parts = ["trashed = false"]
    if query.strip():
        # Match filename containing query
        safe_query = query.replace("'", "\\'")
        q_parts.append(f"name contains '{safe_query}'")

    params = {
        "q": " and ".join(q_parts),
        "fields": "files(id, name, mimeType, size, modifiedTime, webViewLink)",
        "pageSize": min(limit, 20),
    }

    try:
        response = httpx.get(
            url,
            headers=_drive_headers(access_token),
            params=params,
            timeout=15.0,
        )
        response.raise_for_status()

        data = response.json()
        files = data.get("files", [])
        return [
            {
                "file_id": f.get("id"),
                "name": f.get("name"),
                "mime_type": f.get("mimeType"),
                "size": int(f.get("size", 0)),
                "modified_time": f.get("modifiedTime"),
                "web_view_link": f.get("webViewLink"),
            }
            for f in files
        ]
    except Exception as e:
        logger.error(f"Google Drive MCP error in search_drive_files: {e}")
        return [{"error": str(e)}]


def get_drive_file_metadata(access_token: str, file_id: str) -> Dict[str, Any]:
    """Retrieve detailed metadata for a specific Google Drive file."""
    url = f"{GOOGLE_DRIVE_API_BASE}/files/{file_id}"
    params = {"fields": "id, name, mimeType, size, modifiedTime, webViewLink, description"}

    try:
        response = httpx.get(
            url,
            headers=_drive_headers(access_token),
            params=params,
            timeout=15.0,
        )
        if response.status_code == 404:
            return {"error": f"Drive file '{file_id}' not found."}
        response.raise_for_status()

        data = response.json()
        return {
            "file_id": data.get("id"),
            "name": data.get("name"),
            "mime_type": data.get("mimeType"),
            "size": int(data.get("size", 0)),
            "modified_time": data.get("modifiedTime"),
            "web_view_link": data.get("webViewLink"),
            "description": data.get("description"),
        }
    except Exception as e:
        logger.error(f"Google Drive MCP error in get_drive_file_metadata for {file_id}: {e}")
        return {"error": str(e)}


def read_drive_file_content(
    access_token: str,
    file_id: str,
    mime_type: str = "",
    max_chars: int = 12000,
) -> str:
    """Download and extract the textual content of a Google Drive document or PDF.

    Args:
        access_token: Valid Google OAuth access token.
        file_id: Google Drive file identifier.
        mime_type: File MIME type (if known, avoids extra metadata request).
        max_chars: Maximum characters to return to prevent prompt blowup.
    """
    # 1. If mime_type is unknown, fetch metadata first
    if not mime_type:
        meta = get_drive_file_metadata(access_token, file_id)
        if "error" in meta:
            return f"Error: {meta['error']}"
        mime_type = meta.get("mime_type", "")

    # 2. Case A: Google Docs (native export to plain text)
    if mime_type == "application/vnd.google-apps.document":
        export_url = f"{GOOGLE_DRIVE_API_BASE}/files/{file_id}/export"
        try:
            response = httpx.get(
                export_url,
                headers=_drive_headers(access_token),
                params={"mimeType": "text/plain"},
                timeout=20.0,
            )
            response.raise_for_status()
            return response.text[:max_chars]
        except Exception as e:
            logger.error(f"Error exporting Google Doc {file_id}: {e}")
            return f"Error reading Google Doc: {str(e)}"

    # 3. Case B: Binary or downloadable files (PDF, plain text, etc.)
    download_url = f"{GOOGLE_DRIVE_API_BASE}/files/{file_id}?alt=media"
    try:
        response = httpx.get(
            download_url,
            headers=_drive_headers(access_token),
            timeout=25.0,
        )
        response.raise_for_status()
        raw_bytes = response.content

        # Extract text from PDF
        if "pdf" in mime_type.lower():
            text = extract_text_from_pdf(raw_bytes)
            return text[:max_chars]

        # Plain text, markdown, CSV, or code
        return raw_bytes.decode("utf-8", errors="replace")[:max_chars]

    except Exception as e:
        logger.error(f"Error downloading Drive file {file_id}: {e}")
        return f"Error reading file content: {str(e)}"