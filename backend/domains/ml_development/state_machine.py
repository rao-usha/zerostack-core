"""Run state machine for ML runs.

Provides:
- Clear state transitions
- Retry logic
- Failure categorization
"""
import logging
from typing import Optional, Tuple
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from core.config import settings

logger = logging.getLogger(__name__)


class RunState(str, Enum):
    """Possible states for an ML run."""
    QUEUED = "queued"           # Initial state, waiting to be scheduled
    SCHEDULED = "scheduled"     # Assigned to compute, starting
    RUNNING = "running"         # Executing
    RETRYING = "retrying"       # Failed, will retry
    SUCCEEDED = "succeeded"     # Completed successfully
    FAILED = "failed"           # Failed, no more retries
    CANCELLED = "cancelled"     # Manually cancelled


class FailureType(str, Enum):
    """Types of failures."""
    INFRA = "infra"       # Infrastructure failure (can retry)
    MODEL = "model"       # Model error (usually don't retry)
    TIMEOUT = "timeout"   # Timeout (can retry with longer timeout)
    UNKNOWN = "unknown"   # Unknown error


# Valid state transitions
VALID_TRANSITIONS = {
    RunState.QUEUED: [RunState.SCHEDULED, RunState.CANCELLED],
    RunState.SCHEDULED: [RunState.RUNNING, RunState.FAILED, RunState.CANCELLED],
    RunState.RUNNING: [RunState.SUCCEEDED, RunState.FAILED, RunState.RETRYING, RunState.CANCELLED],
    RunState.RETRYING: [RunState.SCHEDULED, RunState.FAILED, RunState.CANCELLED],
    RunState.SUCCEEDED: [],  # Terminal state
    RunState.FAILED: [],     # Terminal state  
    RunState.CANCELLED: [],  # Terminal state
}

# Errors that indicate infrastructure issues (retriable)
INFRA_ERROR_PATTERNS = [
    'connection refused',
    'connection reset',
    'timeout',
    'oom',
    'out of memory',
    'gpu memory',
    'cuda error',
    'device not found',
    'no available gpu',
    'pod evicted',
    'preempted',
    'spot instance terminated',
]


@dataclass
class StateTransition:
    """Result of a state transition."""
    success: bool
    old_state: RunState
    new_state: RunState
    retry_triggered: bool
    message: str


