"""
Multi-Agent Orchestrator API Route.
Triggers the LangGraph workflow with full multi-user data isolation.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.graph.workflow import run_agent_workflow
from app.models.user import User
from app.schemas.orchestrator import OrchestratorRunRequest, OrchestratorRunResponse
from app.tools.jd_tools import clean_and_normalize_jd, validate_jd_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orchestrator", tags=["Multi-Agent Orchestrator"])


@router.post("/run", response_model=OrchestratorRunResponse)
async def run_orchestrator(
    payload: OrchestratorRunRequest,
    current_user: User = Depends(get_current_user),
):
    """Trigger the multi-agent workflow for the authenticated user.

    Executes:
    1. Job Analysis Agent (Branch 1)
    2. Candidate Analysis Agent (Branch 2) in parallel
    3. Supervisor Agent (Join Node) to evaluate fit and strategy.
    """
    cleaned_jd = clean_and_normalize_jd(payload.job_raw_text)
    is_valid, validation_msg = validate_jd_text(cleaned_jd)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_msg,
        )

    try:
        # Multi-user isolation enforced via current_user.id
        result_state = await run_agent_workflow(
            user_id=current_user.id,
            job_raw_text=cleaned_jd,
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
            errors=result_state.get("errors", []),
        )

    except Exception as e:
        logger.error(f"Error executing multi-agent orchestrator: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration workflow failed: {str(e)}",
        )