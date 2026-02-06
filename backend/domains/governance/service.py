"""Governance service - policies, approvals, and audit logging."""
import logging
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .db_models import policies, approvals, audit_logs, data_classifications
from .models import (
    Policy, PolicyCreate, PolicyUpdate, PolicyType, PolicyStatus,
    Approval, ApprovalCreate, ApprovalStatus,
    AuditLogEntry, AuditLogCreate,
    DataClassification, DataClassificationCreate, Classification,
    PolicyEvaluationRequest, PolicyEvaluationResult,
    ComplianceFramework, ComplianceFrameworkReport, ComplianceCheckResult, ComplianceReportResponse
)

logger = logging.getLogger(__name__)


class PolicyService:
    """Policy management service."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_policy(
        self,
        policy: PolicyCreate,
        created_by: Optional[UUID] = None,
        org_id: Optional[UUID] = None
    ) -> Policy:
        """Create a new governance policy."""
        policy_id = uuid4()

        await self.session.execute(
            policies.insert().values(
                id=policy_id,
                name=policy.name,
                description=policy.description,
                policy_type=policy.policy_type.value,
                status=PolicyStatus.DRAFT.value,
                rules=policy.rules,
                metadata=policy.metadata,
                created_by=created_by,
                org_id=org_id
            )
        )

        logger.info(f"Created policy {policy_id}: {policy.name}")
        return await self.get_policy(policy_id)

    async def get_policy(self, policy_id: UUID) -> Optional[Policy]:
        """Get a policy by ID."""
        result = await self.session.execute(
            select(policies).where(policies.c.id == policy_id)
        )
        row = result.fetchone()

        if not row:
            return None

        return Policy(
            id=row.id,
            name=row.name,
            description=row.description,
            policy_type=PolicyType(row.policy_type),
            status=PolicyStatus(row.status),
            rules=row.rules or {},
            metadata=row.metadata or {},
            created_by=row.created_by,
            org_id=row.org_id,
            created_at=row.created_at,
            updated_at=row.updated_at
        )

    async def list_policies(
        self,
        org_id: Optional[UUID] = None,
        policy_type: Optional[PolicyType] = None,
        status: Optional[PolicyStatus] = None
    ) -> List[Policy]:
        """List policies with optional filters."""
        stmt = select(policies)

        conditions = []
        if org_id:
            conditions.append(policies.c.org_id == org_id)
        if policy_type:
            conditions.append(policies.c.policy_type == policy_type.value)
        if status:
            conditions.append(policies.c.status == status.value)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(policies.c.created_at.desc())

        result = await self.session.execute(stmt)
        rows = result.fetchall()

        return [
            Policy(
                id=row.id,
                name=row.name,
                description=row.description,
                policy_type=PolicyType(row.policy_type),
                status=PolicyStatus(row.status),
                rules=row.rules or {},
                metadata=row.metadata or {},
                created_by=row.created_by,
                org_id=row.org_id,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            for row in rows
        ]

    async def update_policy(self, policy_id: UUID, updates: PolicyUpdate) -> Optional[Policy]:
        """Update a policy."""
        update_values = {"updated_at": datetime.utcnow()}

        if updates.name is not None:
            update_values["name"] = updates.name
        if updates.description is not None:
            update_values["description"] = updates.description
        if updates.status is not None:
            update_values["status"] = updates.status.value
        if updates.rules is not None:
            update_values["rules"] = updates.rules
        if updates.metadata is not None:
            update_values["metadata"] = updates.metadata

        await self.session.execute(
            update(policies).where(policies.c.id == policy_id).values(**update_values)
        )

        logger.info(f"Updated policy {policy_id}")
        return await self.get_policy(policy_id)

    async def delete_policy(self, policy_id: UUID) -> bool:
        """Delete a policy (soft delete via archive)."""
        result = await self.session.execute(
            update(policies)
            .where(policies.c.id == policy_id)
            .values(status=PolicyStatus.ARCHIVED.value, updated_at=datetime.utcnow())
        )
        return result.rowcount > 0

    async def evaluate_policies(
        self,
        request: PolicyEvaluationRequest
    ) -> PolicyEvaluationResult:
        """Evaluate all active policies against a resource/action."""
        # Get all active policies
        active_policies = await self.list_policies(status=PolicyStatus.ACTIVE)

        matching = []
        actions_triggered = set()
        requires_approval = False
        denial_reason = None

        for policy in active_policies:
            rules = policy.rules
            if not rules:
                continue

            # Check if policy applies to this resource type
            applies_to = rules.get("applies_to", {})
            resource_types = applies_to.get("resource_types", [])
            if resource_types and request.resource_type not in resource_types:
                continue

            # Check conditions
            conditions = rules.get("conditions", [])
            conditions_met = True
            for condition in conditions:
                field = condition.get("field")
                operator = condition.get("operator", "eq")
                value = condition.get("value")

                context_value = request.context.get(field)
                if operator == "eq" and context_value != value:
                    conditions_met = False
                    break
                elif operator == "ne" and context_value == value:
                    conditions_met = False
                    break
                elif operator == "in" and context_value not in value:
                    conditions_met = False
                    break

            if conditions_met:
                matching.append(policy)
                policy_actions = rules.get("actions", [])
                actions_triggered.update(policy_actions)

                if "deny" in policy_actions:
                    denial_reason = rules.get("denial_message", f"Denied by policy: {policy.name}")
                if "require_approval" in policy_actions:
                    requires_approval = True

        allowed = "deny" not in actions_triggered

        return PolicyEvaluationResult(
            allowed=allowed,
            matching_policies=matching,
            required_approvals=requires_approval,
            denial_reason=denial_reason,
            actions_triggered=list(actions_triggered)
        )


class ApprovalService:
    """Approval workflow service."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_approval(
        self,
        approval: ApprovalCreate,
        requested_by: UUID,
        triggered_by_policy_id: Optional[UUID] = None
    ) -> Approval:
        """Create an approval request."""
        approval_id = uuid4()

        await self.session.execute(
            approvals.insert().values(
                id=approval_id,
                resource_type=approval.resource_type,
                resource_id=approval.resource_id,
                action=approval.action,
                requested_by=requested_by,
                reason=approval.reason,
                metadata=approval.metadata,
                triggered_by_policy_id=triggered_by_policy_id,
                status=ApprovalStatus.PENDING.value
            )
        )

        logger.info(f"Created approval request {approval_id} for {approval.resource_type}/{approval.resource_id}")
        return await self.get_approval(approval_id)

    async def get_approval(self, approval_id: UUID) -> Optional[Approval]:
        """Get an approval by ID."""
        result = await self.session.execute(
            select(approvals).where(approvals.c.id == approval_id)
        )
        row = result.fetchone()

        if not row:
            return None

        return Approval(
            id=row.id,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            action=row.action,
            requested_by=row.requested_by,
            status=ApprovalStatus(row.status),
            approver=row.approver,
            reason=row.reason,
            metadata=row.metadata or {},
            created_at=row.created_at,
            reviewed_at=row.reviewed_at
        )

    async def list_approvals(
        self,
        status: Optional[ApprovalStatus] = None,
        resource_type: Optional[str] = None,
        requested_by: Optional[UUID] = None
    ) -> List[Approval]:
        """List approvals with optional filters."""
        stmt = select(approvals)

        conditions = []
        if status:
            conditions.append(approvals.c.status == status.value)
        if resource_type:
            conditions.append(approvals.c.resource_type == resource_type)
        if requested_by:
            conditions.append(approvals.c.requested_by == requested_by)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(approvals.c.created_at.desc())

        result = await self.session.execute(stmt)
        rows = result.fetchall()

        return [
            Approval(
                id=row.id,
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                action=row.action,
                requested_by=row.requested_by,
                status=ApprovalStatus(row.status),
                approver=row.approver,
                reason=row.reason,
                metadata=row.metadata or {},
                created_at=row.created_at,
                reviewed_at=row.reviewed_at
            )
            for row in rows
        ]

    async def review_approval(
        self,
        approval_id: UUID,
        approver_id: UUID,
        status: ApprovalStatus,
        reason: Optional[str] = None
    ) -> Optional[Approval]:
        """Review (approve/reject) an approval request."""
        if status not in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]:
            raise ValueError("Review status must be APPROVED or REJECTED")

        await self.session.execute(
            update(approvals)
            .where(approvals.c.id == approval_id)
            .values(
                status=status.value,
                approver=approver_id,
                review_reason=reason,
                reviewed_at=datetime.utcnow()
            )
        )

        logger.info(f"Approval {approval_id} {status.value} by {approver_id}")
        return await self.get_approval(approval_id)

    async def cancel_approval(self, approval_id: UUID) -> Optional[Approval]:
        """Cancel a pending approval request."""
        await self.session.execute(
            update(approvals)
            .where(
                and_(
                    approvals.c.id == approval_id,
                    approvals.c.status == ApprovalStatus.PENDING.value
                )
            )
            .values(status=ApprovalStatus.CANCELLED.value)
        )
        return await self.get_approval(approval_id)


