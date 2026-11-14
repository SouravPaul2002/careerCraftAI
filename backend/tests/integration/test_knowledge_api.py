import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.jwt import create_access_token
from app.database.session import SessionLocal
from app.models.user import User


@pytest.fixture
def auth_client():
    client = TestClient(app)
    db = SessionLocal()
    user = db.query(User).first()
    db.close()
    if not user:
        pytest.skip("No user in test database")

    token = create_access_token({"sub": str(user.id)})
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


def test_get_and_update_profile(auth_client):
    # 1. Get profile
    res = auth_client.get("/api/knowledge/profile")
    assert res.status_code == 200
    data = res.json()
    assert "user_id" in data
    assert "skills" in data

    # 2. Update profile
    payload = {
        "headline": "Lead Software Engineer",
        "skills": ["Python", "FastAPI", "React", "Docker"],
    }
    update_res = auth_client.put("/api/knowledge/profile", json=payload)
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["headline"] == "Lead Software Engineer"
    assert "Docker" in updated["skills"]


def test_search_knowledge_endpoint(auth_client):
    payload = {
        "query": "Software Engineer with Python and FastAPI experience",
        "limit": 3,
    }
    res = auth_client.post("/api/knowledge/search", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == payload["query"]
    assert "total_results" in data
    assert isinstance(data["chunks"], list)

