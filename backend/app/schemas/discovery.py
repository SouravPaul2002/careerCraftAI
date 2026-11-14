from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DiscoveredSourceSummary(BaseModel):
    """Status summary for one external source during candidate discovery."""

    provider: str
    connected: bool
    status: str  # "completed", "not_connected", or "error"
    item_count: int = 0
    error: str | None = None


class DiscoveredItemResponse(BaseModel):
    """One discovered candidate document or GitHub repository."""

    id: int
    source_type: str
    external_id: str
    title: str
    subtitle: str | None = None
    url: str | None = None
    is_relevant: bool
    is_selected: bool
    details: dict[str, Any]
    discovered_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiscoveryWorkflowResponse(BaseModel):
    """Combined candidate data discovery results across Google Drive and GitHub."""

    sources: list[DiscoveredSourceSummary]
    total_items: int
    selected_count: int
    items: list[DiscoveredItemResponse]


class UpdateItemSelectionRequest(BaseModel):
    """Request to include or exclude a discovered item for the knowledge base."""

    is_selected: bool

