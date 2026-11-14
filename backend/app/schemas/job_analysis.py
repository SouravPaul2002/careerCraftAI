from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.agents.job_analysis.output import JobAnalysisOutput, JobRequirements


class JobTextInput(BaseModel):
    """Schema for plain-text job description input."""

    raw_text: str = Field(
        ...,
        min_length=1,
        description="The raw job description text pasted by the candidate.",
    )
    job_title: str | None = Field(
        default=None,
        description="Optional pre-filled job title if known by the candidate.",
    )
    company_name: str | None = Field(
        default=None,
        description="Optional company name if known by the candidate.",
    )


class JobNormalizeResponse(BaseModel):
    """Schema returned after normalizing pasted job text."""

    cleaned_text: str
    character_count: int
    word_count: int
    is_valid: bool
    message: str


class JobAnalysisResponse(BaseModel):
    """Schema for the full job analysis result."""

    analysis: JobAnalysisOutput
    raw_text_length: int
    cleaned_text_length: int
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)

