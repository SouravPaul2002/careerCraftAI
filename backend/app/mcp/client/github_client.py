"""
GitHub MCP Client & Tools for CareerCraft AI.
Enables AI agents to dynamically inspect repositories, read code, and query commit histories.
"""
import base64
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.auth.security import decrypt_token
from app.database.connection import engine
from app.models.external_connection import ExternalConnection
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


def get_user_github_token(user_id: int) -> Optional[str]:
    """Retrieve and decrypt the authenticated user's GitHub OAuth token."""
    with Session(engine) as db:
        connection = (
            db.query(ExternalConnection)
            .filter(
                ExternalConnection.user_id == user_id,
                ExternalConnection.provider == "github",
            )
            .first()
        )
        if not connection or not connection.encrypted_access_token:
            return None
        return decrypt_token(connection.encrypted_access_token)


def _github_headers(access_token: str) -> Dict[str, str]:
    """Construct standard headers for GitHub API requests."""
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "CareerCraftAI-Agent",
    }


def get_repository_details(access_token: str, owner: str, repo: str) -> Dict[str, Any]:
    """Fetch repository metadata including description, language, stars, and topics."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    try:
        response = httpx.get(url, headers=_github_headers(access_token), timeout=15.0)
        if response.status_code == 404:
            return {"error": f"Repository '{owner}/{repo}' not found."}
        response.raise_for_status()

        data = response.json()
        return {
            "name": data.get("name"),
            "full_name": data.get("full_name"),
            "description": data.get("description"),
            "primary_language": data.get("language"),
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "topics": data.get("topics", []),
            "default_branch": data.get("default_branch", "main"),
            "html_url": data.get("html_url"),
        }
    except Exception as e:
        logger.error(f"GitHub MCP error in get_repository_details for {owner}/{repo}: {e}")
        return {"error": str(e)}


def list_repository_tree(
    access_token: str,
    owner: str,
    repo: str,
    path: str = "",
) -> List[Dict[str, Any]]:
    """List directory contents and files within a repository path."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path.lstrip('/')}"
    try:
        response = httpx.get(url, headers=_github_headers(access_token), timeout=15.0)
        if response.status_code == 404:
            return [{"error": f"Path '{path}' not found in '{owner}/{repo}'."}]
        response.raise_for_status()

        items = response.json()
        if not isinstance(items, list):
            items = [items]

        results = []
        for item in items:
            results.append({
                "name": item.get("name"),
                "path": item.get("path"),
                "type": item.get("type"),  # 'file' or 'dir'
                "size": item.get("size", 0),
                "html_url": item.get("html_url"),
            })
        return results
    except Exception as e:
        logger.error(f"GitHub MCP error in list_repository_tree for {owner}/{repo}: {e}")
        return [{"error": str(e)}]


def read_repository_file(
    access_token: str,
    owner: str,
    repo: str,
    file_path: str,
    max_chars: int = 10000,
) -> str:
    """Read and decode the text content of a source file from GitHub."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{file_path.lstrip('/')}"
    try:
        response = httpx.get(url, headers=_github_headers(access_token), timeout=15.0)
        if response.status_code == 404:
            return f"Error: File '{file_path}' not found in '{owner}/{repo}'."
        response.raise_for_status()

        data = response.json()
        content_b64 = data.get("content", "")
        encoding = data.get("encoding", "")

        if encoding == "base64" and content_b64:
            decoded_bytes = base64.b64decode(content_b64)
            text = decoded_bytes.decode("utf-8", errors="replace")
            return text[:max_chars]

        return f"Error: Unsupported file encoding '{encoding}'."
    except Exception as e:
        logger.error(f"GitHub MCP error in read_repository_file for {owner}/{repo}/{file_path}: {e}")
        return f"Error reading file: {str(e)}"


def get_repository_readme(access_token: str, owner: str, repo: str) -> str:
    """Fetch the decoded README markdown text for a repository."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/readme"
    try:
        response = httpx.get(url, headers=_github_headers(access_token), timeout=15.0)
        if response.status_code == 404:
            return f"Error: No README found in '{owner}/{repo}'."
        response.raise_for_status()

        data = response.json()
        content_b64 = data.get("content", "")
        if content_b64:
            decoded = base64.b64decode(content_b64).decode("utf-8", errors="replace")
            return decoded[:12000]
        return "README is empty."
    except Exception as e:
        logger.error(f"GitHub MCP error in get_repository_readme for {owner}/{repo}: {e}")
        return f"Error fetching README: {str(e)}"


def get_recent_commits(
    access_token: str,
    owner: str,
    repo: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Fetch recent commit messages, authors, and dates from the repository."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits"
    try:
        response = httpx.get(
            url,
            headers=_github_headers(access_token),
            params={"per_page": min(limit, 10)},
            timeout=15.0,
        )
        if response.status_code == 404:
            return [{"error": f"Repository '{owner}/{repo}' not found."}]
        response.raise_for_status()

        commits = response.json()
        results = []
        for c in commits:
            commit_data = c.get("commit", {})
            author_data = commit_data.get("author", {})
            results.append({
                "sha": c.get("sha", "")[:7],
                "message": commit_data.get("message", "").split("\n")[0],
                "author": author_data.get("name"),
                "date": author_data.get("date"),
            })
        return results
    except Exception as e:
        logger.error(f"GitHub MCP error in get_recent_commits for {owner}/{repo}: {e}")
        return [{"error": str(e)}]