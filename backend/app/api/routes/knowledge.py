from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.candidate_profile import (
    CandidateProfileResponse,
    CandidateProfileUpdate,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSyncResponse,
    RetrievedChunkItem,
)
from app.services.knowledge_service import (
    delete_candidate_document,
    get_candidate_profile,
    search_candidate_knowledge,
    sync_user_knowledge,
    update_candidate_profile,
)

router = APIRouter(prefix="/api/knowledge", tags=["Candidate Knowledge Base & RAG"])


@router.post("/sync", response_model=KnowledgeSyncResponse)
def trigger_knowledge_sync(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Incrementally ingest selected Drive and GitHub documents and update profile."""
    return sync_user_knowledge(int(current_user.id), db)


@router.get("/profile", response_model=CandidateProfileResponse)
def read_candidate_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve structured candidate profile, skills, and experience."""
    return get_candidate_profile(int(current_user.id), db)


@router.put("/profile", response_model=CandidateProfileResponse)
def edit_candidate_profile(
    payload: CandidateProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually update candidate headline, summary, skills, or experience."""
    return update_candidate_profile(int(current_user.id), payload, db)


@router.post("/search", response_model=KnowledgeSearchResponse)
def search_candidate_chunks(
    payload: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
):
    """Query candidate vector store semantically with similarity scores and citations."""
    results = search_candidate_knowledge(
        user_id=int(current_user.id),
        query=payload.query,
        limit=payload.limit,
        source_type=payload.source_type,
    )

    items = [
        RetrievedChunkItem(
            chunk_id=str(r.get("chunk_id") or r.get("id") or ""),
            content=str(r.get("content") or ""),
            score=float(r.get("score", 0.0)),
            source_type=str(r.get("source_type") or "unknown"),
            title=str(r.get("title") or "Untitled"),
            url=r.get("url"),
            chunk_index=int(r.get("chunk_index") or r.get("metadata", {}).get("chunk_index") or 0),
            total_chunks=int(r.get("total_chunks") or r.get("metadata", {}).get("total_chunks") or 1),
            metadata=r.get("metadata") or {},
        )
        for r in results
    ]

    return KnowledgeSearchResponse(
        query=payload.query,
        total_results=len(items),
        chunks=items,
    )


@router.delete("/documents/{external_id}", status_code=status.HTTP_200_OK)
def remove_candidate_document(
    external_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete all vector chunks for a specific document and deselect it."""
    delete_candidate_document(int(current_user.id), external_id, db)
    return {"message": f"Document '{external_id}' removed from knowledge base"}
