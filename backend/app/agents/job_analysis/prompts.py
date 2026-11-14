from langchain_core.prompt_values import ChatPromptValue
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

# -------------------------------------------------------------------------
# 1. System Message Template: Establishes persona and core mission
# -------------------------------------------------------------------------
SYSTEM_TEMPLATE = """You are an expert technical talent scout and job market analyst.
Your task is to carefully analyze the provided Job Description (JD) and extract structured details including skills, responsibilities, requirements, and domain keywords.
Always adhere strictly to the JSON schema specified in the formatting instructions."""

# -------------------------------------------------------------------------
# 2. Human Message Template: Delivers the actual input variables
# -------------------------------------------------------------------------
HUMAN_TEMPLATE = """Please analyze the following Job Description (JD):

{hints_section}=== JOB DESCRIPTION START ===
{jd_text}
=== JOB DESCRIPTION END ===

Instructions:
1. Extract the exact or most accurate job title and hiring company name.
2. Provide a 2-3 sentence high-level summary of the role.
3. Distinguish between 'required_skills' (strictly mandatory) and 'preferred_skills' (nice-to-have or bonus).
4. Extract the primary day-to-day responsibilities.
5. Extract the minimum required years of experience and education level.
6. Extract key technical and domain keywords (e.g. CI/CD, Docker, Microservices, RAG).

{format_instructions}"""

# -------------------------------------------------------------------------
# 3. ChatPromptTemplate
# -------------------------------------------------------------------------
job_analysis_prompt_template = ChatPromptTemplate(
    messages=[
        SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE),
        HumanMessagePromptTemplate.from_template(HUMAN_TEMPLATE),
    ],
    input_variables=["jd_text", "format_instructions", "hints_section"],
)


def build_job_analysis_prompt(
    jd_text: str,
    format_instructions: str,
    hint_title: str | None = None,
    hint_company: str | None = None,
) -> ChatPromptValue:
    """Build a formatted ChatPromptValue ready to invoke with an LLM.

    Args:
        jd_text: The cleaned job description text.
        format_instructions: PydanticOutputParser instructions for JSON output.
        hint_title: Optional user-provided job title hint.
        hint_company: Optional user-provided company name hint.

    Returns:
        ChatPromptValue containing formatted SystemMessage and HumanMessage.
    """
    hints = []
    if hint_title:
        hints.append(f"User-provided Job Title Hint: {hint_title}")
    if hint_company:
        hints.append(f"User-provided Company Hint: {hint_company}")

    hints_section = ("\n".join(hints) + "\n\n") if hints else ""

    return job_analysis_prompt_template.format_prompt(
        jd_text=jd_text,
        format_instructions=format_instructions,
        hints_section=hints_section,
    )
