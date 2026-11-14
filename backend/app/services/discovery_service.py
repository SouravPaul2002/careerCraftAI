import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.discovered_item import DiscoveredItem
from app.schemas.discovery import (
    DiscoveredItemResponse,
    DiscoveredSourceSummary,
    DiscoveryWorkflowResponse,
)
from app.services.github_service import (
    fetch_authorized_repositories,
    fetch_repository_relevant_files,
    get_github_connection,
)
from app.services.google_drive_service import (
    fetch_relevant_drive_files,
    get_google_connection,
)

SOURCE_DRIVE = "google_drive"
SOURCE_GITHUB = "github_repo"
MAX_REPOS_TO_INSPECT = 5


def _upsert_discovered_item(
    db: Session,
    user_id: int,
    source_type: str,
    external_id: str,
    title: str,
    subtitle: str | None,
    url: str | None,
    is_relevant: bool,
    details: dict,
) -> None:
    """Save or update a discovered item while preserving user selection."""
    item = (
        db.query(DiscoveredItem)
        .filter(
            DiscoveredItem.user_id == user_id,
            DiscoveredItem.source_type == source_type,
            DiscoveredItem.external_id == external_id,
        )
        .first()
    )

    if item is None:
        item = DiscoveredItem(
            user_id=user_id,
            source_type=source_type,
            external_id=external_id,
            title=title,
            subtitle=subtitle,
            url=url,
            is_relevant=is_relevant,
            is_selected=is_relevant,  # Pre-select candidate-relevant items
            details=details,
        )
        db.add(item)
    else:
        item.title = title
        item.subtitle = subtitle
        item.url = url
        item.is_relevant = is_relevant
        item.details = details


def _remove_stale_items(
    db: Session,
    user_id: int,
    source_type: str,
    active_external_ids: set[str],
) -> None:
    """Delete stored items that no longer exist in the latest scan for a source."""
    existing = (
        db.query(DiscoveredItem)
        .filter(
            DiscoveredItem.user_id == user_id,
            DiscoveredItem.source_type == source_type,
        )
        .all()
    )
    for row in existing:
        if row.external_id not in active_external_ids:
            db.delete(row)


def _discover_google_drive(user_id: int, db: Session) -> DiscoveredSourceSummary:
    """Discover PDF and DOCX metadata if Google Drive is connected."""
    if get_google_connection(user_id, db) is None:
        return DiscoveredSourceSummary(
            provider="google_drive",
            connected=False,
            status="not_connected",
            item_count=0,
        )

    try:
        drive_res = fetch_relevant_drive_files(user_id, db)
    except HTTPException as exc:
        return DiscoveredSourceSummary(
            provider="google_drive",
            connected=True,
            status="error",
            item_count=0,
            error=str(exc.detail),
        )
    except httpx.HTTPError:
        return DiscoveredSourceSummary(
            provider="google_drive",
            connected=True,
            status="error",
            item_count=0,
            error="Network error while reaching Google Drive",
        )

    active_ids: set[str] = set()
    for f in drive_res.files:
        active_ids.add(f.id)
        _upsert_discovered_item(
            db=db,
            user_id=user_id,
            source_type=SOURCE_DRIVE,
            external_id=f.id,
            title=f.name,
            subtitle=f.document_type,
            url=f.web_view_link,
            is_relevant=f.is_candidate_relevant,
            details={
                "mime_type": f.mime_type,
                "size_bytes": f.size_bytes,
                "modified_time": f.modified_time,
                "relevance_reason": f.relevance_reason,
            },
        )

    _remove_stale_items(db, user_id, SOURCE_DRIVE, active_ids)
    db.commit()

    return DiscoveredSourceSummary(
        provider="google_drive",
        connected=True,
        status="completed",
        item_count=len(drive_res.files),
    )


