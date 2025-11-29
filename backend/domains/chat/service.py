"""
Chat service layer.

Handles chat conversation management, message persistence, LLM orchestration,
and integration with MCP/Data Explorer tools.
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
    def _execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Data Explorer tool and return result."""
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
                    tools=DATA_EXPLORER_TOOLS,
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
                        tool_output = ChatService._execute_tool(tool_name, tool_input)
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

