"""
Pydantic output schema for the Candidate Analysis Agent.
Defines the structured representation of candidate profile analysis.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class CandidateAnalysisOutput(BaseModel):
    """Structured summary of a candidate's verified background and skills."""

    full_name: str = Field(
        ...,
        description="Full name of the candidate.",
    )
    headline: str = Field(
        ...,
        description="Professional headline or target title (e.g., 'Full-Stack Developer' or 'Aspiring AI Engineer').",
    )
    core_skills: List[str] = Field(
        ...,
        description="Core technical and professional skills possessed by the candidate.",
    )
    primary_domains: List[str] = Field(
        ...,
        description="Primary technical domains or areas of focus (e.g., 'Web Development', 'Machine Learning').",
    )
    experience_summary: Optional[str] = Field(
        default=None,
        description="Summary of professional experience if available; None for freshers or entry-level candidates.",
    )
    top_competencies: List[str] = Field(
        default_factory=list,
        description="Standout technical achievements, notable project highlights, or key strengths.",
    )