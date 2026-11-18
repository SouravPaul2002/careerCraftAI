"""
Candidate Analysis Agent.
Analyzes the candidate's verified profile data and returns a structured CandidateAnalysisOutput.
"""
import logging
import re
from typing import Any, Dict, Union
from langchain_core.output_parsers import PydanticOutputParser

from app.agents.candidate_analysis.output import CandidateAnalysisOutput
from app.agents.candidate_analysis.prompts import candidate_analysis_prompt_template
from app.llm.picker import pick_llm
from app.models.candidate_profile import CandidateProfile

logger = logging.getLogger(__name__)


def format_profile_for_llm(profile: Union[Dict[str, Any], CandidateProfile, None]) -> str:
    """Format candidate profile attributes into structured text for the prompt."""
    if not profile:
        return "No profile details found for this candidate."

    # Helper to read from either a dictionary or SQLAlchemy model
    def get_val(key: str, default: Any = None) -> Any:
        if isinstance(profile, dict):
            return profile.get(key, default)
        return getattr(profile, key, default)

    name = get_val("full_name") or "Candidate"
    headline = get_val("headline") or ""
    summary = get_val("summary") or ""
    skills = get_val("skills") or []
    experience = get_val("experience") or []
    projects = get_val("projects") or []
    education = get_val("education") or []

    lines = [f"Full Name: {name}"]
    if headline:
        lines.append(f"Headline: {headline}")
    if summary:
        lines.append(f"Summary: {summary}")
    if skills:
        lines.append(f"Skills: {', '.join(str(s) for s in skills)}")

    if experience:
        lines.append("Work Experience:")
        for exp in experience:
            if isinstance(exp, dict):
                title = exp.get("title", "")
                company = exp.get("company", "")
                desc = exp.get("description", "")
                lines.append(f"- {title} at {company}: {desc}")
            else:
                lines.append(f"- {exp}")

    if projects:
        lines.append("Key Projects:")
        for proj in projects:
            if isinstance(proj, dict):
                p_name = proj.get("name", "")
                p_desc = proj.get("description", "")
                p_url = proj.get("url") or proj.get("link") or proj.get("html_url")
                url_str = f" [Link: {p_url}]" if p_url else ""
                lines.append(f"- {p_name}{url_str}: {p_desc}")
            else:
                lines.append(f"- {proj}")

    if education:
        lines.append("Education:")
        for edu in education:
            if isinstance(edu, dict):
                degree = edu.get("degree", "")
                institution = edu.get("institution", "")
                score = (
                    edu.get("cgpa")
                    or edu.get("percentage")
                    or edu.get("grade")
                    or edu.get("gpa")
                )
                score_str = f" [Score/CGPA: {score}]" if score else ""
                lines.append(f"- {degree} from {institution}{score_str}")
            else:
                lines.append(f"- {edu}")

    return "\n".join(lines)


def run_candidate_analysis_agent(
    profile_data: Union[Dict[str, Any], CandidateProfile, None] = None,
) -> CandidateAnalysisOutput:
    """Run the Candidate Analysis Agent chain.

    Args:
        profile_data: Dictionary or SQLAlchemy model containing candidate profile information.

    Returns:
        Validated CandidateAnalysisOutput Pydantic model.
    """
    # Step 1: Format candidate profile details into clean text
    profile_text = format_profile_for_llm(profile_data)

    # Step 2: Set up LLM and Output Parser
    llm = pick_llm("medium")
    parser = PydanticOutputParser(pydantic_object=CandidateAnalysisOutput)

    # Step 3: Helper callables for pipe chain
    def call_llm(prompt_value) -> str:
        """Send the formatted prompt to LLM and return its text content."""
        return llm.invoke(prompt_value).content

    def clean_json_text(text: str) -> str:
        """Extract the JSON block between { and } (ignores markdown fences)."""
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return match.group(0) if match else text

    # Step 4: The LCEL pipe chain
    chain = candidate_analysis_prompt_template | call_llm | clean_json_text | parser

    # Step 5: Invoke the chain with formatted input variables
    try:
        result: CandidateAnalysisOutput = chain.invoke(
            {
                "profile_text": profile_text[:5000],
                "format_instructions": parser.get_format_instructions(),
            }
        )
        return result

    except Exception as e:
        logger.warning(f"Candidate analysis chain error: {e}. Returning fallback output.")

        # Determine fallback name safely
        fallback_name = "Candidate"
        fallback_skills = []
        if isinstance(profile_data, dict):
            fallback_name = profile_data.get("full_name") or "Candidate"
            fallback_skills = profile_data.get("skills") or []
        elif profile_data is not None:
            fallback_name = getattr(profile_data, "full_name", None) or "Candidate"
            fallback_skills = getattr(profile_data, "skills", None) or []

        return CandidateAnalysisOutput(
            full_name=fallback_name,
            headline="Technical Professional",
            core_skills=fallback_skills,
            primary_domains=["Software Engineering"],
            experience_summary=None,
            top_competencies=[],
        )