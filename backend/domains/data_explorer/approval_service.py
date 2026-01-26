"""Approval Service for managing approval workflows.

Provides functionality to:
- Create approval requests for dangerous operations
- Approve or reject pending requests
- Execute approved operations
- Track approval history and expiration
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)


# Operation types that require approval
APPROVAL_REQUIRED_OPERATIONS = {
    'materialized_view': {
        'title_template': 'Create Materialized View: {name}',
        'default_expiry_hours': 24,
        'default_risk': 'medium',
    },
    'stored_procedure': {
        'title_template': 'Create Stored Procedure: {name}',
        'default_expiry_hours': 24,
        'default_risk': 'high',
    },
    'bulk_export': {
        'title_template': 'Bulk Export: {name}',
        'default_expiry_hours': 12,
        'default_risk': 'low',
    },
}

# Risk level definitions
RISK_LEVELS = {
    'low': {'color': 'green', 'auto_approve_allowed': True},
    'medium': {'color': 'yellow', 'auto_approve_allowed': False},
    'high': {'color': 'orange', 'auto_approve_allowed': False},
    'critical': {'color': 'red', 'auto_approve_allowed': False},
}


class ApprovalService:
    """Service for managing approval workflows."""

    def __init__(self, session: AsyncSession):
        """Initialize approval service.

        Args:
            session: Async database session
        """
        self.session = session

    @staticmethod
    def assess_risk(
        operation_type: str,
        operation_params: Dict[str, Any],
    ) -> Tuple[str, List[str]]:
        """Assess risk level for an operation.

        Args:
            operation_type: Type of operation
            operation_params: Operation parameters

        Returns:
            Tuple of (risk_level, list of risk reasons)
        """
        reasons = []
        risk_level = APPROVAL_REQUIRED_OPERATIONS.get(
            operation_type, {}
        ).get('default_risk', 'medium')

        # Check for high-risk patterns
        if operation_type == 'stored_procedure':
            source_code = operation_params.get('source_code', '').upper()

            # Check for data modification
            if any(kw in source_code for kw in ['INSERT', 'UPDATE', 'DELETE', 'TRUNCATE']):
                risk_level = 'high'
                reasons.append('Procedure modifies data (INSERT/UPDATE/DELETE)')

            # Check for dynamic SQL
            if 'EXECUTE' in source_code or 'PERFORM' in source_code:
                risk_level = 'high'
                reasons.append('Procedure uses dynamic SQL execution')

            # Check for loop constructs (potential for long-running)
            if 'LOOP' in source_code or 'WHILE' in source_code:
                reasons.append('Procedure contains loops (may be long-running)')

        elif operation_type == 'materialized_view':
            source_query = operation_params.get('source_query', '').upper()

            # Check for joins (complex queries)
            if source_query.count('JOIN') > 2:
                reasons.append('Query has multiple joins (complex)')

            # Check for aggregations
            if any(kw in source_query for kw in ['GROUP BY', 'HAVING', 'DISTINCT']):
                reasons.append('Query uses aggregations')

        elif operation_type == 'bulk_export':
            # Large exports are higher risk
            if operation_params.get('limit') is None:
                risk_level = 'medium'
                reasons.append('No row limit specified (may export large dataset)')

        if not reasons:
            reasons.append('Standard operation')

        return risk_level, reasons

    async def create_request(
        self,
        operation_type: str,
        operation_params: Dict[str, Any],
        requested_by: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        connection_id: str = "default",
        conversation_id: Optional[UUID] = None,
        expiry_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a new approval request.

        Args:
            operation_type: Type of operation (materialized_view, stored_procedure, etc.)
            operation_params: Parameters for the operation
            requested_by: User requesting approval
            title: Optional custom title
            description: Optional description
            connection_id: Database connection
            conversation_id: Optional chat conversation link
            expiry_hours: Hours until request expires

        Returns:
            Dict with request details
        """
        from .approval_models import approval_requests

        # Validate operation type
        if operation_type not in APPROVAL_REQUIRED_OPERATIONS:
            raise ValueError(f"Unknown operation type: {operation_type}")

        op_config = APPROVAL_REQUIRED_OPERATIONS[operation_type]

        # Generate title if not provided
        if not title:
            name = operation_params.get('name', 'unnamed')
            title = op_config['title_template'].format(name=name)

        # Assess risk
        risk_level, risk_reasons = self.assess_risk(operation_type, operation_params)

        # Calculate expiry
        expiry_hours = expiry_hours or op_config['default_expiry_hours']
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)

        # Create request
        request_id = uuid4()
        await self.session.execute(
            approval_requests.insert().values(
                id=request_id,
                request_type=f"create_{operation_type}",
                title=title,
                description=description,
                operation_type=operation_type,
                operation_params=operation_params,
                connection_id=connection_id,
                risk_level=risk_level,
                risk_reasons=risk_reasons,
                status="pending",
                requested_by=requested_by,
                expires_at=expires_at,
                conversation_id=conversation_id,
            )
        )
        await self.session.commit()

        logger.info(f"Created approval request {request_id} for {operation_type} by {requested_by}")

        return {
            "request_id": str(request_id),
            "title": title,
            "operation_type": operation_type,
            "risk_level": risk_level,
            "risk_reasons": risk_reasons,
            "status": "pending",
            "requested_by": requested_by,
            "expires_at": expires_at.isoformat(),
            "expiry_hours": expiry_hours,
        }

    async def approve_request(
        self,
        request_id: UUID,
        decided_by: str,
        reason: Optional[str] = None,
        execute_immediately: bool = True,
    ) -> Dict[str, Any]:
        """Approve a pending request.

        Args:
            request_id: ID of the request to approve
            decided_by: User approving the request
            reason: Optional reason for approval
            execute_immediately: Whether to execute the operation now

        Returns:
            Dict with approval result
        """
        from .approval_models import approval_requests

        # Get request
        result = await self.session.execute(
            select(approval_requests).where(approval_requests.c.id == request_id)
        )
        row = result.fetchone()

        if not row:
            raise ValueError(f"Request {request_id} not found")

        if row.status != "pending":
            raise ValueError(f"Request is not pending (status: {row.status})")

        if row.expires_at < datetime.utcnow():
            # Mark as expired
            await self.session.execute(
                update(approval_requests)
                .where(approval_requests.c.id == request_id)
                .values(status="expired")
            )
            await self.session.commit()
            raise ValueError("Request has expired")

        # Update status to approved
        await self.session.execute(
            update(approval_requests)
            .where(approval_requests.c.id == request_id)
            .values(
                status="approved",
                decided_by=decided_by,
                decided_at=datetime.utcnow(),
                decision_reason=reason,
            )
        )
        await self.session.commit()

        logger.info(f"Approved request {request_id} by {decided_by}")

        result_data = {
            "request_id": str(request_id),
            "status": "approved",
            "decided_by": decided_by,
            "operation_type": row.operation_type,
        }

        # Execute if requested
        if execute_immediately:
            execution_result = await self._execute_operation(request_id, row)
            result_data["execution"] = execution_result

        return result_data

    async def reject_request(
        self,
        request_id: UUID,
        decided_by: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Reject a pending request.

        Args:
            request_id: ID of the request to reject
            decided_by: User rejecting the request
            reason: Reason for rejection (required)

        Returns:
            Dict with rejection result
        """
        from .approval_models import approval_requests

        if not reason:
            raise ValueError("Rejection reason is required")

        # Get request
        result = await self.session.execute(
            select(approval_requests).where(approval_requests.c.id == request_id)
        )
        row = result.fetchone()

        if not row:
            raise ValueError(f"Request {request_id} not found")

        if row.status != "pending":
            raise ValueError(f"Request is not pending (status: {row.status})")

        # Update status to rejected
        await self.session.execute(
            update(approval_requests)
            .where(approval_requests.c.id == request_id)
            .values(
                status="rejected",
                decided_by=decided_by,
                decided_at=datetime.utcnow(),
                decision_reason=reason,
            )
        )
        await self.session.commit()

        logger.info(f"Rejected request {request_id} by {decided_by}: {reason}")

        return {
            "request_id": str(request_id),
            "status": "rejected",
            "decided_by": decided_by,
            "reason": reason,
        }

    async def _execute_operation(
        self,
        request_id: UUID,
        row: Any,
    ) -> Dict[str, Any]:
        """Execute an approved operation.

        Args:
            request_id: Request ID
            row: Database row with operation details

        Returns:
            Dict with execution result
        """
        from .approval_models import approval_requests

        try:
            operation_type = row.operation_type
            params = row.operation_params

            if operation_type == "materialized_view":
                from .materialized_view_service import MaterializedViewService
                mv_service = MaterializedViewService(self.session)
                result = await mv_service.create_materialized_view(**params)
                resource_id = result.get("view_id")

            elif operation_type == "stored_procedure":
                from .stored_procedure_service import StoredProcedureService
                proc_service = StoredProcedureService(self.session)
                result = await proc_service.create_procedure(**params)
                resource_id = result.get("procedure_id")

            else:
                raise ValueError(f"Unknown operation type: {operation_type}")

            # Update request with execution result
            await self.session.execute(
                update(approval_requests)
                .where(approval_requests.c.id == request_id)
                .values(
                    status="executed",
                    executed_at=datetime.utcnow(),
                    execution_result=result,
                    result_resource_id=resource_id,
                )
            )
            await self.session.commit()

            logger.info(f"Executed approved operation for request {request_id}")

            return {
                "success": True,
                "result": result,
            }

        except Exception as e:
            # Update request with error
            await self.session.execute(
                update(approval_requests)
                .where(approval_requests.c.id == request_id)
                .values(
                    execution_error=str(e),
                )
            )
            await self.session.commit()

            logger.error(f"Failed to execute operation for request {request_id}: {e}")

            return {
                "success": False,
                "error": str(e),
            }

    async def get_request(self, request_id: UUID) -> Optional[Dict[str, Any]]:
        """Get request by ID."""
        from .approval_models import approval_requests

        result = await self.session.execute(
            select(approval_requests).where(approval_requests.c.id == request_id)
        )
        row = result.fetchone()

        if not row:
            return None

        return {
            "id": str(row.id),
            "request_type": row.request_type,
            "title": row.title,
            "description": row.description,
            "operation_type": row.operation_type,
            "operation_params": row.operation_params,
            "connection_id": row.connection_id,
            "risk_level": row.risk_level,
            "risk_reasons": row.risk_reasons,
            "status": row.status,
            "decision_reason": row.decision_reason,
            "requested_by": row.requested_by,
            "decided_by": row.decided_by,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
            "decided_at": row.decided_at.isoformat() if row.decided_at else None,
            "executed_at": row.executed_at.isoformat() if row.executed_at else None,
            "execution_result": row.execution_result,
            "execution_error": row.execution_error,
            "result_resource_id": str(row.result_resource_id) if row.result_resource_id else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    async def list_requests(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        requested_by: Optional[str] = None,
        decided_by: Optional[str] = None,
        operation_type: Optional[str] = None,
        include_expired: bool = False,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List approval requests with filtering."""
        from .approval_models import approval_requests

        query = select(approval_requests)
        count_query = select(func.count(approval_requests.c.id))

        if status:
            query = query.where(approval_requests.c.status == status)
            count_query = count_query.where(approval_requests.c.status == status)

        if requested_by:
            query = query.where(approval_requests.c.requested_by == requested_by)
            count_query = count_query.where(approval_requests.c.requested_by == requested_by)

        if decided_by:
            query = query.where(approval_requests.c.decided_by == decided_by)
            count_query = count_query.where(approval_requests.c.decided_by == decided_by)

        if operation_type:
            query = query.where(approval_requests.c.operation_type == operation_type)
            count_query = count_query.where(approval_requests.c.operation_type == operation_type)

        if not include_expired:
            # Exclude expired pending requests
            query = query.where(
                (approval_requests.c.status != "pending") |
                (approval_requests.c.expires_at > datetime.utcnow())
            )
            count_query = count_query.where(
                (approval_requests.c.status != "pending") |
                (approval_requests.c.expires_at > datetime.utcnow())
            )

        query = query.order_by(approval_requests.c.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        rows = result.fetchall()

        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        requests = [
            {
                "id": str(row.id),
                "title": row.title,
                "operation_type": row.operation_type,
                "risk_level": row.risk_level,
                "status": row.status,
                "requested_by": row.requested_by,
                "decided_by": row.decided_by,
                "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]

        return requests, total

    async def expire_old_requests(self) -> int:
        """Mark expired pending requests as expired.

        Returns:
            Number of requests marked as expired
        """
        from .approval_models import approval_requests

        result = await self.session.execute(
            update(approval_requests)
            .where(
                approval_requests.c.status == "pending",
                approval_requests.c.expires_at < datetime.utcnow(),
            )
            .values(status="expired")
        )
        await self.session.commit()

        count = result.rowcount
        if count > 0:
            logger.info(f"Marked {count} approval requests as expired")

        return count

    async def cancel_request(
        self,
        request_id: UUID,
        cancelled_by: str,
    ) -> Dict[str, Any]:
        """Cancel a pending request (by the requestor).

        Args:
            request_id: ID of the request to cancel
            cancelled_by: User cancelling (must be the requestor)

        Returns:
            Dict with cancellation result
        """
        from .approval_models import approval_requests

        # Get request
        result = await self.session.execute(
            select(approval_requests).where(approval_requests.c.id == request_id)
        )
        row = result.fetchone()

        if not row:
            raise ValueError(f"Request {request_id} not found")

        if row.status != "pending":
            raise ValueError(f"Request is not pending (status: {row.status})")

        if row.requested_by != cancelled_by:
            raise ValueError("Only the requestor can cancel a request")

        # Delete the request
        await self.session.execute(
            delete(approval_requests).where(approval_requests.c.id == request_id)
        )
        await self.session.commit()

        logger.info(f"Cancelled request {request_id} by {cancelled_by}")

        return {
            "request_id": str(request_id),
            "status": "cancelled",
        }
