import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.llm.picker import pick_llm
from app.models.candidate_profile import CandidateProfile
from app.models.discovered_item import DiscoveredItem
from app.models.user import User
from app.rag.ingestion.drive_ingestion import ingest_selected_drive_documents
from app.rag.ingestion.github_ingestion import ingest_selected_github_repos
from app.rag.processing.embeddings import embed_texts
from app.rag.processing.metadata import build_chunk_records, compute_content_hash
from app.rag.retrieval.retriever import retrieve_relevant_chunks
from app.rag.vector_store import (
    delete_document_chunks,
    get_collection,
    get_stored_document_hashes,
    upsert_document_chunks,
)
from app.schemas.candidate_profile import CandidateProfileUpdate

logger = logging.getLogger(__name__)


class CandidateExperienceItem(BaseModel):
    title: str = Field(default="", description="Job title")
    company: str = Field(default="", description="Company name")
    duration: str = Field(default="", description="e.g. Mar 2022 - Present")
    highlights: list[str] = Field(default_factory=list, description="Key achievements")


class CandidateProjectItem(BaseModel):
    name: str = Field(default="", description="Project name")
    description: str = Field(default="", description="What the project does and key tech used")
    technologies: list[str] = Field(default_factory=list, description="List of technologies")
    url: str = Field(default="", description="Project or repository URL")


class CandidateEducationItem(BaseModel):
    degree: str = Field(default="", description="Degree and major")
    institution: str = Field(default="", description="University or school")
    year: str = Field(default="", description="Graduation year")


class ExtractedCandidateProfile(BaseModel):
    headline: str = Field(default="Candidate", description="Concise professional headline")
    summary: str = Field(default="", description="2-3 sentence overview highlighting background and strengths")
    skills: list[str] = Field(default_factory=list, description="List of technical and soft skills")
    experience: list[CandidateExperienceItem] = Field(default_factory=list)
    projects: list[CandidateProjectItem] = Field(default_factory=list)
    education: list[CandidateEducationItem] = Field(default_factory=list)


def _extract_profile_with_llm(candidate_text: str, user_name: str) -> dict[str, Any]:
    """Use the LLM, StrOutputParser, and PydanticOutputParser to extract structured profile info."""
    if not candidate_text.strip():
        return {
            "headline": "Professional",
            "summary": "Candidate profile synced from documents.",
            "skills": [],
            "experience": [],
            "projects": [],
            "education": [],
        }

    parser = PydanticOutputParser(pydantic_object=ExtractedCandidateProfile)
    str_parser = StrOutputParser()

    # Limit prompt context length to avoid overwhelming LLM context window
    truncated_text = candidate_text[:5000]

    prompt = f"""You are an expert technical recruiter analyzing candidate documents (resume, projects, GitHub code). \n Extract structured candidate intelligence for candidate: {user_name} \n Candidate Documents: {truncated_text} \n {parser.get_format_instructions()} """

    try:
        llm = pick_llm("medium")
        response = llm.invoke(prompt)
        raw_text = str_parser.invoke(
            response.content if hasattr(response, "content") else str(response)
        )

        # Robust extraction in case LLM wraps JSON in markdown fences
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        clean_json = match.group(0) if match else raw_text

        parsed_profile: ExtractedCandidateProfile = parser.parse(clean_json)
        return parsed_profile.model_dump()
    except Exception as e:
        logger.warning(f"LLM profile extraction failed: {e}. Falling back to defaults.")
        return {
            "headline": "Candidate",
            "summary": "Candidate profile synced from uploaded documents and repositories.",
            "skills": [],
            "experience": [],
            "projects": [],
            "education": [],
        }


