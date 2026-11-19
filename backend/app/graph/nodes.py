"""
LangGraph Node Definitions for CareerCraft AI.
Each node takes the shared AgentGraphState, executes an agent, and returns state updates.
"""
import logging
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.agents.candidate_analysis.agent import run_candidate_analysis_agent
from app.agents.job_analysis.agent import run_job_analysis_agent
from app.agents.supervisor.agent import run_supervisor_agent
from app.database.connection import engine
from app.graph.state import AgentGraphState
from app.models.candidate_profile import CandidateProfile
from app.models.user import User

logger = logging.getLogger(__name__)


def job_analysis_node(state: AgentGraphState) -> Dict[str, Any]:
    """Branch 1 Node: Analyzes the target Job Description."""
    
    logger.info("Executing job_analysis_node...")
    raw_text = state.get("job_raw_text", "")
    hint_title = state.get("hint_title")
    hint_company = state.get("hint_company")

    try:
        output = run_job_analysis_agent(
            raw_text=raw_text,
            hint_title=hint_title,
            hint_company=hint_company,
        )
        return {"job_analysis": output.model_dump()}
    except Exception as e:
        logger.error(f"Error in job_analysis_node: {e}")
        return {
            "job_analysis": None,
            "errors": [f"Job analysis error: {str(e)}"],
        }


def candidate_analysis_node(state: AgentGraphState) -> Dict[str, Any]:
    """Branch 2 Node: Fetches verified profile from PostgreSQL and summarizes candidate background."""

    logger.info("Executing candidate_analysis_node...")
    user_id = state.get("user_id")

    profile_dict: Dict[str, Any] = {}

    # Query the user's candidate profile from PostgreSQL
    try:
        with Session(engine) as db:
            profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
            if profile:
                profile_dict = {
                    "full_name": profile.full_name,
                    "headline": profile.headline,
                    "summary": profile.summary,
                    "skills": profile.skills or [],
                    "experience": profile.experience or [],
                    "projects": profile.projects or [],
                    "education": profile.education or [],
                }
            else:
                user = db.query(User).filter(User.id == user_id).first()
                profile_dict = {
                    "full_name": user.full_name if user else "Candidate",
                    "skills": [],
                    "experience": [],
                    "projects": [],
                    "education": [],
                }

        # Run Candidate Analysis Agent
        analysis_output = run_candidate_analysis_agent(profile_data=profile_dict)

        return {
            "candidate_profile": profile_dict,
            "candidate_analysis": analysis_output.model_dump(),
        }

    except Exception as e:
        logger.error(f"Error in candidate_analysis_node: {e}")
        return {
            "candidate_profile": None,
            "candidate_analysis": None,
            "errors": [f"Candidate analysis error: {str(e)}"],
        }


def supervisor_node(state: AgentGraphState) -> Dict[str, Any]:
    """Join Node: Synthesizes Job Analysis + Candidate Analysis to compute match & recommendations."""
    logger.info("Executing supervisor_node...")
    job_analysis = state.get("job_analysis")
    candidate_analysis = state.get("candidate_analysis")

    try:
        evaluation = run_supervisor_agent(
            job_analysis=job_analysis,
            candidate_analysis=candidate_analysis,
        )
        return {
            "supervisor_evaluation": evaluation.model_dump(),
            "status": "completed",
        }
    except Exception as e:
        logger.error(f"Error in supervisor_node: {e}")
        return {
            "status": "failed",
            "errors": [f"Supervisor error: {str(e)}"],
        }