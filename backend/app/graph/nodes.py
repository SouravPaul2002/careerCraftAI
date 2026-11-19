"""
LangGraph Node Definitions for CareerCraft AI.
Each node takes the shared AgentGraphState, executes an agent, and returns state updates.
"""
import logging
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.agents.application_generation.agent import run_application_generation_agent
from app.agents.candidate_analysis.agent import run_candidate_analysis_agent
from app.agents.job_analysis.agent import run_job_analysis_agent
from app.agents.judge.evaluator import run_judge_agent
from app.agents.revision.agent import run_revision_agent
from app.agents.supervisor.agent import run_supervisor_agent
from app.database.connection import engine
from app.graph.state import AgentGraphState
from app.models.candidate_profile import CandidateProfile
from app.models.generated_application import GeneratedApplication
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
        }
    except Exception as e:
        logger.error(f"Error in supervisor_node: {e}")
        return {
            "status": "failed",
            "errors": [f"Supervisor error: {str(e)}"],
        }


def application_generation_node(state: AgentGraphState) -> Dict[str, Any]:
    """Phase 7 Node: Generates initial tailored Resume & Cover Letter."""
    logger.info("Executing application_generation_node...")
    user_id = state.get("user_id")
    job_analysis = state.get("job_analysis")
    candidate_profile = state.get("candidate_profile")
    candidate_analysis = state.get("candidate_analysis")
    supervisor_evaluation = state.get("supervisor_evaluation")

    try:
        package = run_application_generation_agent(
            job_analysis=job_analysis,
            candidate_profile=candidate_profile,
            candidate_analysis=candidate_analysis,
            supervisor_evaluation=supervisor_evaluation,
        )
        package_dict = package.model_dump()

        job_title = "Tailored Role"
        company_name = None
        if job_analysis:
            job_title = job_analysis.get("job_title") or "Tailored Role"
            company_name = job_analysis.get("company_name")

        # Persist generated application in database
        app_id = None
        with Session(engine) as db:
            app_record = GeneratedApplication(
                user_id=user_id,
                job_title=job_title,
                company_name=company_name,
                resume_data=package_dict.get("resume", {}),
                cover_letter_data=package_dict.get("cover_letter", {}),
                version=1,
                status="generated",
            )
            db.add(app_record)
            db.commit()
            db.refresh(app_record)
            app_id = app_record.id

        return {
            "generated_application": package_dict,
            "application_id": app_id,
            "revision_count": 0,
            "status": "draft_generated",
        }

    except Exception as e:
        logger.error(f"Error in application_generation_node: {e}")
        return {
            "generated_application": None,
            "application_id": None,
            "status": "failed",
            "errors": [f"Application generation error: {str(e)}"],
        }


def judge_node(state: AgentGraphState) -> Dict[str, Any]:
    """ LLM-as-a-Judge audits the application for factual accuracy and JD alignment."""
    logger.info("Executing judge_node...")
    job_analysis = state.get("job_analysis")
    candidate_profile = state.get("candidate_profile")
    candidate_analysis = state.get("candidate_analysis")
    generated_application = state.get("generated_application")

    try:
        evaluation = run_judge_agent(
            job_analysis=job_analysis,
            candidate_profile=candidate_profile,
            candidate_analysis=candidate_analysis,
            generated_application=generated_application,
        )
        return {
            "judge_evaluation": evaluation.model_dump(),
        }
    except Exception as e:
        logger.error(f"Error in judge_node: {e}")
        return {
            "errors": [f"Judge evaluation error: {str(e)}"],
        }


def react_revision_node(state: AgentGraphState) -> Dict[str, Any]:
    """ ReAct Revision Agent corrects unsupported claims and improves alignment."""
    revision_count = state.get("revision_count", 0) + 1
    logger.info(f"Executing react_revision_node (Attempt #{revision_count})...")

    user_id = state.get("user_id")
    job_analysis = state.get("job_analysis")
    candidate_profile = state.get("candidate_profile")
    current_application = state.get("generated_application")
    judge_evaluation = state.get("judge_evaluation")
    human_feedback = state.get("human_feedback")
    app_id = state.get("application_id")

    try:
        revised_package = run_revision_agent(
            job_analysis=job_analysis,
            candidate_profile=candidate_profile,
            current_application=current_application,
            judge_evaluation=judge_evaluation,
            human_feedback=human_feedback,
        )
        revised_dict = revised_package.model_dump()

        # Update persistent database record with new version
        if app_id:
            with Session(engine) as db:
                db.query(GeneratedApplication).filter(GeneratedApplication.id == app_id).update(
                    {
                        "resume_data": revised_dict.get("resume", {}),
                        "cover_letter_data": revised_dict.get("cover_letter", {}),
                        "version": revision_count + 1,
                        "status": "revised",
                    }
                )
                db.commit()

        return {
            "generated_application": revised_dict,
            "revision_count": revision_count,
            "status": "revising",
        }
    except Exception as e:
        logger.error(f"Error in react_revision_node: {e}")
        return {
            "revision_count": revision_count,
            "errors": [f"ReAct revision error: {str(e)}"],
        }


def escalate_human_review_node(state: AgentGraphState) -> Dict[str, Any]:
    """ Escapes the revision loop when max retries (3) are reached."""
    logger.warning("Max revision attempts reached. Escalating to human review.")
    app_id = state.get("application_id")
    if app_id:
        with Session(engine) as db:
            db.query(GeneratedApplication).filter(GeneratedApplication.id == app_id).update(
                {"status": "escalated_review"}
            )
            db.commit()

    return {
        "status": "escalated_human_review",
        "human_approved": False,
    }


def human_review_node(state: AgentGraphState) -> Dict[str, Any]:
    """ Approves the verified package and marks it ready for the user."""
    logger.info("Application package verified and approved.")
    app_id = state.get("application_id")
    if app_id:
        with Session(engine) as db:
            db.query(GeneratedApplication).filter(GeneratedApplication.id == app_id).update(
                {"status": "approved"}
            )
            db.commit()

    return {
        "status": "completed",
        "human_approved": True,
    }