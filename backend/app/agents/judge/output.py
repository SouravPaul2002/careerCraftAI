"""
Pydantic output schema for the LLM-as-a-Judge Agent.
Defines structured evaluation metrics, claim verification, and approval decisions.
"""
from typing import List, Literal
from pydantic import BaseModel, Field


class JudgeEvaluationOutput(BaseModel):
    """Structured evaluation report and verdict produced by the LLM-as-a-Judge."""

    decision: Literal["APPROVED", "REJECTED"] = Field(
        ...,
        description="Final evaluation decision: 'APPROVED' if documents meet quality, factuality, and alignment standards; 'REJECTED' if revisions are required.",
    )
    factual_accuracy_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Score (0-100) reflecting adherence to candidate's verified profile data without hallucination.",
    )
    jd_alignment_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Score (0-100) measuring how well the resume and cover letter address the job requirements and keywords.",
    )
    project_relevance_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Score (0-100) assessing relevance and impact of selected projects for the target position.",
    )
    readability_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Score (0-100) evaluating clarity, professional tone, grammar, and ATS-friendly formatting.",
    )
    overall_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Weighted composite score (0-100) summarizing the application package quality.",
    )
    unsupported_claims: List[str] = Field(
        default_factory=list,
        description="List of specific claims, metrics, or technologies found in the generated documents that lack evidence in the candidate profile.",
    )
    actionable_feedback: List[str] = Field(
        default_factory=list,
        description="Concrete, actionable instructions for the ReAct Revision Agent to fix flagged issues or enhance document strength.",
    )
    summary_verdict: str = Field(
        ...,
        description="2-3 sentence executive summary explaining the rationale behind the approval or rejection decision.",
    )