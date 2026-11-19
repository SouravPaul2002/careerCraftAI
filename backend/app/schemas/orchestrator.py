"""
Pydantic schemas for the Multi-Agent Orchestrator API.
"""
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


class OrchestratorRunRequest(BaseModel):
    """Input payload to trigger the multi-agent orchestration workflow."""

    job_raw_text: str = Field(
        ...,
        min_length=30,
        description="Raw Job Description text to be analyzed.",
    )
    hint_title: Optional[str] = Field(
        default=None,
        description="Optional job title hint provided by candidate.",
    )
    hint_company: Optional[str] = Field(
        default=None,
        description="Optional hiring company hint provided by candidate.",
    )
    thread_id: Optional[str] = Field(
        default=None,
        description="Optional thread ID for continuing or inspecting a checkpointed session.",
    )


class OrchestratorRunResponse(BaseModel):
    """Output payload returning state results from all agent branches."""

    status: str = Field(..., description="Workflow execution status ('completed', 'failed', etc.).")
    thread_id: Optional[str] = Field(default=None, description="Thread identifier for this execution run.")
    job_analysis: Optional[Dict[str, Any]] = Field(default=None, description="Job Analysis Agent output.")
    candidate_profile: Optional[Dict[str, Any]] = Field(default=None, description="Candidate profile data from DB.")
    candidate_analysis: Optional[Dict[str, Any]] = Field(default=None, description="Candidate Analysis Agent output.")
    supervisor_evaluation: Optional[Dict[str, Any]] = Field(default=None, description="Supervisor Agent evaluation.")
    generated_application: Optional[Dict[str, Any]] = Field(default=None, description="Tailored Resume & Cover Letter.")
    application_id: Optional[int] = Field(default=None, description="Persisted application record ID.")
    judge_evaluation: Optional[Dict[str, Any]] = Field(default=None, description="LLM-as-a-Judge evaluation report.")
    revision_count: int = Field(default=0, description="Number of autonomous revision iterations performed.")
    errors: List[str] = Field(default_factory=list, description="Any errors or warnings during execution.")


class OrchestratorResumeRequest(BaseModel):
    """Input payload to resume a paused Human-in-the-Loop checkpoint thread."""

    thread_id: str = Field(..., description="Active thread ID for the checkpointed workflow.")
    action: Literal["approve", "request_changes"] = Field(
        ...,
        description="User decision: 'approve' to lock and complete; 'request_changes' to trigger AI revision.",
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Specific instructions and requested changes if action is 'request_changes'.",
    )