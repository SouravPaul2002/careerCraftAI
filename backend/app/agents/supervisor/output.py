"""
Pydantic output schema for the Supervisor Agent.
Defines the structured evaluation comparing Job Requirements vs Candidate Profile.
"""
from typing import List
from pydantic import BaseModel, Field


class SupervisorEvaluationOutput(BaseModel):
    """Structured evaluation output synthesizing candidate fit against job requirements."""

    fit_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall compatibility score between candidate and job (0 to 100).",
    )
    matched_skills: List[str] = Field(
        default_factory=list,
        description="Skills required or preferred by the job that the candidate possesses.",
    )
    missing_skills: List[str] = Field(
        default_factory=list,
        description="Skills required or preferred by the job that are not found in the candidate profile.",
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="Key alignment points and strong selling propositions of the candidate for this role.",
    )
    weaknesses: List[str] = Field(
        default_factory=list,
        description="Skill gaps, missing experiences, or areas where the candidate falls short.",
    )
    strategy_recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable advice on what projects, achievements, and keywords to emphasize in the application.",
    )