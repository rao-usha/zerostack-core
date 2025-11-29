"""
Chat API router.

Provides endpoints for:
- Creating and managing conversations
- Sending messages with streaming responses
- Viewing conversation history
"""

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session
import json

from .models import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    MessageCreate, MessageResponse, ConversationWithMessages
)
from .service import ChatService
from db_session import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    session: Session = Depends(get_session)
):
    """
    Create a new chat conversation.
    
    Args:
        data: Conversation creation data (provider, model, connection_id, etc.)
        
    Returns:
        Created conversation
    """
    try:
        conversation = ChatService.create_conversation(session, data)
        return ConversationResponse(
            **conversation.model_dump(),
            message_count=0
        )
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = Query(default=0, ge=0, description="Offset"),
    limit: int = Query(default=50, ge=1, le=100, description="Limit"),
    provider: Optional[str] = Query(default=None, description="Filter by provider"),
    session: Session = Depends(get_session)
):
    """
    List conversations ordered by updated_at desc.
    
    Args:
        skip: Number of conversations to skip (pagination)
        limit: Maximum number of conversations to return
        provider: Optional filter by provider
        
    Returns:
        List of conversations with message counts
    """
    try:
        return ChatService.list_conversations(
            session,
            skip=skip,
            limit=limit,
            provider=provider
        )
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    session: Session = Depends(get_session)
):
    """
    Get a conversation with full message history.
    
    Args:
        conversation_id: Conversation UUID
        
    Returns:
        Conversation with all messages
    """
    result = ChatService.get_conversation_with_messages(session, conversation_id)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return result


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    data: ConversationUpdate,
    session: Session = Depends(get_session)
):
    """
    Update conversation metadata (title, metadata).
    
    Args:
        conversation_id: Conversation UUID
        data: Update data
        
    Returns:
        Updated conversation
    """
    result = ChatService.update_conversation(
        session,
        conversation_id,
        title=data.title,
        meta=data.meta
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get message count
    from sqlmodel import select, func
    from .models import ChatMessage
    count_query = select(func.count(ChatMessage.id)).where(
        ChatMessage.conversation_id == conversation_id
    )
    message_count = session.exec(count_query).one()
    
    return ConversationResponse(
        **result.model_dump(),
        message_count=message_count
    )


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: UUID,
    session: Session = Depends(get_session)
):
    """
    Delete a conversation and all its messages.
    
    Args:
        conversation_id: Conversation UUID
    """
    success = ChatService.delete_conversation(session, conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return None


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID,
    data: MessageCreate,
    session: Session = Depends(get_session)
):
    """
    Send a message in a conversation and stream the response.
    
    This endpoint uses Server-Sent Events (SSE) to stream the assistant's response.
    The LLM can call Data Explorer tools during generation.
    
    Event types:
    - delta: Partial response content
    - tool_call: LLM is calling a tool
    - tool_result: Tool execution result
    - done: Response complete
    - error: Error occurred
    
    Args:
        conversation_id: Conversation UUID
        data: Message data (content, optional provider/model overrides, stream flag)
        
    Returns:
        StreamingResponse with SSE events (if stream=True)
        or JSON response with complete message (if stream=False)
    """
    # Check conversation exists
    conversation = ChatService.get_conversation(session, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if data.stream:
        # Stream response with SSE
        async def event_generator():
            try:
                async for event in ChatService.stream_chat_response(
                    session=session,
                    conversation_id=conversation_id,
                    user_message=data.content,
                    provider=data.provider,
                    model=data.model,
                    connection_id=data.connection_id
                ):
                    # Format as SSE
                    event_type = event.get("event", "message")
                    event_data = event.get("data", {})
                    
                    yield f"event: {event_type}\n"
                    yield f"data: {json.dumps(event_data)}\n\n"
                    
                    # End stream on done or error
                    if event_type in ["done", "error"]:
                        break
            
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f"event: error\n"
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    else:
        # Non-streaming: collect full response
        full_content = []
        tool_calls = []
        error = None
        message_id = None
        
        try:
            async for event in ChatService.stream_chat_response(
                session=session,
                conversation_id=conversation_id,
                user_message=data.content,
                provider=data.provider,
                model=data.model,
                connection_id=data.connection_id
            ):
                event_type = event.get("event")
                event_data = event.get("data", {})
                
                if event_type == "delta":
                    full_content.append(event_data.get("content", ""))
                elif event_type == "tool_call":
                    tool_calls.append(event_data)
                elif event_type == "done":
                    message_id = event_data.get("message_id")
                elif event_type == "error":
                    error = event_data.get("error")
        
        except Exception as e:
            logger.error(f"Chat error: {e}")
            error = str(e)
        
        if error:
            raise HTTPException(status_code=500, detail=error)
        
        return {
            "message_id": message_id,
            "content": "".join(full_content),
            "tool_calls": tool_calls
        }