def sync_user_knowledge(user_id: int, db: Session) -> dict[str, Any]:
    """Incrementally synchronize selected Drive and GitHub documents into ChromaDB and update profile."""
    # 1. Fetch user
    user = db.query(User).filter(User.id == user_id).first()
    user_name = user.full_name if user else "Candidate"

    # 2. Ingest documents from Drive and GitHub (handling unconnected integrations gracefully)
    all_documents: list[dict] = []

    try:
        drive_docs = ingest_selected_drive_documents(user_id, db)
        all_documents.extend(drive_docs)
    except HTTPException as e:
        logger.info(f"Drive ingestion skipped: {e.detail}")
    except Exception as e:
        logger.warning(f"Error ingesting Drive documents: {e}")

    try:
        github_docs = ingest_selected_github_repos(user_id, db)
        all_documents.extend(github_docs)
    except HTTPException as e:
        logger.info(f"GitHub ingestion skipped: {e.detail}")
    except Exception as e:
        logger.warning(f"Error ingesting GitHub repositories: {e}")

    # 3. Check existing ChromaDB hashes for incremental synchronization
    stored_hashes = get_stored_document_hashes(user_id)
    current_external_ids = {str(doc["external_id"]) for doc in all_documents}

    # 4. Remove chunks for items that are no longer selected / present
    stale_ids = set(stored_hashes.keys()) - current_external_ids
    for stale_id in stale_ids:
        delete_document_chunks(user_id=user_id, external_id=stale_id)

    synced_items_count = 0
    skipped_items_count = 0
    total_new_chunks = 0
    text_corpus_for_llm: list[str] = []

    # 5. Process each document incrementally
    for doc in all_documents:
        raw_text = doc.get("text", "")
        if not raw_text.strip():
            continue

        text_corpus_for_llm.append(f"--- Document: {doc.get('title')} ---\n{raw_text[:2000]}")

        ext_id = str(doc["external_id"])
        new_hash = compute_content_hash(raw_text)
        old_hash = stored_hashes.get(ext_id)

        # If hash matches, the document has not changed — skip reprocessing!
        if old_hash and old_hash == new_hash:
            skipped_items_count += 1
            continue

        # Document is new or changed: chunk, embed, and store in ChromaDB
        chunk_records = build_chunk_records(user_id=user_id, doc=doc)
        if not chunk_records:
            continue

        chunk_texts = [record["content"] for record in chunk_records]
        embeddings = embed_texts(chunk_texts)

        upsert_document_chunks(
            user_id=user_id,
            chunk_records=chunk_records,
            embeddings=embeddings,
        )

        synced_items_count += 1
        total_new_chunks += len(chunk_records)

    # 6. Extract/update structured profile in PostgreSQL
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if profile is None:
        profile = CandidateProfile(
            user_id=user_id,
            full_name=user_name,
            skills=[],
            experience=[],
            projects=[],
            education=[],
        )
        db.add(profile)

    now = datetime.now(timezone.utc)

    # If new documents were synced or profile has never been populated, update via LLM
    if text_corpus_for_llm and (synced_items_count > 0 or not profile.skills):
        extracted = _extract_profile_with_llm(
            candidate_text="\n\n".join(text_corpus_for_llm),
            user_name=user_name,
        )
        if extracted.get("headline"):
            profile.headline = extracted["headline"]
        if extracted.get("summary"):
            profile.summary = extracted["summary"]
        if extracted.get("skills"):
            profile.skills = extracted["skills"]
        if extracted.get("experience"):
            profile.experience = extracted["experience"]
        if extracted.get("projects"):
            profile.projects = extracted["projects"]
        if extracted.get("education"):
            profile.education = extracted["education"]

    profile.last_synced_at = now
    db.commit()
    db.refresh(profile)

    # Count total chunks in collection for this user
    collection = get_collection()
    user_results = collection.get(where={"user_id": user_id}, include=[])
    total_stored_chunks = len(user_results.get("ids") or [])

    return {
        "message": "Knowledge base synchronization complete",
        "synced_items_count": synced_items_count,
        "skipped_items_count": skipped_items_count,
        "total_chunks": total_stored_chunks,
        "last_synced_at": now,
        "profile_updated": bool(synced_items_count > 0 or not profile.skills),
    }


def get_candidate_profile(user_id: int, db: Session) -> CandidateProfile:
    """Retrieve the candidate profile for the given user, creating an empty one if missing."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if profile is None:
        user = db.query(User).filter(User.id == user_id).first()
        profile = CandidateProfile(
            user_id=user_id,
            full_name=user.full_name if user else "Candidate",
            headline="",
            summary="",
            skills=[],
            experience=[],
            projects=[],
            education=[],
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return profile


def update_candidate_profile(
    user_id: int,
    data: CandidateProfileUpdate,
    db: Session,
) -> CandidateProfile:
    """Update editable candidate profile fields."""
    profile = get_candidate_profile(user_id, db)

    if data.headline is not None:
        profile.headline = data.headline
    if data.summary is not None:
        profile.summary = data.summary
    if data.skills is not None:
        profile.skills = data.skills
    if data.experience is not None:
        profile.experience = data.experience
    if data.projects is not None:
        profile.projects = data.projects
    if data.education is not None:
        profile.education = data.education

    db.commit()
    db.refresh(profile)
    return profile


def search_candidate_knowledge(
    user_id: int,
    query: str,
    limit: int = 5,
    source_type: str | None = None,
) -> list[dict[str, Any]]:
    """Perform semantic retrieval from the candidate vector store."""
    return retrieve_relevant_chunks(
        user_id=user_id,
        query=query,
        top_k=limit,
        source_type=source_type,
    )


def delete_candidate_document(user_id: int, external_id: str, db: Session) -> bool:
    """Delete document chunks from ChromaDB and deselect item in DiscoveredItem."""
    delete_document_chunks(user_id=user_id, external_id=external_id)

    item = (
        db.query(DiscoveredItem)
        .filter(
            DiscoveredItem.user_id == user_id,
            DiscoveredItem.external_id == external_id,
        )
        .first()
    )
    if item:
        item.is_selected = False
        db.commit()

    return True
