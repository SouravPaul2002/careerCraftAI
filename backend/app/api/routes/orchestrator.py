"""
Multi-Agent Orchestrator API Route.
Triggers and resumes the LangGraph workflow with strict multi-user data isolation and guardrails.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.graph.workflow import run_agent_workflow
from app.guardrails.input_validation import validate_and_sanitize_jd, validate_human_feedback
from app.models.generated_application import GeneratedApplication
from app.models.user import User
from app.schemas.orchestrator import (
    OrchestratorResumeRequest,
    OrchestratorRunRequest,
    OrchestratorRunResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orchestrator", tags=["Multi-Agent Orchestrator"])


@router.post("/run", response_model=OrchestratorRunResponse)
async def run_orchestrator(
    payload: OrchestratorRunRequest,
    current_user: User = Depends(get_current_user),
):
    """Trigger the multi-agent workflow with prompt-injection defense and input validation."""
    # 1. Input Validation & Prompt Injection Guardrail
    is_valid, sanitized_jd, error_msg = validate_and_sanitize_jd(payload.job_raw_text)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    try:
        # Multi-user isolation enforced via current_user.id
        result_state = await run_agent_workflow(
            user_id=current_user.id,
            job_raw_text=sanitized_jd,
            hint_title=payload.hint_title,
            hint_company=payload.hint_company,
            thread_id=payload.thread_id,
        )

        return OrchestratorRunResponse(
            status=result_state.get("status", "completed"),
            thread_id=payload.thread_id,
            job_analysis=result_state.get("job_analysis"),
            candidate_profile=result_state.get("candidate_profile"),
            candidate_analysis=result_state.get("candidate_analysis"),
            supervisor_evaluation=result_state.get("supervisor_evaluation"),
            generated_application=result_state.get("generated_application"),
            application_id=result_state.get("application_id"),
            judge_evaluation=result_state.get("judge_evaluation"),
            revision_count=result_state.get("revision_count", 0),
            errors=result_state.get("errors", []),
        )

    except Exception as e:
        logger.error(f"Error executing multi-agent orchestrator: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration workflow failed: {str(e)}",
        )


@router.post("/resume", response_model=OrchestratorRunResponse)
async def resume_orchestrator(
    payload: OrchestratorResumeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Human-in-the-Loop resume endpoint.

    Allows the candidate to approve the application or request specific AI revisions.
    """
    feedback_text = None

    if payload.action == "request_changes":
        if not payload.feedback or not payload.feedback.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Feedback is required when requesting revisions.",
            )
        is_valid, feedback_text, error_msg = validate_human_feedback(payload.feedback)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )

    try:
        # If user explicitly approves, mark the database application as approved
        if payload.action == "approve":
            # Update latest user application for this thread
            app_rec = (
                db.query(GeneratedApplication)
                .filter(GeneratedApplication.user_id == current_user.id)
                .order_by(GeneratedApplication.id.desc())
                .first()
            )
            if app_rec:
                db.query(GeneratedApplication).filter(GeneratedApplication.id == app_rec.id).update(
                    {"status": "approved"}
                )
                db.commit()

            return OrchestratorRunResponse(
                status="approved",
                thread_id=payload.thread_id,
                application_id=app_rec.id if app_rec else None,
                errors=[],
            )

        # User requested changes: resume workflow with human_feedback into ReAct loop
        result_state = await run_agent_workflow(
            user_id=current_user.id,
            job_raw_text="",  # Preserved in checkpointed state
            thread_id=payload.thread_id,
            human_feedback=feedback_text,
        )

        return OrchestratorRunResponse(
            status=result_state.get("status", "completed"),
            thread_id=payload.thread_id,
            job_analysis=result_state.get("job_analysis"),
            candidate_profile=result_state.get("candidate_profile"),
            candidate_analysis=result_state.get("candidate_analysis"),
            supervisor_evaluation=result_state.get("supervisor_evaluation"),
            generated_application=result_state.get("generated_application"),
            application_id=result_state.get("application_id"),
            judge_evaluation=result_state.get("judge_evaluation"),
            revision_count=result_state.get("revision_count", 0),
            errors=result_state.get("errors", []),
        )

    except Exception as e:
        logger.error(f"Error resuming multi-agent orchestrator: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resuming workflow failed: {str(e)}",
        )