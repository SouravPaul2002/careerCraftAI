from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.discovery import (
    DiscoveredItemResponse,
    DiscoveryWorkflowResponse,
    UpdateItemSelectionRequest,
)
from app.services.discovery_service import (
    get_saved_discovery,
    run_candidate_discovery,
    update_discovered_item_selection,
)

router = APIRouter(prefix="/api/discovery", tags=["Candidate Discovery"])


@router.post("/run", response_model=DiscoveryWorkflowResponse)
def start_candidate_discovery(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Collect candidate document and repository metadata from connected accounts."""
    return run_candidate_discovery(int(current_user.id), db)


@router.get("/items", response_model=DiscoveryWorkflowResponse)
def list_discovered_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve previously discovered candidate items saved for the user."""
    return get_saved_discovery(int(current_user.id), db)


@router.patch("/items/{item_id}", response_model=DiscoveredItemResponse)
def toggle_discovered_item(
    item_id: int,
    payload: UpdateItemSelectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Select or deselect a discovered document or repository for review."""
    return update_discovered_item_selection(
        user_id=int(current_user.id),
        item_id=item_id,
        is_selected=payload.is_selected,
        db=db,
    )

