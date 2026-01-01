"""
Chat service layer.

Handles chat conversation management, message persistence, LLM orchestration,
and integration with MCP/Data Explorer tools and Data Dictionary tools.
"""

import json
import logging
from typing import AsyncIterator, List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select, desc
from sqlalchemy import func

from .models import (
    ChatConversation, ChatMessage,
    ConversationCreate, MessageCreate,
    ConversationResponse, MessageResponse,
    ConversationWithMessages
)
from ..data_explorer.service import DataExplorerService
from ..data_explorer import dictionary_enhanced_service as dict_service
from ..data_explorer import dictionary_service as original_dict_service
from ..data_explorer.db_models import DataDictionaryEntry
from llm.providers import get_provider

logger = logging.getLogger(__name__)


# Define Data Explorer tools for LLM function calling
DATA_EXPLORER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_connections",
            "description": "List all available database connections. Use this first to discover which databases you can explore.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_schemas",
            "description": "List all schemas in a database (excluding system schemas). Returns schema names with table counts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {
                        "type": "string",
                        "description": "Database connection ID (default: 'default')",
                        "default": "default"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "List all tables and views in a schema. Returns table names, types (table/view), and row estimates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {
                        "type": "string",
                        "description": "Database connection ID",
                        "default": "default"
                    },
                    "schema": {
                        "type": "string",
                        "description": "Schema name",
                        "default": "public"
                    }
                },
                "required": ["schema"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_table_info",
            "description": "Get detailed column metadata for a specific table. Use before querying to understand structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"}
                },
                "required": ["schema", "table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sample_rows",
            "description": "Sample rows from a table with pagination. Use to preview actual data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"},
                    "limit": {"type": "integer", "description": "Number of rows (default: 50, max: 500)", "default": 50},
                    "offset": {"type": "integer", "description": "Offset (default: 0)", "default": 0}
                },
                "required": ["schema", "table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "profile_table",
            "description": "Generate comprehensive statistical profile for a table including null counts, distinct values, min/max/avg for numeric columns, and top values for categorical columns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"},
                    "max_distinct": {"type": "integer", "description": "Max distinct values for categorical columns", "default": 50}
                },
                "required": ["schema", "table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_query",
            "description": "Execute a custom SQL query (SELECT only, read-only). Query timeout is 30 seconds, max 1000 rows.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "sql": {"type": "string", "description": "SQL query to execute (SELECT only)"},
                    "page": {"type": "integer", "description": "Page number", "default": 1},
                    "page_size": {"type": "integer", "description": "Rows per page (max: 1000)", "default": 100}
                },
                "required": ["sql"]
            }
        }
    }
]


# =============================================================================
# DATA DICTIONARY TOOLS
# Tools for exploring and understanding the curated data dictionary
# =============================================================================

DATA_DICTIONARY_TOOLS = [
    # DISCOVERY TOOLS
    {
        "type": "function",
        "function": {
            "name": "discover_assets",
            "description": "Discover data assets (tables/views) in the data dictionary. Use this to find what data is available with business context, ownership, and trust information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "search": {"type": "string", "description": "Search term for table names, business names, or descriptions"},
                    "schema": {"type": "string", "description": "Filter by schema name"},
                    "business_domain": {"type": "string", "description": "Filter by domain (e.g., 'Sales', 'Finance')"},
                    "trust_tier": {"type": "string", "enum": ["certified", "trusted", "experimental", "deprecated"]},
                    "limit": {"type": "integer", "default": 25}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_documented_tables",
            "description": "List all tables that have data dictionary documentation (column definitions). Use this to see which tables have been documented with business descriptions, examples, and metadata.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Filter by schema name (default: public)", "default": "public"},
                    "include_column_details": {"type": "boolean", "description": "Include column counts and sample definitions", "default": True}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "discover_relationships",
            "description": "Discover relationships between tables in the data dictionary. Shows how tables connect via foreign keys and semantic relationships.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Filter by schema"},
                    "table": {"type": "string", "description": "Get relationships for specific table"},
                    "limit": {"type": "integer", "default": 50}
                },
                "required": []
            }
        }
    },
    # DOCUMENTATION TOOLS
    {
        "type": "function",
        "function": {
            "name": "get_asset_documentation",
            "description": "Get full documentation for a data asset (table/view) including business definition, domain, ownership, grain, and known issues.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"}
                },
                "required": ["schema", "table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_field_documentation",
            "description": "Get documentation for a specific column including business name, definition, semantic role, and data type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"},
                    "column": {"type": "string", "description": "Column name"}
                },
                "required": ["schema", "table", "column"]
            }
        }
    },
    # ANALYSIS TOOLS
    {
        "type": "function",
        "function": {
            "name": "check_data_quality",
            "description": "Check trust tier, quality score, approval status, and known issues for a table. Use to assess if data is fit for your use case.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"}
                },
                "required": ["schema", "table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_trusted_data",
            "description": "Find data assets that are approved for specific use cases like reporting or ML training.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "use_case": {"type": "string", "enum": ["reporting", "ml", "analysis"], "description": "Intended use case"},
                    "min_trust_tier": {"type": "string", "enum": ["certified", "trusted", "experimental"], "default": "trusted"},
                    "business_domain": {"type": "string", "description": "Filter by business domain"},
                    "limit": {"type": "integer", "default": 25}
                },
                "required": ["use_case"]
            }
        }
    },
    # UNDERSTANDING TOOLS
    {
        "type": "function",
        "function": {
            "name": "explain_table",
            "description": "Get a comprehensive explanation of a table including what it is, what one row represents (grain), ownership, trust info, key columns, and relationships.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"}
                },
                "required": ["schema", "table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "explain_grain",
            "description": "Explain what one row represents in a table (the grain). Critical for correct aggregations and joins.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"}
                },
                "required": ["schema", "table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "explain_join",
            "description": "Explain how to join two tables safely. Analyzes relationships, suggests join columns, warns about fanout.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "left_schema": {"type": "string", "description": "Left table schema"},
                    "left_table": {"type": "string", "description": "Left table name"},
                    "right_schema": {"type": "string", "description": "Right table schema"},
                    "right_table": {"type": "string", "description": "Right table name"}
                },
                "required": ["left_schema", "left_table", "right_schema", "right_table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_dictionary",
            "description": "Search the data dictionary using natural language. Searches table names, column names, business definitions, and tags.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "query": {"type": "string", "description": "Search query"},
                    "scope": {"type": "string", "enum": ["all", "tables", "columns", "definitions"], "default": "all"},
                    "schema": {"type": "string", "description": "Limit to specific schema"},
                    "limit": {"type": "integer", "default": 20}
                },
                "required": ["query"]
            }
        }
    },
    # UPDATE TOOLS - for modifying dictionary entries
    {
        "type": "function",
        "function": {
            "name": "preview_dictionary_update",
            "description": "Preview proposed changes to a data dictionary entry BEFORE saving. Shows current vs proposed values. The user must confirm before changes are saved.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"},
                    "column": {"type": "string", "description": "Column name to update"},
                    "business_name": {"type": "string", "description": "New business-friendly name for the column"},
                    "business_description": {"type": "string", "description": "New business description explaining what this column means"},
                    "technical_description": {"type": "string", "description": "New technical description with implementation details"},
                    "examples": {"type": "array", "items": {"type": "string"}, "description": "Example values for this column"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"}
                },
                "required": ["schema", "table", "column"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_dictionary_update",
            "description": "Save a previously previewed dictionary update. Only call this AFTER the user has confirmed they want to save the changes shown in preview_dictionary_update.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"},
                    "column": {"type": "string", "description": "Column name to update"},
                    "business_name": {"type": "string", "description": "New business-friendly name"},
                    "business_description": {"type": "string", "description": "New business description"},
                    "technical_description": {"type": "string", "description": "New technical description"},
                    "examples": {"type": "array", "items": {"type": "string"}, "description": "Example values"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
                    "version_notes": {"type": "string", "description": "Notes explaining why this update was made"}
                },
                "required": ["schema", "table", "column"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_column_history",
            "description": "Get the version history of a column's documentation. Shows all previous versions with who made changes and when.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"},
                    "column": {"type": "string", "description": "Column name"}
                },
                "required": ["schema", "table", "column"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rollback_column_version",
            "description": "Rollback a column's documentation to a previous version. Use get_column_history first to see available versions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entry_id": {"type": "integer", "description": "The ID of the version to restore (from get_column_history)"}
                },
                "required": ["entry_id"]
            }
        }
    }
]

