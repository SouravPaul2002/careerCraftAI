"""
Unit and Integration tests for Phase 5:
- Candidate Analysis schema & profile formatting
- Supervisor Evaluation schema
- LangGraph parallel branching and workflow compilation
- Orchestrator API endpoint
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.agents.candidate_analysis.agent import format_profile_for_llm
from app.agents.candidate_analysis.output import CandidateAnalysisOutput
from app.agents.supervisor.output import SupervisorEvaluationOutput
from app.api.dependencies import get_current_user
from app.graph.workflow import build_graph
from app.main import app
from app.models.user import User


# -------------------------------------------------------------------------
# 1. Schema Tests
# -------------------------------------------------------------------------
def test_candidate_analysis_output_schema():
    """Verify CandidateAnalysisOutput schema validates with required & optional fields."""
    data = {
        "full_name": "Alice Smith",
        "headline": "Junior Full-Stack Developer",
        "core_skills": ["Python", "FastAPI", "React"],
        "primary_domains": ["Web Development"],
        "experience_summary": None,  # Fresher with no formal experience
        "top_competencies": ["API Design", "Database Modeling"],
    }
    model = CandidateAnalysisOutput.model_validate(data)
    assert model.full_name == "Alice Smith"
    assert model.headline == "Junior Full-Stack Developer"
    assert model.experience_summary is None
    assert "Python" in model.core_skills


def test_supervisor_evaluation_output_schema():
    """Verify SupervisorEvaluationOutput schema validates fit score and strategy."""
    data = {
        "fit_score": 88,
        "matched_skills": ["Python", "PostgreSQL"],
        "missing_skills": ["Kubernetes"],
        "strengths": ["Strong relational database experience."],
        "weaknesses": ["Lacks container orchestration background."],
        "strategy_recommendations": [
            "Highlight backend database optimization projects.",
            "Emphasize Docker experience to offset Kubernetes gap.",
        ],
    }
    model = SupervisorEvaluationOutput.model_validate(data)
    assert model.fit_score == 88
    assert "Python" in model.matched_skills
    assert "Kubernetes" in model.missing_skills
    assert len(model.strategy_recommendations) == 2


# -------------------------------------------------------------------------
# 2. Context Formatter Tests
# -------------------------------------------------------------------------
def test_format_profile_for_llm():
    """Verify format_profile_for_llm correctly includes project links and academic CGPA."""
    profile_dict = {
        "full_name": "Bob Taylor",
        "headline": "AI Engineer",
        "summary": "Passionate about LLMs and agents.",
        "skills": ["Python", "LangGraph", "ChromaDB"],
        "experience": [
            {"title": "AI Intern", "company": "TechLab", "description": "Built RAG systems."}
        ],
        "projects": [
            {
                "name": "CareerCraft AI",
                "description": "Multi-agent job assistant",
                "url": "https://github.com/bob/careercraft",
            }
        ],
        "education": [
            {"degree": "B.Tech in CS", "institution": "State University", "cgpa": "9.2"}
        ],
    }

    formatted = format_profile_for_llm(profile_dict)
    assert "Full Name: Bob Taylor" in formatted
    assert "https://github.com/bob/careercraft" in formatted
    assert "[Score/CGPA: 9.2]" in formatted
    assert "TechLab" in formatted


# -------------------------------------------------------------------------
# 3. LangGraph Workflow Structure & Parallel Execution Tests
# -------------------------------------------------------------------------
def test_graph_structure_and_compilation():
    """Verify graph builder registers all nodes and compiles successfully."""
    builder = build_graph()
    graph = builder.compile()

    # Check node names are present in the graph nodes
    assert "job_analysis" in graph.nodes
    assert "candidate_analysis" in graph.nodes
    assert "supervisor" in graph.nodes


@pytest.mark.asyncio
async def test_graph_parallel_execution_mocked():
    """Verify parallel branches run and merge into supervisor join node."""
    builder = build_graph()
    graph = builder.compile()

    with patch("app.graph.nodes.run_job_analysis_agent") as mock_job, \
         patch("app.graph.nodes.Session") as mock_session_cls, \
         patch("app.graph.nodes.run_candidate_analysis_agent") as mock_cand, \
         patch("app.graph.nodes.run_supervisor_agent") as mock_sup, \
         patch("app.graph.nodes.run_application_generation_agent") as mock_gen, \
         patch("app.graph.nodes.run_judge_agent") as mock_judge:

        mock_job.return_value = MagicMock(
            model_dump=lambda: {"job_title": "Backend AI Developer", "required_skills": ["Python"]}
        )
        mock_cand.return_value = MagicMock(
            model_dump=lambda: {"headline": "Full-Stack AI Developer", "core_skills": ["Python"]}
        )
        mock_sup.return_value = MagicMock(
            model_dump=lambda: {"fit_score": 95, "matched_skills": ["Python"]}
        )
        mock_gen.return_value = MagicMock(
            model_dump=lambda: {"resume": {}, "cover_letter": {}}
        )
        mock_judge.return_value = MagicMock(
            model_dump=lambda: {"decision": "APPROVED", "overall_score": 90}
        )

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_session_cls.return_value.__enter__.return_value = mock_db

        init_state = {
            "user_id": 1,
            "job_raw_text": "We are seeking a Backend AI Developer with strong Python skills.",
            "hint_title": None,
            "hint_company": None,
            "job_analysis": None,
            "candidate_profile": None,
            "candidate_analysis": None,
            "supervisor_evaluation": None,
            "status": "in_progress",
            "errors": [],
        }

        result = await graph.ainvoke(init_state)

        assert result["status"] == "completed"
        assert result["job_analysis"]["job_title"] == "Backend AI Developer"
        assert result["candidate_analysis"]["headline"] == "Full-Stack AI Developer"
        assert result["supervisor_evaluation"]["fit_score"] == 95


# -------------------------------------------------------------------------
# 4. API Route Integration Tests
# -------------------------------------------------------------------------
def test_orchestrator_endpoint_validation():
    """Verify 422 for schema violation and 400 if JD fails word-count validation."""
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.is_active = True

    app.dependency_overrides[get_current_user] = lambda: mock_user
    client = TestClient(app)

    try:
        # Pydantic schema validation: min_length=30
        res_422 = client.post(
            "/api/orchestrator/run",
            json={"job_raw_text": "Too short"},
        )
        assert res_422.status_code == 422

        # JD length validation (< 50 characters, but >= 30 for Pydantic)
        res_400 = client.post(
            "/api/orchestrator/run",
            json={"job_raw_text": "Short string that is over 30 chars"},
        )
        assert res_400.status_code == 400
    finally:
        app.dependency_overrides.clear()


def test_orchestrator_endpoint_success():
    """Verify successful 200 response from /api/orchestrator/run with realistic JD."""
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.is_active = True

    app.dependency_overrides[get_current_user] = lambda: mock_user
    client = TestClient(app)

    valid_jd = """
    We are looking for an experienced Senior Backend Software Engineer to join our core team.
    You will design and implement scalable distributed services using Python, FastAPI, and PostgreSQL.
    Requirements:
    - 3+ years experience in Python and REST API development.
    - Strong knowledge of databases, Docker containerization, and automated testing.
    """

    payload = {
        "job_raw_text": valid_jd,
        "hint_title": "Senior Backend Engineer",
        "hint_company": "Tech Corp",
    }

    mock_state = {
        "status": "completed",
        "job_analysis": {"job_title": "Senior Backend Engineer"},
        "candidate_profile": {"full_name": "Alice"},
        "candidate_analysis": {"headline": "Senior Backend Engineer"},
        "supervisor_evaluation": {"fit_score": 92, "matched_skills": ["Python", "FastAPI"]},
        "errors": [],
    }

    try:
        with patch("app.api.routes.orchestrator.run_agent_workflow", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_state
            response = client.post("/api/orchestrator/run", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["job_analysis"]["job_title"] == "Senior Backend Engineer"
            assert data["supervisor_evaluation"]["fit_score"] == 92
    finally:
        app.dependency_overrides.clear()
