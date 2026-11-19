"""
Model Context Protocol (MCP) API Routes.
Enables inspection and direct execution of MCP tools with multi-user isolation.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.mcp.client.drive_client import get_user_drive_token
from app.mcp.client.github_client import get_user_github_token
from app.mcp.registry import get_mcp_tools_for_user
from app.models.user import User
from app.schemas.mcp import (
    MCPToolExecuteRequest,
    MCPToolExecuteResponse,
    MCPToolItem,
    MCPToolsStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mcp", tags=["Model Context Protocol (MCP)"])


@router.get("/tools", response_model=MCPToolsStatusResponse)
def list_available_mcp_tools(current_user: User = Depends(get_current_user)):
    """List all standardized MCP tools available to the current authenticated user."""
    # Enforce multi-user isolation by building tools for current user
    tools = get_mcp_tools_for_user(current_user.id)

    has_github = get_user_github_token(current_user.id) is not None
    has_drive = get_user_drive_token(current_user.id) is not None

    tool_items = [
        MCPToolItem(name=t.name, description=t.description)
        for t in tools
    ]

    return MCPToolsStatusResponse(
        github_connected=has_github,
        google_drive_connected=has_drive,
        tools_count=len(tool_items),
        tools=tool_items,
    )


@router.post("/execute", response_model=MCPToolExecuteResponse)
def execute_mcp_tool(
    payload: MCPToolExecuteRequest,
    current_user: User = Depends(get_current_user),
):
    """Execute a specific MCP tool dynamically on behalf of the authenticated user."""
    tools = get_mcp_tools_for_user(current_user.id)
    tool_map = {t.name: t for t in tools}

    if payload.tool_name not in tool_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP tool '{payload.tool_name}' not found. Available: {list(tool_map.keys())}",
        )

    tool = tool_map[payload.tool_name]

    try:
        result = tool.invoke(payload.arguments)
        return MCPToolExecuteResponse(
            tool_name=payload.tool_name,
            success=True,
            result=result,
        )
    except Exception as e:
        logger.error(f"Error executing MCP tool '{payload.tool_name}': {e}")
        return MCPToolExecuteResponse(
            tool_name=payload.tool_name,
            success=False,
            error=str(e),
        )