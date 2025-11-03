"""MCP API router."""
from fastapi import APIRouter, HTTPException
from typing import List
from uuid import UUID
from domains.mcp.models import MCPTool, MCPToolCreate, MCPToolExecution, MCPToolExecutionRequest
from domains.mcp.service import MCPRegistry, MCPRunner

router = APIRouter(prefix="/mcp", tags=["mcp"])

mcp_registry = MCPRegistry()
mcp_runner = MCPRunner()


@router.post("/tools", response_model=MCPTool, status_code=201)
async def register_tool(tool: MCPToolCreate):
    """Register an MCP tool."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/tools", response_model=List[MCPTool])
async def list_tools():
    """List all MCP tools."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/tools/{tool_id}", response_model=MCPTool)
async def get_tool(tool_id: UUID):
    """Get an MCP tool."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/tools/{tool_id}", status_code=204)
async def unregister_tool(tool_id: UUID):
    """Unregister an MCP tool."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/execute", response_model=MCPToolExecution, status_code=201)
async def execute_tool(execution: MCPToolExecutionRequest):
    """Execute an MCP tool."""
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/executions/{execution_id}", response_model=MCPToolExecution)
async def get_execution(execution_id: UUID):
    """Get execution status."""
    raise HTTPException(status_code=501, detail="Not implemented")

