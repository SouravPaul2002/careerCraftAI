from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CandidateProfileBase(BaseModel):
    full_name: str | None = None
    headline: str | None = None
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)


class CandidateProfileUpdate(BaseModel):
    headline: str | None = None
    summary: str | None = None
    skills: list[str] | None = None
    experience: list[dict[str, Any]] | None = None
    projects: list[dict[str, Any]] | None = None
    education: list[dict[str, Any]] | None = None


class CandidateProfileResponse(CandidateProfileBase):
    id: int
    user_id: int
    last_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeSyncResponse(BaseModel):
    message: str
    synced_items_count: int
    skipped_items_count: int
    total_chunks: int
    last_synced_at: datetime
    profile_updated: bool


class KnowledgeSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=20)
    source_type: str | None = None


class RetrievedChunkItem(BaseModel):
    chunk_id: str
    content: str
    score: float
    source_type: str
    title: str
    url: str | None = None
    chunk_index: int
    total_chunks: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeSearchResponse(BaseModel):
    query: str
    total_results: int
    chunks: list[RetrievedChunkItem]
