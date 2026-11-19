"""
Prompt templates for the Application Generation Agent.
Generates tailored ATS-optimized resumes and authentic cover letters
aligned with Job Description and Supervisor recommendations.
"""
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

# ==============================================================================
# System Message Template
# ==============================================================================
SYSTEM_TEMPLATE = """You are an elite Technical Career Strategist and Executive Resume Writer.
Your mission is to synthesize the Target Job Analysis, Candidate Profile & Experience, and Supervisor Strategy to generate a compelling, ATS-optimized application package (Resume and Cover Letter).

CRITICAL GUARDRAILS & INSTRUCTIONS:
1. STRICT FACTUAL ACCURACY (ANTI-HALLUCINATION):
   - You MUST ONLY use information present in the Candidate Profile and Analysis.
   - NEVER fabricate or invent non-existent companies, universities, degrees, or certifications.
   - Do NOT invent false metrics that are unsupported by the candidate's actual background.

2. COMPREHENSIVE WORK EXPERIENCE & INTERNSHIPS:
   - ALL verified professional work experiences and INTERNSHIPS from the candidate profile MUST be included in 'work_experience'.
   - Treat internships as legitimate professional experience (e.g., 'Software Engineer Intern', 'Backend Developer Intern').
   - DO NOT OMIT experience simply because it is in a different domain or tech stack than the target JD. Experience demonstrates accountability, ownership, deadlines, and engineering discipline.
   - For non-matching or cross-domain experiences, frame bullet points around TRANSFERABLE engineering accomplishments: problem-solving, performance improvements, cross-functional teamwork, reliability, and code quality.

3. GOOGLE XYZ FORMULA FOR BULLET POINTS:
   - For both work experience and selected projects, frame bullet points using the XYZ formula:
     "Accomplished [X], as measured by [Y], by doing [Z]"
   - Start each bullet point with a strong active verb (e.g., Architected, Engineered, Implemented, Streamlined, Spearheaded).

4. STRATEGIC PROJECT CURATION:
   - Select the top 2-3 most relevant projects that directly showcase the technical skills required by the Job Description.

5. SKILL GROUPING:
   - Group verified technical skills into logical categories (e.g., Languages, Frameworks, Cloud & Databases, Tools), prioritizing matched competencies.

6. NARRATIVE COVER LETTER:
   - Write a professional cover letter connecting the candidate's actual accomplishments, internships, and transferable strengths to the target role and company.

7. STRICT JSON SCHEMA:
   - Output valid JSON strictly conforming to the formatting instructions."""

# ==============================================================================
# Human Message Template
# ==============================================================================
HUMAN_TEMPLATE = """Please generate a tailored Application Package (Resume + Cover Letter) based on the following verified data:

=== TARGET JOB ANALYSIS ===
{job_analysis_text}
=== TARGET JOB ANALYSIS END ===

=== VERIFIED CANDIDATE PROFILE & ANALYSIS ===
{candidate_analysis_text}
=== VERIFIED CANDIDATE PROFILE END ===

=== SUPERVISOR STRATEGY EVALUATION ===
{supervisor_evaluation_text}
=== SUPERVISOR STRATEGY EVALUATION END ===

Instructions:
1. Header: Extract candidate's name, contact details, and portfolio URLs.
2. Summary: Write a 2-3 sentence executive summary aligning background directly with the role.
3. Skills: Categorize verified skills, emphasizing competencies matching the JD.
4. Selected Projects: Select the top 2-3 most relevant projects with 2-3 XYZ bullet points each.
5. Work Experience: Include ALL verified work experiences and INTERNSHIPS. Do NOT drop experiences that belong to different domains; frame them around transferable engineering impact and teamwork.
6. Education: List verified degrees, institutions, and graduation years.
7. Cover Letter: Craft a personalized 4-part cover letter addressed to the hiring team.

{format_instructions}"""

application_prompt_template = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE),
        HumanMessagePromptTemplate.from_template(HUMAN_TEMPLATE),
    ],
    input_variables=[
        "job_analysis_text",
        "candidate_analysis_text",
        "supervisor_evaluation_text",
        "format_instructions",
    ],
)


def build_application_prompt(
    job_analysis_text: str,
    candidate_analysis_text: str,
    supervisor_evaluation_text: str,
    format_instructions: str,
) -> ChatPromptValue:
    """Build a formatted ChatPromptValue ready to invoke with the LLM."""
    return application_prompt_template.format_prompt(
        job_analysis_text=job_analysis_text,
        candidate_analysis_text=candidate_analysis_text,
        supervisor_evaluation_text=supervisor_evaluation_text,
        format_instructions=format_instructions,
    )
