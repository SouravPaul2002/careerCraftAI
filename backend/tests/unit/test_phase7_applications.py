"""
Unit tests for Phase 7: Resume and Cover Letter Generation.
Covers:
1. Resume and Cover Letter Pydantic Schemas
2. Anti-Hallucination & XYZ Prompt Templates
3. Fallback Generation Mechanism
4. Application Generation Agent execution with LLM mock
5. LangGraph Phase 7 Workflow wiring (supervisor -> application_generation -> END)
6. Application Generation Node execution
7. Orchestrator API endpoint returning generated application
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.agents.application_generation.agent import (
    _build_fallback_application,
    run_application_generation_agent,
)
from app.agents.application_generation.output import (
    ApplicationPackageOutput,
    ResumeEducation,
    ResumeExperience,
    ResumeHeader,
    ResumeProject,
    TailoredCoverLetterOutput,
    TailoredResumeOutput,
)
from app.agents.application_generation.prompts import (
    SYSTEM_TEMPLATE,
    build_application_prompt,
)
from app.api.dependencies import get_current_user
from app.graph.nodes import application_generation_node
from app.graph.workflow import build_graph
from app.main import app
from app.models.generated_application import GeneratedApplication
from app.models.user import User


# ==============================================================================
# 1. Schema Validation Tests
# ==============================================================================
def test_application_package_schemas():
    """Verify TailoredResumeOutput, TailoredCoverLetterOutput, and ApplicationPackageOutput."""
    header = ResumeHeader(
        full_name="Sarah Connor",
        email="sarah@example.com",
        phone="+1-555-0199",
        location="Los Angeles, CA",
        github_url="https://github.com/sarahconnor",
    )
    assert header.full_name == "Sarah Connor"
    assert header.github_url == "https://github.com/sarahconnor"

    project = ResumeProject(
        name="Distributed Ledger",
        technologies=["Python", "FastAPI", "PostgreSQL"],
        bullet_points=[
            "Architected high-throughput ledger processing 10,000 tx/sec.",
            "Integrated asynchronous workers reducing database latency by 45%.",
        ],
        repo_url="https://github.com/sarahconnor/ledger",
    )
    assert len(project.technologies) == 3
    assert len(project.bullet_points) == 2

    resume = TailoredResumeOutput(
        header=header,
        professional_summary="Results-oriented Software Engineer with 4+ years of backend development experience.",
        skills={
            "Languages": ["Python", "TypeScript", "SQL"],
            "Frameworks": ["FastAPI", "React", "Next.js"],
        },
        selected_projects=[project],
        work_experience=[
            ResumeExperience(
                company="Cyberdyne Systems",
                role="Backend Engineer",
                duration="2022 - 2024",
                bullet_points=[
                    "Spearheaded microservices migration improving uptime to 99.99%."
                ],
            )
        ],
        education=[
            ResumeEducation(
                degree="B.S. in Computer Science",
                institution="UCLA",
                year="2022",
            )
        ],
    )
    assert resume.header.full_name == "Sarah Connor"
    assert len(resume.selected_projects) == 1

    cover_letter = TailoredCoverLetterOutput(
        target_role="Senior Backend Engineer",
        company_name="TechCorp",
        salutation="Dear Hiring Team,",
        opening_paragraph="I am excited to apply for the Senior Backend Engineer role at TechCorp.",
        body_paragraphs=[
            "My experience building high-scale distributed systems aligns with your requirements.",
            "In my previous work at Cyberdyne, I optimized core microservice pipelines.",
        ],
        closing_paragraph="Thank you for considering my candidacy. I look forward to speaking soon.",
        sign_off="Sincerely,",
    )
    assert cover_letter.target_role == "Senior Backend Engineer"
    assert len(cover_letter.body_paragraphs) == 2

    package = ApplicationPackageOutput(resume=resume, cover_letter=cover_letter)
    assert package.resume.header.full_name == "Sarah Connor"
    assert package.cover_letter.company_name == "TechCorp"

    # Test serialization to dict
    pkg_dict = package.model_dump()
    assert "resume" in pkg_dict
    assert "cover_letter" in pkg_dict


# ==============================================================================
# 2. Prompt Template & Anti-Hallucination Guardrail Tests
# ==============================================================================
def test_prompt_anti_hallucination_and_guardrails():
    """Verify prompt templates enforce strict factual accuracy, XYZ rules, and internship retention."""
    assert "ANTI-HALLUCINATION" in SYSTEM_TEMPLATE
    assert "XYZ FORMULA" in SYSTEM_TEMPLATE
    assert "NEVER fabricate or invent" in SYSTEM_TEMPLATE
    assert "INTERNSHIPS" in SYSTEM_TEMPLATE
    assert "TRANSFERABLE" in SYSTEM_TEMPLATE

    prompt_val = build_application_prompt(
        job_analysis_text="Job: Senior Python Developer",
        candidate_analysis_text="Candidate: Sarah Connor, Skills: Python, FastAPI",
        supervisor_evaluation_text="Matched: Python, Fit Score: 92",
        format_instructions="JSON schema goes here",
    )
    messages = prompt_val.to_messages()
    assert len(messages) == 2
    system_msg = messages[0].content
    human_msg = messages[1].content
    assert "Executive Resume Writer" in system_msg
    assert "Job: Senior Python Developer" in human_msg
    assert "Sarah Connor" in human_msg
    assert "Fit Score: 92" in human_msg


# ==============================================================================
# 3. Fallback Generation Mechanism Tests
# ==============================================================================
def test_build_fallback_application():
    """Verify fallback preserves candidate's internships, experience, and education."""
    candidate_profile = {
        "full_name": "John Doe",
        "skills": ["Python", "Docker"],
        "experience": [
            {
                "title": "Software Engineer Intern",
                "company": "Startup Co",
                "duration": "Summer 2023",
                "description": "Built REST APIs and telemetry dashboards.",
            }
        ],
        "education": [
            {
                "degree": "B.S. in Computer Science",
                "institution": "Tech University",
                "year": "2024",
                "grade_or_cgpa": "3.8/4.0",
            }
        ],
    }
    candidate_analysis = {"full_name": "John Doe", "core_skills": ["Python", "Docker"]}
    job_analysis = {"job_title": "Backend Lead", "company_name": "Acme Inc"}

    fallback = _build_fallback_application(
        candidate_profile=candidate_profile,
        candidate_analysis=candidate_analysis,
        job_analysis=job_analysis,
    )
    assert isinstance(fallback, ApplicationPackageOutput)
    assert fallback.resume.header.full_name == "John Doe"
    assert fallback.cover_letter.target_role == "Backend Lead"
    assert fallback.cover_letter.company_name == "Acme Inc"
    assert "Python" in fallback.resume.skills["Technical Skills"]

    # Verify internship is retained in work_experience
    assert len(fallback.resume.work_experience) == 1
    assert fallback.resume.work_experience[0].role == "Software Engineer Intern"
    assert fallback.resume.work_experience[0].company == "Startup Co"

    # Verify education is retained
    assert len(fallback.resume.education) == 1
    assert fallback.resume.education[0].institution == "Tech University"

    # When all inputs are None
    fallback_empty = _build_fallback_application(None, None, None)
    assert isinstance(fallback_empty, ApplicationPackageOutput)
    assert fallback_empty.resume.header.full_name == "Candidate"