def _discover_github(user_id: int, db: Session) -> DiscoveredSourceSummary:
    """Discover public GitHub repositories and inspect top projects' relevant files."""
    if get_github_connection(user_id, db) is None:
        return DiscoveredSourceSummary(
            provider="github",
            connected=False,
            status="not_connected",
            item_count=0,
        )

    try:
        repos_res = fetch_authorized_repositories(user_id, db)
    except HTTPException as exc:
        return DiscoveredSourceSummary(
            provider="github",
            connected=True,
            status="error",
            item_count=0,
            error=str(exc.detail),
        )
    except httpx.HTTPError:
        return DiscoveredSourceSummary(
            provider="github",
            connected=True,
            status="error",
            item_count=0,
            error="Network error while reaching GitHub",
        )

    inspected_count = 0
    active_ids: set[str] = set()

    for repo in repos_res.repos:
        active_ids.add(repo.full_name)
        details: dict = {
            "description": repo.description,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "topics": repo.topics,
            "is_fork": repo.is_fork,
            "default_branch": repo.default_branch,
            "updated_at": repo.updated_at,
            "relevance_reason": repo.relevance_reason,
        }

        # Inspect file tree for top candidate-relevant repositories
        if repo.is_candidate_relevant and inspected_count < MAX_REPOS_TO_INSPECT:
            inspected_count += 1
            try:
                files_info = fetch_repository_relevant_files(
                    user_id=user_id,
                    owner=repo.owner,
                    repo=repo.name,
                    db=db,
                )
                details["has_readme"] = files_info.has_readme
                details["manifests"] = files_info.manifests
                details["relevant_files_count"] = files_info.relevant_count
                details["total_files_scanned"] = files_info.total_files_scanned
                details["sample_files"] = [item.path for item in files_info.files[:10]]
            except (HTTPException, httpx.HTTPError):
                details["file_inspection_error"] = "Could not inspect repository files"

        _upsert_discovered_item(
            db=db,
            user_id=user_id,
            source_type=SOURCE_GITHUB,
            external_id=repo.full_name,
            title=repo.full_name,
            subtitle=repo.language,
            url=repo.html_url,
            is_relevant=repo.is_candidate_relevant,
            details=details,
        )

    _remove_stale_items(db, user_id, SOURCE_GITHUB, active_ids)
    db.commit()

    return DiscoveredSourceSummary(
        provider="github",
        connected=True,
        status="completed",
        item_count=len(repos_res.repos),
    )


def get_saved_discovery(
    user_id: int,
    db: Session,
    sources: list[DiscoveredSourceSummary] | None = None,
) -> DiscoveryWorkflowResponse:
    """Return all saved discovered items for the user."""
    rows = (
        db.query(DiscoveredItem)
        .filter(DiscoveredItem.user_id == user_id)
        .order_by(
            DiscoveredItem.is_relevant.desc(),
            DiscoveredItem.source_type.asc(),
            DiscoveredItem.title.asc(),
        )
        .all()
    )

    items = [DiscoveredItemResponse.model_validate(row) for row in rows]
    selected_count = sum(1 for item in items if item.is_selected)

    if sources is None:
        drive_count = sum(1 for item in items if item.source_type == SOURCE_DRIVE)
        github_count = sum(1 for item in items if item.source_type == SOURCE_GITHUB)
        drive_connected = get_google_connection(user_id, db) is not None
        github_connected = get_github_connection(user_id, db) is not None

        sources = [
            DiscoveredSourceSummary(
                provider="google_drive",
                connected=drive_connected,
                status="completed" if (drive_connected and drive_count > 0) else ("ready" if drive_connected else "not_connected"),
                item_count=drive_count,
            ),
            DiscoveredSourceSummary(
                provider="github",
                connected=github_connected,
                status="completed" if (github_connected and github_count > 0) else ("ready" if github_connected else "not_connected"),
                item_count=github_count,
            ),
        ]

    return DiscoveryWorkflowResponse(
        sources=sources,
        total_items=len(items),
        selected_count=selected_count,
        items=items,
    )


def run_candidate_discovery(user_id: int, db: Session) -> DiscoveryWorkflowResponse:
    """Run the initial candidate discovery workflow across connected accounts."""
    drive_summary = _discover_google_drive(user_id, db)
    github_summary = _discover_github(user_id, db)
    return get_saved_discovery(user_id, db, sources=[drive_summary, github_summary])


def update_discovered_item_selection(
    user_id: int,
    item_id: int,
    is_selected: bool,
    db: Session,
) -> DiscoveredItemResponse:
    """Toggle whether a discovered item should be included in the candidate profile."""
    item = (
        db.query(DiscoveredItem)
        .filter(DiscoveredItem.id == item_id, DiscoveredItem.user_id == user_id)
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discovered item not found",
        )

    item.is_selected = is_selected
    db.commit()
    db.refresh(item)
    return DiscoveredItemResponse.model_validate(item)

