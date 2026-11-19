from typing import Any
from typing_extensions import TypedDict


class AgentGraphState(TypedDict):
    """Shared state dictionary passed across all nodes in the LangGraph workflow."""

    # Inputs provided by user
    user_id: int
    job_raw_text: str
    hint_title: str | None
    hint_company: str | None

    # Branch 1 Output: Job Analysis Agent
    job_analysis: dict[str, Any] | None #Stores extracted job title, required skills, preferred skills, responsibilities

    # Branch 2 Output: Candidate Profile Agent

    # Stores candidate's full skills, experience, and repositories from PostgreSQL
    candidate_profile: dict[str, Any] | None
    # Stores candidate's strengths and domain summary
    candidate_analysis: dict[str, Any] | None

    # Join Output: Supervisor Agent

    # Stores matched skills, skill gaps, fit score (%), and resume strategy
    supervisor_evaluation: dict[str, Any] | None

    # Application Generation Agent
    generated_application: dict[str, Any] | None
    application_id: int | None

    # LLM Judge & ReAct Revision
    judge_evaluation: dict[str, Any] | None
    revision_count: int
    human_feedback: str | None
    human_approved: bool

    # Graph execution status & error tracking
    status: str
    errors: list[str]