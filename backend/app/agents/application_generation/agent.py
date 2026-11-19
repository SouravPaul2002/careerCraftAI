"""
Application Generation Agent.
Synthesizes Job Analysis, Candidate Analysis, and Supervisor Strategy to produce
a tailored, ATS-compliant Resume and authentic Cover Letter.
"""
import json
import logging
import re
from typing import Any, Dict, List, Union

from langchain_core.output_parsers import PydanticOutputParser

from app.agents.application_generation.output import (
    ApplicationPackageOutput,
    ResumeEducation,
    ResumeExperience,
    ResumeHeader,
    ResumeProject,
    TailoredCoverLetterOutput,
    TailoredResumeOutput,
)
from app.agents.application_generation.prompts import application_prompt_template
from app.agents.candidate_analysis.output import CandidateAnalysisOutput
from app.agents.job_analysis.output import JobAnalysisOutput
from app.agents.supervisor.output import SupervisorEvaluationOutput
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


def _build_fallback_application(
    candidate_profile: Union[Dict[str, Any], None],
    candidate_analysis: Union[Dict[str, Any], CandidateAnalysisOutput, None],
    job_analysis: Union[Dict[str, Any], JobAnalysisOutput, None],
) -> ApplicationPackageOutput:
    """Create a structured fallback package preserving candidate's internships, experience, and education."""
    candidate_name = "Candidate"
    skills: List[str] = []

    # Read from candidate profile or analysis
    if candidate_profile and isinstance(candidate_profile, dict):
        candidate_name = candidate_profile.get("full_name") or candidate_name
        skills = candidate_profile.get("skills") or []
    elif candidate_analysis:
        if isinstance(candidate_analysis, dict):
            candidate_name = candidate_analysis.get("full_name") or candidate_name
            skills = candidate_analysis.get("core_skills") or []
        elif hasattr(candidate_analysis, "full_name"):
            candidate_name = candidate_analysis.full_name or candidate_name
            skills = getattr(candidate_analysis, "core_skills", []) or []

    job_title = "Target Role"
    company_name = "Target Company"
    if job_analysis:
        if isinstance(job_analysis, dict):
            job_title = job_analysis.get("job_title") or job_title
            company_name = job_analysis.get("company_name") or company_name
        elif hasattr(job_analysis, "job_title"):
            job_title = job_analysis.job_title or job_title
            company_name = getattr(job_analysis, "company_name", None) or company_name

    sample_skills = skills if skills else ["Python", "FastAPI", "React", "PostgreSQL"]

    # Extract all verified experiences including internships
    fallback_experience: List[ResumeExperience] = []
    if candidate_profile and isinstance(candidate_profile, dict):
        for exp in candidate_profile.get("experience", []):
            if isinstance(exp, dict):
                fallback_experience.append(
                    ResumeExperience(
                        company=exp.get("company") or "Company",
                        role=exp.get("title") or "Role / Intern",
                        duration=exp.get("duration"),
                        location=exp.get("location"),
                        bullet_points=[
                            exp.get("description")
                            or "Contributed to software development, teamwork, and system delivery."
                        ],
                    )
                )

    # Extract verified education
    fallback_education: List[ResumeEducation] = []
    if candidate_profile and isinstance(candidate_profile, dict):
        for edu in candidate_profile.get("education", []):
            if isinstance(edu, dict):
                fallback_education.append(
                    ResumeEducation(
                        degree=edu.get("degree") or "Degree",
                        institution=edu.get("institution") or "University",
                        year=edu.get("year"),
                        grade_or_cgpa=edu.get("grade_or_cgpa"),
                    )
                )

    return ApplicationPackageOutput(
        resume=TailoredResumeOutput(
            header=ResumeHeader(
                full_name=candidate_name,
                email="candidate@example.com",
                location="Remote / Flexible",
            ),
            professional_summary=(
                f"Dedicated technical professional targeting the {job_title} role at {company_name}, "
                f"bringing hands-on experience in modern software engineering and proven execution."
            ),
            skills={"Technical Skills": sample_skills},
            selected_projects=[
                ResumeProject(
                    name="Application Architecture & Development",
                    technologies=sample_skills[:4],
                    bullet_points=[
                        "Engineered modular software application following clean architecture principles.",
                        "Optimized data retrieval pipelines and system responsiveness across core workflows.",
                    ],
                )
            ],
            work_experience=fallback_experience,
            education=fallback_education,
        ),
        cover_letter=TailoredCoverLetterOutput(
            target_role=job_title,
            company_name=company_name,
            salutation="Dear Hiring Team,",
            opening_paragraph=(
                f"I am writing to express my enthusiastic interest in the {job_title} position "
                f"at {company_name}."
            ),
            body_paragraphs=[
                (
                    f"With a strong foundation in modern engineering workflows, I have focused on "
                    f"building maintainable, scalable solutions utilizing {', '.join(sample_skills[:3])}."
                ),
                (
                    f"I am confident that my technical skills, internship experience, and proactive learning "
                    f"mindset will allow me to make an immediate impact at {company_name}."
                ),
            ],
            closing_paragraph=(
                "Thank you for considering my application. I welcome the opportunity to discuss "
                "how my background aligns with your engineering objectives."
            ),
            sign_off="Sincerely,",
        ),
    )


