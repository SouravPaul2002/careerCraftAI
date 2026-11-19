"""
Unit tests for Phase 9: LaTeX Generation, Escaping, Validation, Versioning, and API Routes.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.main import app
from app.models.user import User
from app.models.generated_application import GeneratedApplication
from app.models.document_version import DocumentVersion
from app.services.latex_service import (
    escape_latex,
    validate_latex_syntax,
    render_resume_latex,
    render_cover_letter_latex,
    compile_latex_to_pdf,
    RESUME_TEMPLATES,
    COVER_LETTER_TEMPLATES,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_auth():
    user = User(id=1, email="test@example.com", full_name="Test User", hashed_password="pw")
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides.pop(get_current_user, None)
    raw = r"100% of $50 & Python_code #1 {braces} ~tilde ^caret \backslash"
    escaped = escape_latex(raw)
    assert r"100\%" in escaped
    assert r"\$50" in escaped
    assert r"\&" in escaped
    assert r"Python\_code" in escaped
    assert r"\#1" in escaped
    assert r"\{braces\}" in escaped
    assert r"\textasciitilde{}" in escaped
    assert r"\textasciicircum{}" in escaped
    assert r"\textbackslash{}" in escaped


def test_escape_latex_none_and_types():
    assert escape_latex(None) == ""
    assert escape_latex(123) == "123"
    assert escape_latex(45.67) == "45.67"


def test_validate_latex_syntax_valid():
    valid_tex = r"""\documentclass{article}
\begin{document}
Hello world!
\begin{itemize}
    \item Item 1
\end{itemize}
\end{document}"""
    is_valid, err = validate_latex_syntax(valid_tex)
    assert is_valid is True
    assert err is None


def test_validate_latex_syntax_missing_structure():
    no_doc = r"\begin{document} Hello \end{document}"
    is_valid, err = validate_latex_syntax(no_doc)
    assert is_valid is False
    assert "documentclass" in err.lower()

    no_end = r"\documentclass{article}\begin{document} Hello"
    is_valid, err = validate_latex_syntax(no_end)
    assert is_valid is False
    assert "end{document}" in err.lower()


def test_validate_latex_syntax_mismatched_braces():
    bad_braces = r"\documentclass{article}\begin{document} Hello {world \end{document}"
    is_valid, err = validate_latex_syntax(bad_braces)
    assert is_valid is False
    assert "curly braces" in err.lower()


def test_validate_latex_syntax_mismatched_environments():
    bad_env = r"""\documentclass{article}
\begin{document}
\begin{itemize}
    \item test
\end{enumerate}
\end{document}"""
    is_valid, err = validate_latex_syntax(bad_env)
    assert is_valid is False
    assert "environment mismatch" in err.lower()


def test_validate_latex_syntax_prohibits_dangerous_commands():
    malicious = r"""\documentclass{article}
