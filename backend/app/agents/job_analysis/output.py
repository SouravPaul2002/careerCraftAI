from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobRequirements(BaseModel):
    """Education and experience requirements extracted from the job description."""

    minimum_years_experience: int | None = Field(
        default=None,
        description="Minimum years of professional experience required (e.g., 3, 5). None if not mentioned.",
    )
    education_level: str | None = Field(
        default=None,
        description="Degree or education required (e.g., 'Bachelor in Computer Science or equivalent').",
    )


class JobAnalysisOutput(BaseModel):
    """Structured job analysis produced by the Job Analysis Agent."""

    job_title: str = Field(
        default="Software Engineer",
        description="The primary job title of the position (e.g., 'Senior Backend Engineer').",
    )
    company_name: str | None = Field(
        default=None,
        description="The name of the hiring company or organization, if mentioned.",
    )
    role_summary: str = Field(
        default="",
        description="A concise 2-3 sentence overview of the role and its core mission.",
    )
    required_skills: list[str] = Field(
        default_factory=list,
        description="Must-have technical or domain skills explicitly required by the job posting.",
    )
    preferred_skills: list[str] = Field(
        default_factory=list,
        description="Nice-to-have, bonus, or secondary skills that are advantageous but not strictly mandatory.",
    )
    responsibilities: list[str] = Field(
        default_factory=list,
        description="Key duties, tasks, and everyday responsibilities of the role.",
    )
    requirements: JobRequirements = Field(
        default_factory=JobRequirements,
        description="Experience duration and educational qualifications required.",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Important domain keywords, methodologies, and architectural patterns (e.g., 'Microservices', 'CI/CD', 'RAG').",
    )

    model_config = ConfigDict(from_attributes=True)

