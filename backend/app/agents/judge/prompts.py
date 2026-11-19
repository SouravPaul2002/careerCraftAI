"""
Prompt templates for the LLM-as-a-Judge Agent.
Audits generated application documents against verified candidate profile
and target Job Description for factual accuracy and alignment.
"""
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

# System Message Template
SYSTEM_TEMPLATE = """You are an impartial, highly rigorous Technical Hiring Committee Chair and Executive Auditor (LLM-as-a-Judge).
Your sole mission is to audit a generated job application package (Resume and Cover Letter) against the Candidate's Ground-Truth Profile and the Target Job Description.

AUDIT CRITERIA & SCORING RULES:
1. FACTUAL ACCURACY & EVIDENCE GROUNDING (Weight: 40%):
   - Compare every past employer, internship, job title, degree, and project in the generated resume against the Ground-Truth Profile.
   - Flag ANY claim, credential, or experience not present in the verified profile under 'unsupported_claims'.
   - Legitimate internships and cross-domain experience present in the candidate profile are verified and valid.
   - If ANY company, job, degree, or major claim is fabricated out of thin air, 'factual_accuracy_score' MUST be below 70 and the application MUST be 'REJECTED'.

2. JOB DESCRIPTION ALIGNMENT (Weight: 25%):
   - Measure how effectively the resume and cover letter target the specific technical competencies, responsibilities, and keywords of the Job Description.

3. PROJECT RELEVANCE (Weight: 20%):
   - Verify that the selected projects represent the candidate's strongest demonstrations of skills relevant to the target role.

4. READABILITY & EXECUTIVE TONE (Weight: 15%):
   - Assess clarity, ATS-friendly phrasing, use of Google's XYZ formula ("Accomplished [X], as measured by [Y], by doing [Z]"), and professional polish.

5. FINAL DECISION POLICY:
   - Mark 'APPROVED' ONLY IF:
     * 'factual_accuracy_score' >= 80, AND
     * 'overall_score' >= 75, AND
     * 'unsupported_claims' is empty (or contains only minor wording critiques, not fake credentials).
   - Otherwise, mark 'REJECTED' and provide clear, prescriptive instructions in 'actionable_feedback' for the ReAct Revision Agent.

6. STRICT JSON SCHEMA:
   - Always output valid JSON strictly conforming to the provided format instructions."""

# Human Message Template
HUMAN_TEMPLATE = """Please evaluate the following application package against ground truth:

=== TARGET JOB DESCRIPTION ===
{job_analysis_text}
=== TARGET JOB DESCRIPTION END ===

=== CANDIDATE GROUND-TRUTH PROFILE ===
{candidate_profile_text}
=== CANDIDATE GROUND-TRUTH END ===

=== GENERATED APPLICATION PACKAGE (RESUME + COVER LETTER) ===
{generated_application_text}
=== GENERATED APPLICATION PACKAGE END ===

Instructions:
1. Audit factual accuracy: Cross-check every experience, internship, project, and credential against the ground-truth profile.
2. Populate 'unsupported_claims' with any invented companies, non-existent degrees, or unsupported assertions.
3. Score each dimension from 0 to 100 ('factual_accuracy_score', 'jd_alignment_score', 'project_relevance_score', 'readability_score').
4. Compute an 'overall_score' (weighted: 40% accuracy, 25% alignment, 20% relevance, 15% readability).
5. If score is >= 75 and no major hallucinations exist, set decision to 'APPROVED'. If rejected, set decision to 'REJECTED'.
6. Provide specific, numbered bullet points in 'actionable_feedback' instructing what to fix, rewrite, or verify.
7. Write a concise 2-3 sentence 'summary_verdict'.

{format_instructions}"""

judge_prompt_template = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE),
        HumanMessagePromptTemplate.from_template(HUMAN_TEMPLATE),
    ],
    input_variables=[
        "job_analysis_text",
        "candidate_profile_text",
        "generated_application_text",
        "format_instructions",
    ],
)


def build_judge_prompt(
    job_analysis_text: str,
    candidate_profile_text: str,
    generated_application_text: str,
    format_instructions: str,
) -> ChatPromptValue:
    """Build a formatted ChatPromptValue ready to invoke with an LLM."""
    return judge_prompt_template.format_prompt(
        job_analysis_text=job_analysis_text,
        candidate_profile_text=candidate_profile_text,
        generated_application_text=generated_application_text,
        format_instructions=format_instructions,
    )