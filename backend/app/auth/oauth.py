from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
import jwt

from app.config.settings import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Strictly read-only Drive scope + email so we can show which Google account is connected
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
]

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"

# Public repositories + basic profile only (matches user choice)
GITHUB_SCOPES = ["read:user", "public_repo"]


def create_oauth_state(user_id: int, provider: str) -> str:
    """Create a short-lived signed state token to prevent CSRF during OAuth."""
    payload = {
        "sub": str(user_id),
        "provider": provider,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_oauth_state(state: str, expected_provider: str) -> int | None:
    """Verify the OAuth state token and return the user_id, or None if invalid."""
    try:
        payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("provider") != expected_provider:
            return None
        user_id = payload.get("sub")
        return int(user_id) if user_id is not None else None
    except (jwt.PyJWTError, ValueError):
        return None


def build_google_auth_url(state: str) -> str:
    """Build the Google OAuth 2.0 consent page URL."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",  # Request refresh_token
        "prompt": "consent",       # Always return refresh_token on connect
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_google_code(code: str) -> dict:
    """Exchange the temporary authorization code for access and refresh tokens."""
    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        },
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()


def refresh_google_access_token(refresh_token: str) -> dict:
    """Use a stored refresh_token to get a new Google access_token."""
    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()


def get_google_user_info(access_token: str) -> dict:
    """Fetch basic Google account details (id, email) for the connected user."""
    response = httpx.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()


def build_github_auth_url(state: str) -> str:
    """Build the GitHub OAuth authorization URL."""
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": " ".join(GITHUB_SCOPES),
        "state": state,
    }
    return f"{GITHUB_AUTH_URL}?{urlencode(params)}"


def exchange_github_code(code: str) -> dict:
    """Exchange the temporary GitHub OAuth code for an access token."""
    response = httpx.post(
        GITHUB_TOKEN_URL,
        data={
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
        },
        headers={"Accept": "application/json"},
        timeout=15.0,
    )
    response.raise_for_status()
    data = response.json()
    if "error" in data or "access_token" not in data:
        raise ValueError(data.get("error_description") or "GitHub token exchange failed")
    return data


def get_github_user_info(access_token: str) -> dict:
    """Fetch basic GitHub profile details (id, login, email)."""
    response = httpx.get(
        GITHUB_USER_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "CareerCraftAI",
        },
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()


