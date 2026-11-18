"""
Prompt templates for the Candidate Analysis Agent.
Constructs ChatPromptValue for analyzing candidate background and skills.
"""
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
# System Message Template: Persona and core evaluation mission

SYSTEM_TEMPLATE = """You are an expert career strategist and technical profile evaluator.
Your task is to analyze a candidate's background, verified skills, projects, and career history to produce an objective, high-level profile assessment.
CRITICAL GUARDRAILS:
1. GROUNDED FACTUALITY: Strictly rely ONLY on the information present in the candidate profile. Do NOT invent, assume, or extrapolate companies, degrees, certifications, or skills that are not explicitly stated or directly demonstrated.
2. NO FABRICATION: If specific information (such as work experience or education) is missing, sparse, or not found, do NOT fabricate it. Simply omit it or set it to null / empty list.
3. SCHEMA CONFORMANCE: Always adhere strictly to the JSON schema specified in the formatting instructions."""

# Human Message Template: Profile details & instructions

HUMAN_TEMPLATE = """Please analyze the following candidate profile details:
=== CANDIDATE PROFILE START ===
{profile_text}
=== CANDIDATE PROFILE END ===
Instructions:
1. Extract or confirm the candidate's full name. If not explicitly found, use the known account name or 'Candidate'.
2. Formulate a sharp, professional headline strictly grounded in their demonstrated skills or projects (e.g., 'Full-Stack Developer' or 'Aspiring AI/ML Engineer').
3. Identify their verified 'core_skills' (strictly programming languages, frameworks, and tools evidenced in the profile).
4. Identify their 'primary_domains' of focus (e.g., 'Web Development', 'Machine Learning') based strictly on their actual projects and background.
5. Provide a 2-3 sentence 'experience_summary' highlighting career trajectory.
   - If the candidate is a fresher, student, or has NO formal employment history in the text, you MUST set 'experience_summary' to null. Do not invent past jobs.
6. Extract standout achievements or notable projects in 'top_competencies'. If none are evident, return an empty list [].
Guardrail Reminder:
- If the candidate profile text is minimal or empty, report only what is present. Never assume unmentioned credentials.
{format_instructions}"""


# Chat prompt Templates 
candidate_analysis_prompt_template= ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE),
        HumanMessagePromptTemplate.from_template(HUMAN_TEMPLATE)
    ],
    input_variables=["profile_text", "format_instructions"],
)

def build_candidate_analysis_prompt(
    profile_text: str,
    format_instructions: str,
) -> ChatPromptValue:
    """Build a formatted ChatPromptValue ready to invoke with an LLM.
    Args:
        profile_text: Textual representation of candidate profile, skills, projects, and experience.
        format_instructions: PydanticOutputParser instructions for JSON output.
    Returns:
        ChatPromptValue containing formatted SystemMessage and HumanMessage.
    """
    return candidate_analysis_prompt_template.format_prompt(
        profile_text=profile_text,
        format_instructions=format_instructions
    )
