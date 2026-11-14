from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.job_analysis.agent import run_job_analysis_agent
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.job_analysis import (
    JobAnalysisResponse,
    JobNormalizeResponse,
    JobTextInput,
)
from app.tools.jd_tools import clean_and_normalize_jd, validate_jd_text

router = APIRouter(prefix="/api/jobs", tags=["Job Description Ingestion & Analysis"])


@router.post("/normalize", response_model=JobNormalizeResponse)
def normalize_job_description(
    payload: JobTextInput,
    current_user: User = Depends(get_current_user),
):
    """Clean and normalize pasted job description text before analysis."""
    cleaned = clean_and_normalize_jd(payload.raw_text)
    is_valid, msg = validate_jd_text(cleaned)

    word_count = len(cleaned.split()) if cleaned else 0
    char_count = len(cleaned)

    return JobNormalizeResponse(
        cleaned_text=cleaned,
        character_count=char_count,
        word_count=word_count,
        is_valid=is_valid,
        message=msg if not is_valid else "Job description normalized successfully.",
    )


@router.post("/analyze", response_model=JobAnalysisResponse)
def analyze_job_description(
    payload: JobTextInput,
    current_user: User = Depends(get_current_user),
):
    """Analyze a pasted job description using the Job Analysis Agent."""
    cleaned = clean_and_normalize_jd(payload.raw_text)
    is_valid, msg = validate_jd_text(cleaned)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )

    # Call the Job Analysis Agent
    analysis = run_job_analysis_agent(
        raw_text=cleaned,
        hint_title=payload.job_title,
        hint_company=payload.company_name,
    )

    return JobAnalysisResponse(
        analysis=analysis,
        raw_text_length=len(payload.raw_text),
        cleaned_text_length=len(cleaned),
        analyzed_at=datetime.now(timezone.utc),
    )

