"""
LP Collection service layer.

Provides read-only access to LP data stored in the NexData database.
Uses the Data Explorer connection pattern for database access.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import date
from ..data_explorer.connection import get_explorer_connection
from .models import (
    LPFundSummary,
    LPFundDetail,
    LPKeyContact,
    LPDocumentSummary,
    LPDocumentDetail,
    LPDocumentTextSection,
    LPStrategySnapshot,
    LPStrategyThematicTag,
    LPAssetClassAllocation,
    LPAssetClassProjection,
    LPManagerExposure,
    LPCollectionStats,
    LPSearchFilters,
)


class LPCollectionService:
    """Service for accessing LP collection data."""

    # Default database ID for NexData
    DEFAULT_DB_ID = "default"

    @staticmethod
    def list_funds(
        filters: LPSearchFilters,
        db_id: str = None
    ) -> Tuple[List[LPFundSummary], int]:
        """
        List LP funds with filtering, pagination, and sorting.

        Args:
            filters: Search and filter parameters
            db_id: Database configuration ID

        Returns:
            Tuple of (list of fund summaries, total count)
        """
        db_id = db_id or LPCollectionService.DEFAULT_DB_ID

        # Build WHERE clauses
        where_clauses = []
        params = []

        if filters.lp_name:
            where_clauses.append("lp_name ILIKE %s")
            params.append(f"%{filters.lp_name}%")

        if filters.fund_name:
            where_clauses.append("fund_name ILIKE %s")
            params.append(f"%{filters.fund_name}%")

        if filters.fund_type:
            where_clauses.append("fund_type = %s")
            params.append(filters.fund_type)

        if filters.strategy:
            where_clauses.append("strategy ILIKE %s")
            params.append(f"%{filters.strategy}%")

        if filters.vintage_year:
            where_clauses.append("vintage_year = %s")
            params.append(filters.vintage_year)

        if filters.vintage_year_min:
            where_clauses.append("vintage_year >= %s")
            params.append(filters.vintage_year_min)

        if filters.vintage_year_max:
            where_clauses.append("vintage_year <= %s")
            params.append(filters.vintage_year_max)

        if filters.min_commitment:
            where_clauses.append("commitment >= %s")
            params.append(filters.min_commitment)

        if filters.max_commitment:
            where_clauses.append("commitment <= %s")
            params.append(filters.max_commitment)

        if filters.status:
            where_clauses.append("status = %s")
            params.append(filters.status)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Allowed sort columns for safety
        allowed_sort_columns = {
            "id", "fund_name", "lp_name", "commitment",
            "vintage_year", "strategy", "fund_type", "status"
        }
        sort_by = filters.sort_by if filters.sort_by in allowed_sort_columns else "fund_name"
        sort_order = "DESC" if filters.sort_desc else "ASC"

        # Calculate pagination
        offset = (filters.page - 1) * filters.page_size

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                # Get total count
                count_sql = f"SELECT COUNT(*) FROM lp_fund {where_sql}"
                cur.execute(count_sql, params)
                total = cur.fetchone()[0]

                # Get paginated results
                query_sql = f"""
                    SELECT
                        id, fund_name, lp_name, commitment, commitment_currency,
                        vintage_year, strategy, fund_type, status
                    FROM lp_fund
                    {where_sql}
                    ORDER BY {sort_by} {sort_order}
                    LIMIT %s OFFSET %s
                """
                cur.execute(query_sql, params + [filters.page_size, offset])
                rows = cur.fetchall()

        funds = [
            LPFundSummary(
                id=row[0],
                fund_name=row[1],
                lp_name=row[2],
                commitment=float(row[3]) if row[3] else None,
                commitment_currency=row[4],
                vintage_year=row[5],
                strategy=row[6],
                fund_type=row[7],
                status=row[8]
            )
            for row in rows
        ]

        return funds, total

    @staticmethod
    def get_fund_detail(fund_id: int, db_id: str = None) -> Optional[LPFundDetail]:
        """
        Get full detail for an LP fund including all related data.

        Args:
            fund_id: ID of the LP fund
            db_id: Database configuration ID

        Returns:
            Fund detail with nested contacts, documents, etc. or None if not found
        """
        db_id = db_id or LPCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                # Get fund details
                cur.execute("""
                    SELECT
                        id, fund_name, lp_name, commitment, commitment_currency,
                        vintage_year, strategy, fund_type, status, description,
                        aum, headquarters, website, created_at, updated_at
                    FROM lp_fund
                    WHERE id = %s
                """, (fund_id,))
                row = cur.fetchone()

                if not row:
                    return None

                fund = LPFundDetail(
                    id=row[0],
                    fund_name=row[1],
                    lp_name=row[2],
                    commitment=float(row[3]) if row[3] else None,
                    commitment_currency=row[4],
                    vintage_year=row[5],
                    strategy=row[6],
                    fund_type=row[7],
                    status=row[8],
                    description=row[9],
                    aum=float(row[10]) if row[10] else None,
                    headquarters=row[11],
                    website=row[12],
                    created_at=row[13],
                    updated_at=row[14],
                    contacts=[],
                    documents=[],
                    strategy_snapshots=[],
                    allocations=[],
                    projections=[],
                    exposures=[]
                )

                # Get related contacts
                fund.contacts = LPCollectionService.get_fund_contacts(fund_id, db_id)

                # Get related documents (summaries only for detail view)
                docs, _ = LPCollectionService.get_fund_documents(fund_id, db_id)
                fund.documents = docs

                # Get strategy snapshots
                fund.strategy_snapshots = LPCollectionService._get_fund_strategy_snapshots(
                    fund_id, cur
                )

                # Get allocations
                fund.allocations = LPCollectionService.get_fund_allocations(fund_id, db_id)

                # Get projections
                fund.projections = LPCollectionService._get_fund_projections(fund_id, cur)

                # Get exposures
                fund.exposures = LPCollectionService.get_fund_exposures(fund_id, db_id)

        return fund

    @staticmethod
    def get_fund_contacts(fund_id: int, db_id: str = None) -> List[LPKeyContact]:
        """
        Get contacts for an LP fund.

        Args:
            fund_id: ID of the LP fund
            db_id: Database configuration ID

        Returns:
            List of contacts
        """
        db_id = db_id or LPCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        id, fund_id, name, title, email, phone,
                        role, is_primary, notes
                    FROM lp_key_contact
                    WHERE fund_id = %s
                    ORDER BY is_primary DESC, name ASC
                """, (fund_id,))
                rows = cur.fetchall()

        return [
            LPKeyContact(
                id=row[0],
                fund_id=row[1],
                name=row[2],
                title=row[3],
                email=row[4],
                phone=row[5],
                role=row[6],
                is_primary=row[7],
                notes=row[8]
            )
            for row in rows
        ]

    @staticmethod
    def get_fund_documents(
        fund_id: int,
        db_id: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[LPDocumentSummary], int]:
        """
        Get documents for an LP fund.

        Args:
            fund_id: ID of the LP fund
            db_id: Database configuration ID
            limit: Maximum number of documents to return
            offset: Number of documents to skip

        Returns:
            Tuple of (list of documents, total count)
        """
        db_id = db_id or LPCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                # Get total count
                cur.execute(
                    "SELECT COUNT(*) FROM lp_document WHERE fund_id = %s",
                    (fund_id,)
                )
                total = cur.fetchone()[0]

                # Get paginated documents
                cur.execute("""
                    SELECT
                        id, fund_id, document_type, document_name,
                        document_date, source_url, created_at
                    FROM lp_document
                    WHERE fund_id = %s
                    ORDER BY document_date DESC NULLS LAST, created_at DESC
                    LIMIT %s OFFSET %s
                """, (fund_id, limit, offset))
                rows = cur.fetchall()

        documents = [
            LPDocumentSummary(
                id=row[0],
                fund_id=row[1],
                document_type=row[2],
                document_name=row[3],
                document_date=row[4],
                source_url=row[5],
                created_at=row[6]
            )
            for row in rows
        ]

        return documents, total

    @staticmethod
    def get_document_detail(doc_id: int, db_id: str = None) -> Optional[LPDocumentDetail]:
        """
        Get full document detail with text sections.

        Args:
            doc_id: ID of the document
            db_id: Database configuration ID

        Returns:
            Document detail with text sections or None if not found
        """
        db_id = db_id or LPCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                # Get document
                cur.execute("""
                    SELECT
                        id, fund_id, document_type, document_name,
                        document_date, source_url, created_at
                    FROM lp_document
                    WHERE id = %s
                """, (doc_id,))
                row = cur.fetchone()

                if not row:
                    return None

                # Get text sections
                cur.execute("""
                    SELECT
                        id, document_id, section_name, section_text,
                        page_number, section_order
                    FROM lp_document_text_section
                    WHERE document_id = %s
                    ORDER BY section_order ASC, page_number ASC
                """, (doc_id,))
                section_rows = cur.fetchall()

        text_sections = [
            LPDocumentTextSection(
                id=sr[0],
                document_id=sr[1],
                section_name=sr[2],
                section_text=sr[3],
                page_number=sr[4],
                section_order=sr[5]
            )
            for sr in section_rows
        ]

        return LPDocumentDetail(
            id=row[0],
            fund_id=row[1],
            document_type=row[2],
            document_name=row[3],
            document_date=row[4],
            source_url=row[5],
            created_at=row[6],
            text_sections=text_sections
        )

    @staticmethod
    def get_fund_allocations(fund_id: int, db_id: str = None) -> List[LPAssetClassAllocation]:
        """
        Get target allocations for an LP fund.

        Args:
            fund_id: ID of the LP fund
            db_id: Database configuration ID

        Returns:
            List of asset class allocations
        """
        db_id = db_id or LPCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        id, fund_id, asset_class, target_allocation,
                        current_allocation, min_allocation, max_allocation, as_of_date
                    FROM lp_asset_class_target_allocation
                    WHERE fund_id = %s
                    ORDER BY target_allocation DESC NULLS LAST
                """, (fund_id,))
                rows = cur.fetchall()

        return [
            LPAssetClassAllocation(
                id=row[0],
                fund_id=row[1],
                asset_class=row[2],
                target_allocation=float(row[3]) if row[3] else None,
                current_allocation=float(row[4]) if row[4] else None,
                min_allocation=float(row[5]) if row[5] else None,
                max_allocation=float(row[6]) if row[6] else None,
                as_of_date=row[7]
            )
            for row in rows
        ]

    @staticmethod
    def get_fund_exposures(fund_id: int, db_id: str = None) -> List[LPManagerExposure]:
        """
        Get manager/vehicle exposures for an LP fund.

        Args:
            fund_id: ID of the LP fund
            db_id: Database configuration ID

        Returns:
            List of manager exposures
        """
        db_id = db_id or LPCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        id, fund_id, manager_name, vehicle_name,
                        exposure_amount, exposure_percentage, asset_class,
                        strategy, vintage_year, as_of_date
                    FROM lp_manager_or_vehicle_exposure
                    WHERE fund_id = %s
                    ORDER BY exposure_amount DESC NULLS LAST
                """, (fund_id,))
                rows = cur.fetchall()

        return [
            LPManagerExposure(
                id=row[0],
                fund_id=row[1],
                manager_name=row[2],
                vehicle_name=row[3],
                exposure_amount=float(row[4]) if row[4] else None,
                exposure_percentage=float(row[5]) if row[5] else None,
                asset_class=row[6],
                strategy=row[7],
                vintage_year=row[8],
                as_of_date=row[9]
            )
            for row in rows
        ]

    @staticmethod
    def _get_fund_strategy_snapshots(
        fund_id: int,
        cur
    ) -> List[LPStrategySnapshot]:
        """
        Get strategy snapshots for an LP fund (internal helper).

        Args:
            fund_id: ID of the LP fund
            cur: Database cursor

        Returns:
            List of strategy snapshots with thematic tags
        """
        cur.execute("""
            SELECT
                id, fund_id, snapshot_date, strategy_name,
                allocation_percentage, target_return, risk_tolerance, notes
            FROM lp_strategy_snapshot
            WHERE fund_id = %s
            ORDER BY snapshot_date DESC NULLS LAST
        """, (fund_id,))
        rows = cur.fetchall()

        snapshots = []
        for row in rows:
            snapshot = LPStrategySnapshot(
                id=row[0],
                fund_id=row[1],
                snapshot_date=row[2],
                strategy_name=row[3],
                allocation_percentage=float(row[4]) if row[4] else None,
                target_return=float(row[5]) if row[5] else None,
                risk_tolerance=row[6],
                notes=row[7],
                thematic_tags=[]
            )

            # Get thematic tags for this snapshot
            cur.execute("""
                SELECT
                    id, strategy_snapshot_id, tag_name, tag_category, weight
                FROM lp_strategy_thematic_tag
                WHERE strategy_snapshot_id = %s
                ORDER BY weight DESC NULLS LAST, tag_name ASC
            """, (row[0],))
            tag_rows = cur.fetchall()

            snapshot.thematic_tags = [
                LPStrategyThematicTag(
                    id=tr[0],
                    strategy_snapshot_id=tr[1],
                    tag_name=tr[2],
                    tag_category=tr[3],
                    weight=float(tr[4]) if tr[4] else None
                )
                for tr in tag_rows
            ]

            snapshots.append(snapshot)

        return snapshots

    @staticmethod
    def _get_fund_projections(fund_id: int, cur) -> List[LPAssetClassProjection]:
        """
        Get asset class projections for an LP fund (internal helper).

        Args:
            fund_id: ID of the LP fund
            cur: Database cursor

        Returns:
            List of asset class projections
        """
        cur.execute("""
            SELECT
                id, fund_id, asset_class, projection_date,
                projected_allocation, confidence_level, scenario
            FROM lp_asset_class_projection
            WHERE fund_id = %s
            ORDER BY projection_date ASC
        """, (fund_id,))
        rows = cur.fetchall()

        return [
            LPAssetClassProjection(
                id=row[0],
                fund_id=row[1],
                asset_class=row[2],
                projection_date=row[3],
                projected_allocation=float(row[4]) if row[4] else None,
                confidence_level=row[5],
                scenario=row[6]
            )
            for row in rows
        ]

    @staticmethod
    def get_stats(db_id: str = None) -> LPCollectionStats:
        """
        Get aggregate statistics for the LP collection.

        Args:
            db_id: Database configuration ID

        Returns:
            Collection statistics
        """
        db_id = db_id or LPCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                # Total funds
                cur.execute("SELECT COUNT(*) FROM lp_fund")
                total_funds = cur.fetchone()[0]

                # Total contacts
                cur.execute("SELECT COUNT(*) FROM lp_key_contact")
                total_contacts = cur.fetchone()[0]

                # Total documents
                cur.execute("SELECT COUNT(*) FROM lp_document")
                total_documents = cur.fetchone()[0]

                # Total commitment (assuming USD as default)
                cur.execute("""
                    SELECT
                        SUM(commitment),
                        commitment_currency
                    FROM lp_fund
                    WHERE commitment IS NOT NULL
                    GROUP BY commitment_currency
                    ORDER BY SUM(commitment) DESC
                    LIMIT 1
                """)
                commit_row = cur.fetchone()
                total_commitment = float(commit_row[0]) if commit_row and commit_row[0] else None
                commitment_currency = commit_row[1] if commit_row else None

                # Funds by strategy
                cur.execute("""
                    SELECT strategy, COUNT(*)
                    FROM lp_fund
                    WHERE strategy IS NOT NULL
                    GROUP BY strategy
                    ORDER BY COUNT(*) DESC
                """)
                funds_by_strategy = {row[0]: row[1] for row in cur.fetchall()}

                # Funds by vintage year
                cur.execute("""
                    SELECT vintage_year, COUNT(*)
                    FROM lp_fund
                    WHERE vintage_year IS NOT NULL
                    GROUP BY vintage_year
                    ORDER BY vintage_year DESC
                """)
                funds_by_vintage = {str(row[0]): row[1] for row in cur.fetchall()}

                # Funds by status
                cur.execute("""
                    SELECT status, COUNT(*)
                    FROM lp_fund
                    WHERE status IS NOT NULL
                    GROUP BY status
                    ORDER BY COUNT(*) DESC
                """)
                funds_by_status = {row[0]: row[1] for row in cur.fetchall()}

        return LPCollectionStats(
            total_funds=total_funds,
            total_contacts=total_contacts,
            total_documents=total_documents,
            total_commitment=total_commitment,
            total_commitment_currency=commitment_currency,
            funds_by_strategy=funds_by_strategy,
            funds_by_vintage=funds_by_vintage,
            funds_by_status=funds_by_status
        )

    @staticmethod
    def fund_exists(fund_id: int, db_id: str = None) -> bool:
        """
        Check if an LP fund exists.

        Args:
            fund_id: ID of the LP fund
            db_id: Database configuration ID

        Returns:
            True if fund exists, False otherwise
        """
        db_id = db_id or LPCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT EXISTS(SELECT 1 FROM lp_fund WHERE id = %s)",
                    (fund_id,)
                )
                return cur.fetchone()[0]
