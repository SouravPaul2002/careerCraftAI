from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.auth.oauth import (
    build_github_auth_url,
    create_oauth_state,
    exchange_github_code,
    get_github_user_info,
    verify_oauth_state,
)
from app.config.settings import settings
from app.database.session import get_db
from app.models.user import User
from app.schemas.integration import (
    GitHubConnectionStatus,
    GitHubRepoFilesResponse,
    GitHubReposResponse,
    OAuthUrlResponse,
)
from app.services.github_service import (
    disconnect_github_connection,
    fetch_authorized_repositories,
    fetch_repository_relevant_files,
    get_github_connection,
    save_github_connection,
)

router = APIRouter(prefix="/api/integrations/github", tags=["GitHub"])


@router.get("/auth-url", response_model=OAuthUrlResponse)
def get_github_auth_url(current_user: User = Depends(get_current_user)):
    """Generate the GitHub OAuth authorization URL for the logged-in user."""
    if (
        not settings.GITHUB_CLIENT_ID.strip()
        or not settings.GITHUB_CLIENT_SECRET.strip()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "GitHub OAuth is not configured yet. "
                "Add GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET to backend/.env."
            ),
        )

    state = create_oauth_state(int(current_user.id), provider="github")
    return OAuthUrlResponse(auth_url=build_github_auth_url(state))


@router.get("/callback")
def github_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    """Handle GitHub's redirect after the user approves or cancels access."""
    dashboard_url = f"{settings.FRONTEND_URL}/dashboard"

    if error:
        return RedirectResponse(
            url=f"{dashboard_url}?github=error&message={quote(error)}"
        )

    if not code or not state:
        return RedirectResponse(
            url=f"{dashboard_url}?github=error&message={quote('Missing OAuth code or state')}"
        )

    user_id = verify_oauth_state(state, expected_provider="github")
    if user_id is None:
        return RedirectResponse(
            url=f"{dashboard_url}?github=error&message={quote('Invalid or expired OAuth state')}"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return RedirectResponse(
            url=f"{dashboard_url}?github=error&message={quote('User account not found')}"
        )

    try:
        token_data = exchange_github_code(code)
        user_info = get_github_user_info(token_data["access_token"])
    except (httpx.HTTPError, ValueError):
        return RedirectResponse(
            url=f"{dashboard_url}?github=error&message={quote('Failed to complete GitHub authentication')}"
        )

    save_github_connection(
        user_id=user_id,
        token_data=token_data,
        user_info=user_info,
        db=db,
    )
    return RedirectResponse(url=f"{dashboard_url}?github=connected")


@router.get("/status", response_model=GitHubConnectionStatus)
def get_github_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check whether the logged-in user has connected GitHub."""
    connection = get_github_connection(int(current_user.id), db)
    if connection is None:
        return GitHubConnectionStatus(connected=False)

    scopes_text = str(connection.scopes) if connection.scopes else ""
    scopes_list = scopes_text.replace(",", " ").split() if scopes_text else []
    return GitHubConnectionStatus(
        connected=True,
        username=str(connection.provider_email) if connection.provider_email else None,
        scopes=scopes_list,
        connected_at=connection.created_at,
    )


@router.delete("/disconnect")
def disconnect_github(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect GitHub and remove stored tokens for the logged-in user."""
    disconnect_github_connection(int(current_user.id), db)
    return {"message": "GitHub disconnected"}


@router.get("/repos", response_model=GitHubReposResponse)
def list_github_repos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve authorized public repositories for the connected GitHub user."""
    return fetch_authorized_repositories(int(current_user.id), db)


@router.get("/repos/{owner}/{repo}/files", response_model=GitHubRepoFilesResponse)
def list_github_repo_files(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Identify documentation, manifest, and source files inside a public repo."""
    return fetch_repository_relevant_files(int(current_user.id), owner, repo, db)

