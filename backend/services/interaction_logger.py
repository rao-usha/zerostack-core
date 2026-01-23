"""Interaction logging service for audit trail."""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4
from enum import Enum

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Interaction event types."""
    # Chat events
    CHAT_MESSAGE = "CHAT_MESSAGE"
    
    # Dataset events
    DATASET_RESOLVE = "DATASET_RESOLVE"
    INGEST_START = "INGEST_START"
    INGEST_COMPLETE = "INGEST_COMPLETE"
    
    # Run events
    RUN_SUBMITTED = "RUN_SUBMITTED"
    RUN_STARTED = "RUN_STARTED"
    RUN_COMPLETED = "RUN_COMPLETED"
    RUN_FAILED = "RUN_FAILED"
    RUN_CANCELLED = "RUN_CANCELLED"
    
    # Asset events
    ASSET_CREATED = "ASSET_CREATED"
    ASSET_PROMOTED = "ASSET_PROMOTED"
    ASSET_DELETED = "ASSET_DELETED"
    
    # View events
    VIEW_STATUS = "VIEW_STATUS"
    VIEW_LOGS = "VIEW_LOGS"


class InteractionLogger:
    """
    Service for logging interactions to the interaction_logs table.
    
    Provides an append-only audit trail linking:
    - Chat sessions to runs to assets
    - All significant actions with timestamps
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the logger.
        
        Args:
            session: Async database session
        """
        self.session = session
    
    async def log(
        self,
        event_type: EventType,
        actor: str = "system",
        message: Optional[str] = None,
        refs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        chat_session_id: Optional[str] = None
    ) -> str:
        """
        Log an interaction event.
        
        Args:
            event_type: Type of event
            actor: Who performed the action (user, assistant, system)
            message: Optional human-readable message
            refs: References to related entities {run_id, asset_id, dataset_id, etc.}
            metadata: Additional metadata
            chat_session_id: Link to chat session if applicable
            
        Returns:
            ID of created log entry
        """
        from db.models import interaction_logs
        
        interaction_id = str(uuid4())
        
        await self.session.execute(
            insert(interaction_logs).values(
                id=interaction_id,
                chat_session_id=chat_session_id,
                actor=actor,
                event_type=event_type.value if isinstance(event_type, EventType) else event_type,
                message=message,
                refs=refs or {},
                metadata=metadata or {},
                created_at=datetime.utcnow()
            )
        )
        
        logger.debug(f"Logged interaction: {event_type} refs={refs}")
        return interaction_id
    
    async def log_chat_message(
        self,
        chat_session_id: str,
        actor: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a chat message."""
        return await self.log(
            event_type=EventType.CHAT_MESSAGE,
            actor=actor,
            message=message,
            chat_session_id=chat_session_id,
            metadata=metadata
        )
    
    async def log_run_submitted(
        self,
        run_id: str,
        recipe_id: str,
        dataset_id: Optional[str] = None,
        chat_session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a run submission."""
        return await self.log(
            event_type=EventType.RUN_SUBMITTED,
            refs={
                'run_id': run_id,
                'recipe_id': recipe_id,
                'dataset_id': dataset_id
            },
            chat_session_id=chat_session_id,
            metadata=metadata
        )
    
    async def log_asset_promoted(
        self,
        asset_id: str,
        run_id: str,
        promoted_by: Optional[str] = None,
        chat_session_id: Optional[str] = None
    ) -> str:
        """Log asset promotion to permanent."""
        return await self.log(
            event_type=EventType.ASSET_PROMOTED,
            actor=promoted_by or "user",
            refs={'asset_id': asset_id, 'run_id': run_id},
            chat_session_id=chat_session_id
        )
    
    async def get_session_history(
        self,
        chat_session_id: str,
        limit: int = 100
    ) -> list:
        """
        Get interaction history for a chat session.
        
        Args:
            chat_session_id: Session to get history for
            limit: Maximum entries to return
            
        Returns:
            List of interaction log entries
        """
        from db.models import interaction_logs
        
        result = await self.session.execute(
            select(interaction_logs)
            .where(interaction_logs.c.chat_session_id == chat_session_id)
            .order_by(interaction_logs.c.created_at.desc())
            .limit(limit)
        )
        return result.fetchall()
    
    async def get_run_history(self, run_id: str) -> list:
        """
        Get all interactions related to a specific run.
        
        Args:
            run_id: Run to get history for
            
        Returns:
            List of interaction log entries
        """
        from db.models import interaction_logs
        from sqlalchemy import cast
        from sqlalchemy.dialects.postgresql import JSONB
        
        # Query for entries where refs contains this run_id
        result = await self.session.execute(
            select(interaction_logs)
            .where(interaction_logs.c.refs['run_id'].astext == run_id)
            .order_by(interaction_logs.c.created_at.asc())
        )
        return result.fetchall()


# Convenience function for getting logger instance
def get_interaction_logger(session: AsyncSession) -> InteractionLogger:
    """Get an interaction logger instance."""
    return InteractionLogger(session)
