"""
Data Ingestion Persistence Service

Handles file storage and database persistence for ingested files.
"""
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

import pandas as pd

from sqlalchemy import select, func, desc
from sqlmodel import Session

from domains.data_ingestion.db_models import (
    PEDeal,
    IngestedFile,
    IngestionIssue,
    FileStatus,
    UploadSource,
    IssueType,
    IssueSeverity,
    IssueStatus,
)
from domains.data_ingestion.models import (
    FileAnalysisResponse,
    DealCreate,
    DealUpdate,
    DealResponse,
    DealSummary,
    IngestedFileResponse,
    IngestedFileDetail,
    IssueResponse,
    IssueSummary,
    UploadResponse,
    ReAnalyzeResponse,
)
from domains.data_ingestion.anomaly_service import AnomalyDetectionService
from domains.data_ingestion.red_flag_scanner import RedFlagScanner
from domains.data_ingestion.service import DataIngestionService


class IngestionPersistenceService:
    """Service for persisting ingested files and analysis results"""

    def __init__(self, session: Session):
        self.session = session
        self.analyzer = DataIngestionService()

    # --- Deals ---

    def create_deal(self, data: DealCreate) -> DealResponse:
        """Create a new PE deal"""
        deal = PEDeal(
            name=data.name,
            target_company=data.target_company,
            description=data.description,
            deal_stage=data.deal_stage,
            deal_owner=data.deal_owner,
        )
        if data.target_close_date:
            from datetime import date
            deal.target_close_date = date.fromisoformat(data.target_close_date)

        self.session.add(deal)
        self.session.commit()
        self.session.refresh(deal)

        return self._deal_to_response(deal)

    def get_deal(self, deal_id: UUID) -> Optional[DealResponse]:
        """Get a deal by ID"""
        deal = self.session.get(PEDeal, deal_id)
        if not deal:
            return None
        return self._deal_to_response(deal)

    def list_deals(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DealResponse]:
        """List all deals"""
        stmt = select(PEDeal).order_by(desc(PEDeal.created_at))
        if status:
            stmt = stmt.where(PEDeal.status == status)
        stmt = stmt.offset(offset).limit(limit)

        deals = self.session.exec(stmt).all()
        return [self._deal_to_response(d) for d in deals]

    def update_deal(self, deal_id: UUID, data: DealUpdate) -> Optional[DealResponse]:
        """Update a deal"""
        deal = self.session.get(PEDeal, deal_id)
        if not deal:
            return None

        if data.name is not None:
            deal.name = data.name
        if data.target_company is not None:
            deal.target_company = data.target_company
        if data.description is not None:
            deal.description = data.description
        if data.status is not None:
            deal.status = data.status
        if data.deal_stage is not None:
            deal.deal_stage = data.deal_stage
        if data.deal_owner is not None:
            deal.deal_owner = data.deal_owner
        if data.target_close_date is not None:
            from datetime import date
            deal.target_close_date = date.fromisoformat(data.target_close_date)

        deal.updated_at = datetime.utcnow()
        self.session.add(deal)
        self.session.commit()
        self.session.refresh(deal)

        return self._deal_to_response(deal)

    def get_deal_summary(self, deal_id: UUID) -> Optional[DealSummary]:
        """Get deal summary with aggregated stats"""
        deal = self.session.get(PEDeal, deal_id)
        if not deal:
            return None

        # Get file stats
        file_stmt = select(
            func.count(IngestedFile.id).label('count'),
            func.sum(IngestedFile.row_count).label('total_rows'),
            func.avg(IngestedFile.quality_score).label('avg_quality'),
        ).where(IngestedFile.deal_id == deal_id)
        file_stats = self.session.exec(file_stmt).first()

        # Get issue counts
        issue_stmt = select(func.count(IngestionIssue.id)).where(
            IngestionIssue.deal_id == deal_id
        )
        issue_count = self.session.exec(issue_stmt).one()

        critical_stmt = select(func.count(IngestionIssue.id)).where(
            IngestionIssue.deal_id == deal_id,
            IngestionIssue.severity == IssueSeverity.CRITICAL,
        )
        critical_count = self.session.exec(critical_stmt).one()

        # Get detected categories
        cat_stmt = select(IngestedFile.detected_categories).where(
            IngestedFile.deal_id == deal_id,
            IngestedFile.detected_categories.isnot(None),
        )
        all_categories = set()
        for row in self.session.exec(cat_stmt):
            if row:
                all_categories.update(row)

        return DealSummary(
            id=str(deal.id),
            name=deal.name,
            target_company=deal.target_company,
            status=deal.status,
            file_count=file_stats.count or 0,
            total_rows=file_stats.total_rows or 0,
            issue_count=issue_count,
            critical_issues=critical_count,
            avg_quality_score=float(file_stats.avg_quality) if file_stats.avg_quality else None,
            detected_categories=list(all_categories),
            created_at=deal.created_at,
        )

    def _deal_to_response(self, deal: PEDeal) -> DealResponse:
        """Convert deal to response"""
        # Count files
        file_count = self.session.exec(
            select(func.count(IngestedFile.id)).where(IngestedFile.deal_id == deal.id)
        ).one()

        # Count issues
        issue_count = self.session.exec(
            select(func.count(IngestionIssue.id)).where(IngestionIssue.deal_id == deal.id)
        ).one()

        # Average quality
        avg_quality = self.session.exec(
            select(func.avg(IngestedFile.quality_score)).where(IngestedFile.deal_id == deal.id)
        ).one()

        return DealResponse(
            id=str(deal.id),
            name=deal.name,
            target_company=deal.target_company,
            description=deal.description,
            status=deal.status,
            deal_stage=deal.deal_stage,
            deal_owner=deal.deal_owner,
            target_close_date=deal.target_close_date.isoformat() if deal.target_close_date else None,
            file_count=file_count,
            issue_count=issue_count,
            avg_quality_score=float(avg_quality) if avg_quality else None,
            created_at=deal.created_at,
            updated_at=deal.updated_at,
        )

    # --- Files ---

    def upload_and_persist(
        self,
        file_content: bytes,
        filename: str,
        file_type: str,
        deal_id: Optional[UUID] = None,
        uploaded_by: Optional[str] = None,
        upload_source: str = "manual",
    ) -> UploadResponse:
        """Upload, analyze, and persist a file"""
        # Compute content hash
        content_hash = hashlib.sha256(file_content).hexdigest()

        # Check for duplicate
        existing = self.session.exec(
            select(IngestedFile).where(IngestedFile.content_hash == content_hash)
        ).first()
        if existing:
            # Return existing file info
            return UploadResponse(
                file_id=str(existing.id),
                filename=existing.filename,
                file_size_bytes=existing.file_size_bytes,
                file_type=existing.file_type,
                quality_score=existing.quality_score or 0,
                row_count=existing.row_count or 0,
                column_count=existing.column_count or 0,
                sheet_count=existing.sheet_count,
                detected_categories=existing.detected_categories or [],
                issue_count=len(existing.issues) if existing.issues else 0,
                analysis_summary=existing.analysis_summary or "Duplicate file - already analyzed",
                status=existing.status,
            )

        # Create file record
        ingested_file = IngestedFile(
            deal_id=deal_id,
            filename=filename,
            original_filename=filename,
            file_type=file_type,
            file_size_bytes=len(file_content),
            content_hash=content_hash,
            upload_source=upload_source,
            status=FileStatus.ANALYZING,
            uploaded_by=uploaded_by,
        )
        self.session.add(ingested_file)
        self.session.flush()

        try:
            # Analyze file
            analysis = self.analyzer.analyze_file(file_content, filename, file_type)

            # Update file record with analysis
            ingested_file.quality_score = analysis.overall_quality_score
            ingested_file.row_count = analysis.total_rows
            ingested_file.column_count = analysis.total_columns
            ingested_file.sheet_count = len(analysis.sheets)
            ingested_file.detected_categories = analysis.detected_data_categories
            ingested_file.schema_analysis = {
                "sheets": [s.model_dump() for s in analysis.sheets]
            }
            ingested_file.analysis_summary = analysis.summary
            ingested_file.status = FileStatus.COMPLETED
            ingested_file.analyzed_at = datetime.utcnow()

            # Create issues from analysis
            issue_count = self._create_issues_from_analysis(ingested_file, analysis)

            self.session.commit()

            return UploadResponse(
                file_id=str(ingested_file.id),
                filename=filename,
                file_size_bytes=len(file_content),
                file_type=file_type,
                quality_score=analysis.overall_quality_score,
                row_count=analysis.total_rows,
                column_count=analysis.total_columns,
                sheet_count=len(analysis.sheets),
                detected_categories=analysis.detected_data_categories,
                issue_count=issue_count,
                analysis_summary=analysis.summary,
                status=FileStatus.COMPLETED,
            )

        except Exception as e:
            ingested_file.status = FileStatus.FAILED
            ingested_file.error_message = str(e)
            self.session.commit()
            raise

    def _create_issues_from_analysis(
        self,
        ingested_file: IngestedFile,
        analysis: FileAnalysisResponse,
    ) -> int:
        """Create issue records from analysis results"""
        issue_count = 0

        # Create issues from potential_issues
        for issue_text in analysis.potential_issues:
            # Parse issue text to extract details
            severity = IssueSeverity.MEDIUM
            if "critical" in issue_text.lower() or "limited data" in issue_text.lower():
                severity = IssueSeverity.HIGH

            issue = IngestionIssue(
                file_id=ingested_file.id,
                deal_id=ingested_file.deal_id,
                issue_type=IssueType.QUALITY,
                severity=severity,
                title=issue_text[:200],
                description=issue_text,
            )
            self.session.add(issue)
            issue_count += 1

        # Create issues from column quality flags
        for sheet in analysis.sheets:
            for col in sheet.columns:
                for flag in col.quality_flags:
                    severity = IssueSeverity.LOW
                    if flag.value in ["missing_values", "empty_column"]:
                        severity = IssueSeverity.MEDIUM
                    if col.null_percent > 50:
                        severity = IssueSeverity.HIGH

                    issue = IngestionIssue(
                        file_id=ingested_file.id,
                        deal_id=ingested_file.deal_id,
                        issue_type=IssueType.QUALITY,
                        severity=severity,
                        category="data_quality",
                        sheet_name=sheet.sheet_name,
                        column_name=col.name,
                        title=f"{col.name}: {flag.value.replace('_', ' ').title()}",
                        description=f"Column '{col.name}' has {flag.value}: {col.null_percent:.1f}% null values, {col.unique_count} unique values",
                        details={
                            "flag": flag.value,
                            "null_percent": col.null_percent,
                            "unique_count": col.unique_count,
                        },
                    )
                    self.session.add(issue)
                    issue_count += 1

            # Create issues from anomalies
            for anomaly in sheet.anomalies:
                severity_map = {
                    "low": IssueSeverity.LOW,
                    "medium": IssueSeverity.MEDIUM,
                    "high": IssueSeverity.HIGH,
                    "critical": IssueSeverity.CRITICAL,
                }
                severity = severity_map.get(anomaly.get('severity', 'medium'), IssueSeverity.MEDIUM)

                issue = IngestionIssue(
                    file_id=ingested_file.id,
                    deal_id=ingested_file.deal_id,
                    issue_type=IssueType.ANOMALY,
                    severity=severity,
                    category=anomaly.get('anomaly_type', 'statistical'),
                    sheet_name=sheet.sheet_name,
                    column_name=anomaly.get('column_name'),
                    title=anomaly.get('title', 'Anomaly detected')[:200],
                    description=anomaly.get('description'),
                    details=anomaly.get('evidence'),
                    recommendation=anomaly.get('recommendation'),
                )
                self.session.add(issue)
                issue_count += 1

            # Create issues from red flags
            for red_flag in sheet.red_flags:
                severity_map = {
                    "low": IssueSeverity.LOW,
                    "medium": IssueSeverity.MEDIUM,
                    "high": IssueSeverity.HIGH,
                    "critical": IssueSeverity.CRITICAL,
                }
                severity = severity_map.get(red_flag.get('severity', 'medium'), IssueSeverity.MEDIUM)

                # Get first affected column if any
                affected_cols = red_flag.get('affected_columns', [])
                column_name = affected_cols[0] if affected_cols else None

                issue = IngestionIssue(
                    file_id=ingested_file.id,
                    deal_id=ingested_file.deal_id,
                    issue_type=IssueType.RED_FLAG,
                    severity=severity,
                    category=red_flag.get('category', 'general'),
                    sheet_name=sheet.sheet_name,
                    column_name=column_name,
                    title=red_flag.get('title', 'Red flag detected')[:200],
                    description=red_flag.get('description'),
                    details=red_flag.get('evidence'),
                    recommendation=red_flag.get('recommendation'),
                )
                self.session.add(issue)
                issue_count += 1

        return issue_count

    def get_file(self, file_id: UUID) -> Optional[IngestedFileDetail]:
        """Get file details with full analysis"""
        file = self.session.get(IngestedFile, file_id)
        if not file:
            return None
        return self._file_to_detail(file)

    def list_files(
        self,
        deal_id: Optional[UUID] = None,
        status: Optional[str] = None,
        upload_source: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[IngestedFileResponse]:
        """List ingested files"""
        stmt = select(IngestedFile).order_by(desc(IngestedFile.uploaded_at))

        if deal_id:
            stmt = stmt.where(IngestedFile.deal_id == deal_id)
        if status:
            stmt = stmt.where(IngestedFile.status == status)
        if upload_source:
            stmt = stmt.where(IngestedFile.upload_source == upload_source)

        stmt = stmt.offset(offset).limit(limit)
        files = self.session.exec(stmt).all()

        return [self._file_to_response(f) for f in files]

    def delete_file(self, file_id: UUID) -> bool:
        """Delete a file and its issues"""
        file = self.session.get(IngestedFile, file_id)
        if not file:
            return False

        self.session.delete(file)
        self.session.commit()
        return True

    def reanalyze_file(
        self,
        file_id: UUID,
        run_anomaly_detection: bool = True,
        run_red_flag_scan: bool = True,
    ) -> Optional[ReAnalyzeResponse]:
        """
        Re-run anomaly detection and red flag scanning on an existing file.

        Args:
            file_id: ID of the file to re-analyze
            run_anomaly_detection: Whether to run anomaly detection
            run_red_flag_scan: Whether to run red flag scanning

        Returns:
            ReAnalyzeResponse with counts of new issues, or None if file not found
        """
        file = self.session.get(IngestedFile, file_id)
        if not file:
            return None

        if not file.schema_analysis or 'sheets' not in file.schema_analysis:
            return ReAnalyzeResponse(
                file_id=str(file_id),
                new_anomalies=0,
                new_red_flags=0,
                total_issues=0,
                analysis_summary="No schema analysis available for this file",
            )

        new_anomalies = 0
        new_red_flags = 0

        # Process each sheet from the stored analysis
        for sheet_data in file.schema_analysis.get('sheets', []):
            sheet_name = sheet_data.get('sheet_name', 'Unknown')

            # Try to reconstruct DataFrame from sample data and columns
            # For full re-analysis, we would need the original file content
            # For now, we use the stored column statistics

            columns = sheet_data.get('columns', [])
            detected_categories = file.detected_categories or []

            if run_anomaly_detection:
                # Note: Full anomaly detection requires original data
                # This is a simplified version using stored statistics
                anomaly_service = AnomalyDetectionService()
                for col in columns:
                    col_name = col.get('name', '')
                    inferred_type = col.get('inferred_type', 'string')

                    # Check for conditions we can detect from stored stats
                    if col.get('null_percent', 0) > 80:
                        # Create high missing data anomaly
                        issue = IngestionIssue(
                            file_id=file.id,
                            deal_id=file.deal_id,
                            issue_type=IssueType.ANOMALY,
                            severity=IssueSeverity.HIGH,
                            category='data_quality',
                            sheet_name=sheet_name,
                            column_name=col_name,
                            title=f"Extremely high missing data in '{col_name}'",
                            description=f"Column has {col.get('null_percent', 0):.1f}% missing values",
                            details={'null_percent': col.get('null_percent', 0)},
                            recommendation="Investigate data source for missing values",
                        )
                        self.session.add(issue)
                        new_anomalies += 1

            if run_red_flag_scan:
                # For red flag scanning, we can check some metrics from stored stats
                red_flag_scanner = RedFlagScanner()

                # Check for suspicious patterns in column statistics
                for col in columns:
                    col_name = col.get('name', '').lower()

                    # Check revenue-related columns for negative min values
                    if any(kw in col_name for kw in ['revenue', 'sales', 'income']):
                        min_val = col.get('min_value')
                        if min_val is not None:
                            try:
                                if float(min_val.replace('$', '').replace(',', '')) < 0:
                                    issue = IngestionIssue(
                                        file_id=file.id,
                                        deal_id=file.deal_id,
                                        issue_type=IssueType.RED_FLAG,
                                        severity=IssueSeverity.CRITICAL,
                                        category='financial',
                                        sheet_name=sheet_name,
                                        column_name=col.get('name', ''),
                                        title=f"Negative values detected in '{col.get('name', '')}'",
                                        description="Revenue/sales columns should not contain negative values",
                                        details={'min_value': min_val},
                                        recommendation="Verify negative values against source documents",
                                    )
                                    self.session.add(issue)
                                    new_red_flags += 1
                            except (ValueError, AttributeError):
                                pass

        self.session.commit()

        # Get total issue count
        total_issues = self.session.exec(
            select(func.count(IngestionIssue.id)).where(IngestionIssue.file_id == file_id)
        ).one()

        return ReAnalyzeResponse(
            file_id=str(file_id),
            new_anomalies=new_anomalies,
            new_red_flags=new_red_flags,
            total_issues=total_issues,
            analysis_summary=(
                f"Re-analysis complete. Found {new_anomalies} new anomalies and "
                f"{new_red_flags} new red flags. Total issues: {total_issues}."
            ),
        )

    def _file_to_response(self, file: IngestedFile) -> IngestedFileResponse:
        """Convert file to response"""
        deal_name = None
        if file.deal_id:
            deal = self.session.get(PEDeal, file.deal_id)
            deal_name = deal.name if deal else None

        issue_count = self.session.exec(
            select(func.count(IngestionIssue.id)).where(IngestionIssue.file_id == file.id)
        ).one()

        return IngestedFileResponse(
            id=str(file.id),
            deal_id=str(file.deal_id) if file.deal_id else None,
            deal_name=deal_name,
            filename=file.filename,
            original_filename=file.original_filename,
            file_type=file.file_type,
            file_size_bytes=file.file_size_bytes,
            upload_source=file.upload_source,
            quality_score=file.quality_score,
            row_count=file.row_count,
            column_count=file.column_count,
            sheet_count=file.sheet_count,
            detected_categories=file.detected_categories or [],
            status=file.status,
            issue_count=issue_count,
            uploaded_by=file.uploaded_by,
            uploaded_at=file.uploaded_at,
            analyzed_at=file.analyzed_at,
        )

    def _file_to_detail(self, file: IngestedFile) -> IngestedFileDetail:
        """Convert file to detailed response"""
        deal_name = None
        if file.deal_id:
            deal = self.session.get(PEDeal, file.deal_id)
            deal_name = deal.name if deal else None

        # Get issues
        issues = self.session.exec(
            select(IngestionIssue)
            .where(IngestionIssue.file_id == file.id)
            .order_by(desc(IngestionIssue.severity))
        ).all()

        return IngestedFileDetail(
            id=str(file.id),
            deal_id=str(file.deal_id) if file.deal_id else None,
            deal_name=deal_name,
            filename=file.filename,
            original_filename=file.original_filename,
            file_type=file.file_type,
            file_size_bytes=file.file_size_bytes,
            content_hash=file.content_hash,
            upload_source=file.upload_source,
            source_system=file.source_system,
            quality_score=file.quality_score,
            row_count=file.row_count,
            column_count=file.column_count,
            sheet_count=file.sheet_count,
            detected_categories=file.detected_categories or [],
            schema_analysis=file.schema_analysis,
            analysis_summary=file.analysis_summary,
            status=file.status,
            error_message=file.error_message,
            issues=[self._issue_to_response(i) for i in issues],
            uploaded_by=file.uploaded_by,
            uploaded_at=file.uploaded_at,
            analyzed_at=file.analyzed_at,
        )

    # --- Issues ---

    def get_issue(self, issue_id: UUID) -> Optional[IssueResponse]:
        """Get an issue by ID"""
        issue = self.session.get(IngestionIssue, issue_id)
        if not issue:
            return None
        return self._issue_to_response(issue)

    def list_issues(
        self,
        file_id: Optional[UUID] = None,
        deal_id: Optional[UUID] = None,
        severity: Optional[str] = None,
        issue_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[IssueResponse]:
        """List issues with filters"""
        stmt = select(IngestionIssue).order_by(
            desc(IngestionIssue.severity),
            desc(IngestionIssue.created_at),
        )

        if file_id:
            stmt = stmt.where(IngestionIssue.file_id == file_id)
        if deal_id:
            stmt = stmt.where(IngestionIssue.deal_id == deal_id)
        if severity:
            stmt = stmt.where(IngestionIssue.severity == severity)
        if issue_type:
            stmt = stmt.where(IngestionIssue.issue_type == issue_type)
        if status:
            stmt = stmt.where(IngestionIssue.status == status)

        stmt = stmt.offset(offset).limit(limit)
        issues = self.session.exec(stmt).all()

        return [self._issue_to_response(i) for i in issues]

    def acknowledge_issue(
        self,
        issue_id: UUID,
        acknowledged_by: str,
        resolution_notes: Optional[str] = None,
        new_status: Optional[str] = None,
    ) -> Optional[IssueResponse]:
        """Acknowledge an issue"""
        issue = self.session.get(IngestionIssue, issue_id)
        if not issue:
            return None

        issue.acknowledged = True
        issue.acknowledged_by = acknowledged_by
        issue.acknowledged_at = datetime.utcnow()
        if resolution_notes:
            issue.resolution_notes = resolution_notes
        if new_status:
            issue.status = new_status
        else:
            issue.status = IssueStatus.ACKNOWLEDGED

        self.session.add(issue)
        self.session.commit()
        self.session.refresh(issue)

        return self._issue_to_response(issue)

    def get_issue_summary(
        self,
        file_id: Optional[UUID] = None,
        deal_id: Optional[UUID] = None,
    ) -> IssueSummary:
        """Get summary of issues"""
        base_stmt = select(IngestionIssue)
        if file_id:
            base_stmt = base_stmt.where(IngestionIssue.file_id == file_id)
        if deal_id:
            base_stmt = base_stmt.where(IngestionIssue.deal_id == deal_id)

        issues = self.session.exec(base_stmt).all()

        by_severity: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        unacknowledged = 0
        critical_count = 0

        for issue in issues:
            by_severity[issue.severity] = by_severity.get(issue.severity, 0) + 1
            by_type[issue.issue_type] = by_type.get(issue.issue_type, 0) + 1
            if not issue.acknowledged:
                unacknowledged += 1
            if issue.severity == IssueSeverity.CRITICAL:
                critical_count += 1

        return IssueSummary(
            total=len(issues),
            by_severity=by_severity,
            by_type=by_type,
            unacknowledged=unacknowledged,
            critical_count=critical_count,
        )

    def _issue_to_response(self, issue: IngestionIssue) -> IssueResponse:
        """Convert issue to response"""
        return IssueResponse(
            id=str(issue.id),
            file_id=str(issue.file_id),
            deal_id=str(issue.deal_id) if issue.deal_id else None,
            issue_type=issue.issue_type,
            severity=issue.severity,
            category=issue.category,
            sheet_name=issue.sheet_name,
            column_name=issue.column_name,
            row_number=issue.row_number,
            title=issue.title,
            description=issue.description,
            recommendation=issue.recommendation,
            status=issue.status,
            acknowledged=issue.acknowledged,
            acknowledged_by=issue.acknowledged_by,
            acknowledged_at=issue.acknowledged_at,
            created_at=issue.created_at,
        )