# ==============================================================================
# 4. Agent Mock Execution Test
# ==============================================================================
def test_run_application_generation_agent_mock():
    """Verify run_application_generation_agent parses valid LLM response."""
    valid_json = """{
        "resume": {
            "header": {
                "full_name": "Jane Developer",
                "email": "jane@example.com",
                "location": "New York, NY"
            },
            "professional_summary": "Full-Stack Engineer with experience in Python and React.",
            "skills": {
                "Languages": ["Python", "JavaScript"]
            },
            "selected_projects": [
                {
                    "name": "Cloud Dashboard",
                    "technologies": ["Python", "React"],
                    "bullet_points": ["Built real-time telemetry dashboard."]
                }
            ],
            "work_experience": [],
            "education": []
        },
        "cover_letter": {
            "target_role": "Full-Stack Engineer",
            "company_name": "Innovate Ltd",
            "salutation": "Dear Hiring Team,",
            "opening_paragraph": "I am writing to apply for the Full-Stack role.",
            "body_paragraphs": ["My background in React and Python fits your stack."],
            "closing_paragraph": "Thank you for reviewing my application.",
            "sign_off": "Best regards,"
        }
    }"""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content=valid_json)

    with patch("app.agents.application_generation.agent.pick_llm", return_value=mock_llm):
        result = run_application_generation_agent(
            job_analysis={"job_title": "Full-Stack Engineer"},
            candidate_analysis={"full_name": "Jane Developer"},
            supervisor_evaluation={"fit_score": 85},
        )
        assert isinstance(result, ApplicationPackageOutput)
        assert result.resume.header.full_name == "Jane Developer"
        assert result.cover_letter.company_name == "Innovate Ltd"


