"""
Unit tests for Phase 8: LLM-as-a-Judge and ReAct Revision Agent.
Covers:
1. Judge Evaluation Pydantic Schema
2. Judge Prompt Templates & Scoring Weights
3. Judge Evaluator Agent execution & fallback
4. ReAct Revision Agent execution & fallback
5. Conditional Edge Routing Logic (APPROVED -> human_review, REJECTED -> react_revision, max retries -> escalate)
6. LangGraph Phase 8 Graph Structure & Compilation
7. Orchestrator API returning Judge evaluation and revision count
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.agents.application_generation.output import (
    ApplicationPackageOutput,
    ResumeHeader,
    ResumeProject,
    TailoredCoverLetterOutput,
    TailoredResumeOutput,
)
from app.agents.judge.evaluator import _build_fallback_judge_output, run_judge_agent
from app.agents.judge.output import JudgeEvaluationOutput
from app.agents.judge.prompts import SYSTEM_TEMPLATE as JUDGE_SYSTEM_TEMPLATE, build_judge_prompt
from app.agents.revision.agent import run_revision_agent
from app.agents.revision.prompts import SYSTEM_TEMPLATE as REVISION_SYSTEM_TEMPLATE
from app.api.dependencies import get_current_user
from app.graph.routing import route_judge_decision
from app.graph.workflow import build_graph
from app.main import app
from app.models.user import User


# ==============================================================================
# Helper Mock Application Package
# ==============================================================================
def _create_mock_application() -> ApplicationPackageOutput:
    return ApplicationPackageOutput(
        resume=TailoredResumeOutput(
            header=ResumeHeader(full_name="Sarah Connor", email="sarah@example.com"),
            professional_summary="Experienced Backend Engineer specializing in Python and cloud services.",
            skills={"Languages": ["Python", "SQL"]},
            selected_projects=[
                ResumeProject(
                    name="Microservice Gateway",
                    technologies=["Python", "FastAPI"],
                    bullet_points=["Architected API gateway handling 50k requests/min."],
                )
            ],
            work_experience=[],
            education=[],
        ),
        cover_letter=TailoredCoverLetterOutput(
            target_role="Senior Backend Engineer",
            company_name="TechCorp",
            salutation="Dear Hiring Team,",
            opening_paragraph="I am excited to apply for the Senior Backend Engineer role.",
            body_paragraphs=["My background aligns with your microservices architecture."],
            closing_paragraph="Thank you for considering my application.",
            sign_off="Sincerely,",
        ),
    )


# ==============================================================================
# 1. Judge Output Schema Tests
# ==============================================================================
def test_judge_evaluation_output_schema():
    """Verify JudgeEvaluationOutput validates scores, decisions, and feedback lists."""
    report = JudgeEvaluationOutput(
        decision="APPROVED",
        factual_accuracy_score=95,
        jd_alignment_score=90,
        project_relevance_score=88,
        readability_score=92,
        overall_score=92,
        unsupported_claims=[],
        actionable_feedback=["Minor typo check in summary."],
        summary_verdict="Application package is accurate, well-tailored, and approved.",
    )
    assert report.decision == "APPROVED"
    assert report.factual_accuracy_score == 95
    assert len(report.unsupported_claims) == 0

    # Test rejection with unsupported claims
    rejection = JudgeEvaluationOutput(
        decision="REJECTED",
        factual_accuracy_score=60,
        jd_alignment_score=70,
        project_relevance_score=65,
        readability_score=80,
        overall_score=66,
        unsupported_claims=["Candidate never worked at Google."],
        actionable_feedback=["Remove Google experience and replace with verified startup role."],
        summary_verdict="Rejected due to unverified employer claim.",
    )
    assert rejection.decision == "REJECTED"
    assert len(rejection.unsupported_claims) == 1


# ==============================================================================
# 2. Judge Prompt Template Tests
# ==============================================================================
def test_judge_prompt_templates():
    """Verify Judge prompts enforce audit weights and anti-hallucination rules."""
    assert "FACTUAL ACCURACY" in JUDGE_SYSTEM_TEMPLATE
    assert "Weight: 40%" in JUDGE_SYSTEM_TEMPLATE
    assert "LLM-as-a-Judge" in JUDGE_SYSTEM_TEMPLATE

    prompt = build_judge_prompt(
        job_analysis_text="Role: Python Developer",
        candidate_profile_text="Verified: Python, FastAPI",
        generated_application_text="Generated Resume & Cover Letter",
        format_instructions="JSON instructions",
    )
    messages = prompt.to_messages()
    assert len(messages) == 2
    assert "Role: Python Developer" in messages[1].content
    assert "Verified: Python, FastAPI" in messages[1].content


# ==============================================================================
# 3. Judge Evaluator Agent Execution & Fallback Tests
# ==============================================================================
def test_judge_agent_fallback_and_execution():
    """Verify run_judge_agent handles missing input and parses valid LLM response."""
    # When no application is provided, must reject safely
    fallback = _build_fallback_judge_output(None)
    assert fallback.decision == "REJECTED"
    assert fallback.factual_accuracy_score == 0

    # Mock valid LLM response
    valid_json = """{
        "decision": "APPROVED",
        "factual_accuracy_score": 90,
        "jd_alignment_score": 85,
        "project_relevance_score": 85,
        "readability_score": 90,
        "overall_score": 88,
        "unsupported_claims": [],
        "actionable_feedback": [],
        "summary_verdict": "Verified and approved."
    }"""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content=valid_json)

    with patch("app.agents.judge.evaluator.pick_llm", return_value=mock_llm):
        result = run_judge_agent(
            job_analysis={"job_title": "Backend Engineer"},
            candidate_profile={"full_name": "Sarah Connor"},
            generated_application=_create_mock_application(),
        )
        assert isinstance(result, JudgeEvaluationOutput)
        assert result.decision == "APPROVED"
        assert result.overall_score == 88


# ==============================================================================
# 4. ReAct Revision Agent Execution Tests
# ==============================================================================
def test_react_revision_agent_execution():
    """Verify ReAct Revision Agent incorporates feedback and produces revised package."""
    assert "Reason -> Act -> Observe" in REVISION_SYSTEM_TEMPLATE

    app_mock = _create_mock_application()

    # Revised LLM output fixing a flagged claim
    revised_json = """{
        "resume": {
            "header": {
                "full_name": "Sarah Connor",
                "email": "sarah@example.com"
            },
            "professional_summary": "Revised Senior Backend Engineer specializing in Python and distributed systems.",
            "skills": {
                "Languages": ["Python", "SQL", "Go"]
            },
            "selected_projects": [
                {
                    "name": "Microservice Gateway",
                    "technologies": ["Python", "FastAPI"],
                    "bullet_points": ["Engineered high-throughput API gateway handling 50k req/min."]
                }
            ],
            "work_experience": [],
            "education": []
        },
        "cover_letter": {
            "target_role": "Senior Backend Engineer",
            "company_name": "TechCorp",
            "salutation": "Dear Hiring Team,",
            "opening_paragraph": "I am thrilled to apply for the Senior Backend Engineer role.",
            "body_paragraphs": ["My proven track record in microservices makes me an ideal fit."],
            "closing_paragraph": "Thank you for your consideration.",
            "sign_off": "Sincerely,"
        }
    }"""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content=revised_json)

    with patch("app.agents.revision.agent.pick_llm", return_value=mock_llm):
        revised = run_revision_agent(
            job_analysis={"job_title": "Senior Backend Engineer"},
            candidate_profile={"full_name": "Sarah Connor"},
            current_application=app_mock,
            judge_evaluation={"unsupported_claims": ["Remove unverified Kubernetes claim"]},
            human_feedback="Emphasize distributed systems in the summary.",
        )
        assert isinstance(revised, ApplicationPackageOutput)
        assert "Revised" in revised.resume.professional_summary


# ==============================================================================
# 5. Conditional Edge Routing Logic Tests
# ==============================================================================
def test_route_judge_decision_logic():
    """Verify route_judge_decision strictly implements the 3 conditional branches."""
    # 1. Approved -> route to human_review
    state_approved = {
        "judge_evaluation": {"decision": "APPROVED", "overall_score": 90},
        "revision_count": 0,
    }
    assert route_judge_decision(state_approved) == "human_review"

    # 2. Rejected with retries remaining (0, 1, 2) -> route to react_revision
    state_rejected_first = {
        "judge_evaluation": {"decision": "REJECTED", "overall_score": 60},
        "revision_count": 0,
    }
    assert route_judge_decision(state_rejected_first) == "react_revision"

    state_rejected_second = {
        "judge_evaluation": {"decision": "REJECTED", "overall_score": 65},
        "revision_count": 2,
    }
    assert route_judge_decision(state_rejected_second) == "react_revision"

    # 3. Rejected with max retries reached (>= 3) -> route to escalate_human_review
    state_rejected_max = {
        "judge_evaluation": {"decision": "REJECTED", "overall_score": 68},
        "revision_count": 3,
    }
    assert route_judge_decision(state_rejected_max) == "escalate_human_review"


# ==============================================================================
# 6. LangGraph Phase 8 Compilation & Node Verification Tests
# ==============================================================================
def test_graph_structure_phase8():
    """Verify build_graph registers all 8 nodes and connects the ReAct loop."""
    graph = build_graph()
    nodes = graph.nodes
    expected_nodes = [
        "job_analysis",
        "candidate_analysis",
        "supervisor",
        "application_generation",
        "judge",
        "react_revision",
        "escalate_human_review",
        "human_review",
    ]
    for node in expected_nodes:
        assert node in nodes, f"Expected node '{node}' missing from graph."


# ==============================================================================
# 7. Orchestrator API Integration Test with Phase 8 Output
# ==============================================================================
def test_orchestrator_endpoint_phase8_response():
    """Verify POST /api/orchestrator/run returns judge_evaluation and revision_count."""
    fake_user = User(id=1, email="candidate@example.com", full_name="Candidate")
    app.dependency_overrides[get_current_user] = lambda: fake_user

    mock_state = {
        "status": "completed",
        "job_analysis": {"job_title": "Cloud Architect"},
        "candidate_profile": {"full_name": "Candidate"},
        "candidate_analysis": {"full_name": "Candidate"},
        "supervisor_evaluation": {"fit_score": 95},
        "generated_application": {
            "resume": {"header": {"full_name": "Candidate"}},
            "cover_letter": {"target_role": "Cloud Architect"},
        },
        "application_id": 202,
        "judge_evaluation": {
            "decision": "APPROVED",
            "factual_accuracy_score": 95,
            "overall_score": 92,
            "summary_verdict": "Fully approved by committee.",
        },
        "revision_count": 1,
        "errors": [],
    }

    client = TestClient(app)
    with patch("app.api.routes.orchestrator.run_agent_workflow", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_state
        response = client.post(
            "/api/orchestrator/run",
            json={
                "job_raw_text": "Seeking an experienced Cloud Architect to manage AWS and GCP infrastructure.",
                "hint_title": "Cloud Architect",
                "hint_company": "CloudFlow Inc",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["application_id"] == 202
        assert "judge_evaluation" in data
        assert data["judge_evaluation"]["decision"] == "APPROVED"
        assert data["revision_count"] == 1

    app.dependency_overrides.clear()
