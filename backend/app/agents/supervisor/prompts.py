"""
Prompt templates for the Supervisor Agent.
Synthesizes Job Analysis and Candidate Profile Analysis to evaluate match and strategy.
"""
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)


# System Message Template 
SYSTEM_TEMPLATE = """You are an expert Technical Hiring Manager and Senior Career Strategist.
Your mission is to perform a rigorous, objective comparison between a target Job Description and a Candidate's verified profile.
CRITICAL GUARDRAILS:
1. OBJECTIVITY: Base your evaluation, fit score, and skill matching strictly on the provided Job Analysis and Candidate Analysis.
2. ACCURATE SKILL MATCHING: Only include skills in 'matched_skills' if they are clearly required or preferred by the job AND explicitly present in the candidate's profile.
3. REALISTIC SCORING: Calculate 'fit_score' realistically (0-100) based on coverage of required skills, domain alignment, and experience level.
4. NO FABRICATION: Do not assume unstated credentials or invent skills for either party.
5. STRICT SCHEMA: Always adhere strictly to the JSON schema specified in the formatting instructions."""

# Human Message Template 
HUMAN_TEMPLATE = """Please evaluate the alignment between this Job Opportunity and the Candidate:
=== TARGET JOB ANALYSIS ===
{job_analysis_text}
=== TARGET JOB ANALYSIS END ===
=== CANDIDATE ANALYSIS ===
{candidate_analysis_text}
=== CANDIDATE ANALYSIS END ===
Instructions:
1. Compare the job's required and preferred skills with the candidate's core skills and competencies.
2. Populate 'matched_skills' with skills present in both the job requirements and candidate profile.
3. Populate 'missing_skills' with critical job requirements that the candidate currently lacks.
4. Calculate a realistic 'fit_score' between 0 and 100 based on skill overlap, domain relevance, and seniority.
5. List 2-4 key 'strengths' explaining why the candidate is a compelling fit for this role.
6. List 2-4 'weaknesses' or gaps that could concern a hiring manager.
7. Provide 2-4 actionable 'strategy_recommendations' advising what projects, metrics, or experiences to emphasize in the application.
{format_instructions}"""

# ChatPromptTemplate 
supervisor_prompt_template = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE),
        HumanMessagePromptTemplate.from_template(HUMAN_TEMPLATE),
    ],
    input_variables=["job_analysis_text", "candidate_analysis_text", "format_instructions"],
)
def build_supervisor_prompt(
    job_analysis_text: str,
    candidate_analysis_text: str,
    format_instructions: str,
) -> ChatPromptValue:
    """Build a formatted ChatPromptValue ready to invoke with an LLM.
    Args:
        job_analysis_text: Formatted string representation of JobAnalysisOutput.
        candidate_analysis_text: Formatted string representation of CandidateAnalysisOutput.
        format_instructions: PydanticOutputParser instructions for JSON output.
    Returns:
        ChatPromptValue containing formatted SystemMessage and HumanMessage.
    """
    return supervisor_prompt_template.format_prompt(
        job_analysis_text=job_analysis_text,
        candidate_analysis_text=candidate_analysis_text,
        format_instructions=format_instructions,
    )