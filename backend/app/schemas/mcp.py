"""
Pydantic schemas for the Model Context Protocol (MCP) API endpoints.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MCPToolItem(BaseModel):
    """Metadata describing an available MCP tool."""

    name: str = Field(..., description="Unique tool identifier name.")
    description: str = Field(..., description="High-level description of what the tool does.")


class MCPToolsStatusResponse(BaseModel):
    """Status payload returning connected services and active MCP tools for the user."""

    github_connected: bool = Field(..., description="Whether user has connected GitHub OAuth.")
    google_drive_connected: bool = Field(..., description="Whether user has connected Google Drive OAuth.")
    tools_count: int = Field(..., description="Total number of active MCP tools available.")
    tools: List[MCPToolItem] = Field(default_factory=list, description="List of available tools.")


class MCPToolExecuteRequest(BaseModel):
    """Input payload to execute an MCP tool directly."""

    tool_name: str = Field(..., description="Name of the MCP tool to execute (e.g. 'github_get_repo_details').")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Key-value arguments for the tool.")


class MCPToolExecuteResponse(BaseModel):
    """Output payload returning the result of tool execution."""

    tool_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None