def run_application_generation_agent(
    job_analysis: Union[Dict[str, Any], JobAnalysisOutput, None] = None,
    candidate_profile: Union[Dict[str, Any], None] = None,
    candidate_analysis: Union[Dict[str, Any], CandidateAnalysisOutput, None] = None,
    supervisor_evaluation: Union[Dict[str, Any], SupervisorEvaluationOutput, None] = None,
) -> ApplicationPackageOutput:
    """Run the Application Generation Agent to produce a tailored Resume and Cover Letter.

    Preserves all internships and experiences regardless of domain alignment.
    """
    # 1. Format inputs for LLM prompt context
    job_text = _format_section(job_analysis)

    # Combine raw verified profile (containing all internships/degrees) with analysis synthesis
    candidate_context_parts = []
    if candidate_profile:
        candidate_context_parts.append(
            f"--- VERIFIED CANDIDATE HISTORY (INTERNSHIPS, EXPERIENCE, EDUCATION, PROJECTS) ---\n"
            f"{_format_section(candidate_profile)}"
        )
    if candidate_analysis:
        candidate_context_parts.append(
            f"--- CANDIDATE STRENGTHS & SYNTHESIS ---\n"
            f"{_format_section(candidate_analysis)}"
        )
    candidate_text = "\n\n".join(candidate_context_parts) if candidate_context_parts else "No profile available."

    supervisor_text = _format_section(supervisor_evaluation)

    # 2. Pick LLM (Groq Cloud) and Output Parser
    llm = pick_llm("medium")
    parser = PydanticOutputParser(pydantic_object=ApplicationPackageOutput)

    def call_llm(prompt_value) -> str:
        return llm.invoke(prompt_value).content

    def clean_json_text(response) -> str:
        text = response.content if hasattr(response, "content") else str(response)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return match.group(0) if match else text

    chain = application_prompt_template | call_llm | clean_json_text | parser

    # 3. Execute chain with graceful fallback
    try:
        result: ApplicationPackageOutput = chain.invoke(
            {
                "job_analysis_text": job_text[:5000],
                "candidate_analysis_text": candidate_text[:6000],
                "supervisor_evaluation_text": supervisor_text[:5000],
                "format_instructions": parser.get_format_instructions(),
            }
        )
        return result

    except Exception as e:
        logger.warning(
            f"Application generation agent chain error: {e}. Returning fallback application."
        )
        return _build_fallback_application(candidate_profile, candidate_analysis, job_analysis)
