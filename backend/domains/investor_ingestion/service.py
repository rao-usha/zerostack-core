"""
Investor Ingestion Service

Core logic for ingesting FO/LP data from uploaded files.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from contextlib import contextmanager

import pandas as pd
import psycopg
from sqlmodel import Session, select

from db_session import get_sync_engine
from ..data_explorer.db_configs import get_database_config_by_id
from .models import (
    IngestionStatus,
    TargetEntityType,
    FieldMapping,
    IngestionError,
    IngestionJobSummary,
    IngestionJobDetail,
    MappingTemplate,
    UploadPreviewResponse,
    ColumnPreview,
    MappingSuggestion,
)
from .db_models import IngestionJob, MappingTemplateDB
from .file_parser import FileParser
from .field_mapper import FieldMapper, ENTITY_TABLE_MAP

logger = logging.getLogger(__name__)


@contextmanager
def get_writable_connection(db_id: str = "default"):
    """
    Get a writable database connection (not read-only).

    Args:
        db_id: Database configuration ID

    Yields:
        psycopg.Connection: Writable database connection
    """
    conn = None
    try:
        db_config = get_database_config_by_id(db_id)
        conn_string = f"host={db_config.host} port={db_config.port} user={db_config.user} password={db_config.password} dbname={db_config.database}"
        conn = psycopg.connect(conn_string)
        yield conn
    finally:
        if conn:
            conn.close()


class InvestorIngestionService:
    """Service for ingesting investor (FO/LP) data."""

    @staticmethod
    def preview_upload(
        file_content: bytes,
        filename: str,
        file_type: str = None
    ) -> UploadPreviewResponse:
        """
        Preview an uploaded file and suggest mappings.

        Args:
            file_content: Raw file bytes
            filename: Original filename
            file_type: MIME type

        Returns:
            UploadPreviewResponse with preview data and suggestions
        """
        # Parse file
        sheets = FileParser.parse_file(file_content, filename, file_type)

        if not sheets:
            raise ValueError("No data found in file")

        # Use first sheet
        sheet_name, df = sheets[0]

        # Get column previews
        columns = FileParser.get_column_preview(df)
        column_previews = [
            ColumnPreview(
                name=c["name"],
                inferred_type=c["inferred_type"],
                sample_values=c["sample_values"],
                null_count=c["null_count"],
                unique_count=c["unique_count"]
            )
            for c in columns
        ]

        # Get sample data
        sample_data = FileParser.get_sample_data(df)

        # Suggest entity type
        column_names = [c["name"] for c in columns]
        suggested_entity = FieldMapper.suggest_entity_type(column_names)

        # Suggest mappings if entity type detected
        mapping_suggestions = []
        if suggested_entity:
            mapping_suggestions = FieldMapper.suggest_mappings(
                column_names,
                suggested_entity
            )

        return UploadPreviewResponse(
            filename=filename,
            file_size_bytes=len(file_content),
            total_rows=len(df),
            total_columns=len(df.columns),
            columns=column_previews,
            sample_data=sample_data,
            suggested_entity=suggested_entity,
            mapping_suggestions=mapping_suggestions
        )

    @staticmethod
    def create_job(
        file_content: bytes,
        filename: str,
        file_type: str,
        target_entity: TargetEntityType,
        field_mappings: List[FieldMapping],
        parent_id: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None
    ) -> IngestionJob:
        """
        Create a new ingestion job.

        Args:
            file_content: Raw file bytes
            filename: Original filename
            file_type: MIME type
            target_entity: Target entity type
            field_mappings: Field mappings to use
            parent_id: Parent entity ID (e.g., family_office_id)
            options: Additional options
            created_by: User who created the job

        Returns:
            Created IngestionJob
        """
        # Parse to get row count
        sheets = FileParser.parse_file(file_content, filename, file_type)
        if not sheets:
            raise ValueError("No data found in file")

        _, df = sheets[0]

        # Create job record
        job = IngestionJob(
            id=uuid4(),
            filename=f"investor_upload_{uuid4().hex[:8]}",
            original_filename=filename,
            file_type=file_type,
            file_size_bytes=len(file_content),
            target_entity=target_entity.value,
            parent_id=parent_id,
            field_mappings=[fm.model_dump() for fm in field_mappings],
            status=IngestionStatus.PENDING.value,
            total_rows=len(df),
            rows_processed=0,
            rows_inserted=0,
            rows_updated=0,
            rows_failed=0,
            options=options or {},
            created_by=created_by,
            created_at=datetime.utcnow()
        )

        # Save to database
        engine = get_sync_engine()
        with Session(engine) as session:
            session.add(job)
            session.commit()
            session.refresh(job)

        return job

    @staticmethod
    def process_job(
        job_id: UUID,
        file_content: bytes,
        db_id: str = "default"
    ) -> IngestionJobDetail:
        """
        Process an ingestion job.

        Args:
            job_id: Job ID
            file_content: File content bytes
            db_id: Target database ID

        Returns:
            Updated job detail
        """
        engine = get_sync_engine()

        with Session(engine) as session:
            # Get job
            job = session.get(IngestionJob, job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            # Update status
            job.status = IngestionStatus.PROCESSING.value
            job.started_at = datetime.utcnow()
            session.commit()

            try:
                # Parse file
                sheets = FileParser.parse_file(
                    file_content,
                    job.original_filename,
                    job.file_type
                )

                if not sheets:
                    raise ValueError("No data found in file")

                _, df = sheets[0]

                # Process rows
                errors = []
                rows_inserted = 0
                rows_updated = 0
                rows_failed = 0

                # Get target table
                target_entity = TargetEntityType(job.target_entity)
                table_name = ENTITY_TABLE_MAP.get(target_entity)

                if not table_name:
                    raise ValueError(f"Unknown target entity: {job.target_entity}")

                # Build field mappings dict
                mappings = {
                    fm["source_field"]: fm
                    for fm in job.field_mappings
                }

                # Process each row
                with get_writable_connection(db_id) as conn:
                    with conn.cursor() as cur:
                        for idx, row in df.iterrows():
                            try:
                                # Apply mappings
                                record = InvestorIngestionService._apply_mappings(
                                    row, mappings, target_entity, job.parent_id
                                )

                                if not record:
                                    rows_failed += 1
                                    continue

                                # Insert row
                                columns = list(record.keys())
                                values = list(record.values())
                                placeholders = ", ".join(["%s"] * len(values))
                                col_names = ", ".join(columns)

                                insert_sql = f"""
                                    INSERT INTO {table_name} ({col_names})
                                    VALUES ({placeholders})
                                """
                                cur.execute(insert_sql, values)
                                rows_inserted += 1

                            except Exception as e:
                                rows_failed += 1
                                errors.append({
                                    "row_number": idx + 2,  # +2 for header and 0-index
                                    "error_type": type(e).__name__,
                                    "message": str(e)
                                })

                                if len(errors) >= 100:
                                    break

                        conn.commit()

                # Update job with results
                job.status = IngestionStatus.COMPLETED.value
                job.rows_processed = len(df)
                job.rows_inserted = rows_inserted
                job.rows_updated = rows_updated
                job.rows_failed = rows_failed
                job.errors = errors[:100] if errors else None
                job.completed_at = datetime.utcnow()
                session.commit()

            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}")
                job.status = IngestionStatus.FAILED.value
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                session.commit()
                raise

            return InvestorIngestionService._job_to_detail(job)

    @staticmethod
    def get_job(job_id: UUID) -> Optional[IngestionJobDetail]:
        """Get an ingestion job by ID."""
        engine = get_sync_engine()

        with Session(engine) as session:
            job = session.get(IngestionJob, job_id)
            if not job:
                return None
            return InvestorIngestionService._job_to_detail(job)

    @staticmethod
    def list_jobs(
        page: int = 1,
        page_size: int = 50,
        status: Optional[str] = None,
        target_entity: Optional[str] = None
    ) -> Tuple[List[IngestionJobSummary], int]:
        """
        List ingestion jobs with filtering.

        Args:
            page: Page number
            page_size: Items per page
            status: Filter by status
            target_entity: Filter by target entity

        Returns:
            Tuple of (jobs, total count)
        """
        engine = get_sync_engine()

        with Session(engine) as session:
            # Build query
            query = select(IngestionJob)

            if status:
                query = query.where(IngestionJob.status == status)
            if target_entity:
                query = query.where(IngestionJob.target_entity == target_entity)

            query = query.order_by(IngestionJob.created_at.desc())

            # Get total count
            count_query = select(IngestionJob)
            if status:
                count_query = count_query.where(IngestionJob.status == status)
            if target_entity:
                count_query = count_query.where(IngestionJob.target_entity == target_entity)

            all_jobs = session.exec(count_query).all()
            total = len(all_jobs)

            # Paginate
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

            jobs = session.exec(query).all()

            summaries = [
                IngestionJobSummary(
                    id=str(job.id),
                    filename=job.original_filename,
                    target_entity=job.target_entity,
                    status=IngestionStatus(job.status),
                    total_rows=job.total_rows,
                    rows_processed=job.rows_processed,
                    rows_inserted=job.rows_inserted,
                    rows_updated=job.rows_updated,
                    rows_failed=job.rows_failed,
                    created_at=job.created_at,
                    completed_at=job.completed_at
                )
                for job in jobs
            ]

            return summaries, total

    @staticmethod
    def _apply_mappings(
        row: pd.Series,
        mappings: Dict[str, Dict[str, Any]],
        target_entity: TargetEntityType,
        parent_id: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """Apply field mappings to a row."""
        record = {}

        # Add parent ID if applicable
        if parent_id:
            parent_field = InvestorIngestionService._get_parent_field(target_entity)
            if parent_field:
                record[parent_field] = parent_id

        for source_field, mapping in mappings.items():
            if source_field not in row.index:
                # Use default value if specified
                if mapping.get("default_value") is not None:
                    record[mapping["target_field"]] = mapping["default_value"]
                continue

            value = row[source_field]

            # Handle null values
            if pd.isna(value):
                if mapping.get("default_value") is not None:
                    record[mapping["target_field"]] = mapping["default_value"]
                continue

            # Apply transform if specified
            transform = mapping.get("transform")
            if transform:
                value = InvestorIngestionService._apply_transform(value, transform)

            record[mapping["target_field"]] = value

        return record if record else None

    @staticmethod
    def _get_parent_field(target_entity: TargetEntityType) -> Optional[str]:
        """Get the parent foreign key field for an entity type."""
        parent_fields = {
            TargetEntityType.FO_CONTACT: "family_office_id",
            TargetEntityType.FO_INTERACTION: "family_office_id",
            TargetEntityType.CO_INVESTMENT: "family_office_id",
            TargetEntityType.PORTFOLIO_COMPANY: "family_office_id",
            TargetEntityType.INVESTOR_THEME: "family_office_id",
            TargetEntityType.IMPACT_ANALYSIS: "family_office_id",
            TargetEntityType.LP_CONTACT: "fund_id",
            TargetEntityType.LP_DOCUMENT: "fund_id",
            TargetEntityType.LP_ALLOCATION: "fund_id",
            TargetEntityType.LP_EXPOSURE: "fund_id",
        }
        return parent_fields.get(target_entity)

    @staticmethod
    def _apply_transform(value: Any, transform: str) -> Any:
        """Apply a transformation to a value."""
        if transform == "uppercase":
            return str(value).upper()
        elif transform == "lowercase":
            return str(value).lower()
        elif transform == "strip":
            return str(value).strip()
        elif transform == "date_parse":
            return pd.to_datetime(value).date()
        elif transform == "float":
            return float(value)
        elif transform == "int":
            return int(float(value))
        return value

    @staticmethod
    def _job_to_detail(job: IngestionJob) -> IngestionJobDetail:
        """Convert IngestionJob to IngestionJobDetail."""
        return IngestionJobDetail(
            id=str(job.id),
            filename=job.filename,
            original_filename=job.original_filename,
            file_size_bytes=job.file_size_bytes,
            target_entity=job.target_entity,
            status=IngestionStatus(job.status),
            total_rows=job.total_rows,
            rows_processed=job.rows_processed,
            rows_inserted=job.rows_inserted,
            rows_updated=job.rows_updated,
            rows_failed=job.rows_failed,
            field_mappings=[
                FieldMapping(**fm) for fm in (job.field_mappings or [])
            ],
            errors=[
                IngestionError(
                    row_number=e.get("row_number", 0),
                    field=e.get("field"),
                    error_type=e.get("error_type", "unknown"),
                    message=e.get("message", ""),
                    raw_value=e.get("raw_value")
                )
                for e in (job.errors or [])
            ],
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message
        )

    # ========================================
    # Template Management
    # ========================================

    @staticmethod
    def save_template(
        name: str,
        target_entity: TargetEntityType,
        field_mappings: List[FieldMapping],
        created_by: Optional[str] = None
    ) -> MappingTemplate:
        """Save a field mapping template."""
        engine = get_sync_engine()

        template = MappingTemplateDB(
            id=uuid4(),
            name=name,
            target_entity=target_entity.value,
            field_mappings=[fm.model_dump() for fm in field_mappings],
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        with Session(engine) as session:
            session.add(template)
            session.commit()
            session.refresh(template)

        return MappingTemplate(
            id=str(template.id),
            name=template.name,
            target_entity=TargetEntityType(template.target_entity),
            field_mappings=[FieldMapping(**fm) for fm in template.field_mappings],
            created_at=template.created_at,
            updated_at=template.updated_at
        )

    @staticmethod
    def list_templates(
        target_entity: Optional[TargetEntityType] = None
    ) -> List[MappingTemplate]:
        """List saved mapping templates."""
        engine = get_sync_engine()

        with Session(engine) as session:
            query = select(MappingTemplateDB)

            if target_entity:
                query = query.where(
                    MappingTemplateDB.target_entity == target_entity.value
                )

            query = query.order_by(MappingTemplateDB.name)
            templates = session.exec(query).all()

            return [
                MappingTemplate(
                    id=str(t.id),
                    name=t.name,
                    target_entity=TargetEntityType(t.target_entity),
                    field_mappings=[FieldMapping(**fm) for fm in t.field_mappings],
                    created_at=t.created_at,
                    updated_at=t.updated_at
                )
                for t in templates
            ]

    @staticmethod
    def get_template(template_id: UUID) -> Optional[MappingTemplate]:
        """Get a mapping template by ID."""
        engine = get_sync_engine()

        with Session(engine) as session:
            template = session.get(MappingTemplateDB, template_id)
            if not template:
                return None

            return MappingTemplate(
                id=str(template.id),
                name=template.name,
                target_entity=TargetEntityType(template.target_entity),
                field_mappings=[FieldMapping(**fm) for fm in template.field_mappings],
                created_at=template.created_at,
                updated_at=template.updated_at
            )
