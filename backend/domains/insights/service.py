"""Insights service with database persistence."""
from typing import Optional, List, Tuple
from uuid import UUID, uuid4
from datetime import datetime
import pandas as pd

from sqlmodel import Session, select, func
from db_session import get_session_context

from services.insights import InsightsGenerator
from domains.insights.db_models import InsightReport
from domains.insights.models import (
    InsightGenerateRequest,
    InsightReportResponse,
    InsightListItem,
    InsightListResponse,
)
from domains.datasets.storage import get_dataset_storage
from domains.datasets.db_models import datasets as datasets_table


class InsightsService:
    """Service for generating and persisting insights."""

    def __init__(self):
        self.generator = InsightsGenerator()

    def generate_insights(
        self,
        request: InsightGenerateRequest,
        session: Session,
    ) -> InsightReportResponse:
        """
        Generate insights for a dataset and optionally persist.

        Args:
            request: The insight generation request
            session: Database session

        Returns:
            InsightReportResponse with all generated insights
        """
        # Load the dataset
        df = self._load_dataset(request.dataset_id, session)

        # Generate insights using the existing generator
        insights_data = self.generator.generate(df, request.context)

        # Create report ID
        report_id = uuid4()
        now = datetime.utcnow()

        # Build title
        title = request.title or f"Insights Report - {now.strftime('%Y-%m-%d %H:%M')}"

        # Create database model if persisting
        if request.persist:
            report = InsightReport(
                id=report_id,
                dataset_id=request.dataset_id,
                title=title,
                context=request.context,
                performance_score=insights_data.get("performance_score", {}),
                executive_kpis=insights_data.get("executive_kpis", []),
                trend_data=insights_data.get("trend_data", []),
                growth_metrics=insights_data.get("growth_metrics", {}),
                risk_indicators=insights_data.get("risk_indicators", []),
                distribution_data=insights_data.get("distribution_data", {}),
                recommendations=insights_data.get("recommendations", []),
                summary=insights_data.get("summary", ""),
                trends=insights_data.get("trends", []),
                anomalies=insights_data.get("anomalies", []),
                correlations=insights_data.get("correlations", []),
                key_metrics=insights_data.get("key_metrics", {}),
                created_at=now,
                updated_at=now,
            )
            session.add(report)
            session.commit()
            session.refresh(report)

        # Return response
        return InsightReportResponse(
            id=report_id,
            dataset_id=request.dataset_id,
            title=title,
            context=request.context,
            performance_score=insights_data.get("performance_score", {}),
            executive_kpis=insights_data.get("executive_kpis", []),
            trend_data=insights_data.get("trend_data", []),
            growth_metrics=insights_data.get("growth_metrics", {}),
            risk_indicators=insights_data.get("risk_indicators", []),
            distribution_data=insights_data.get("distribution_data", {}),
            recommendations=insights_data.get("recommendations", []),
            summary=insights_data.get("summary", ""),
            trends=insights_data.get("trends", []),
            anomalies=insights_data.get("anomalies", []),
            correlations=insights_data.get("correlations", []),
            key_metrics=insights_data.get("key_metrics", {}),
            created_at=now,
            updated_at=now,
        )

    def get_insight(self, insight_id: UUID, session: Session) -> Optional[InsightReportResponse]:
        """
        Get an insight report by ID.

        Args:
            insight_id: The insight report ID
            session: Database session

        Returns:
            InsightReportResponse if found, None otherwise
        """
        report = session.get(InsightReport, insight_id)
        if not report:
            return None

        return InsightReportResponse.model_validate(report)

    def list_insights(
        self,
        session: Session,
        dataset_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> InsightListResponse:
        """
        List insight reports with pagination.

        Args:
            session: Database session
            dataset_id: Optional filter by dataset
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            InsightListResponse with paginated results
        """
        # Build base query
        query = select(InsightReport)
        count_query = select(func.count()).select_from(InsightReport)

        # Apply dataset filter if provided
        if dataset_id:
            query = query.where(InsightReport.dataset_id == dataset_id)
            count_query = count_query.where(InsightReport.dataset_id == dataset_id)

        # Get total count
        total = session.exec(count_query).one()

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = query.order_by(InsightReport.created_at.desc()).offset(offset).limit(page_size)

        # Execute query
        reports = session.exec(query).all()

        # Convert to list items
        items = [
            InsightListItem(
                id=r.id,
                dataset_id=r.dataset_id,
                title=r.title,
                context=r.context,
                summary=r.summary or "",
                created_at=r.created_at,
            )
            for r in reports
        ]

        return InsightListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def delete_insight(self, insight_id: UUID, session: Session) -> bool:
        """
        Delete an insight report.

        Args:
            insight_id: The insight report ID
            session: Database session

        Returns:
            True if deleted, False if not found
        """
        report = session.get(InsightReport, insight_id)
        if not report:
            return False

        session.delete(report)
        session.commit()
        return True

    def _load_dataset(self, dataset_id: UUID, session: Session) -> pd.DataFrame:
        """
        Load dataset from storage.

        Supports both new system (PostgreSQL + MinIO) and legacy SQLite.

        Args:
            dataset_id: The dataset ID
            session: Database session

        Returns:
            DataFrame with dataset data

        Raises:
            ValueError: If dataset not found
        """
        df = None

        # Try new dataset system first (PostgreSQL + MinIO)
        try:
            result = session.execute(
                datasets_table.select().where(datasets_table.c.id == dataset_id)
            )
            row = result.fetchone()

            if row:
                storage = get_dataset_storage()
                df = storage.read_dataframe(
                    dataset_id,
                    row.current_version_number or 1,
                    row.storage_format or "parquet"
                )
        except Exception:
            # New system failed, rollback and try legacy
            session.rollback()
            pass

        # Fall back to legacy SQLite system
        if df is None:
            try:
                from database import Database
                db = Database()
                dataset = db.get_dataset(str(dataset_id))
                if dataset is not None:
                    df = pd.read_json(dataset['data'], orient='records')
            except Exception:
                pass

        if df is None:
            raise ValueError(f"Dataset {dataset_id} not found")

        return df
