"""
Unit and integration tests for Phase 6:
- GitHub MCP client tools
- Google Drive MCP client tools
- Central MCP Tool Registry & Multi-user isolation
"""
import base64
from unittest.mock import MagicMock, patch
import pytest

from app.mcp.client.drive_client import (
    get_drive_file_metadata,
    read_drive_file_content,
    search_drive_files,
)
from app.mcp.client.github_client import (
    get_recent_commits,
    get_repository_details,
    get_repository_readme,
    list_repository_tree,
    read_repository_file,
)
from app.mcp.registry import get_mcp_tools_for_user


# -------------------------------------------------------------------------
# 1. GitHub MCP Tools Tests
# -------------------------------------------------------------------------
def test_github_get_repository_details_success():
    """Verify repo details extraction with mocked httpx response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "name": "careercraft-ai",
        "full_name": "user/careercraft-ai",
        "description": "Multi-agent career assistant",
        "language": "Python",
        "stargazers_count": 42,
        "forks_count": 7,
        "topics": ["ai", "fastapi", "react"],
        "default_branch": "main",
        "html_url": "https://github.com/user/careercraft-ai",
    }

    with patch("httpx.get", return_value=mock_resp):
        res = get_repository_details("fake-token", "user", "careercraft-ai")
        assert res["name"] == "careercraft-ai"
        assert res["primary_language"] == "Python"
        assert res["stars"] == 42
        assert "ai" in res["topics"]


def test_github_get_repository_details_404():
    """Verify clean error dict when repository does not exist."""
    mock_resp = MagicMock()
    mock_resp.status_code = 404

    with patch("httpx.get", return_value=mock_resp):
        res = get_repository_details("fake-token", "user", "unknown-repo")
        assert "error" in res
        assert "not found" in res["error"]


def test_github_read_repository_file_decoding():
    """Verify base64 encoded source files are decoded to clean text."""
    raw_code = "def hello():\n    return 'world'"
    encoded = base64.b64encode(raw_code.encode("utf-8")).decode("utf-8")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "content": encoded,
        "encoding": "base64",
    }

    with patch("httpx.get", return_value=mock_resp):
        text = read_repository_file("fake-token", "user", "repo", "main.py")
        assert "def hello():" in text
        assert "return 'world'" in text


def test_github_get_recent_commits():
    """Verify commit history extraction and truncation."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "sha": "1234567890abcdef",
            "commit": {
                "message": "Add LangGraph state machine\n\nDetailed notes here...",
                "author": {"name": "Alice", "date": "2026-11-19T10:00:00Z"},
            },
        }
    ]

    with patch("httpx.get", return_value=mock_resp):
        commits = get_recent_commits("fake-token", "user", "repo", limit=1)
        assert len(commits) == 1
        assert commits[0]["sha"] == "1234567"
        assert commits[0]["message"] == "Add LangGraph state machine"
        assert commits[0]["author"] == "Alice"


# -------------------------------------------------------------------------
# 2. Google Drive MCP Tools Tests
# -------------------------------------------------------------------------
def test_drive_search_files():
    """Verify search_drive_files filters and formats search results."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "files": [
            {
                "id": "file-123",
                "name": "Resume_2026.pdf",
                "mimeType": "application/pdf",
                "size": "1048576",
                "modifiedTime": "2026-11-19T08:00:00Z",
                "webViewLink": "https://drive.google.com/file/d/file-123/view",
            }
        ]
    }

    with patch("httpx.get", return_value=mock_resp):
        files = search_drive_files("fake-token", query="Resume")
        assert len(files) == 1
        assert files[0]["file_id"] == "file-123"
        assert files[0]["name"] == "Resume_2026.pdf"
        assert files[0]["mime_type"] == "application/pdf"


def test_drive_read_google_doc_export():
    """Verify Google Docs are exported to plain text via the export endpoint."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "Career Summary:\nExperienced Python & Cloud Engineer."

    with patch("httpx.get", return_value=mock_resp):
        content = read_drive_file_content(
            access_token="fake-token",
            file_id="doc-999",
            mime_type="application/vnd.google-apps.document",
        )
        assert "Experienced Python & Cloud Engineer." in content


# -------------------------------------------------------------------------
# 3. Registry & Multi-User Isolation Tests
# -------------------------------------------------------------------------
def test_registry_produces_all_tools():
    """Verify registry outputs all 8 standardized MCP tools."""
    with patch("app.mcp.registry.get_user_github_token", return_value="user-token-gh"), \
         patch("app.mcp.registry.get_user_drive_token", return_value="user-token-drive"):

        tools = get_mcp_tools_for_user(user_id=1)
        tool_names = [t.name for t in tools]

        assert len(tools) == 8
        assert "github_get_repo_details" in tool_names
        assert "github_list_files" in tool_names
        assert "github_read_file" in tool_names
        assert "github_get_readme" in tool_names
        assert "github_get_recent_commits" in tool_names
        assert "drive_search_files" in tool_names
        assert "drive_get_file_metadata" in tool_names
        assert "drive_read_file_content" in tool_names


def test_registry_disconnected_account_handling():
    """Verify tools return clean error notice when user has not connected service."""
    # When user has no tokens
    with patch("app.mcp.registry.get_user_github_token", return_value=None), \
         patch("app.mcp.registry.get_user_drive_token", return_value=None):

        tools = get_mcp_tools_for_user(user_id=42)
        gh_tool = next(t for t in tools if t.name == "github_get_repo_details")
        drive_tool = next(t for t in tools if t.name == "drive_search_files")

        gh_res = gh_tool.invoke({"owner": "alice", "repo": "app"})
        assert "GitHub is not connected" in str(gh_res)

        drive_res = drive_tool.invoke({"query": "Resume"})
        assert "Google Drive is not connected" in str(drive_res)


# -------------------------------------------------------------------------
# 4. MCP API Routes Tests
# -------------------------------------------------------------------------
def test_mcp_api_routes():
    """Verify GET /api/mcp/tools and POST /api/mcp/execute."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.dependencies import get_current_user
    from app.models.user import User

    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.is_active = True
    app.dependency_overrides[get_current_user] = lambda: mock_user

    client = TestClient(app)

    try:
        # Test listing tools
        res = client.get("/api/mcp/tools")
        assert res.status_code == 200
        data = res.json()
        assert data["tools_count"] == 8

        # Test executing a tool
        exec_res = client.post(
            "/api/mcp/execute",
            json={"tool_name": "github_get_repo_details", "arguments": {"owner": "test", "repo": "demo"}},
        )
        assert exec_res.status_code == 200
        exec_data = exec_res.json()
        assert exec_data["success"] is True

        # Test executing non-existent tool -> 404
        bad_res = client.post(
            "/api/mcp/execute",
            json={"tool_name": "invalid_tool", "arguments": {}},
        )
        assert bad_res.status_code == 404
    finally:
        app.dependency_overrides.clear()
