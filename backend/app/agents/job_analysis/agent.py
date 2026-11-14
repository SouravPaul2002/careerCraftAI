import logging
import re
from langchain_core.output_parsers import PydanticOutputParser

from app.agents.job_analysis.output import JobAnalysisOutput
from app.agents.job_analysis.prompts import job_analysis_prompt_template
from app.llm.picker import pick_llm
from app.tools.jd_tools import clean_and_normalize_jd

logger = logging.getLogger(__name__)


def run_job_analysis_agent(
    raw_text: str,
    hint_title: str | None = None,
    hint_company: str | None = None,
) -> JobAnalysisOutput:
    """Job Analysis Agent.

    This function takes raw job description text and returns
    a validated JobAnalysisOutput Pydantic model with extracted skills,
    responsibilities, requirements, and keywords.

    Steps:
        1. Clean and normalize the raw JD text.
        2. Set up PydanticOutputParser for JobAnalysisOutput.
        3. Build the prompt using the parser's format instructions.
        4. Call local Ollama LLM (medium temperature).
        5. Extract raw string response with StrOutputParser.
        6. Parse clean JSON into JobAnalysisOutput.
    """
    # Step 1: Clean and normalize the raw pasted JD text
    cleaned_jd = clean_and_normalize_jd(raw_text)
    if not cleaned_jd:
        return JobAnalysisOutput(
            job_title="Unknown Role",
            role_summary="No content provided for analysis.",
        )

    # Step 2: Set up LLM and Output Parser
    llm = pick_llm("medium")
    parser = PydanticOutputParser(pydantic_object=JobAnalysisOutput)

    # Step 3: helper functions for the pipe chain
    def call_llm(prompt_value) -> str:
        """Send the formatted prompt to Ollama and return its text content."""
        return llm.invoke(prompt_value).content

    def clean_json_text(text: str) -> str:
        """Extract the JSON block between { and } (ignores markdown ```json fences)."""
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return match.group(0) if match else text

    # Step 4: The classic LangChain pipe chain!
    chain = job_analysis_prompt_template | call_llm | clean_json_text | parser

    # Prepare optional user hints
    hints = []
    if hint_title:
        hints.append(f"User-provided Job Title Hint: {hint_title}")
    if hint_company:
        hints.append(f"User-provided Company Hint: {hint_company}")
    hints_section = ("\n".join(hints) + "\n\n") if hints else ""

    # Step 5: Invoke the chain with our input_variables
    try:
        result: JobAnalysisOutput = chain.invoke(
            {
                "jd_text": cleaned_jd[:6000],
                "format_instructions": parser.get_format_instructions(),
                "hints_section": hints_section,
            }
        )
        return result

    except Exception as e:
        logger.warning(f"Job analysis chain error: {e}. Returning fallback output.")
        return JobAnalysisOutput(
            job_title=hint_title or "Software Engineer",
            company_name=hint_company,
            role_summary=cleaned_jd[:200] + "...",
            required_skills=[],
            preferred_skills=[],
            responsibilities=[],
            keywords=[],
        )