# Combine all tools
ALL_CHAT_TOOLS = DATA_EXPLORER_TOOLS + DATA_DICTIONARY_TOOLS


class ChatService:
    """Service for managing chat conversations and messages."""
    
    @staticmethod
    def create_conversation(session: Session, data: ConversationCreate) -> ChatConversation:
        """Create a new chat conversation."""
        conversation = ChatConversation(
            title=data.title,
            provider=data.provider,
            model=data.model,
            connection_id=data.connection_id,
            meta=data.meta
        )
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        return conversation
    
    @staticmethod
    def list_conversations(
        session: Session,
        skip: int = 0,
        limit: int = 50,
        provider: Optional[str] = None
    ) -> List[ConversationResponse]:
        """List conversations ordered by updated_at desc."""
        query = select(ChatConversation)
        
        if provider:
            query = query.where(ChatConversation.provider == provider)
        
        query = query.order_by(desc(ChatConversation.updated_at)).offset(skip).limit(limit)
        
        conversations = session.exec(query).all()
        
        # Add message count
        results = []
        for conv in conversations:
            count_query = select(func.count(ChatMessage.id)).where(
                ChatMessage.conversation_id == conv.id
            )
            message_count = session.exec(count_query).one()
            
            conv_dict = conv.model_dump()
            conv_dict['message_count'] = message_count
            results.append(ConversationResponse(**conv_dict))
        
        return results
    
    @staticmethod
    def get_conversation(session: Session, conversation_id: UUID) -> Optional[ChatConversation]:
        """Get a conversation by ID."""
        return session.get(ChatConversation, conversation_id)
    
    @staticmethod
    def get_conversation_with_messages(
        session: Session,
        conversation_id: UUID
    ) -> Optional[ConversationWithMessages]:
        """Get conversation with full message history."""
        conversation = session.get(ChatConversation, conversation_id)
        if not conversation:
            return None
        
        # Get messages ordered by sequence
        messages_query = select(ChatMessage).where(
            ChatMessage.conversation_id == conversation_id
        ).order_by(ChatMessage.sequence)
        
        messages = session.exec(messages_query).all()
        
        return ConversationWithMessages(
            **conversation.model_dump(),
            message_count=len(messages),
            messages=[MessageResponse(**msg.model_dump()) for msg in messages]
        )
    
    @staticmethod
    def update_conversation(
        session: Session,
        conversation_id: UUID,
        title: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> Optional[ChatConversation]:
        """Update conversation metadata."""
        conversation = session.get(ChatConversation, conversation_id)
        if not conversation:
            return None
        
        if title is not None:
            conversation.title = title
        if meta is not None:
            conversation.meta = meta
        
        conversation.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(conversation)
        return conversation
    
    @staticmethod
    def delete_conversation(session: Session, conversation_id: UUID) -> bool:
        """Delete a conversation and all its messages."""
        conversation = session.get(ChatConversation, conversation_id)
        if not conversation:
            return False
        
        session.delete(conversation)
        session.commit()
        return True
    
    @staticmethod
    def _get_next_sequence(session: Session, conversation_id: UUID) -> int:
        """Get next sequence number for a conversation."""
        query = select(func.max(ChatMessage.sequence)).where(
            ChatMessage.conversation_id == conversation_id
        )
        max_seq = session.exec(query).one()
        return (max_seq or 0) + 1
    
    @staticmethod
    def _save_message(
        session: Session,
        conversation_id: UUID,
        role: str,
        content: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_input: Optional[Dict[str, Any]] = None,
        tool_output: Optional[Dict[str, Any]] = None,
        raw_request: Optional[Dict[str, Any]] = None,
        raw_response: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Save a message to the database."""
        sequence = ChatService._get_next_sequence(session, conversation_id)
        
        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sequence=sequence,
            provider=provider,
            model=model,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            raw_request=raw_request,
            raw_response=raw_response
        )
        
        session.add(message)
        session.commit()
        session.refresh(message)
        return message
    
    @staticmethod
    def _execute_tool(tool_name: str, tool_input: Dict[str, Any], session: Session = None) -> Dict[str, Any]:
        """Execute a Data Explorer or Data Dictionary tool and return result."""
        connection_id = tool_input.get("connection_id", "default")
        
        try:
            if tool_name == "list_connections":
                from ..data_explorer.db_configs import get_database_configs
                configs = get_database_configs()
                return {
                    "success": True,
                    "data": [
                        {
                            "id": config.id,
                            "label": f"{config.name} ({config.description})",
                            "host": config.host,
                            "port": config.port,
                            "database": config.database
                        }
                        for config in configs
                    ]
                }
            
            elif tool_name == "list_schemas":
                schemas = DataExplorerService.get_schemas(db_id=connection_id)
                return {
                    "success": True,
                    "data": [{"name": s.name, "table_count": s.table_count} for s in schemas]
                }
            
            elif tool_name == "list_tables":
                schema = tool_input.get("schema", "public")
                tables = DataExplorerService.get_tables(schema=schema, db_id=connection_id)
                return {
                    "success": True,
                    "data": [
                        {
                            "schema": t.schema,
                            "name": t.name,
                            "type": t.type,
                            "row_estimate": t.row_estimate
                        }
                        for t in tables
                    ]
                }
            
            elif tool_name == "get_table_info":
                columns = DataExplorerService.get_columns(
                    schema=tool_input["schema"],
                    table=tool_input["table"],
                    db_id=connection_id
                )
                return {
                    "success": True,
                    "data": {
                        "schema": tool_input["schema"],
                        "table": tool_input["table"],
                        "columns": [
                            {
                                "name": c.name,
                                "data_type": c.data_type,
                                "is_nullable": c.is_nullable,
                                "default": c.default,
                                "ordinal_position": c.ordinal_position
                            }
                            for c in columns
                        ]
                    }
                }
            
            elif tool_name == "sample_rows":
                limit = tool_input.get("limit", 50)
                offset = tool_input.get("offset", 0)
                page = (offset // limit) + 1
                
                result = DataExplorerService.get_table_rows(
                    schema=tool_input["schema"],
                    table=tool_input["table"],
                    page=page,
                    page_size=min(limit, 500),
                    db_id=connection_id
                )
                return {
                    "success": True,
                    "data": {
                        "schema": result.schema,
                        "table": result.table,
                        "columns": result.columns,
                        "rows": result.rows,
                        "total_rows": result.total_rows
                    }
                }
            
            elif tool_name == "profile_table":
                max_distinct = tool_input.get("max_distinct", 50)
                result = DataExplorerService.profile_table(
                    schema=tool_input["schema"],
                    table=tool_input["table"],
                    max_distinct=max_distinct,
                    db_id=connection_id
                )
                return {"success": True, "data": result}
            
            elif tool_name == "run_query":
                result = DataExplorerService.execute_query(
                    sql=tool_input["sql"],
                    page=tool_input.get("page", 1),
                    page_size=tool_input.get("page_size", 100),
                    db_id=connection_id
                )
                
                response_data = {
                    "columns": result.columns,
                    "rows": result.rows,
                    "total_rows_estimate": result.total_rows_estimate,
                    "execution_time_ms": result.execution_time_ms,
                    "error": result.error
                }
                
                if not result.error:
                    row_count = len(result.rows)
                    response_data["summary"] = (
                        f"Query returned {row_count} row(s) "
                        f"in {result.execution_time_ms:.2f}ms"
                    )
                
                return {
                    "success": not bool(result.error),
                    "data": response_data
                }
            
            # =================================================================
            # DATA DICTIONARY TOOLS
            # =================================================================
            
            elif tool_name == "discover_assets":
                return ChatService._execute_discover_assets(session, tool_input)
            
            elif tool_name == "list_documented_tables":
                return ChatService._execute_list_documented_tables(session, tool_input)
            
            elif tool_name == "discover_relationships":
                return ChatService._execute_discover_relationships(session, tool_input)
            
            elif tool_name == "get_asset_documentation":
                return ChatService._execute_get_asset_documentation(session, tool_input)
            
            elif tool_name == "get_field_documentation":
                return ChatService._execute_get_field_documentation(session, tool_input)
            
            elif tool_name == "check_data_quality":
                return ChatService._execute_check_data_quality(session, tool_input)
            
            elif tool_name == "find_trusted_data":
                return ChatService._execute_find_trusted_data(session, tool_input)
            
            elif tool_name == "explain_table":
                return ChatService._execute_explain_table(session, tool_input)
            
            elif tool_name == "explain_grain":
                return ChatService._execute_explain_grain(session, tool_input)
            
            elif tool_name == "explain_join":
                return ChatService._execute_explain_join(session, tool_input)
            
            elif tool_name == "search_dictionary":
                return ChatService._execute_search_dictionary(session, tool_input)
            
            # UPDATE TOOLS
            elif tool_name == "preview_dictionary_update":
                return ChatService._execute_preview_dictionary_update(session, tool_input)
            
            elif tool_name == "save_dictionary_update":
                return ChatService._execute_save_dictionary_update(session, tool_input)
            
            elif tool_name == "get_column_history":
                return ChatService._execute_get_column_history(session, tool_input)
            
            elif tool_name == "rollback_column_version":
                return ChatService._execute_rollback_column_version(session, tool_input)
            
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        except Exception as e:
            logger.error(f"Tool execution error: {tool_name} - {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def stream_chat_response(
        session: Session,
        conversation_id: UUID,
        user_message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        connection_id: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream chat response with tool calling support.
        
        Yields stream events:
        - {"event": "delta", "data": {"content": str}}
        - {"event": "tool_call", "data": {"tool_name": str, "tool_input": dict}}
        - {"event": "tool_result", "data": {"tool_name": str, "result": dict}}
        - {"event": "done", "data": {"message_id": str}}
        - {"event": "error", "data": {"error": str}}
        """
        conversation = session.get(ChatConversation, conversation_id)
        if not conversation:
            yield {"event": "error", "data": {"error": "Conversation not found"}}
            return
        
        # Use conversation settings if not overridden
        provider = provider or conversation.provider
        model = model or conversation.model
        connection_id = connection_id or conversation.connection_id or "default"
        
        # Save user message
        ChatService._save_message(
            session,
            conversation_id=conversation_id,
            role="user",
            content=user_message
        )
        
        # Get conversation history
        messages_query = select(ChatMessage).where(
            ChatMessage.conversation_id == conversation_id
        ).order_by(ChatMessage.sequence)
        
        history = session.exec(messages_query).all()
        
        # Convert to LLM format with proper tool call handling
        llm_messages = []
        i = 0
        while i < len(history):
            msg = history[i]
            
            if msg.role == "user":
                llm_messages.append({"role": "user", "content": msg.content})
                i += 1
            
            elif msg.role == "assistant":
                llm_messages.append({"role": "assistant", "content": msg.content})
                i += 1
            
            elif msg.role == "tool":
                # Group consecutive tool messages
                tool_messages = []
                tool_calls = []
                
                while i < len(history) and history[i].role == "tool":
                    tool_msg = history[i]
                    # Generate a short tool call ID (max 40 chars for OpenAI)
                    # Use first 32 chars of UUID hex (no dashes)
                    tool_call_id = str(tool_msg.id).replace('-', '')[:32]
                    
                    # Build tool call for assistant message
                    tool_calls.append({
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": tool_msg.tool_name,
                            "arguments": json.dumps(tool_msg.tool_input) if tool_msg.tool_input else "{}"
                        }
                    })
                    
                    # Build tool result message
                    tool_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": json.dumps(tool_msg.tool_output) if tool_msg.tool_output else "{}"
                    })
                    
                    i += 1
                
                # Add assistant message with tool calls
                llm_messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls
                })
                
                # Add all tool result messages
                llm_messages.extend(tool_messages)
            
            else:
                # Skip unknown roles
                i += 1
        
        logger.info(f"Loaded {len(llm_messages)} messages for LLM context")
        if logger.isEnabledFor(logging.DEBUG):
            for idx, msg in enumerate(llm_messages):
                role = msg.get("role")
                has_content = bool(msg.get("content"))
                has_tool_calls = bool(msg.get("tool_calls"))
                logger.debug(f"  [{idx}] role={role}, has_content={has_content}, has_tool_calls={has_tool_calls}")
        
        # Get LLM provider
        try:
            llm = get_provider(provider=provider, model=model)
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            yield {"event": "error", "data": {"error": str(e)}}
            return
        
        # Stream response with tool calling loop
        assistant_content = []
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        try:
            while iteration < max_iterations:
                iteration += 1
                logger.info(f"Chat iteration {iteration}, message count: {len(llm_messages)}")
                
                has_tool_call = False
                pending_tool_calls = []
                tool_call_messages = []  # Track assistant messages with tool calls
                
                async for event in llm.stream_chat(
                    messages=llm_messages,
                    tools=ALL_CHAT_TOOLS,
                    tool_choice="auto"
                ):
                    logger.debug(f"Stream event: {event['type']}")
                    
                    if event["type"] == "delta":
                        # Stream text delta
                        content = event["content"]
                        assistant_content.append(content)
                        yield {"event": "delta", "data": {"content": content}}
                    
                    elif event["type"] == "tool_call":
                        has_tool_call = True
                        tool_name = event["tool_name"]
                        tool_input = event["tool_input"]
                        # Use the tool_call_id from the event, or generate a short one
                        tool_call_id = event.get("tool_call_id", f"{tool_name}_{iteration}")
                        
                        logger.info(f"Tool call: {tool_name} with input: {tool_input}")
                        
                        yield {"event": "tool_call", "data": {
                            "tool_name": tool_name,
                            "tool_input": tool_input
                        }}
                        
                        # Execute tool
                        tool_output = ChatService._execute_tool(tool_name, tool_input, session)
                        logger.info(f"Tool result: {tool_name} - success: {tool_output.get('success')}")
                        
                        # Save tool call
                        ChatService._save_message(
                            session,
                            conversation_id=conversation_id,
                            role="tool",
                            tool_name=tool_name,
                            tool_input=tool_input,
                            tool_output=tool_output
                        )
                        
                        yield {"event": "tool_result", "data": {
                            "tool_name": tool_name,
                            "result": tool_output
                        }}
                        
                        # Accumulate tool calls for the assistant message
                        pending_tool_calls.append({
                            "id": tool_call_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(tool_input)
                            }
                        })
                        
                        # Also accumulate for adding to messages
                        tool_call_messages.append({
                            "id": tool_call_id,
                            "name": tool_name,
                            "output": tool_output
                        })
                    
                    elif event["type"] == "done":
                        logger.info(f"Stream done, had_tool_call: {has_tool_call}, finish_reason: {event.get('finish_reason')}")
                        
                        # If we had tool calls, add them to messages and continue
                        if has_tool_call and tool_call_messages:
                            # Add assistant message with tool calls (required by OpenAI)
                            llm_messages.append({
                                "role": "assistant",
                                "content": None,
                                "tool_calls": pending_tool_calls
                            })
                            
                            # Add all tool results
                            for tool_call in tool_call_messages:
                                llm_messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call["id"],
                                    "content": json.dumps(tool_call["output"])
                                })
                            
                            # Clear for next iteration
                            pending_tool_calls = []
                            tool_call_messages = []
                            break  # Break inner loop, continue outer while loop
                        
                        # No tool calls - save final response and exit
                        final_content = "".join(assistant_content)
                        logger.info(f"Final content length: {len(final_content)}")
                        
                        if final_content.strip():
                            message = ChatService._save_message(
                                session,
                                conversation_id=conversation_id,
                                role="assistant",
                                content=final_content,
                                provider=provider,
                                model=model
                            )
                            
                            # Auto-generate title if this is the first exchange
                            if not conversation.title and len(history) <= 2:
                                title = user_message[:50] + ("..." if len(user_message) > 50 else "")
                                conversation.title = title
                                session.commit()
                            
                            yield {"event": "done", "data": {"message_id": str(message.id)}}
                        else:
                            yield {"event": "done", "data": {"message_id": None}}
                        
                        return  # Exit completely
                    
                    elif event["type"] == "error":
                        logger.error(f"Stream error: {event.get('error')}")
                        yield {"event": "error", "data": {"error": event["error"]}}
                        return
                
                # If we didn't have tool calls in this iteration, exit
                if not has_tool_call:
                    logger.warning("Stream ended without tool calls or completion")
                    break
            
            # Max iterations reached
            if iteration >= max_iterations:
                logger.warning(f"Max iterations ({max_iterations}) reached")
                final_content = "".join(assistant_content)
                if final_content.strip():
                    message = ChatService._save_message(
                        session,
                        conversation_id=conversation_id,
                        role="assistant",
                        content=final_content,
                        provider=provider,
                        model=model
                    )
                    yield {"event": "done", "data": {"message_id": str(message.id)}}
                else:
                    yield {"event": "error", "data": {"error": "Max iterations reached without response"}}
        
        except Exception as e:
            logger.error(f"Chat streaming error: {e}", exc_info=True)
            yield {"event": "error", "data": {"error": str(e)}}
    
    # =========================================================================
    # DATA DICTIONARY TOOL HANDLERS
    # =========================================================================
    
    @staticmethod
    def _execute_discover_assets(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute discover_assets tool - cross-references database tables with BOTH dictionary sources."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            trust_tier = tool_input.get("trust_tier")
            business_domain = tool_input.get("business_domain")
            schema = tool_input.get("schema", "public")
            search = (tool_input.get("search") or "").lower()
            limit = tool_input.get("limit", 25)
            
            # === SOURCE 1: Enhanced dictionary (dictionary_assets - table-level) ===
            dict_results, dict_total = dict_service.search_assets(
                session=session,
                connection_id=connection_id,
                schema_name=schema if schema != "public" else None,
                search_term=None,
                trust_tier=None,
                business_domain=None,
                limit=500,
                offset=0
            )
            
            # Build lookup by schema.table
            enhanced_lookup = {}
            for asset in dict_results:
                key = f"{asset.schema_name}.{asset.table_name}".lower()
                enhanced_lookup[key] = asset
            
            # === SOURCE 2: Original dictionary (data_dictionary_entries - column-level) ===
            # Get distinct tables that have column definitions
            original_entries = session.exec(
                select(
                    DataDictionaryEntry.schema_name,
                    DataDictionaryEntry.table_name,
                    func.count(DataDictionaryEntry.id).label("column_count")
                ).where(
                    DataDictionaryEntry.schema_name == schema,
                    DataDictionaryEntry.is_active == True
                ).group_by(
                    DataDictionaryEntry.schema_name,
                    DataDictionaryEntry.table_name
                )
            ).all()
            
            # Build lookup for original dictionary
            original_lookup = {}
            for entry in original_entries:
                key = f"{entry.schema_name}.{entry.table_name}".lower()
                original_lookup[key] = {
                    "schema": entry.schema_name,
                    "table": entry.table_name,
                    "columns_documented": entry.column_count
                }
            
            logger.info(f"Found {len(enhanced_lookup)} tables in enhanced dict, {len(original_lookup)} in original dict")
            
            # === SOURCE 3: Raw tables from database (nexdata) ===
            raw_tables = []
            try:
                tables = DataExplorerService.get_tables(schema=schema, db_id=connection_id)
                raw_tables = list(tables)
            except Exception as e:
                logger.warning(f"Could not get raw tables: {e}")
            
            # === MERGE all sources ===
            assets = []
            in_dictionary = 0
            not_in_dictionary = 0
            
            # Track which tables we've processed
            processed_keys = set()
            
            for t in raw_tables:
                key = f"{t.schema}.{t.name}".lower()
                processed_keys.add(key)
                
                enhanced_entry = enhanced_lookup.get(key)
                original_entry = original_lookup.get(key)
                has_dictionary = bool(enhanced_entry or original_entry)
                
                # Apply search filter
                if search:
                    name_match = search in t.name.lower()
                    business_match = enhanced_entry and enhanced_entry.business_name and search in enhanced_entry.business_name.lower()
                    desc_match = enhanced_entry and enhanced_entry.business_definition and search in enhanced_entry.business_definition.lower()
                    if not (name_match or business_match or desc_match):
                        continue
                
                # Apply trust_tier filter (enhanced dictionary only)
                if trust_tier:
                    if not enhanced_entry or enhanced_entry.trust_tier != trust_tier:
                        continue
                
                # Apply business_domain filter (enhanced dictionary only)
                if business_domain:
                    if not enhanced_entry or enhanced_entry.business_domain != business_domain:
                        continue
                
                if has_dictionary:
                    in_dictionary += 1
                    asset_data = {
                        "schema": t.schema,
                        "table": t.name,
                        "type": t.type,
                        "row_count": t.row_estimate,
                        "in_dictionary": True,
                        "dictionary_sources": []
                    }
                    
                    if enhanced_entry:
                        asset_data["dictionary_sources"].append("dictionary_assets")
                        asset_data["business_name"] = enhanced_entry.business_name
                        asset_data["description"] = (enhanced_entry.business_definition or "")[:200]
                        asset_data["domain"] = enhanced_entry.business_domain
                        asset_data["owner"] = enhanced_entry.owner
                        asset_data["trust_tier"] = enhanced_entry.trust_tier
                        asset_data["trust_score"] = enhanced_entry.trust_score
                        asset_data["tags"] = enhanced_entry.tags or []
                    
                    if original_entry:
                        asset_data["dictionary_sources"].append("data_dictionary_entries")
                        asset_data["columns_documented"] = original_entry["columns_documented"]
                        if not enhanced_entry:
                            # Only original dictionary - add basic info
                            asset_data["note"] = f"Has {original_entry['columns_documented']} column definitions"
                    
                    assets.append(asset_data)
                else:
                    not_in_dictionary += 1
                    # Only include non-dictionary tables if not filtering by dictionary-only fields
                    if not trust_tier and not business_domain:
                        assets.append({
                            "schema": t.schema,
                            "table": t.name,
                            "type": t.type,
                            "row_count": t.row_estimate,
                            "in_dictionary": False,
                            "dictionary_sources": [],
                            "business_name": None,
                            "description": None,
                            "trust_tier": "not_curated",
                            "note": "Not yet in data dictionary"
                        })
            
            # Also add any original dict entries for tables not in raw_tables
            for key, orig in original_lookup.items():
                if key not in processed_keys:
                    in_dictionary += 1
                    assets.append({
                        "schema": orig["schema"],
                        "table": orig["table"],
                        "type": "table",
                        "row_count": None,
                        "in_dictionary": True,
                        "dictionary_sources": ["data_dictionary_entries"],
                        "columns_documented": orig["columns_documented"],
                        "note": f"Has {orig['columns_documented']} column definitions (table not in current connection)"
                    })
            
            # Sort: dictionary entries first (by columns_documented or trust_score), then non-dictionary
            assets.sort(key=lambda x: (
                0 if x.get("in_dictionary") else 1,
                -(x.get("columns_documented") or 0),
                -(x.get("trust_score") or 0)
            ))
            
            # Build summary
            total = len(assets)
            if trust_tier or business_domain:
                summary = f"Found {total} assets matching filters"
                if trust_tier:
                    summary += f" (trust_tier='{trust_tier}')"
                if business_domain:
                    summary += f" (domain='{business_domain}')"
            else:
                summary = f"Found {total} tables in {schema} schema: {in_dictionary} have data dictionary entries, {not_in_dictionary} not yet documented"
            
            return {
                "success": True,
                "data": {
                    "assets": assets[:limit],
                    "total": total,
                    "in_dictionary": in_dictionary,
                    "not_in_dictionary": not_in_dictionary,
                    "tables_with_column_definitions": len(original_lookup),
                    "tables_with_enhanced_metadata": len(enhanced_lookup),
                    "summary": summary
                }
            }
        except Exception as e:
            logger.error(f"discover_assets error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_list_documented_tables(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """List all tables that have data dictionary documentation."""
        try:
            schema = tool_input.get("schema", "public")
            include_details = tool_input.get("include_column_details", True)
            
            # Query the data_dictionary_entries table for documented tables
            query = session.exec(
                select(
                    DataDictionaryEntry.schema_name,
                    DataDictionaryEntry.table_name,
                    func.count(DataDictionaryEntry.id).label("column_count"),
                    func.min(DataDictionaryEntry.created_at).label("first_documented"),
                    func.max(DataDictionaryEntry.updated_at).label("last_updated")
                ).where(
                    DataDictionaryEntry.schema_name == schema,
                    DataDictionaryEntry.is_active == True
                ).group_by(
                    DataDictionaryEntry.schema_name,
                    DataDictionaryEntry.table_name
                ).order_by(
                    DataDictionaryEntry.table_name
                )
            ).all()
            
            documented_tables = []
            for row in query:
                table_info = {
                    "schema": row.schema_name,
                    "table": row.table_name,
                    "columns_documented": row.column_count,
                    "first_documented": row.first_documented.isoformat() if row.first_documented else None,
                    "last_updated": row.last_updated.isoformat() if row.last_updated else None
                }
                
                if include_details:
                    # Get sample column definitions for this table
                    sample_columns = session.exec(
                        select(DataDictionaryEntry).where(
                            DataDictionaryEntry.schema_name == row.schema_name,
                            DataDictionaryEntry.table_name == row.table_name,
                            DataDictionaryEntry.is_active == True
                        ).limit(5)
                    ).all()
                    
                    table_info["sample_columns"] = [
                        {
                            "column": col.column_name,
                            "business_name": col.business_name,
                            "description": (col.business_description or "")[:100]
                        }
                        for col in sample_columns
                    ]
                
                documented_tables.append(table_info)
            
            return {
                "success": True,
                "data": {
                    "documented_tables": documented_tables,
                    "total_tables": len(documented_tables),
                    "total_columns_documented": sum(t["columns_documented"] for t in documented_tables),
                    "schema": schema,
                    "summary": f"Found {len(documented_tables)} tables with data dictionary documentation in {schema} schema, covering a total of {sum(t['columns_documented'] for t in documented_tables)} column definitions"
                }
            }
        except Exception as e:
            logger.error(f"list_documented_tables error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_discover_relationships(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute discover_relationships tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            schema = tool_input.get("schema")
            table = tool_input.get("table")
            
            relationships = []
            
            if schema and table:
                try:
                    rels = dict_service.get_relationships_for_table(
                        session, connection_id, schema, table
                    )
                    for rel in rels:
                        # Handle both old (source_schema) and new (left_ref) model structures
                        if hasattr(rel, 'source_schema'):
                            relationships.append({
                                "source": f"{rel.source_schema}.{rel.source_table}.{rel.source_column}",
                                "target": f"{rel.target_schema}.{rel.target_table}.{rel.target_column}",
                                "cardinality": rel.cardinality,
                                "confidence": getattr(rel, 'confidence', None)
                            })
                        elif hasattr(rel, 'left_ref') and rel.left_ref:
                            left = rel.left_ref
                            right = rel.right_ref or {}
                            relationships.append({
                                "source": f"{left.get('schema', '')}.{left.get('table', '')}.{left.get('column', '')}",
                                "target": f"{right.get('schema', '')}.{right.get('table', '')}.{right.get('column', '')}",
                                "cardinality": rel.cardinality,
                                "confidence": rel.confidence_score
                            })
                except Exception as e:
                    logger.warning(f"Could not get relationships for table: {e}")
            else:
                # Get all relationships from semantics model
                from ..data_explorer.dictionary_semantics_models import DictionaryRelationship
                rels = list(session.exec(select(DictionaryRelationship).limit(tool_input.get("limit", 50))).all())
                
                for rel in rels:
                    left = rel.left_ref or {}
                    right = rel.right_ref or {}
                    relationships.append({
                        "source": f"{left.get('schema', '')}.{left.get('table', '')}.{left.get('column', '')}",
                        "target": f"{right.get('schema', '')}.{right.get('table', '')}.{right.get('column', '')}",
                        "type": rel.relationship_type,
                        "cardinality": rel.cardinality,
                        "status": rel.status,
                        "confidence": rel.confidence_score
                    })
            
            return {
                "success": True,
                "data": {
                    "relationships": relationships,
                    "count": len(relationships),
                    "message": f"Found {len(relationships)} relationships" + (f" for {schema}.{table}" if table else "")
                }
            }
        except Exception as e:
            logger.error(f"discover_relationships error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_get_asset_documentation(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get_asset_documentation tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            schema = tool_input["schema"]
            table = tool_input["table"]
            
            result_data = {
                "table": f"{schema}.{table}",
                "sources": []
            }
            
            # Check 1: Enhanced dictionary (dictionary_assets - table-level)
            asset = dict_service.get_asset_by_table(session, connection_id, schema, table)
            if asset:
                result_data["sources"].append("dictionary_assets")
                result_data["enhanced_dictionary"] = {
                    "business_name": asset.business_name,
                    "business_definition": asset.business_definition,
                    "business_domain": asset.business_domain,
                    "grain": asset.grain or asset.row_meaning,
                    "owner": asset.owner,
                    "steward": asset.steward,
                    "trust_tier": asset.trust_tier,
                    "trust_score": asset.trust_score,
                    "tags": asset.tags or [],
                    "known_issues": asset.known_issues,
                    "approved_for_reporting": asset.approved_for_reporting,
                    "approved_for_ml": asset.approved_for_ml
                }
            
            # Check 2: Original dictionary (data_dictionary_entries - column-level)
            # Try with connection_id as database_name first, then "default"
            original_entries = original_dict_service.get_dictionary_for_tables(
                session, connection_id, schema, [table], active_only=True
            )
            if not original_entries:
                original_entries = original_dict_service.get_dictionary_for_tables(
                    session, "default", schema, [table], active_only=True
                )
            if not original_entries:
                # Try with "nexdata" as database_name
                original_entries = original_dict_service.get_dictionary_for_tables(
                    session, "nexdata", schema, [table], active_only=True
                )
            
            if original_entries:
                result_data["sources"].append("data_dictionary_entries")
                result_data["column_definitions"] = [
                    {
                        "column_name": e.column_name,
                        "business_name": e.business_name,
                        "business_description": e.business_description,
                        "technical_description": e.technical_description,
                        "data_type": e.data_type,
                        "examples": e.examples or [],
                        "tags": e.tags or [],
                        "source": e.source,
                        "version": e.version_number
                    }
                    for e in original_entries
                ]
                result_data["column_count_documented"] = len(original_entries)
            
            # Check 3: Raw database structure if nothing else found
            if not result_data["sources"]:
                try:
                    columns = DataExplorerService.get_columns(schema=schema, table=table, db_id=connection_id)
                    tables = DataExplorerService.get_tables(schema=schema, db_id=connection_id)
                    table_info = next((t for t in tables if t.name == table), None)
                    
                    if columns:
                        result_data["sources"].append("database")
                        result_data["raw_structure"] = {
                            "row_count": table_info.row_estimate if table_info else None,
                            "type": table_info.type if table_info else "table",
                            "column_count": len(columns),
                            "columns": [
                                {"name": c.name, "type": c.data_type, "nullable": c.is_nullable}
                                for c in columns
                            ]
                        }
                        result_data["message"] = "Table found in database but no dictionary documentation exists."
                    else:
                        return {"success": False, "error": f"Table {schema}.{table} not found"}
                except Exception as e:
                    return {"success": False, "error": f"Table {schema}.{table} not found: {str(e)}"}
            
            # Add summary
            if "data_dictionary_entries" in result_data["sources"]:
                result_data["summary"] = f"Found {len(result_data.get('column_definitions', []))} column definitions in data dictionary"
            elif "dictionary_assets" in result_data["sources"]:
                result_data["summary"] = "Found table-level documentation in enhanced dictionary"
            else:
                result_data["summary"] = "Table exists but no documentation found"
            
            return {"success": True, "data": result_data}
        except Exception as e:
            logger.error(f"get_asset_documentation error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_get_field_documentation(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get_field_documentation tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            schema = tool_input["schema"]
            table = tool_input["table"]
            column = tool_input["column"]
            
            result_data = {
                "table": f"{schema}.{table}",
                "column": column,
                "sources": []
            }
            
            # Check 1: Enhanced dictionary (dictionary_fields)
            asset = dict_service.get_asset_by_table(session, connection_id, schema, table)
            if asset:
                fields = dict_service.get_fields_for_asset(session, asset.id)
                for f in fields:
                    if f.column_name.lower() == column.lower():
                        result_data["sources"].append("dictionary_fields")
                        result_data["enhanced"] = {
                            "column_name": f.column_name,
                            "business_name": f.business_name,
                            "business_definition": f.business_definition,
                            "data_type": f.data_type,
                            "nullable": f.is_nullable,
                            "entity_role": f.entity_role,
                            "tags": f.tags or [],
                            "known_issues": f.known_issues,
                            "trust_tier": f.trust_tier,
                            "trust_score": f.trust_score
                        }
                        break
            
            # Check 2: Original dictionary (data_dictionary_entries)
            # Try multiple database_name variations
            for db_name in [connection_id, "default", "nexdata"]:
                entry = session.exec(
                    select(DataDictionaryEntry).where(
                        DataDictionaryEntry.database_name == db_name,
                        DataDictionaryEntry.schema_name == schema,
                        DataDictionaryEntry.table_name == table,
                        DataDictionaryEntry.column_name == column,
                        DataDictionaryEntry.is_active == True
                    )
                ).first()
                
                if entry:
                    result_data["sources"].append("data_dictionary_entries")
                    result_data["original"] = {
                        "column_name": entry.column_name,
                        "business_name": entry.business_name,
                        "business_description": entry.business_description,
                        "technical_description": entry.technical_description,
                        "data_type": entry.data_type,
                        "examples": entry.examples or [],
                        "tags": entry.tags or [],
                        "source": entry.source,
                        "version": entry.version_number
                    }
                    break
            
            # Check 3: Raw column info if no dictionary entry found
            if not result_data["sources"]:
                try:
                    columns = DataExplorerService.get_columns(schema=schema, table=table, db_id=connection_id)
                    for c in columns:
                        if c.name.lower() == column.lower():
                            result_data["sources"].append("database")
                            result_data["raw"] = {
                                "column_name": c.name,
                                "data_type": c.data_type,
                                "nullable": c.is_nullable,
                                "default": c.default,
                                "position": c.ordinal_position
                            }
                            result_data["message"] = "Column found but no dictionary documentation exists."
                            break
                    
                    if not result_data["sources"]:
                        return {"success": False, "error": f"Column {column} not found in {schema}.{table}"}
                except Exception as e:
                    return {"success": False, "error": f"Could not get column info: {str(e)}"}
            
            # Merge results for best available data
            if "data_dictionary_entries" in result_data["sources"]:
                orig = result_data.get("original", {})
                result_data["best"] = {
                    "column_name": orig.get("column_name"),
                    "business_name": orig.get("business_name"),
                    "description": orig.get("business_description"),
                    "technical_description": orig.get("technical_description"),
                    "data_type": orig.get("data_type"),
                    "examples": orig.get("examples", []),
                    "tags": orig.get("tags", [])
                }
            elif "dictionary_fields" in result_data["sources"]:
                enh = result_data.get("enhanced", {})
                result_data["best"] = {
                    "column_name": enh.get("column_name"),
                    "business_name": enh.get("business_name"),
                    "description": enh.get("business_definition"),
                    "data_type": enh.get("data_type"),
                    "entity_role": enh.get("entity_role"),
                    "tags": enh.get("tags", [])
                }
            
            return {"success": True, "data": result_data}
        except Exception as e:
            logger.error(f"get_field_documentation error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_check_data_quality(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute check_data_quality tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            schema = tool_input["schema"]
            table = tool_input["table"]
            
            asset = dict_service.get_asset_by_table(session, connection_id, schema, table)
            
            if not asset:
                return {"success": False, "error": f"Table {schema}.{table} not found"}
            
            return {
                "success": True,
                "data": {
                    "table": f"{schema}.{table}",
                    "trust_tier": asset.trust_tier,
                    "trust_score": asset.trust_score,
                    "approved_for_reporting": asset.approved_for_reporting,
                    "approved_for_ml": asset.approved_for_ml,
                    "known_issues": asset.known_issues,
                    "issue_tags": asset.issue_tags or [],
                    "summary": f"{asset.trust_tier.upper()} tier (score: {asset.trust_score}/100)"
                }
            }
        except Exception as e:
            logger.error(f"check_data_quality error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_find_trusted_data(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute find_trusted_data tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            use_case = tool_input["use_case"]
            min_tier = tool_input.get("min_trust_tier", "trusted")
            
            # Get all assets from dictionary
            results, total = dict_service.search_assets(
                session=session,
                connection_id=connection_id,
                business_domain=tool_input.get("business_domain"),
                limit=200,
                offset=0
            )
            
            # Check if dictionary is empty
            if total == 0:
                return {
                    "success": True,
                    "data": {
                        "assets": [],
                        "count": 0,
                        "use_case": use_case,
                        "message": (
                            "No assets found in the data dictionary. "
                            "The dictionary needs to be synced and assets need to be curated with trust tiers. "
                            "Use list_tables to see raw database tables."
                        )
                    }
                }
            
            # Filter by trust tier and use case
            tier_order = {"deprecated": 0, "experimental": 1, "trusted": 2, "certified": 3}
            min_tier_level = tier_order.get(min_tier, 2)
            
            qualified = []
            for asset in results:
                tier_level = tier_order.get(asset.trust_tier, 1)
                if tier_level < min_tier_level:
                    continue
                
                if use_case == "reporting" and not asset.approved_for_reporting:
                    continue
                if use_case == "ml" and not asset.approved_for_ml:
                    continue
                
                qualified.append({
                    "schema": asset.schema_name,
                    "table": asset.table_name,
                    "business_name": asset.business_name,
                    "trust_tier": asset.trust_tier,
                    "trust_score": asset.trust_score,
                    "owner": asset.owner
                })
            
            # Sort by trust score
            qualified.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
            
            # Build message
            if qualified:
                message = f"Found {len(qualified)} assets qualified for {use_case}"
            else:
                message = (
                    f"No assets found with trust tier '{min_tier}' or higher that are approved for {use_case}. "
                    f"Found {total} total assets in dictionary, but none meet the criteria."
                )
            
            return {
                "success": True,
                "data": {
                    "assets": qualified[:tool_input.get("limit", 25)],
                    "count": len(qualified),
                    "use_case": use_case,
                    "total_in_dictionary": total,
                    "message": message
                }
            }
        except Exception as e:
            logger.error(f"find_trusted_data error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_explain_table(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute explain_table tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            schema = tool_input["schema"]
            table = tool_input["table"]
            
            explanation = {
                "full_name": f"{schema}.{table}",
                "sources": []
            }
            
            # Check 1: Enhanced dictionary (dictionary_assets)
            asset = dict_service.get_asset_by_table(session, connection_id, schema, table)
            if asset:
                explanation["sources"].append("dictionary_assets")
                context = dict_service.get_dictionary_context(
                    session=session,
                    connection_id=connection_id,
                    schema_name=schema,
                    table_name=table
                )
                
                explanation["identity"] = {
                    "business_name": context["table"].get("business_name"),
                    "description": context["table"].get("definition"),
                    "domain": context["table"].get("domain")
                }
                explanation["grain"] = {
                    "description": context["table"].get("grain"),
                    "row_count": context["table"].get("row_count")
                }
                explanation["ownership"] = {
                    "owner": asset.owner,
                    "steward": asset.steward
                }
                explanation["trust"] = {
                    "tier": asset.trust_tier,
                    "score": asset.trust_score,
                    "approved_for_reporting": asset.approved_for_reporting,
                    "approved_for_ml": asset.approved_for_ml,
                    "known_issues": asset.known_issues
                }
                explanation["relationships"] = context.get("relationships", [])
            
            # Check 2: Original dictionary (data_dictionary_entries - column-level)
            original_entries = None
            for db_name in [connection_id, "default", "nexdata"]:
                entries = original_dict_service.get_dictionary_for_tables(
                    session, db_name, schema, [table], active_only=True
                )
                if entries:
                    original_entries = entries
                    break
            
            if original_entries:
                explanation["sources"].append("data_dictionary_entries")
                explanation["column_definitions"] = [
                    {
                        "column_name": e.column_name,
                        "business_name": e.business_name,
                        "description": e.business_description,
                        "technical_description": e.technical_description,
                        "data_type": e.data_type,
                        "examples": e.examples or [],
                        "tags": e.tags or []
                    }
                    for e in original_entries
                ]
                explanation["documented_columns"] = len(original_entries)
            
            # Check 3: Raw database structure
            try:
                columns = DataExplorerService.get_columns(schema=schema, table=table, db_id=connection_id)
                tables = DataExplorerService.get_tables(schema=schema, db_id=connection_id)
                table_info = next((t for t in tables if t.name == table), None)
                
                if columns:
                    explanation["sources"].append("database")
                    explanation["structure"] = {
                        "type": table_info.type if table_info else "table",
                        "row_count": table_info.row_estimate if table_info else None,
                        "total_columns": len(columns)
                    }
                    
                    # If no dictionary, include all columns
                    if "data_dictionary_entries" not in explanation["sources"]:
                        explanation["columns"] = [
                            {"name": c.name, "type": c.data_type, "nullable": c.is_nullable}
                            for c in columns
                        ]
                        
                        # Infer key columns from naming
                        key_columns = []
                        for col in columns:
                            name_lower = col.name.lower()
                            if name_lower == 'id' or name_lower.endswith('_id'):
                                key_columns.append({
                                    "name": col.name,
                                    "type": col.data_type,
                                    "inferred_role": "identifier" if name_lower == 'id' else "possible_foreign_key"
                                })
                        if key_columns:
                            explanation["inferred_keys"] = key_columns
            except Exception as e:
                logger.warning(f"Could not get raw structure: {e}")
            
            # Generate summary
            if not explanation["sources"]:
                return {"success": False, "error": f"Table {schema}.{table} not found"}
            
            if "data_dictionary_entries" in explanation["sources"]:
                doc_count = explanation.get("documented_columns", 0)
                total_count = explanation.get("structure", {}).get("total_columns", doc_count)
                explanation["summary"] = f"Found {doc_count} column definitions in data dictionary (out of {total_count} total columns)"
            elif "dictionary_assets" in explanation["sources"]:
                explanation["summary"] = "Found in enhanced dictionary with table-level documentation"
            else:
                explanation["summary"] = "Table exists in database but has no dictionary documentation"
            
            return {"success": True, "data": explanation}
        except Exception as e:
            logger.error(f"explain_table error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_explain_grain(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute explain_grain tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            schema = tool_input["schema"]
            table = tool_input["table"]
            
            asset = dict_service.get_asset_by_table(session, connection_id, schema, table)
            
            if not asset:
                return {"success": False, "error": f"Table {schema}.{table} not found"}
            
            # Get fields to find primary key
            fields = dict_service.get_fields_for_asset(session, asset.id)
            primary_key = [f.column_name for f in fields if f.entity_role == "primary_identifier"]
            
            grain_description = asset.grain or asset.row_meaning
            
            return {
                "success": True,
                "data": {
                    "table": f"{schema}.{table}",
                    "grain_description": grain_description,
                    "primary_key": primary_key or None,
                    "aggregation_guidance": (
                        f"Each row represents: {grain_description}. Aggregate accordingly."
                        if grain_description else
                        "Grain not documented. Review table structure before aggregating."
                    )
                }
            }
        except Exception as e:
            logger.error(f"explain_grain error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_explain_join(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute explain_join tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            left_schema = tool_input["left_schema"]
            left_table = tool_input["left_table"]
            right_schema = tool_input["right_schema"]
            right_table = tool_input["right_table"]
            
            # Try to get relationships for left table
            try:
                rels = dict_service.get_relationships_for_table(
                    session, connection_id, left_schema, left_table
                )
            except Exception as e:
                logger.warning(f"Could not get relationships: {e}")
                rels = []
            
            # Find direct relationship - handle both model structures
            direct_rel = None
            left_col = None
            right_col = None
            
            for rel in rels:
                # Try old model structure (source_schema, source_table, etc.)
                if hasattr(rel, 'source_schema') and hasattr(rel, 'target_schema'):
                    if (rel.target_schema == right_schema and rel.target_table == right_table):
                        direct_rel = rel
                        left_col = rel.source_column
                        right_col = rel.target_column
                        break
                    if (rel.source_schema == right_schema and rel.source_table == right_table):
                        direct_rel = rel
                        left_col = rel.target_column
                        right_col = rel.source_column
                        break
                # Try new model structure (left_ref, right_ref)
                elif hasattr(rel, 'left_ref') and rel.left_ref:
                    left = rel.left_ref
                    right = rel.right_ref or {}
                    if (right.get('schema') == right_schema and right.get('table') == right_table):
                        direct_rel = rel
                        left_col = left.get('column')
                        right_col = right.get('column')
                        break
                    if (left.get('schema') == right_schema and left.get('table') == right_table):
                        direct_rel = rel
                        left_col = right.get('column')
                        right_col = left.get('column')
                        break
            
            if direct_rel and left_col and right_col:
                warnings = []
                cardinality = direct_rel.cardinality
                if cardinality == "one_to_many":
                    warnings.append("1:N join - aggregations on the 'one' side may cause fanout")
                elif cardinality == "many_to_many":
                    warnings.append("N:M join - use with caution, consider aggregating first")
                
                return {
                    "success": True,
                    "data": {
                        "can_join": True,
                        "join_type": "direct",
                        "join_columns": {"left": left_col, "right": right_col},
                        "cardinality": cardinality,
                        "warnings": warnings,
                        "example_sql": f"""SELECT *
FROM {left_schema}.{left_table} l
LEFT JOIN {right_schema}.{right_table} r
  ON l.{left_col} = r.{right_col}"""
                    }
                }
            else:
                return {
                    "success": True,
                    "data": {
                        "can_join": False,
                        "message": f"No direct relationship found between {left_schema}.{left_table} and {right_schema}.{right_table}",
                        "suggestion": "Check table structure with get_table_info or use discover_relationships to explore connections"
                    }
                }
        except Exception as e:
            logger.error(f"explain_join error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_search_dictionary(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search_dictionary tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            query = tool_input["query"]
            scope = tool_input.get("scope", "all")
            schema = tool_input.get("schema")
            limit = tool_input.get("limit", 20)
            
            results = []
            
            # Search assets (tables)
            if scope in ("all", "tables", "definitions"):
                assets, _ = dict_service.search_assets(
                    session=session,
                    connection_id=connection_id,
                    schema_name=schema,
                    search_term=query,
                    limit=limit
                )
                
                for asset in assets:
                    relevance = "high" if query.lower() in (asset.table_name or "").lower() else "medium"
                    results.append({
                        "match_type": "table",
                        "schema": asset.schema_name,
                        "table": asset.table_name,
                        "business_name": asset.business_name,
                        "description": (asset.business_definition or "")[:150],
                        "relevance": relevance
                    })
            
            # Search fields (columns) - would need additional service method
            # For now, just return table results
            
            # Sort by relevance
            relevance_order = {"high": 0, "medium": 1, "low": 2}
            results.sort(key=lambda x: relevance_order.get(x.get("relevance", "low"), 2))
            
            return {
                "success": True,
                "data": {
                    "query": query,
                    "results": results[:limit],
                    "count": len(results)
                }
            }
        except Exception as e:
            logger.error(f"search_dictionary error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_preview_dictionary_update(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Preview proposed changes to a dictionary entry before saving."""
        try:
            schema = tool_input["schema"]
            table = tool_input["table"]
            column = tool_input["column"]
            
            # Get current entry
            current_entry = None
            for db_name in ["default", "nexdata"]:
                entry = session.exec(
                    select(DataDictionaryEntry).where(
                        DataDictionaryEntry.database_name == db_name,
                        DataDictionaryEntry.schema_name == schema,
                        DataDictionaryEntry.table_name == table,
                        DataDictionaryEntry.column_name == column,
                        DataDictionaryEntry.is_active == True
                    )
                ).first()
                if entry:
                    current_entry = entry
                    break
            
            # Build the preview
            current_values = {}
            proposed_values = {}
            changes = []
            
            if current_entry:
                current_values = {
                    "business_name": current_entry.business_name,
                    "business_description": current_entry.business_description,
                    "technical_description": current_entry.technical_description,
                    "examples": current_entry.examples or [],
                    "tags": current_entry.tags or [],
                    "version": current_entry.version_number,
                    "source": current_entry.source
                }
            else:
                current_values = {
                    "business_name": None,
                    "business_description": None,
                    "technical_description": None,
                    "examples": [],
                    "tags": [],
                    "version": 0,
                    "source": None
                }
            
            # Build proposed values and track changes
            fields_to_update = ["business_name", "business_description", "technical_description", "examples", "tags"]
            
            for field in fields_to_update:
                if field in tool_input and tool_input[field] is not None:
                    proposed_values[field] = tool_input[field]
                    if tool_input[field] != current_values.get(field):
                        changes.append({
                            "field": field,
                            "current": current_values.get(field),
                            "proposed": tool_input[field]
                        })
                else:
                    proposed_values[field] = current_values.get(field)
            
            if not changes:
                return {
                    "success": True,
                    "data": {
                        "message": "No changes detected. The proposed values are the same as the current values.",
                        "column": f"{schema}.{table}.{column}",
                        "current": current_values
                    }
                }
            
            return {
                "success": True,
                "data": {
                    "message": "Please review the proposed changes below. Say 'confirm' or 'save' to apply them, or 'cancel' to discard.",
                    "column": f"{schema}.{table}.{column}",
                    "is_new_entry": current_entry is None,
                    "current_version": current_values.get("version", 0),
                    "will_create_version": (current_values.get("version", 0) or 0) + 1,
                    "changes": changes,
                    "current": current_values,
                    "proposed": proposed_values,
                    "action_required": "User must confirm to save these changes"
                }
            }
        except Exception as e:
            logger.error(f"preview_dictionary_update error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_save_dictionary_update(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Save a dictionary update after user confirmation."""
        try:
            schema = tool_input["schema"]
            table = tool_input["table"]
            column = tool_input["column"]
            version_notes = tool_input.get("version_notes", "Updated via chat")
            
            # Find current entry to get database_name
            current_entry = None
            db_name = "default"
            for try_db_name in ["default", "nexdata"]:
                entry = session.exec(
                    select(DataDictionaryEntry).where(
                        DataDictionaryEntry.database_name == try_db_name,
                        DataDictionaryEntry.schema_name == schema,
                        DataDictionaryEntry.table_name == table,
                        DataDictionaryEntry.column_name == column,
                        DataDictionaryEntry.is_active == True
                    )
                ).first()
                if entry:
                    current_entry = entry
                    db_name = try_db_name
                    break
            
            # Build the entry data
            entry_data = {
                "database_name": db_name,
                "schema_name": schema,
                "table_name": table,
                "column_name": column,
                "source": "human_edited",  # Mark as human-edited for versioning
                "version_notes": version_notes
            }
            
            # Add optional fields if provided
            if "business_name" in tool_input:
                entry_data["business_name"] = tool_input["business_name"]
            elif current_entry:
                entry_data["business_name"] = current_entry.business_name
            
            if "business_description" in tool_input:
                entry_data["business_description"] = tool_input["business_description"]
            elif current_entry:
                entry_data["business_description"] = current_entry.business_description
            
            if "technical_description" in tool_input:
                entry_data["technical_description"] = tool_input["technical_description"]
            elif current_entry:
                entry_data["technical_description"] = current_entry.technical_description
            
            if "examples" in tool_input:
                entry_data["examples"] = tool_input["examples"]
            elif current_entry:
                entry_data["examples"] = current_entry.examples
            
            if "tags" in tool_input:
                entry_data["tags"] = tool_input["tags"]
            elif current_entry:
                entry_data["tags"] = current_entry.tags
            
            # Get data_type from current entry or leave None
            if current_entry:
                entry_data["data_type"] = current_entry.data_type
            
            # Use the existing upsert function with create_new_version=True for human edits
            count = original_dict_service.upsert_dictionary_entries(
                session=session,
                entries=[entry_data],
                database_name=db_name,
                create_new_version=True  # Always create new version for human edits
            )
            
            # Get the updated entry to return
            updated_entry = session.exec(
                select(DataDictionaryEntry).where(
                    DataDictionaryEntry.database_name == db_name,
                    DataDictionaryEntry.schema_name == schema,
                    DataDictionaryEntry.table_name == table,
                    DataDictionaryEntry.column_name == column,
                    DataDictionaryEntry.is_active == True
                )
            ).first()
            
            return {
                "success": True,
                "data": {
                    "message": f"Successfully saved dictionary update for {schema}.{table}.{column}",
                    "column": f"{schema}.{table}.{column}",
                    "new_version": updated_entry.version_number if updated_entry else None,
                    "updated_at": updated_entry.updated_at.isoformat() if updated_entry else None,
                    "saved_values": {
                        "business_name": updated_entry.business_name if updated_entry else None,
                        "business_description": updated_entry.business_description if updated_entry else None,
                        "technical_description": updated_entry.technical_description if updated_entry else None,
                        "examples": updated_entry.examples if updated_entry else [],
                        "tags": updated_entry.tags if updated_entry else []
                    }
                }
            }
        except Exception as e:
            logger.error(f"save_dictionary_update error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_get_column_history(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Get version history for a column's dictionary entry."""
        try:
            schema = tool_input["schema"]
            table = tool_input["table"]
            column = tool_input["column"]
            
            # Try to find versions with different database_name values
            versions = []
            for db_name in ["default", "nexdata"]:
                db_versions = original_dict_service.get_column_versions(
                    session=session,
                    database_name=db_name,
                    schema_name=schema,
                    table_name=table,
                    column_name=column
                )
                if db_versions:
                    versions = db_versions
                    break
            
            if not versions:
                return {
                    "success": True,
                    "data": {
                        "message": f"No version history found for {schema}.{table}.{column}",
                        "column": f"{schema}.{table}.{column}",
                        "versions": []
                    }
                }
            
            version_history = []
            for v in versions:
                version_history.append({
                    "entry_id": v.id,
                    "version": v.version_number,
                    "is_active": v.is_active,
                    "source": v.source,
                    "business_name": v.business_name,
                    "business_description": (v.business_description or "")[:100] + ("..." if v.business_description and len(v.business_description) > 100 else ""),
                    "version_notes": v.version_notes,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "updated_at": v.updated_at.isoformat() if v.updated_at else None
                })
            
            return {
                "success": True,
                "data": {
                    "column": f"{schema}.{table}.{column}",
                    "total_versions": len(versions),
                    "versions": version_history,
                    "tip": "Use rollback_column_version with an entry_id to restore a previous version"
                }
            }
        except Exception as e:
            logger.error(f"get_column_history error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_rollback_column_version(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback a column to a previous version."""
        try:
            entry_id = tool_input["entry_id"]
            
            # Get the entry to rollback to
            target_entry = session.get(DataDictionaryEntry, entry_id)
            if not target_entry:
                return {"success": False, "error": f"Entry with ID {entry_id} not found"}
            
            # Use the existing activate_version function
            activated = original_dict_service.activate_version(session, entry_id)
            
            return {
                "success": True,
                "data": {
                    "message": f"Successfully rolled back {target_entry.schema_name}.{target_entry.table_name}.{target_entry.column_name} to version {activated.version_number}",
                    "column": f"{target_entry.schema_name}.{target_entry.table_name}.{target_entry.column_name}",
                    "restored_version": activated.version_number,
                    "restored_values": {
                        "business_name": activated.business_name,
                        "business_description": activated.business_description,
                        "technical_description": activated.technical_description,
                        "examples": activated.examples,
                        "tags": activated.tags
                    }
                }
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"rollback_column_version error: {e}")
            return {"success": False, "error": str(e)}

