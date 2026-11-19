"""
Supervisor Agent.
Synthesizes Job Analysis and Candidate Analysis into a final compatibility evaluation and strategy report.
"""
import json
import logging
import re
from typing import Any, Dict, Union
from langchain_core.output_parsers import PydanticOutputParser

from app.agents.candidate_analysis.output import CandidateAnalysisOutput
from app.agents.job_analysis.output import JobAnalysisOutput
from app.agents.supervisor.output import SupervisorEvaluationOutput
from app.agents.supervisor.prompts import supervisor_prompt_template
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


def run_supervisor_agent(
    job_analysis: Union[Dict[str, Any], JobAnalysisOutput, None] = None,
    candidate_analysis: Union[Dict[str, Any], CandidateAnalysisOutput, None] = None,
) -> SupervisorEvaluationOutput:
    """Run the Supervisor Agent chain to evaluate job-candidate fit.

    Args:
        job_analysis: Output from the Job Analysis branch.
        candidate_analysis: Output from the Candidate Analysis branch.

    Returns:
        Validated SupervisorEvaluationOutput Pydantic model.
    """
    # Format both inputs as clean JSON strings
    job_text = _format_section(job_analysis)
    candidate_text = _format_section(candidate_analysis)

    # Set up LLM and Output Parser
    llm = pick_llm("medium")
    parser = PydanticOutputParser(pydantic_object=SupervisorEvaluationOutput)

    def call_llm(prompt_value) -> list[dict[Any, Any] | str] | str:
        """Send formatted prompt to Ollama and return text content."""
        return llm.invoke(prompt_value).content

    # Helper to extract clean JSON string from LLM response
    def clean_json_text(response) -> str:
        """Extract content from AIMessage and extract JSON block between { and }."""
        text = response.content if hasattr(response, "content") else str(response)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return match.group(0) if match else text

    chain = supervisor_prompt_template | call_llm | clean_json_text | parser

    # Invoke the chain
    try:
        result: SupervisorEvaluationOutput = chain.invoke(
            {
                "job_analysis_text": job_text[:5000],
                "candidate_analysis_text": candidate_text[:5000],
                "format_instructions": parser.get_format_instructions(),
            }
        )
        return result

    except Exception as e:
        logger.warning(f"Supervisor agent chain error: {e}. Returning fallback evaluation.")

        # Safe fallback so graph execution never crashes
        return SupervisorEvaluationOutput(
            fit_score=60,
            matched_skills=[],
            missing_skills=[],
            strengths=["Demonstrates technical foundation relevant to the target domain."],
            weaknesses=["Unable to complete full automated gap analysis; manual review recommended."],
            strategy_recommendations=[
                "Highlight key projects demonstrating required technologies in the resume.",
                "Emphasize transferable skills and relevant coursework or certifications.",
            ],
        )