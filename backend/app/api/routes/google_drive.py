from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.auth.oauth import (
    build_google_auth_url,
    create_oauth_state,
    exchange_google_code,
    get_google_user_info,
    verify_oauth_state,
)
from app.config.settings import settings
from app.database.session import get_db
from app.models.user import User
from app.schemas.integration import (
    DriveFilesResponse,
    GoogleConnectionStatus,
    OAuthUrlResponse,
)
from app.services.google_drive_service import (
    disconnect_google_connection,
    fetch_relevant_drive_files,
    get_google_connection,
    save_google_connection,
)

router = APIRouter(prefix="/api/integrations/google", tags=["Google Drive"])


@router.get("/auth-url", response_model=OAuthUrlResponse)
def get_google_auth_url(current_user: User = Depends(get_current_user)):
    """Generate the Google OAuth 2.0 consent URL for the logged-in user."""
    if (
        not settings.GOOGLE_CLIENT_ID.strip()
        or not settings.GOOGLE_CLIENT_SECRET.strip()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Google OAuth is not configured yet. "
                "Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to backend/.env."
            ),
        )

    state = create_oauth_state(int(current_user.id), provider="google_drive")
    return OAuthUrlResponse(auth_url=build_google_auth_url(state))


@router.get("/callback")
def google_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    """Handle Google's redirect after the user grants or denies permission."""
    dashboard_url = f"{settings.FRONTEND_URL}/dashboard"

    if error:
        return RedirectResponse(url=f"{dashboard_url}?google=error&message={quote(error)}")

    if not code or not state:
        return RedirectResponse(
            url=f"{dashboard_url}?google=error&message={quote('Missing OAuth code or state')}"
        )

    user_id = verify_oauth_state(state, expected_provider="google_drive")
    if user_id is None:
        return RedirectResponse(
            url=f"{dashboard_url}?google=error&message={quote('Invalid or expired OAuth state')}"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return RedirectResponse(
            url=f"{dashboard_url}?google=error&message={quote('User account not found')}"
        )

    try:
        token_data = exchange_google_code(code)
        user_info = get_google_user_info(token_data["access_token"])
    except httpx.HTTPError:
        return RedirectResponse(
            url=f"{dashboard_url}?google=error&message={quote('Failed to complete Google authentication')}"
        )

    save_google_connection(
        user_id=user_id,
        token_data=token_data,
        user_info=user_info,
        db=db,
    )
    return RedirectResponse(url=f"{dashboard_url}?google=connected")


@router.get("/status", response_model=GoogleConnectionStatus)
def get_google_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check whether the logged-in user has connected Google Drive."""
    connection = get_google_connection(int(current_user.id), db)
    if connection is None:
        return GoogleConnectionStatus(connected=False)

    scopes_text = str(connection.scopes) if connection.scopes else ""
    return GoogleConnectionStatus(
        connected=True,
        email=str(connection.provider_email) if connection.provider_email else None,
        scopes=scopes_text.split() if scopes_text else [],
        connected_at=connection.created_at,
    )


@router.delete("/disconnect")
def disconnect_google(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect Google Drive and delete stored tokens for the logged-in user."""
    disconnect_google_connection(int(current_user.id), db)
    return {"message": "Google Drive disconnected"}


@router.get("/files", response_model=DriveFilesResponse)
def list_google_drive_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve authorized PDF and DOCX metadata from the user's Google Drive."""
    return fetch_relevant_drive_files(int(current_user.id), db)