\begin{document}
\write18{rm -rf /}
\end{document}"""
    is_valid, err = validate_latex_syntax(malicious)
    assert is_valid is False
    assert "unsafe" in err.lower() or "prohibited" in err.lower()


def test_render_all_resume_templates():
    sample_resume = {
        "header": {
            "full_name": "Dev User",
            "email": "dev@test.com",
            "location": "Boston, MA",
            "linkedin_url": "https://linkedin.com/in/devuser",
        },
        "professional_summary": "Full stack engineer specializing in Python and React.",
        "skills": {
            "Languages": ["Python", "JavaScript", "SQL"],
        },
        "work_experience": [
            {
                "role": "Software Engineer",
                "company": "Acme Inc & Co",
                "duration": "2022 - Present",
                "bullet_points": ["Increased throughput by 50% using async workers"],
            }
        ],
        "selected_projects": [
            {
                "name": "Project Alpha",
                "technologies": ["FastAPI", "Postgres"],
                "bullet_points": ["Developed robust REST API"],
            }
        ],
        "education": [
            {
                "degree": "B.S. in Computer Science",
                "institution": "Boston University",
                "year": "2022",
            }
        ],
    }

    for t_name in RESUME_TEMPLATES.keys():
        tex = render_resume_latex(sample_resume, template_name=t_name)
        assert r"\documentclass" in tex
        assert "Dev User" in tex
        assert r"Acme Inc \& Co" in tex  # Escaped &
        assert r"50\%" in tex  # Escaped %
        is_valid, err = validate_latex_syntax(tex)
        assert is_valid is True, f"Template {t_name} failed validation: {err}"


def test_render_all_cover_letter_templates():
    sample_cl = {
        "candidate_name": "Dev User",
        "company_name": "Acme Innovations",
        "target_role": "Senior Engineer",
        "opening_paragraph": "I am excited to apply for the Senior Engineer position.",
        "body_paragraphs": [
            "With over 5 years in distributed systems, I have delivered scalable solutions."
        ],
        "closing_paragraph": "Thank you for your consideration.",
        "sign_off": "Best regards,",
    }

    contact = {
        "full_name": "Dev User",
        "email": "dev@test.com",
        "location": "Boston, MA",
    }

    for t_name in COVER_LETTER_TEMPLATES.keys():
        tex = render_cover_letter_latex(sample_cl, contact_info=contact, template_name=t_name)
        assert r"\documentclass" in tex
        assert "Dev User" in tex
        assert "Acme Innovations" in tex
        assert "Senior Engineer" in tex
        is_valid, err = validate_latex_syntax(tex)
        assert is_valid is True, f"Cover Letter template {t_name} failed validation: {err}"


def test_compile_latex_to_pdf_output():
    simple_tex = r"""\documentclass{article}
\begin{document}
Test PDF Compilation
\end{document}"""
    pdf_bytes = compile_latex_to_pdf(simple_tex)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 100
    assert pdf_bytes.startswith(b"%PDF-")


# API Routes Tests

def test_api_list_templates():
    response = client.get("/api/latex/templates", headers={"Authorization": "Bearer token"})
    assert response.status_code == 200
    data = response.json()
    assert "resume_templates" in data
    assert "cover_letter_templates" in data
    ids = [t["id"] for t in data["resume_templates"]]
    assert "modern" in ids
    assert "classic" in ids
    assert "minimal" in ids


def test_api_validate_latex():
    # Valid
    res = client.post(
        "/api/latex/validate",
        json={"latex_code": r"\documentclass{article}\begin{document}Hello\end{document}"},
    )
    assert res.status_code == 200
    assert res.json()["is_valid"] is True

    # Invalid
    res_bad = client.post(
        "/api/latex/validate",
        json={"latex_code": r"\documentclass{article}\begin{document}Hello"},
    )
    assert res_bad.status_code == 200
    assert res_bad.json()["is_valid"] is False


def test_api_render_latex_unauthorized():
    with patch("app.api.routes.latex.verify_application_ownership", return_value=None):
        res = client.post(
            "/api/latex/render",
            json={"application_id": 999, "document_type": "resume", "template_name": "modern"},
        )
        assert res.status_code == 404


def test_api_render_latex_success():
    mock_app = MagicMock(spec=GeneratedApplication)
    mock_app.id = 1
    mock_app.user_id = 1
    mock_app.resume_data = {
        "header": {"full_name": "Alice Smith"},
        "professional_summary": "Expert dev",
        "skills": {"Languages": ["Go", "Python"]},
    }
    mock_app.cover_letter_data = {}

    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    with patch("app.api.routes.latex.verify_application_ownership", return_value=mock_app):
        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            res = client.post(
                "/api/latex/render",
                json={"application_id": 1, "document_type": "resume", "template_name": "modern"},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["application_id"] == 1
            assert data["document_type"] == "resume"
            assert "Alice Smith" in data["latex_code"]
        finally:
            app.dependency_overrides.pop(get_db, None)
