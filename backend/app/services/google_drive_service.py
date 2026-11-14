from datetime import datetime, timedelta, timezone

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.oauth import refresh_google_access_token
from app.auth.security import decrypt_token, encrypt_token
from app.models.external_connection import ExternalConnection
from app.schemas.integration import DriveFileItem, DriveFilesResponse

GOOGLE_PROVIDER = "google_drive"
GOOGLE_DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"

# Strictly PDF and DOCX MIME types as configured
PDF_MIME_TYPE = "application/pdf"
DOCX_MIME_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

SUPPORTED_MIME_TYPES = {
    PDF_MIME_TYPE: "PDF",
    DOCX_MIME_TYPE: "DOCX",
}

CANDIDATE_KEYWORDS = (
    "resume",
    "cv",
    "cover",
    "portfolio",
    "experience",
    "profile",
    "bio",
    "certificate",
    "transcript",
    "letter",
    "career",
)


def get_google_connection(user_id: int, db: Session) -> ExternalConnection | None:
    """Fetch the user's stored Google Drive connection, if any."""
    return (
        db.query(ExternalConnection)
        .filter(
            ExternalConnection.user_id == user_id,
            ExternalConnection.provider == GOOGLE_PROVIDER,
        )
        .first()
    )


def save_google_connection(
    user_id: int,
    token_data: dict,
    user_info: dict,
    db: Session,
) -> ExternalConnection:
    """Create or update an encrypted Google Drive connection for the user."""
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_in = int(token_data.get("expires_in", 3600))
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    connection = get_google_connection(user_id, db)
    if connection is None:
        connection = ExternalConnection(
            user_id=user_id,
            provider=GOOGLE_PROVIDER,
            provider_account_id=user_info.get("id"),
            provider_email=user_info.get("email"),
            encrypted_access_token=encrypt_token(access_token),
            encrypted_refresh_token=(
                encrypt_token(refresh_token) if refresh_token else None
            ),
            token_expires_at=expires_at,
            scopes=token_data.get("scope", ""),
        )
        db.add(connection)
    else:
        connection.provider_account_id = user_info.get("id")
        connection.provider_email = user_info.get("email")
        connection.encrypted_access_token = encrypt_token(access_token)
        if refresh_token:
            connection.encrypted_refresh_token = encrypt_token(refresh_token)
        connection.token_expires_at = expires_at
        connection.scopes = token_data.get("scope", connection.scopes)

    db.commit()
    db.refresh(connection)
    return connection


def disconnect_google_connection(user_id: int, db: Session) -> bool:
    """Remove the user's stored Google Drive connection."""
    connection = get_google_connection(user_id, db)
    if connection is None:
        return False
    db.delete(connection)
    db.commit()
    return True


def _refresh_connection_token(connection: ExternalConnection, db: Session) -> str:
    """Refresh an expired Google access token and store the new encrypted token."""
    if not connection.encrypted_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google Drive token expired. Please reconnect your Google Drive.",
        )

    refresh_token = decrypt_token(str(connection.encrypted_refresh_token))
    try:
        token_data = refresh_google_access_token(refresh_token)
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh Google Drive session. Please reconnect.",
        )

    new_access_token = token_data["access_token"]
    expires_in = int(token_data.get("expires_in", 3600))
    connection.encrypted_access_token = encrypt_token(new_access_token)
    connection.token_expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=expires_in
    )
    db.commit()
    db.refresh(connection)
    return new_access_token


def _get_valid_access_token(connection: ExternalConnection, db: Session) -> str:
    """Return a valid Google access token, refreshing if close to expiration."""
    expires_at = connection.token_expires_at
    if expires_at is not None:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) >= expires_at - timedelta(seconds=60):
            return _refresh_connection_token(connection, db)

    return decrypt_token(str(connection.encrypted_access_token))


def classify_drive_file(raw_file: dict) -> DriveFileItem | None:
    """Keep strictly PDF and DOCX files and annotate candidate relevance."""
    mime_type = raw_file.get("mimeType", "")
    document_type = SUPPORTED_MIME_TYPES.get(mime_type)
    if document_type is None:
        return None

    name = raw_file.get("name", "Untitled")
    lower_name = name.lower()
    matched_keyword = next(
        (kw for kw in CANDIDATE_KEYWORDS if kw in lower_name),
        None,
    )

    if matched_keyword:
        is_relevant = True
        reason = f"Matches candidate keyword '{matched_keyword}'"
    else:
        is_relevant = False
        reason = f"Authorized {document_type} file"

    raw_size = raw_file.get("size")
    size_bytes = int(raw_size) if raw_size is not None else None

    return DriveFileItem(
        id=raw_file["id"],
        name=name,
        mime_type=mime_type,
        document_type=document_type,
        size_bytes=size_bytes,
        modified_time=raw_file.get("modifiedTime"),
        web_view_link=raw_file.get("webViewLink"),
        is_candidate_relevant=is_relevant,
        relevance_reason=reason,
    )


def fetch_relevant_drive_files(user_id: int, db: Session) -> DriveFilesResponse:
    """Retrieve authorized PDF and DOCX file metadata from Google Drive."""
    connection = get_google_connection(user_id, db)
    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google Drive is not connected yet",
        )

    access_token = _get_valid_access_token(connection, db)

    query = (
        "trashed = false and "
        f"(mimeType = '{PDF_MIME_TYPE}' or mimeType = '{DOCX_MIME_TYPE}')"
    )
    params = {
        "q": query,
        "fields": "files(id, name, mimeType, size, modifiedTime, webViewLink)",
        "orderBy": "modifiedTime desc",
        "pageSize": 50,
    }

    response = httpx.get(
        GOOGLE_DRIVE_FILES_URL,
        params=params,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15.0,
    )

    # Retry once with refreshed token if Google rejected the access token
    if response.status_code == 401 and connection.encrypted_refresh_token:
        access_token = _refresh_connection_token(connection, db)
        response = httpx.get(
            GOOGLE_DRIVE_FILES_URL,
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15.0,
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch files from Google Drive API",
        )

    raw_files = response.json().get("files", [])
    classified_files = []
    for raw_file in raw_files:
        item = classify_drive_file(raw_file)
        if item is not None:
            classified_files.append(item)

    # Put likely candidate documents (resumes, CVs, etc.) first
    classified_files.sort(key=lambda item: not item.is_candidate_relevant)
    relevant_count = sum(1 for item in classified_files if item.is_candidate_relevant)

    return DriveFilesResponse(
        total_files=len(classified_files),
        relevant_count=relevant_count,
        files=classified_files,
    )

