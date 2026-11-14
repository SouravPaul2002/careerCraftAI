import logging
import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import decrypt_token
from app.models.discovered_item import DiscoveredItem
from app.services.github_service import (
    GITHUB_API_BASE,
    _github_headers,
    fetch_repository_relevant_files,
    get_github_connection,
)

logger = logging.getLogger(__name__)

MAX_FILE_BYTES = 100_000  # Skip huge files (> 100 KB)
MAX_FILES_PER_REPO = 3    # Focus on README + manifest files for fast indexing


def download_github_file_text(
    owner: str,
    repo: str,
    file_path: str,
    branch: str,
    access_token: str,
) -> str:
    """Download the raw text content of a single file from GitHub."""
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{file_path}"
    headers = {
        **_github_headers(access_token),
        "Accept": "application/vnd.github.raw+json",
    }

    try:
        response = httpx.get(
            url,
            params={"ref": branch},
            headers=headers,
            timeout=15.0,
        )
        if response.status_code != 200:
            return ""
        return response.text.strip()
    except Exception as err:
        logger.warning(f"Error downloading {owner}/{repo}/{file_path}: {err}")
        return ""


def ingest_selected_github_repos(user_id: int, db: Session) -> list[dict]:
    """Extract README, manifest, and key source file text from selected repos."""
    connection = get_github_connection(user_id, db)
    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub is not connected",
        )

    selected_repos = (
        db.query(DiscoveredItem)
        .filter(
            DiscoveredItem.user_id == user_id,
            DiscoveredItem.source_type == "github_repo",
            DiscoveredItem.is_selected.is_(True),
        )
        .all()
    )

    access_token = decrypt_token(str(connection.encrypted_access_token))
    documents: list[dict] = []

    for item in selected_repos:
        full_name = str(item.external_id)
        if "/" not in full_name:
            continue
        owner, repo_name = full_name.split("/", 1)

        try:
            repo_files = fetch_repository_relevant_files(user_id, owner, repo_name, db)
        except HTTPException as err:
            if err.status_code == 401:
                logger.warning(f"GitHub token expired or revoked. Halting GitHub ingestion: {err.detail}")
                break
            logger.warning(f"Skipping repo '{full_name}' due to error: {err}")
            continue
        except Exception as err:
            logger.warning(f"Skipping repo '{full_name}' due to error: {err}")
            continue

        details = item.details if isinstance(item.details, dict) else {}

        # Prioritize README and documentation first, then manifests
        sorted_files = sorted(
            repo_files.files,
            key=lambda f: 0 if f.category == "documentation" else (1 if f.category == "manifest" else 2),
        )

        chosen_files = [
            f
            for f in sorted_files
            if (f.size_bytes is None or f.size_bytes <= MAX_FILE_BYTES)
        ][:MAX_FILES_PER_REPO]

        for f in chosen_files:
            text = download_github_file_text(
                owner=owner,
                repo=repo_name,
                file_path=f.path,
                branch=repo_files.default_branch,
                access_token=access_token,
            )
            if not text:
                continue

            documents.append(
                {
                    "external_id": f"{full_name}:{f.path}",
                    "repo": full_name,
                    "source_type": "github_repo",
                    "category": f.category,
                    "title": f"{full_name}/{f.path}",
                    "url": (
                        f"{item.url}/blob/{repo_files.default_branch}/{f.path}"
                        if item.url
                        else None
                    ),
                    "updated_at": details.get("updated_at"),
                    "text": text,
                }
            )

    return documents
