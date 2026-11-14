from datetime import datetime
from pydantic import BaseModel


class OAuthUrlResponse(BaseModel):
    """Consent screen URL returned to start an OAuth connection."""

    auth_url: str


class GoogleConnectionStatus(BaseModel):
    """Current user's Google Drive connection status."""

    connected: bool
    email: str | None = None
    scopes: list[str] = []
    connected_at: datetime | None = None


class DriveFileItem(BaseModel):
    """Metadata for a single PDF or DOCX file discovered in Google Drive."""

    id: str
    name: str
    mime_type: str
    document_type: str
    size_bytes: int | None = None
    modified_time: str | None = None
    web_view_link: str | None = None
    is_candidate_relevant: bool
    relevance_reason: str


class DriveFilesResponse(BaseModel):
    """List of PDF and DOCX documents retrieved from Google Drive."""

    total_files: int
    relevant_count: int
    files: list[DriveFileItem]


class GitHubConnectionStatus(BaseModel):
    """Current user's GitHub connection status."""

    connected: bool
    username: str | None = None
    scopes: list[str] = []
    connected_at: datetime | None = None


class GitHubRepoItem(BaseModel):
    """Metadata for an authorized public GitHub repository."""

    id: int
    name: str
    full_name: str
    owner: str
    description: str | None = None
    html_url: str
    language: str | None = None
    stargazers_count: int = 0
    forks_count: int = 0
    topics: list[str] = []
    is_fork: bool = False
    default_branch: str = "main"
    updated_at: str | None = None
    is_candidate_relevant: bool
    relevance_reason: str


class GitHubReposResponse(BaseModel):
    """List of authorized public repositories retrieved from GitHub."""

    total_repos: int
    relevant_count: int
    repos: list[GitHubRepoItem]


class GitHubFileItem(BaseModel):
    """Relevant file identified inside a GitHub repository."""

    path: str
    category: str  # "documentation", "manifest", or "source"
    size_bytes: int | None = None


class GitHubRepoFilesResponse(BaseModel):
    """Summary of relevant files and tech manifests inside a GitHub repository."""

    repo_full_name: str
    default_branch: str
    total_files_scanned: int
    relevant_count: int
    has_readme: bool
    manifests: list[str]
    files: list[GitHubFileItem]
