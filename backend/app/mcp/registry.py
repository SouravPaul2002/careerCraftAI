"""
MCP Tool Registry for CareerCraft AI.
Binds authenticated user tokens and produces standardized LangChain StructuredTools for AI agents.
"""
from typing import Any, Dict, List
from langchain_core.tools import BaseTool, StructuredTool

from app.mcp.client.drive_client import (
    get_drive_file_metadata,
    get_user_drive_token,
    read_drive_file_content,
    search_drive_files,
)
from app.mcp.client.github_client import (
    get_recent_commits,
    get_repository_details,
    get_repository_readme,
    get_user_github_token,
    list_repository_tree,
    read_repository_file,
)


def get_mcp_tools_for_user(user_id: int) -> List[BaseTool]:
    """Construct a list of standardized MCP tools configured for the given authenticated user.

    Ensures strict multi-user data isolation by scoping every tool call to the user's
    decrypted OAuth credentials.
    """
    tools: List[BaseTool] = []

    github_token = get_user_github_token(user_id)
    drive_token = get_user_drive_token(user_id)


    # GitHub MCP Tools
    def _github_get_repo(owner: str, repo: str) -> Dict[str, Any]:
        """Fetch repository metadata including description, stars, primary language, and topics."""
        if not github_token:
            return {"error": "GitHub is not connected for this account. Connect GitHub in settings."}
        return get_repository_details(github_token, owner, repo)

    def _github_list_files(owner: str, repo: str, path: str = "") -> List[Dict[str, Any]]:
        """List files and subdirectories within a repository path."""
        if not github_token:
            return [{"error": "GitHub is not connected for this account. Connect GitHub in settings."}]
        return list_repository_tree(github_token, owner, repo, path)

    def _github_read_file(owner: str, repo: str, file_path: str) -> str:
        """Read the raw text content of a source code file or manifest (e.g. Dockerfile, package.json)."""
        if not github_token:
            return "Error: GitHub is not connected for this account."
        return read_repository_file(github_token, owner, repo, file_path)

    def _github_get_readme(owner: str, repo: str) -> str:
        """Fetch the full README markdown documentation of a repository."""
        if not github_token:
            return "Error: GitHub is not connected for this account."
        return get_repository_readme(github_token, owner, repo)

    def _github_get_commits(owner: str, repo: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve recent commit messages, authors, and timestamps to evaluate project activity."""
        if not github_token:
            return [{"error": "GitHub is not connected for this account."}]
        return get_recent_commits(github_token, owner, repo, limit)

    tools.extend([
        StructuredTool.from_function(
            func=_github_get_repo,
            name="github_get_repo_details",
            description="Get repository description, primary language, stars, and topics.",
        ),
        StructuredTool.from_function(
            func=_github_list_files,
            name="github_list_files",
            description="List files and folders in a repository directory.",
        ),
        StructuredTool.from_function(
            func=_github_read_file,
            name="github_read_file",
            description="Read the source code or text content of a file in a repository.",
        ),
        StructuredTool.from_function(
            func=_github_get_readme,
            name="github_get_readme",
            description="Fetch the README documentation markdown for a repository.",
        ),
        StructuredTool.from_function(
            func=_github_get_commits,
            name="github_get_recent_commits",
            description="Get recent commit messages and timestamps for a repository.",
        ),
    ])


    # Google Drive MCP Tools

    def _drive_search(query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Search or list documents, resumes, and project notes in Google Drive."""
        if not drive_token:
            return [{"error": "Google Drive is not connected for this account. Connect Drive in settings."}]
        return search_drive_files(drive_token, query, limit)

    def _drive_get_metadata(file_id: str) -> Dict[str, Any]:
        """Get file metadata (name, MIME type, size, modified time, link) for a Google Drive file."""
        if not drive_token:
            return {"error": "Google Drive is not connected for this account."}
        return get_drive_file_metadata(drive_token, file_id)

    def _drive_read_content(file_id: str, mime_type: str = "") -> str:
        """Read and extract text content from a Google Doc, PDF, or text document in Google Drive."""
        if not drive_token:
            return "Error: Google Drive is not connected for this account."
        return read_drive_file_content(drive_token, file_id, mime_type)

    tools.extend([
        StructuredTool.from_function(
            func=_drive_search,
            name="drive_search_files",
            description="Search or list documents and files in Google Drive.",
        ),
        StructuredTool.from_function(
            func=_drive_get_metadata,
            name="drive_get_file_metadata",
            description="Retrieve metadata for a specific Google Drive file.",
        ),
        StructuredTool.from_function(
            func=_drive_read_content,
            name="drive_read_file_content",
            description="Read the extracted text content of a Google Doc or PDF.",
        ),
    ])

    return tools