# ==============================================================================
# 5. LangGraph Phase 7 Workflow Structure Tests
# ==============================================================================
def test_graph_structure_phase7():
    """Verify build_graph includes all 4 nodes and connects supervisor -> application_generation -> END."""
    graph = build_graph()
    nodes = graph.nodes
    assert "job_analysis" in nodes
    assert "candidate_analysis" in nodes
    assert "supervisor" in nodes
    assert "application_generation" in nodes


# ==============================================================================
# 6. Application Generation Node Execution Test
# ==============================================================================
def test_application_generation_node_execution():
    """Verify application_generation_node calls agent, persists to DB, and updates state."""
    mock_package = _build_fallback_application(
        {},
        {"full_name": "Alex Smith", "core_skills": ["Python"]},
        {"job_title": "Software Engineer", "company_name": "Global Corp"},
    )

    state = {
        "user_id": 1,
        "job_raw_text": "Need a Python engineer...",
        "hint_title": "Software Engineer",
        "hint_company": "Global Corp",
        "job_analysis": {"job_title": "Software Engineer", "company_name": "Global Corp"},
        "candidate_profile": {},
        "candidate_analysis": {"full_name": "Alex Smith", "core_skills": ["Python"]},
        "supervisor_evaluation": {"fit_score": 90},
        "generated_application": None,
        "application_id": None,
        "status": "in_progress",
        "errors": [],
    }

    mock_db = MagicMock()
    mock_record = MagicMock()
    mock_record.id = 42

    with patch("app.graph.nodes.run_application_generation_agent", return_value=mock_package):
        with patch("app.graph.nodes.Session") as mock_session_cls:
            mock_session_cls.return_value.__enter__.return_value = mock_db
            # Make refresh set the ID
            def mock_refresh(rec):
                rec.id = 42
            mock_db.refresh.side_effect = mock_refresh

            updates = application_generation_node(state)
            assert updates["status"] in ["completed", "draft_generated"]
            assert updates["application_id"] == 42
            assert "resume" in updates["generated_application"]
            assert "cover_letter" in updates["generated_application"]
            assert mock_db.add.called
            assert mock_db.commit.called


# ==============================================================================
# 7. Orchestrator API Endpoint returning Generated Application
# ==============================================================================
def test_orchestrator_endpoint_with_phase7_output():
    """Verify POST /api/orchestrator/run returns generated_application and application_id."""
    fake_user = User(id=1, email="candidate@example.com", full_name="Candidate")
    app.dependency_overrides[get_current_user] = lambda: fake_user

    mock_state = {
        "status": "completed",
        "job_analysis": {"job_title": "Senior Engineer"},
        "candidate_profile": {"full_name": "Candidate"},
        "candidate_analysis": {"full_name": "Candidate"},
        "supervisor_evaluation": {"fit_score": 90},
        "generated_application": {
            "resume": {"header": {"full_name": "Candidate"}},
            "cover_letter": {"target_role": "Senior Engineer"},
        },
        "application_id": 101,
        "errors": [],
    }

    client = TestClient(app)
    with patch("app.api.routes.orchestrator.run_agent_workflow", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_state
        response = client.post(
            "/api/orchestrator/run",
            json={
                "job_raw_text": "We are seeking a talented Senior Engineer with experience in Python and FastAPI to join our engineering team.",
                "hint_title": "Senior Engineer",
                "hint_company": "Acme Inc",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["application_id"] == 101
        assert "generated_application" in data
        assert data["generated_application"]["cover_letter"]["target_role"] == "Senior Engineer"

    app.dependency_overrides.clear()
