import os
import re

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import decrypt_token, encrypt_token
from app.models.external_connection import ExternalConnection
from app.schemas.integration import (
    GitHubFileItem,
    GitHubRepoFilesResponse,
    GitHubRepoItem,
    GitHubReposResponse,
)

GITHUB_PROVIDER = "github"
GITHUB_API_BASE = "https://api.github.com"

IGNORED_DIR_PARTS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "venv",
    ".venv",
    "myenv",
    "__pycache__",
    ".next",
    "target",
    "vendor",
}

MANIFEST_FILENAMES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "setup.py",
    "pipfile",
    "pom.xml",
    "build.gradle",
    "go.mod",
    "cargo.toml",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
}

SOURCE_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".cs",
    ".rb",
    ".php",
    ".sql",
    ".kt",
    ".swift",
}

SLUG_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def _github_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "CareerCraftAI",
    }


def get_github_connection(user_id: int, db: Session) -> ExternalConnection | None:
    """Fetch the user's stored GitHub connection, if any."""
    return (
        db.query(ExternalConnection)
        .filter(
            ExternalConnection.user_id == user_id,
            ExternalConnection.provider == GITHUB_PROVIDER,
        )
        .first()
    )


def save_github_connection(
    user_id: int,
    token_data: dict,
    user_info: dict,
    db: Session,
) -> ExternalConnection:
    """Create or update an encrypted GitHub connection for the user."""
    access_token = token_data["access_token"]
    username = user_info.get("login") or user_info.get("email")

    connection = get_github_connection(user_id, db)
    if connection is None:
        connection = ExternalConnection(
            user_id=user_id,
            provider=GITHUB_PROVIDER,
            provider_account_id=str(user_info.get("id", "")),
            provider_email=username,
            encrypted_access_token=encrypt_token(access_token),
            scopes=token_data.get("scope", ""),
        )
        db.add(connection)
    else:
        connection.provider_account_id = str(user_info.get("id", ""))
        connection.provider_email = username
        connection.encrypted_access_token = encrypt_token(access_token)
        connection.scopes = token_data.get("scope", connection.scopes)

    db.commit()
    db.refresh(connection)
    return connection


def disconnect_github_connection(user_id: int, db: Session) -> bool:
    """Remove the user's stored GitHub connection."""
    connection = get_github_connection(user_id, db)
    if connection is None:
        return False
    db.delete(connection)
    db.commit()
    return True


def classify_github_repo(raw_repo: dict) -> GitHubRepoItem:
    """Convert raw GitHub repo JSON into clean metadata with relevance hint."""
    is_fork = bool(raw_repo.get("fork", False))
    language = raw_repo.get("language")
    description = raw_repo.get("description")

    if not is_fork and (language or description):
        is_relevant = True
        reason = f"Original {language or 'project'} repository"
    elif is_fork:
        is_relevant = False
        reason = "Forked repository"
    else:
        is_relevant = False
        reason = "Public repository (minimal metadata)"

    owner_login = raw_repo.get("owner", {}).get("login", "")

    return GitHubRepoItem(
        id=raw_repo["id"],
        name=raw_repo["name"],
        full_name=raw_repo["full_name"],
        owner=owner_login,
        description=description,
        html_url=raw_repo["html_url"],
        language=language,
        stargazers_count=int(raw_repo.get("stargazers_count", 0)),
        forks_count=int(raw_repo.get("forks_count", 0)),
        topics=raw_repo.get("topics") or [],
        is_fork=is_fork,
        default_branch=raw_repo.get("default_branch") or "main",
        updated_at=raw_repo.get("updated_at"),
        is_candidate_relevant=is_relevant,
        relevance_reason=reason,
    )


