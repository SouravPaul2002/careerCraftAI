"""
Prompt templates for the ReAct Revision Agent.
Implements the Reason -> Act -> Observe paradigm to correct unsupported claims,
enhance JD alignment, and incorporate Judge or Human feedback.
"""
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

# System Message Template
SYSTEM_TEMPLATE = """You are an expert Technical Resume Revision Specialist and ReAct Problem-Solver.
Your task is to revise a draft Job Application Package (Resume and Cover Letter) following the Reason -> Act -> Observe cycle to address specific critiques from the LLM Judge or Human Reviewer.

REVISION GUARDRAILS & PROCESS:
1. REASON:
   - Carefully analyze each item in 'unsupported_claims', 'actionable_feedback', and any 'human_feedback'.
   - Identify the exact bullet points, skills, or paragraphs where inaccuracies or weak alignment exist.

2. ACT:
   - ELIMINATE ALL UNSUPPORTED CLAIMS: Replace any fabricated metric, ungrounded company, or unverified technology with real, verified facts from the Ground-Truth Profile.
   - PRESERVE VERIFIED FACTS: Do not modify sections, internships, or verified achievements that were not criticized.
   - APPLY GOOGLE XYZ FORMULA: Ensure all rewritten bullet points follow: "Accomplished [X], as measured by [Y], by doing [Z]" using strong action verbs.
   - ENHANCE JD ALIGNMENT: Incorporate missing keywords and prioritize skills matching the Job Description where supported by candidate background.

3. OBSERVE:
   - Verify that all critique items have been addressed and no new unverified assertions are introduced.

4. STRICT JSON SCHEMA:
   - Output the complete, revised Application Package strictly conforming to the formatting instructions."""


# Human Message Template
HUMAN_TEMPLATE = """Please revise the draft Application Package based on the critique below:

=== TARGET JOB DESCRIPTION ===
{job_analysis_text}
=== TARGET JOB DESCRIPTION END ===

=== CANDIDATE GROUND-TRUTH PROFILE ===
{candidate_profile_text}
=== CANDIDATE GROUND-TRUTH END ===

=== CURRENT DRAFT APPLICATION PACKAGE ===
{current_application_text}
=== CURRENT DRAFT APPLICATION PACKAGE END ===

=== EVALUATION CRITIQUE & FEEDBACK ===
Unsupported Claims Flagged by Judge:
{unsupported_claims_text}

Actionable Feedback from Judge:
{actionable_feedback_text}

Human Reviewer Feedback (if any):
{human_feedback_text}
=== CRITIQUE END ===

Instructions:
1. Review every unsupported claim and remove or replace it with verified data from the Candidate Ground-Truth Profile.
2. Directly implement each actionable recommendation to improve JD alignment and impact.
3. Keep verified internships, work experiences, and genuine achievements intact.
4. Output the complete revised Application Package (Resume and Cover Letter) matching the schema.

{format_instructions}"""

revision_prompt_template = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE),
        HumanMessagePromptTemplate.from_template(HUMAN_TEMPLATE),
    ],
    input_variables=[
        "job_analysis_text",
        "candidate_profile_text",
        "current_application_text",
        "unsupported_claims_text",
        "actionable_feedback_text",
        "human_feedback_text",
        "format_instructions",
    ],
)


def build_revision_prompt(
    job_analysis_text: str,
    candidate_profile_text: str,
    current_application_text: str,
    unsupported_claims_text: str,
    actionable_feedback_text: str,
    human_feedback_text: str,
    format_instructions: str,
) -> ChatPromptValue:
    """Build a formatted ChatPromptValue ready to invoke with the LLM."""
    return revision_prompt_template.format_prompt(
        job_analysis_text=job_analysis_text,
        candidate_profile_text=candidate_profile_text,
        current_application_text=current_application_text,
        unsupported_claims_text=unsupported_claims_text,
        actionable_feedback_text=actionable_feedback_text,
        human_feedback_text=human_feedback_text,
        format_instructions=format_instructions,
    )