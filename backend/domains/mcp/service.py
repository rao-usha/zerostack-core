"""MCP service."""
from typing import List, Optional
from uuid import UUID
from .models import MCPTool, MCPToolCreate, MCPToolExecution, MCPToolExecutionRequest


class MCPRegistry:
    """MCP tools registry."""
    
    def register_tool(self, tool: MCPToolCreate) -> MCPTool:
        """
        Register an MCP tool.
        
        TODO: Implement tool registration with:
        - Schema validation
        - Implementation verification
        - Metadata storage
        """
        raise NotImplementedError("TODO: Implement tool registration")
    
    def list_tools(self) -> List[MCPTool]:
        """List all registered tools."""
        raise NotImplementedError("TODO: Implement tool listing")
    
    def get_tool(self, tool_id: UUID) -> Optional[MCPTool]:
        """Get a tool by ID."""
        raise NotImplementedError("TODO: Implement tool retrieval")
    
    def unregister_tool(self, tool_id: UUID) -> bool:
        """Unregister a tool."""
        raise NotImplementedError("TODO: Implement tool unregistration")


class MCPRunner:
    """MCP tool execution runner."""
    
    def execute(self, execution_request: MCPToolExecutionRequest) -> MCPToolExecution:
        """
        Execute an MCP tool.
        
        TODO: Implement tool execution with:
        - Input validation against schema
        - Async execution support
        - Error handling
        - Result capture
        """
        raise NotImplementedError("TODO: Implement tool execution")
    
    def get_execution(self, execution_id: UUID) -> Optional[MCPToolExecution]:
        """Get execution status."""
        raise NotImplementedError("TODO: Implement execution retrieval")
    
    def cancel_execution(self, execution_id: UUID) -> bool:
        """Cancel a running execution."""
        raise NotImplementedError("TODO: Implement execution cancellation")