class AuditLogService:
    """Audit logging service - immutable record of all actions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        resource_name: Optional[str] = None,
        user_id: Optional[UUID] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        compliance_tags: Optional[List[str]] = None
    ) -> AuditLogEntry:
        """Create an immutable audit log entry."""
        entry_id = uuid4()

        await self.session.execute(
            audit_logs.insert().values(
                id=entry_id,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                details=details or {},
                status=status,
                error_message=error_message,
                compliance_tags=compliance_tags or []
            )
        )

        return await self._get_entry(entry_id)

    async def _get_entry(self, entry_id: UUID) -> AuditLogEntry:
        """Get an audit log entry by ID."""
        result = await self.session.execute(
            select(audit_logs).where(audit_logs.c.id == entry_id)
        )
        row = result.fetchone()

        return AuditLogEntry(
            id=row.id,
            user_id=row.user_id,
            action=row.action,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            resource_name=row.resource_name,
            details=row.details or {},
            ip_address=row.ip_address,
            user_agent=row.user_agent,
            status=row.status,
            error_message=row.error_message,
            compliance_tags=row.compliance_tags or [],
            created_at=row.created_at
        )

    async def query(
        self,
        user_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[AuditLogEntry], int]:
        """Query audit log with filters."""
        stmt = select(audit_logs)
        count_stmt = select(audit_logs)

        conditions = []
        if user_id:
            conditions.append(audit_logs.c.user_id == user_id)
        if resource_type:
            conditions.append(audit_logs.c.resource_type == resource_type)
        if resource_id:
            conditions.append(audit_logs.c.resource_id == resource_id)
        if action:
            conditions.append(audit_logs.c.action == action)
        if start_date:
            conditions.append(audit_logs.c.created_at >= start_date)
        if end_date:
            conditions.append(audit_logs.c.created_at <= end_date)

        if conditions:
            stmt = stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))

        # Get total count
        count_result = await self.session.execute(count_stmt)
        total = len(count_result.fetchall())

        # Get paginated results
        stmt = stmt.order_by(audit_logs.c.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        rows = result.fetchall()

        entries = [
            AuditLogEntry(
                id=row.id,
                user_id=row.user_id,
                action=row.action,
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                resource_name=row.resource_name,
                details=row.details or {},
                ip_address=row.ip_address,
                user_agent=row.user_agent,
                status=row.status,
                error_message=row.error_message,
                compliance_tags=row.compliance_tags or [],
                created_at=row.created_at
            )
            for row in rows
        ]

        return entries, total


class DataClassificationService:
    """Data classification service."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def classify(
        self,
        classification_data: DataClassificationCreate,
        classified_by: Optional[UUID] = None
    ) -> DataClassification:
        """Classify a data resource."""
        classification_id = uuid4()

        await self.session.execute(
            data_classifications.insert().values(
                id=classification_id,
                resource_type=classification_data.resource_type,
                resource_id=classification_data.resource_id,
                resource_path=classification_data.resource_path,
                classification=classification_data.classification.value,
                sub_classification=classification_data.sub_classification,
                compliance_tags=classification_data.compliance_tags,
                retention_days=classification_data.retention_days,
                classified_by=classified_by,
                notes=classification_data.notes
            )
        )

        return await self.get_classification(classification_id)

    async def get_classification(self, classification_id: UUID) -> Optional[DataClassification]:
        """Get a classification by ID."""
        result = await self.session.execute(
            select(data_classifications).where(data_classifications.c.id == classification_id)
        )
        row = result.fetchone()

        if not row:
            return None

        return DataClassification(
            id=row.id,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            resource_path=row.resource_path,
            classification=Classification(row.classification),
            sub_classification=row.sub_classification,
            compliance_tags=row.compliance_tags or [],
            retention_days=row.retention_days,
            classified_by=row.classified_by,
            notes=row.notes,
            created_at=row.created_at,
            updated_at=row.updated_at
        )

    async def get_resource_classification(
        self,
        resource_type: str,
        resource_id: UUID
    ) -> Optional[DataClassification]:
        """Get classification for a specific resource."""
        result = await self.session.execute(
            select(data_classifications).where(
                and_(
                    data_classifications.c.resource_type == resource_type,
                    data_classifications.c.resource_id == resource_id
                )
            )
        )
        row = result.fetchone()

        if not row:
            return None

        return DataClassification(
            id=row.id,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            resource_path=row.resource_path,
            classification=Classification(row.classification),
            sub_classification=row.sub_classification,
            compliance_tags=row.compliance_tags or [],
            retention_days=row.retention_days,
            classified_by=row.classified_by,
            notes=row.notes,
            created_at=row.created_at,
            updated_at=row.updated_at
        )

    async def list_classifications(
        self,
        resource_type: Optional[str] = None,
        classification: Optional[Classification] = None
    ) -> List[DataClassification]:
        """List classifications with filters."""
        stmt = select(data_classifications)

        conditions = []
        if resource_type:
            conditions.append(data_classifications.c.resource_type == resource_type)
        if classification:
            conditions.append(data_classifications.c.classification == classification.value)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(data_classifications.c.created_at.desc())

        result = await self.session.execute(stmt)
        rows = result.fetchall()

        return [
            DataClassification(
                id=row.id,
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                resource_path=row.resource_path,
                classification=Classification(row.classification),
                sub_classification=row.sub_classification,
                compliance_tags=row.compliance_tags or [],
                retention_days=row.retention_days,
                classified_by=row.classified_by,
                notes=row.notes,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            for row in rows
        ]


class ComplianceService:
    """Compliance reporting service."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._classification_service = DataClassificationService(session)
        self._policy_service = PolicyService(session)
        self._audit_service = AuditLogService(session)

    async def generate_report(
        self,
        frameworks: Optional[List[ComplianceFramework]] = None
    ) -> ComplianceReportResponse:
        """Generate a compliance report for specified frameworks."""
        if not frameworks:
            frameworks = list(ComplianceFramework)

        report_id = uuid4()
        framework_reports = []
        all_recommendations = []

        for framework in frameworks:
            checks = await self._run_framework_checks(framework)
            passed = sum(1 for c in checks if c.status == "passed")
            failed = sum(1 for c in checks if c.status == "failed")
            warnings = sum(1 for c in checks if c.status == "warning")
            total = len(checks)

            score = (passed / total * 100) if total > 0 else 0

            if failed > 0:
                overall_status = "non_compliant"
            elif warnings > 0:
                overall_status = "partial"
            elif passed == total and total > 0:
                overall_status = "compliant"
            else:
                overall_status = "not_assessed"

            # Collect recommendations from failed checks
            for check in checks:
                if check.status == "failed" and check.recommendation:
                    all_recommendations.append(f"[{framework.value.upper()}] {check.recommendation}")

            framework_reports.append(ComplianceFrameworkReport(
                framework=framework,
                overall_status=overall_status,
                compliance_score=score,
                checks=checks,
                last_assessed=datetime.utcnow()
            ))

        total_checks = sum(len(fr.checks) for fr in framework_reports)
        total_passed = sum(sum(1 for c in fr.checks if c.status == "passed") for fr in framework_reports)
        total_failed = sum(sum(1 for c in fr.checks if c.status == "failed") for fr in framework_reports)
        total_warnings = sum(sum(1 for c in fr.checks if c.status == "warning") for fr in framework_reports)

        return ComplianceReportResponse(
            report_id=report_id,
            generated_at=datetime.utcnow(),
            frameworks=framework_reports,
            summary={
                "total_checks": total_checks,
                "passed": total_passed,
                "failed": total_failed,
                "warnings": total_warnings
            },
            recommendations=all_recommendations[:10]  # Top 10 recommendations
        )

    async def _run_framework_checks(self, framework: ComplianceFramework) -> List[ComplianceCheckResult]:
        """Run compliance checks for a specific framework."""
        checks = []

        if framework == ComplianceFramework.GDPR:
            checks = await self._run_gdpr_checks()
        elif framework == ComplianceFramework.HIPAA:
            checks = await self._run_hipaa_checks()
        elif framework == ComplianceFramework.CCPA:
            checks = await self._run_ccpa_checks()
        elif framework == ComplianceFramework.SOC2:
            checks = await self._run_soc2_checks()
        elif framework == ComplianceFramework.PCI_DSS:
            checks = await self._run_pci_dss_checks()

        return checks

    async def _run_gdpr_checks(self) -> List[ComplianceCheckResult]:
        """Run GDPR compliance checks."""
        checks = []

        # Check 1: Data classification exists for PII
        classifications = await self._classification_service.list_classifications(
            classification=Classification.PII
        )
        checks.append(ComplianceCheckResult(
            check_name="PII Data Classification",
            description="All PII data should be classified and tagged",
            status="passed" if classifications else "warning",
            details=f"Found {len(classifications)} PII classifications",
            recommendation="Classify all datasets containing personal data" if not classifications else None
        ))

        # Check 2: Data access policies exist
        policies = await self._policy_service.list_policies(
            policy_type=PolicyType.DATA_ACCESS,
            status=PolicyStatus.ACTIVE
        )
        checks.append(ComplianceCheckResult(
            check_name="Data Access Policies",
            description="Active data access policies should be in place",
            status="passed" if policies else "failed",
            details=f"Found {len(policies)} active data access policies",
            recommendation="Create data access policies for sensitive data" if not policies else None
        ))

        # Check 3: Privacy policies exist
        privacy_policies = await self._policy_service.list_policies(
            policy_type=PolicyType.PRIVACY,
            status=PolicyStatus.ACTIVE
        )
        checks.append(ComplianceCheckResult(
            check_name="Privacy Policies",
            description="Active privacy policies should be in place",
            status="passed" if privacy_policies else "failed",
            details=f"Found {len(privacy_policies)} active privacy policies",
            recommendation="Create privacy policies for data handling" if not privacy_policies else None
        ))

        # Check 4: Retention policies exist
        retention_policies = await self._policy_service.list_policies(
            policy_type=PolicyType.RETENTION,
            status=PolicyStatus.ACTIVE
        )
        checks.append(ComplianceCheckResult(
            check_name="Data Retention Policies",
            description="Data retention policies should be defined",
            status="passed" if retention_policies else "warning",
            details=f"Found {len(retention_policies)} active retention policies",
            recommendation="Define data retention periods for all data types" if not retention_policies else None
        ))

        # Check 5: Audit logging is active
        entries, total = await self._audit_service.query(limit=1)
        checks.append(ComplianceCheckResult(
            check_name="Audit Logging",
            description="All data access should be logged",
            status="passed" if total > 0 else "warning",
            details=f"Total audit log entries: {total}",
            recommendation="Enable comprehensive audit logging" if total == 0 else None
        ))

        return checks

    async def _run_hipaa_checks(self) -> List[ComplianceCheckResult]:
        """Run HIPAA compliance checks."""
        checks = []

        # Check: PHI classification
        checks.append(ComplianceCheckResult(
            check_name="PHI Classification",
            description="Protected Health Information should be classified",
            status="warning",
            details="Manual verification required",
            recommendation="Ensure all PHI data is properly classified and tagged"
        ))

        # Check: Access controls
        policies = await self._policy_service.list_policies(
            policy_type=PolicyType.DATA_ACCESS,
            status=PolicyStatus.ACTIVE
        )
        checks.append(ComplianceCheckResult(
            check_name="Access Controls",
            description="Minimum necessary access controls should be in place",
            status="passed" if policies else "failed",
            details=f"Found {len(policies)} access control policies",
            recommendation="Implement minimum necessary access policies" if not policies else None
        ))

        # Check: Audit trail
        entries, total = await self._audit_service.query(limit=1)
        checks.append(ComplianceCheckResult(
            check_name="Audit Trail",
            description="Complete audit trail for PHI access",
            status="passed" if total > 0 else "failed",
            details=f"Total audit entries: {total}",
            recommendation="Enable comprehensive PHI access logging" if total == 0 else None
        ))

        return checks

    async def _run_ccpa_checks(self) -> List[ComplianceCheckResult]:
        """Run CCPA compliance checks."""
        return [
            ComplianceCheckResult(
                check_name="Consumer Data Inventory",
                description="Maintain inventory of consumer personal information",
                status="warning",
                details="Manual verification required",
                recommendation="Document all consumer data collection and usage"
            ),
            ComplianceCheckResult(
                check_name="Data Deletion Capability",
                description="Ability to delete consumer data upon request",
                status="warning",
                details="Manual verification required",
                recommendation="Implement data deletion workflows"
            )
        ]

    async def _run_soc2_checks(self) -> List[ComplianceCheckResult]:
        """Run SOC2 compliance checks."""
        checks = []

        # Security: Access policies
        policies = await self._policy_service.list_policies(status=PolicyStatus.ACTIVE)
        checks.append(ComplianceCheckResult(
            check_name="Security Policies",
            description="Security policies should be documented and active",
            status="passed" if policies else "failed",
            details=f"Found {len(policies)} active policies",
            recommendation="Document and implement security policies" if not policies else None
        ))

        # Availability: N/A for this service
        checks.append(ComplianceCheckResult(
            check_name="Availability Monitoring",
            description="System availability should be monitored",
            status="not_applicable",
            details="Covered by infrastructure monitoring"
        ))

        return checks

    async def _run_pci_dss_checks(self) -> List[ComplianceCheckResult]:
        """Run PCI-DSS compliance checks."""
        return [
            ComplianceCheckResult(
                check_name="Cardholder Data Protection",
                description="Cardholder data must be encrypted and protected",
                status="warning",
                details="Manual verification required",
                recommendation="Classify and encrypt all cardholder data"
            ),
            ComplianceCheckResult(
                check_name="Access Logging",
                description="All access to cardholder data must be logged",
                status="warning",
                details="Manual verification required",
                recommendation="Enable detailed access logging for payment data"
            )
        ]