class RunStateMachine:
    """State machine for managing ML run lifecycle."""
    
    def __init__(self, engine: Optional[Engine] = None):
        self.engine = engine or create_engine(settings.database_url)
    
    def get_run_state(self, run_id: str) -> Tuple[Optional[RunState], dict]:
        """
        Get current state and metadata for a run.
        
        Returns:
            Tuple of (state, metadata_dict)
        """
        query = """
            SELECT status, retry_count, max_retries, failure_reason, failure_type
            FROM ml_run WHERE id = :run_id
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'run_id': run_id}).fetchone()
            if not result:
                return None, {}
            
            row = dict(result._mapping)
            try:
                state = RunState(row['status'])
            except ValueError:
                state = RunState.QUEUED
            
            return state, {
                'retry_count': row['retry_count'] or 0,
                'max_retries': row['max_retries'] or 2,
                'failure_reason': row['failure_reason'],
                'failure_type': row['failure_type']
            }
    
    def can_transition(self, from_state: RunState, to_state: RunState) -> bool:
        """Check if a state transition is valid."""
        valid_targets = VALID_TRANSITIONS.get(from_state, [])
        return to_state in valid_targets
    
    def classify_failure(self, error_message: str) -> FailureType:
        """
        Classify a failure based on error message.
        
        Args:
            error_message: The error message/reason
            
        Returns:
            FailureType indicating the category
        """
        if not error_message:
            return FailureType.UNKNOWN
        
        lower_message = error_message.lower()
        
        # Check for infrastructure errors
        for pattern in INFRA_ERROR_PATTERNS:
            if pattern in lower_message:
                return FailureType.INFRA
        
        # Check for timeout
        if 'timeout' in lower_message or 'timed out' in lower_message:
            return FailureType.TIMEOUT
        
        # Assume model error for other cases
        return FailureType.MODEL
    
    def should_retry(
        self,
        failure_type: FailureType,
        retry_count: int,
        max_retries: int
    ) -> bool:
        """
        Determine if a run should be retried.
        
        Args:
            failure_type: Type of failure
            retry_count: Current retry count
            max_retries: Maximum retries allowed
            
        Returns:
            True if should retry
        """
        if retry_count >= max_retries:
            return False
        
        # Only retry infrastructure and timeout errors
        if failure_type in [FailureType.INFRA, FailureType.TIMEOUT]:
            return True
        
        # Don't retry model errors by default
        return False
    
    def transition(
        self,
        run_id: str,
        to_state: RunState,
        failure_reason: str = None,
        failure_type: FailureType = None
    ) -> StateTransition:
        """
        Transition a run to a new state.
        
        Args:
            run_id: The run ID
            to_state: Target state
            failure_reason: Reason for failure (if applicable)
            failure_type: Type of failure (if applicable)
            
        Returns:
            StateTransition with result
        """
        current_state, metadata = self.get_run_state(run_id)
        
        if current_state is None:
            return StateTransition(
                success=False,
                old_state=None,
                new_state=to_state,
                retry_triggered=False,
                message=f"Run {run_id} not found"
            )
        
        # Check if transition is valid
        if not self.can_transition(current_state, to_state):
            return StateTransition(
                success=False,
                old_state=current_state,
                new_state=to_state,
                retry_triggered=False,
                message=f"Invalid transition from {current_state.value} to {to_state.value}"
            )
        
        retry_triggered = False
        final_state = to_state
        
        # Handle failure with potential retry
        if to_state == RunState.FAILED and failure_reason:
            if failure_type is None:
                failure_type = self.classify_failure(failure_reason)
            
            retry_count = metadata.get('retry_count', 0)
            max_retries = metadata.get('max_retries', 2)
            
            if self.should_retry(failure_type, retry_count, max_retries):
                final_state = RunState.RETRYING
                retry_triggered = True
        
        # Perform the update
        updates = ['status = :status']
        params = {'run_id': run_id, 'status': final_state.value}
        
        if failure_reason:
            updates.append('failure_reason = :failure_reason')
            params['failure_reason'] = failure_reason
        
        if failure_type:
            updates.append('failure_type = :failure_type')
            params['failure_type'] = failure_type.value
        
        if retry_triggered:
            updates.append('retry_count = retry_count + 1')
        
        query = f"UPDATE ml_run SET {', '.join(updates)} WHERE id = :run_id"
        
        with self.engine.begin() as conn:
            conn.execute(text(query), params)
        
        logger.info(f"Run {run_id}: {current_state.value} → {final_state.value}" + 
                   (" (retry triggered)" if retry_triggered else ""))
        
        return StateTransition(
            success=True,
            old_state=current_state,
            new_state=final_state,
            retry_triggered=retry_triggered,
            message=f"Transitioned to {final_state.value}"
        )
    
    def start_run(self, run_id: str) -> StateTransition:
        """Mark a run as scheduled/starting."""
        return self.transition(run_id, RunState.SCHEDULED)
    
    def mark_running(self, run_id: str) -> StateTransition:
        """Mark a run as actively running."""
        return self.transition(run_id, RunState.RUNNING)
    
    def complete_run(self, run_id: str) -> StateTransition:
        """Mark a run as successfully completed."""
        return self.transition(run_id, RunState.SUCCEEDED)
    
    def fail_run(self, run_id: str, reason: str, failure_type: FailureType = None) -> StateTransition:
        """
        Mark a run as failed, with potential retry.
        
        Args:
            run_id: The run ID
            reason: Failure reason
            failure_type: Type of failure (auto-detected if not provided)
            
        Returns:
            StateTransition (may trigger retry)
        """
        return self.transition(run_id, RunState.FAILED, reason, failure_type)
    
    def cancel_run(self, run_id: str) -> StateTransition:
        """Cancel a run."""
        return self.transition(run_id, RunState.CANCELLED)
    
    def retry_run(self, run_id: str) -> StateTransition:
        """
        Manually trigger a retry for a run in RETRYING state.
        
        Transitions back to SCHEDULED.
        """
        current_state, _ = self.get_run_state(run_id)
        
        if current_state != RunState.RETRYING:
            return StateTransition(
                success=False,
                old_state=current_state,
                new_state=RunState.SCHEDULED,
                retry_triggered=False,
                message=f"Can only retry runs in RETRYING state, current: {current_state.value if current_state else 'unknown'}"
            )
        
        return self.transition(run_id, RunState.SCHEDULED)


# Singleton instance
_machine_instance: Optional[RunStateMachine] = None


def get_state_machine() -> RunStateMachine:
    """Get singleton state machine instance."""
    global _machine_instance
    if _machine_instance is None:
        _machine_instance = RunStateMachine()
    return _machine_instance
