import pytest
from app.tools.jd_tools import clean_and_normalize_jd, validate_jd_text
from app.agents.job_analysis.output import JobAnalysisOutput, JobRequirements


def test_clean_and_normalize_jd():
    raw = """
        • Build REST APIs using Python & FastAPI
        ▪ Maintain PostgreSQL database
        * Write unit tests
        
        
        Requirements:
        – 3+ years experience
    """
    cleaned = clean_and_normalize_jd(raw)
    assert "- Build REST APIs using Python & FastAPI" in cleaned
    assert "- Maintain PostgreSQL database" in cleaned
    assert "- Write unit tests" in cleaned
    assert "- 3+ years experience" in cleaned
    assert "\n\n\n" not in cleaned


def test_validate_jd_text():
    # Empty
    valid, msg = validate_jd_text("")
    assert not valid
    assert "cannot be empty" in msg

    # Too short
    valid, msg = validate_jd_text("Too short")
    assert not valid
    assert "too short" in msg

    # Valid job description
    valid_jd = """
    Software Engineer - Backend & Cloud
    We are looking for a Software Engineer to join our team.
    You will develop high-throughput microservices using FastAPI,
    manage PostgreSQL databases, and deploy containers with Docker.
    Requirements:
    - 3+ years of professional backend development
    - Bachelor's degree in Computer Science or related field
    """
    valid, msg = validate_jd_text(valid_jd)
    assert valid
    assert msg == ""


def test_job_analysis_output_schema():
    data = {
        "job_title": "Backend AI Engineer",
        "company_name": "Google",
        "role_summary": "Building modern agentic applications.",
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "preferred_skills": ["Docker", "LangChain"],
        "responsibilities": ["Design APIs", "Write clean code"],
        "requirements": {
            "minimum_years_experience": 3,
            "education_level": "B.Tech in CS",
        },
        "keywords": ["RAG", "Microservices", "REST"],
    }
    model = JobAnalysisOutput.model_validate(data)
    assert model.job_title == "Backend AI Engineer"
    assert "Python" in model.required_skills
    assert model.requirements.minimum_years_experience == 3

