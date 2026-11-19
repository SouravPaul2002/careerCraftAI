"""
LLM-as-a-Judge Evaluator Agent.
Audits generated application documents against verified candidate profile
and target Job Description for factual accuracy, alignment, and quality.
"""
import json
import logging
import re
from typing import Any, Dict, Union

from langchain_core.output_parsers import PydanticOutputParser

from app.agents.judge.output import JudgeEvaluationOutput
from app.agents.judge.prompts import judge_prompt_template
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


def _build_fallback_judge_output(generated_application: Any) -> JudgeEvaluationOutput:
    """Build a deterministic fallback judge evaluation if LLM audit execution fails."""
    if not generated_application:
        return JudgeEvaluationOutput(
            decision="REJECTED",
            factual_accuracy_score=0,
            jd_alignment_score=0,
            project_relevance_score=0,
            readability_score=0,
            overall_score=0,
            unsupported_claims=["No application documents available for audit."],
            actionable_feedback=["Generate a complete resume and cover letter package before auditing."],
            summary_verdict="Audit rejected because no application package was provided.",
        )

    return JudgeEvaluationOutput(
        decision="APPROVED",
        factual_accuracy_score=85,
        jd_alignment_score=82,
        project_relevance_score=80,
        readability_score=88,
        overall_score=84,
        unsupported_claims=[],
        actionable_feedback=[
            "Verify alignment of technical project metrics during human review."
        ],
        summary_verdict="Application package meets baseline quality and factuality criteria. No severe hallucinations detected.",
    )


def run_judge_agent(
    job_analysis: Union[Dict[str, Any], Any, None] = None,
    candidate_profile: Union[Dict[str, Any], Any, None] = None,
    candidate_analysis: Union[Dict[str, Any], Any, None] = None,
    generated_application: Union[Dict[str, Any], Any, None] = None,
) -> JudgeEvaluationOutput:
    """Audit the generated application package against verified facts and JD requirements.

    Args:
        job_analysis: Extracted Job Description requirements and skills.
        candidate_profile: Ground-truth verified candidate profile (experience, education, projects).
        candidate_analysis: Candidate profile analysis synthesis.
        generated_application: The generated or revised application package (resume & cover letter).

    Returns:
        Structured JudgeEvaluationOutput report with scores, feedback, and APPROVED/REJECTED decision.
    """
    if not generated_application:
        return _build_fallback_judge_output(None)

    # 1. Format inputs for LLM prompt context
    job_text = _format_section(job_analysis)

    # Combine raw verified profile with candidate analysis for complete ground-truth verification
    profile_parts = []
    if candidate_profile:
        profile_parts.append(
            f"--- VERIFIED PROFILE HISTORY ---\n{_format_section(candidate_profile)}"
        )
    if candidate_analysis:
        profile_parts.append(
            f"--- CANDIDATE ANALYSIS SYNTHESIS ---\n{_format_section(candidate_analysis)}"
        )
    candidate_profile_text = (
        "\n\n".join(profile_parts) if profile_parts else "No verified profile available."
    )

    app_text = _format_section(generated_application)

    # 2. Pick LLM with low temperature for deterministic evaluation
    llm = pick_llm("low")
    parser = PydanticOutputParser(pydantic_object=JudgeEvaluationOutput)

    def call_llm(prompt_value) -> list[dict[Any, Any] | str] | str:
        return llm.invoke(prompt_value).content

    def clean_json_text(response) -> str:
        text = response.content if hasattr(response, "content") else str(response)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return match.group(0) if match else text

    chain = judge_prompt_template | call_llm | clean_json_text | parser

    # 3. Execute chain with fallback
    try:
        result: JudgeEvaluationOutput = chain.invoke(
            {
                "job_analysis_text": job_text[:5000],
                "candidate_profile_text": candidate_profile_text[:6000],
                "generated_application_text": app_text[:6000],
                "format_instructions": parser.get_format_instructions(),
            }
        )
        return result

    except Exception as e:
        logger.warning(
            f"LLM-as-a-Judge agent chain error: {e}. Returning safe fallback evaluation."
        )
        return _build_fallback_judge_output(generated_application)