def fetch_authorized_repositories(user_id: int, db: Session) -> GitHubReposResponse:
    """Retrieve authorized public repositories for the connected GitHub account."""
    connection = get_github_connection(user_id, db)
    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub is not connected yet",
        )

    access_token = decrypt_token(str(connection.encrypted_access_token))
    response = httpx.get(
        f"{GITHUB_API_BASE}/user/repos",
        params={"visibility": "public", "sort": "updated", "per_page": 30},
        headers=_github_headers(access_token),
        timeout=15.0,
    )

    if response.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub authorization expired or revoked. Please reconnect GitHub.",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch repositories from GitHub API",
        )

    raw_repos = response.json()
    public_repos = [
        classify_github_repo(repo)
        for repo in raw_repos
        if not repo.get("private", False)
    ]

    # Put candidate-relevant (original) projects first
    public_repos.sort(key=lambda repo: not repo.is_candidate_relevant)
    relevant_count = sum(1 for repo in public_repos if repo.is_candidate_relevant)

    return GitHubReposResponse(
        total_repos=len(public_repos),
        relevant_count=relevant_count,
        repos=public_repos,
    )


def classify_repo_file(path: str, size_bytes: int | None = None) -> GitHubFileItem | None:
    """Identify whether a file is documentation, a project manifest, or source code."""
    parts = [part.lower() for part in path.split("/")]
    if any(part in IGNORED_DIR_PARTS for part in parts[:-1]):
        return None

    filename = parts[-1]
    _, ext = os.path.splitext(filename)

    if filename.startswith("readme") or (ext == ".md" and (len(parts) == 1 or parts[0] == "docs")):
        return GitHubFileItem(path=path, category="documentation", size_bytes=size_bytes)

    if filename in MANIFEST_FILENAMES:
        return GitHubFileItem(path=path, category="manifest", size_bytes=size_bytes)

    if ext in SOURCE_EXTENSIONS:
        return GitHubFileItem(path=path, category="source", size_bytes=size_bytes)

    return None


def fetch_repository_relevant_files(
    user_id: int,
    owner: str,
    repo: str,
    db: Session,
) -> GitHubRepoFilesResponse:
    """Inspect a public repository and identify documentation, manifests, and source files."""
    if not SLUG_PATTERN.match(owner) or not SLUG_PATTERN.match(repo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid repository owner or name",
        )

    connection = get_github_connection(user_id, db)
    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub is not connected yet",
        )

    access_token = decrypt_token(str(connection.encrypted_access_token))
    headers = _github_headers(access_token)

    # 1. Fetch repository metadata to verify it's public and get default branch
    repo_resp = httpx.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
        headers=headers,
        timeout=15.0,
    )
    if repo_resp.status_code == 401:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub authorization expired or revoked. Please reconnect GitHub.",
        )
    if repo_resp.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )
    if repo_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch repository details from GitHub",
        )

    repo_data = repo_resp.json()
    if repo_data.get("private", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only public repositories are allowed",
        )

    default_branch = repo_data.get("default_branch") or "main"
    full_name = repo_data.get("full_name") or f"{owner}/{repo}"

    # 2. Fetch the repository file tree in one request
    tree_resp = httpx.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{default_branch}",
        params={"recursive": "1"},
        headers=headers,
        timeout=15.0,
    )

    # 409 means the repository is empty (no commits yet)
    if tree_resp.status_code in (404, 409):
        return GitHubRepoFilesResponse(
            repo_full_name=full_name,
            default_branch=default_branch,
            total_files_scanned=0,
            relevant_count=0,
            has_readme=False,
            manifests=[],
            files=[],
        )

    if tree_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch repository file tree from GitHub",
        )

    tree_entries = tree_resp.json().get("tree", [])
    blobs = [entry for entry in tree_entries if entry.get("type") == "blob"]

    relevant_files: list[GitHubFileItem] = []
    for entry in blobs:
        item = classify_repo_file(entry["path"], entry.get("size"))
        if item is not None:
            relevant_files.append(item)

    category_order = {"documentation": 0, "manifest": 1, "source": 2}
    relevant_files.sort(key=lambda item: (category_order[item.category], item.path))

    has_readme = any(
        os.path.basename(item.path).lower().startswith("readme")
        for item in relevant_files
        if item.category == "documentation"
    )
    manifests = [
        item.path for item in relevant_files if item.category == "manifest"
    ]

    return GitHubRepoFilesResponse(
        repo_full_name=full_name,
        default_branch=default_branch,
        total_files_scanned=len(blobs),
        relevant_count=len(relevant_files),
        has_readme=has_readme,
        manifests=manifests,
        files=relevant_files[:100],
    )

