"""
ReAct Revision Agent.
Executes Reason -> Act -> Observe loop to autonomously revise application packages
based on Judge critiques or Human feedback.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional, Union

from langchain_core.output_parsers import PydanticOutputParser

from app.agents.application_generation.output import ApplicationPackageOutput
from app.agents.judge.output import JudgeEvaluationOutput
from app.agents.revision.prompts import revision_prompt_template
from app.llm.picker import pick_llm

logger = logging.getLogger(__name__)


def _format_section(data: Union[Dict[str, Any], Any, None]) -> str:
    """Helper to convert a Pydantic model, dictionary, or raw data into a formatted JSON string."""
    if not data:
        return "No information available."
    if hasattr(data, "model_dump_json"):
        return data.model_dump_json(indent=2)
    if isinstance(data, dict):
        return json.dumps(data, indent=2)
    return str(data)


def run_revision_agent(
    job_analysis: Union[Dict[str, Any], Any, None] = None,
    candidate_profile: Union[Dict[str, Any], Any, None] = None,
    current_application: Union[Dict[str, Any], ApplicationPackageOutput, None] = None,
    judge_evaluation: Union[Dict[str, Any], JudgeEvaluationOutput, None] = None,
    human_feedback: Optional[str] = None,
) -> ApplicationPackageOutput:
    """Execute the ReAct Revision Agent to improve the application package.

    Args:
        job_analysis: Target Job Description details.
        candidate_profile: Ground-truth verified candidate profile.
        current_application: The current draft resume and cover letter.
        judge_evaluation: The Judge's evaluation report with unsupported claims and feedback.
        human_feedback: Optional feedback provided by the human reviewer.

    Returns:
        Revised ApplicationPackageOutput conforming to the schema.
    """
    if not current_application:
        raise ValueError("Cannot run revision without a current_application draft.")

    # 1. Format inputs for LLM prompt context
    job_text = _format_section(job_analysis)
    profile_text = _format_section(candidate_profile)
    app_text = _format_section(current_application)

    # Extract critique details from Judge
    unsupported_claims: List[str] = []
    actionable_feedback: List[str] = []

    if judge_evaluation:
        if isinstance(judge_evaluation, dict):
            unsupported_claims = judge_evaluation.get("unsupported_claims", [])
            actionable_feedback = judge_evaluation.get("actionable_feedback", [])
        else:
            unsupported_claims = getattr(judge_evaluation, "unsupported_claims", []) or []
            actionable_feedback = getattr(judge_evaluation, "actionable_feedback", []) or []

    unsupported_text = (
        "\n".join(f"- {c}" for c in unsupported_claims)
        if unsupported_claims
        else "No unsupported claims flagged."
    )
    feedback_text = (
        "\n".join(f"- {f}" for f in actionable_feedback)
        if actionable_feedback
        else "No specific revision instructions from Judge."
    )
    human_text = human_feedback.strip() if human_feedback else "No additional human feedback provided."

    # 2. Pick LLM and Output Parser
    llm = pick_llm("medium")
    parser = PydanticOutputParser(pydantic_object=ApplicationPackageOutput)

    def call_llm(prompt_value) -> list[dict[Any, Any] | str] | str:
        return llm.invoke(prompt_value).content

    def clean_json_text(response) -> str:
        text = response.content if hasattr(response, "content") else str(response)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return match.group(0) if match else text

    chain = revision_prompt_template | call_llm | clean_json_text | parser

    # 3. Execute revision chain with fallback to current draft
    try:
        result: ApplicationPackageOutput = chain.invoke(
            {
                "job_analysis_text": job_text[:5000],
                "candidate_profile_text": profile_text[:6000],
                "current_application_text": app_text[:6000],
                "unsupported_claims_text": unsupported_text,
                "actionable_feedback_text": feedback_text,
                "human_feedback_text": human_text,
                "format_instructions": parser.get_format_instructions(),
            }
        )
        return result

    except Exception as e:
        logger.warning(
            f"Revision agent chain error: {e}. Falling back to previous draft."
        )
        if isinstance(current_application, ApplicationPackageOutput):
            return current_application
        return ApplicationPackageOutput.model_validate(current_application)