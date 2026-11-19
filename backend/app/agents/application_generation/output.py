"""
Pydantic output schemas for the Application Generation Agent.
Defines structured representations of tailored resumes and cover letters.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ResumeHeader(BaseModel):
    """Candidate contact and profile identity header."""

    full_name: str = Field(..., description="Full name of the candidate.")
    email: Optional[str] = Field(default=None, description="Contact email address.")
    phone: Optional[str] = Field(default=None, description="Contact phone number.")
    location: Optional[str] = Field(default=None, description="City, State, or Country.")
    github_url: Optional[str] = Field(default=None, description="GitHub profile URL.")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn profile URL.")
    portfolio_url: Optional[str] = Field(default=None, description="Personal website or portfolio link.")


class ResumeProject(BaseModel):
    """Curated project entry specifically selected for its relevance to the target job."""

    name: str = Field(..., description="Project title.")
    technologies: List[str] = Field(
        default_factory=list,
        description="Core technologies, frameworks, and tools used in this project.",
    )
    bullet_points: List[str] = Field(
        default_factory=list,
        description="2-3 impact-focused bullet points describing technical architecture, problem solved, and metrics.",
    )
    repo_url: Optional[str] = Field(
        default=None,
        description="Direct link to GitHub repository or live demonstration.",
    )


class ResumeExperience(BaseModel):
    """Work experience or internship entry highlighting professional accomplishments and transferable impact."""

    company: str = Field(..., description="Company, organization, or startup name.")
    role: str = Field(..., description="Job title or internship position held (e.g. 'Software Engineer Intern').")
    location: Optional[str] = Field(default=None, description="Work location (e.g., 'San Francisco, CA' or 'Remote').")
    duration: Optional[str] = Field(default=None, description="Employment or internship dates (e.g., 'Summer 2023').")
    bullet_points: List[str] = Field(
        default_factory=list,
        description="Action-oriented bullet points (XYZ format) emphasizing accomplishments, teamwork, and transferable skills.",
    )


class ResumeEducation(BaseModel):
    """Educational qualification entry."""

    degree: str = Field(..., description="Degree and major (e.g., 'B.S. in Computer Science').")
    institution: str = Field(..., description="University or college name.")
    year: Optional[str] = Field(default=None, description="Graduation year or date range.")
    grade_or_cgpa: Optional[str] = Field(default=None, description="CGPA, GPA, or honors classification.")


class TailoredResumeOutput(BaseModel):
    """Complete structured resume tailored to the target Job Description."""

    header: ResumeHeader = Field(..., description="Candidate contact header.")
    professional_summary: str = Field(
        ...,
        description="2-3 sentence executive summary aligning candidate background directly with the role requirements.",
    )
    skills: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Categorized technical skills (e.g. 'Languages', 'Frameworks', 'Databases & Cloud', 'Tools').",
    )
    selected_projects: List[ResumeProject] = Field(
        default_factory=list,
        description="The top 2-3 most relevant projects selected from candidate portfolio to demonstrate job fit.",
    )
    work_experience: List[ResumeExperience] = Field(
        default_factory=list,
        description="All verified professional work and internship experiences. Retains cross-domain experiences with focus on transferable engineering skills.",
    )
    education: List[ResumeEducation] = Field(
        default_factory=list,
        description="Educational degrees and certifications.",
    )


class TailoredCoverLetterOutput(BaseModel):
    """Personalized cover letter tailored to the hiring manager and company."""

    target_role: str = Field(..., description="Job title applied for.")
    company_name: Optional[str] = Field(default=None, description="Target hiring company.")
    salutation: str = Field(default="Dear Hiring Team,", description="Formal greeting.")
    opening_paragraph: str = Field(
        ...,
        description="Engaging hook stating interest in the role, referencing company mission and candidate core value.",
    )
    body_paragraphs: List[str] = Field(
        default_factory=list,
        description="2 focused paragraphs detailing relevant skills, key project achievements, and cultural fit.",
    )
    closing_paragraph: str = Field(
        ...,
        description="Enthusiastic closing reiterating fit, expressing eagerness for an interview, and professional thanks.",
    )
    sign_off: str = Field(default="Sincerely,", description="Formal closing sign-off.")


class ApplicationPackageOutput(BaseModel):
    """Complete application package combining tailored resume and cover letter."""

    resume: TailoredResumeOutput = Field(..., description="Structured tailored resume.")
    cover_letter: TailoredCoverLetterOutput = Field(..., description="Personalized cover letter.")