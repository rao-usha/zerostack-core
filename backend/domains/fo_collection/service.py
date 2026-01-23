"""
FO (Family Office) Collection service layer.

Provides read-only access to Family Office data stored in the NexData database.
Uses the Data Explorer connection pattern for database access.
"""
from typing import List, Optional, Tuple
from ..data_explorer.connection import get_explorer_connection
from .models import (
    FamilyOfficeSummary,
    FamilyOfficeDetail,
    FOContact,
    FOInteraction,
    CoInvestment,
    PortfolioCompany,
    InvestorTheme,
    ImpactAnalysis,
    FOCollectionStats,
    FOSearchFilters,
)


class FOCollectionService:
    """Service for accessing Family Office collection data."""

    # Default database ID for NexData
    DEFAULT_DB_ID = "default"

    @staticmethod
    def list_offices(
        filters: FOSearchFilters,
        db_id: str = None
    ) -> Tuple[List[FamilyOfficeSummary], int]:
        """
        List family offices with filtering, pagination, and sorting.

        Args:
            filters: Search and filter parameters
            db_id: Database configuration ID

        Returns:
            Tuple of (list of office summaries, total count)
        """
        db_id = db_id or FOCollectionService.DEFAULT_DB_ID

        # Build WHERE clauses
        where_clauses = []
        params = []

        if filters.name:
            where_clauses.append("name ILIKE %s")
            params.append(f"%{filters.name}%")

        if filters.family_name:
            where_clauses.append("family_name ILIKE %s")
            params.append(f"%{filters.family_name}%")

        if filters.headquarters:
            where_clauses.append("headquarters ILIKE %s")
            params.append(f"%{filters.headquarters}%")

        if filters.office_type:
            where_clauses.append("office_type = %s")
            params.append(filters.office_type)

        if filters.investment_focus:
            where_clauses.append("investment_focus ILIKE %s")
            params.append(f"%{filters.investment_focus}%")

        if filters.min_aum:
            where_clauses.append("aum >= %s")
            params.append(filters.min_aum)

        if filters.max_aum:
            where_clauses.append("aum <= %s")
            params.append(filters.max_aum)

        if filters.status:
            where_clauses.append("status = %s")
            params.append(filters.status)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Allowed sort columns for safety
        allowed_sort_columns = {
            "id", "name", "family_name", "aum",
            "headquarters", "office_type", "status"
        }
        sort_by = filters.sort_by if filters.sort_by in allowed_sort_columns else "name"
        sort_order = "DESC" if filters.sort_desc else "ASC"

        # Calculate pagination
        offset = (filters.page - 1) * filters.page_size

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                # Get total count
                count_sql = f"SELECT COUNT(*) FROM family_offices {where_sql}"
                cur.execute(count_sql, params)
                total = cur.fetchone()[0]

                # Get paginated results
                query_sql = f"""
                    SELECT
                        id, name, aum, aum_currency, headquarters,
                        family_name, office_type, investment_focus, status
                    FROM family_offices
                    {where_sql}
                    ORDER BY {sort_by} {sort_order}
                    LIMIT %s OFFSET %s
                """
                cur.execute(query_sql, params + [filters.page_size, offset])
                rows = cur.fetchall()

        offices = [
            FamilyOfficeSummary(
                id=row[0],
                name=row[1],
                aum=float(row[2]) if row[2] else None,
                aum_currency=row[3],
                headquarters=row[4],
                family_name=row[5],
                office_type=row[6],
                investment_focus=row[7],
                status=row[8]
            )
            for row in rows
        ]

        return offices, total

    @staticmethod
    def get_office_detail(office_id: int, db_id: str = None) -> Optional[FamilyOfficeDetail]:
        """
        Get full detail for a family office including all related data.

        Args:
            office_id: ID of the family office
            db_id: Database configuration ID

        Returns:
            Office detail with nested contacts, interactions, etc. or None if not found
        """
        db_id = db_id or FOCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                # Get office details
                cur.execute("""
                    SELECT
                        id, name, aum, aum_currency, headquarters,
                        family_name, office_type, investment_focus, status,
                        description, founded_year, website, linkedin,
                        investment_horizon, min_investment, max_investment,
                        created_at, updated_at
                    FROM family_offices
                    WHERE id = %s
                """, (office_id,))
                row = cur.fetchone()

                if not row:
                    return None

                office = FamilyOfficeDetail(
                    id=row[0],
                    name=row[1],
                    aum=float(row[2]) if row[2] else None,
                    aum_currency=row[3],
                    headquarters=row[4],
                    family_name=row[5],
                    office_type=row[6],
                    investment_focus=row[7],
                    status=row[8],
                    description=row[9],
                    founded_year=row[10],
                    website=row[11],
                    linkedin=row[12],
                    investment_horizon=row[13],
                    min_investment=float(row[14]) if row[14] else None,
                    max_investment=float(row[15]) if row[15] else None,
                    created_at=row[16],
                    updated_at=row[17],
                    contacts=[],
                    interactions=[],
                    co_investments=[],
                    portfolio_companies=[],
                    themes=[]
                )

                # Get related contacts
                office.contacts = FOCollectionService.get_office_contacts(office_id, db_id)

                # Get related interactions (limited)
                interactions, _ = FOCollectionService.get_office_interactions(office_id, db_id, limit=20)
                office.interactions = interactions

                # Get co-investments
                co_invests, _ = FOCollectionService.get_office_co_investments(office_id, db_id)
                office.co_investments = co_invests

                # Get portfolio companies
                portfolio, _ = FOCollectionService.get_office_portfolio(office_id, db_id)
                office.portfolio_companies = portfolio

                # Get themes
                office.themes = FOCollectionService.get_office_themes(office_id, db_id)

        return office

    @staticmethod
    def get_office_contacts(office_id: int, db_id: str = None) -> List[FOContact]:
        """
        Get contacts for a family office.

        Args:
            office_id: ID of the family office
            db_id: Database configuration ID

        Returns:
            List of contacts
        """
        db_id = db_id or FOCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        id, family_office_id, name, title, email, phone,
                        role, is_primary, notes
                    FROM family_office_contacts
                    WHERE family_office_id = %s
                    ORDER BY is_primary DESC NULLS LAST, name ASC
                """, (office_id,))
                rows = cur.fetchall()

        return [
            FOContact(
                id=row[0],
                family_office_id=row[1],
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
    def get_office_interactions(
        office_id: int,
        db_id: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[FOInteraction], int]:
        """
        Get interactions for a family office.

        Args:
            office_id: ID of the family office
            db_id: Database configuration ID
            limit: Maximum number of interactions to return
            offset: Number of interactions to skip

        Returns:
            Tuple of (list of interactions, total count)
        """
        db_id = db_id or FOCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                # Get total count
                cur.execute(
                    "SELECT COUNT(*) FROM family_office_interactions WHERE family_office_id = %s",
                    (office_id,)
                )
                total = cur.fetchone()[0]

                # Get paginated interactions
                cur.execute("""
                    SELECT
                        id, family_office_id, interaction_type, interaction_date,
                        subject, notes, outcome, follow_up_required, follow_up_date,
                        created_by, created_at
                    FROM family_office_interactions
                    WHERE family_office_id = %s
                    ORDER BY interaction_date DESC NULLS LAST, created_at DESC
                    LIMIT %s OFFSET %s
                """, (office_id, limit, offset))
                rows = cur.fetchall()

        interactions = [
            FOInteraction(
                id=row[0],
                family_office_id=row[1],
                interaction_type=row[2],
                interaction_date=row[3],
                subject=row[4],
                notes=row[5],
                outcome=row[6],
                follow_up_required=row[7],
                follow_up_date=row[8],
                created_by=row[9],
                created_at=row[10]
            )
            for row in rows
        ]

        return interactions, total

    @staticmethod
    def get_office_co_investments(
        office_id: int,
        db_id: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[CoInvestment], int]:
        """
        Get co-investments for a family office.

        Args:
            office_id: ID of the family office
            db_id: Database configuration ID
            limit: Maximum number of co-investments to return
            offset: Number to skip

        Returns:
            Tuple of (list of co-investments, total count)
        """
        db_id = db_id or FOCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                # Get total count
                cur.execute(
                    "SELECT COUNT(*) FROM co_investments WHERE family_office_id = %s",
                    (office_id,)
                )
                total = cur.fetchone()[0]

                # Get paginated results
                cur.execute("""
                    SELECT
                        id, family_office_id, deal_name, deal_type, sector,
                        investment_amount, investment_currency, status,
                        close_date, description, lead_investor, co_investors
                    FROM co_investments
                    WHERE family_office_id = %s
                    ORDER BY close_date DESC NULLS LAST
                    LIMIT %s OFFSET %s
                """, (office_id, limit, offset))
                rows = cur.fetchall()

        co_investments = [
            CoInvestment(
                id=row[0],
                family_office_id=row[1],
                deal_name=row[2],
                deal_type=row[3],
                sector=row[4],
                investment_amount=float(row[5]) if row[5] else None,
                investment_currency=row[6],
                status=row[7],
                close_date=row[8],
                description=row[9],
                lead_investor=row[10],
                co_investors=row[11]
            )
            for row in rows
        ]

        return co_investments, total

    @staticmethod
    def get_office_portfolio(
        office_id: int,
        db_id: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[PortfolioCompany], int]:
        """
        Get portfolio companies for a family office.

        Args:
            office_id: ID of the family office
            db_id: Database configuration ID
            limit: Maximum number to return
            offset: Number to skip

        Returns:
            Tuple of (list of portfolio companies, total count)
        """
        db_id = db_id or FOCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                # Get total count
                cur.execute(
                    "SELECT COUNT(*) FROM portfolio_companies WHERE family_office_id = %s",
                    (office_id,)
                )
                total = cur.fetchone()[0]

                # Get paginated results
                cur.execute("""
                    SELECT
                        id, family_office_id, company_name, sector, location,
                        investment_date, investment_amount, ownership_percentage,
                        current_valuation, status, description
                    FROM portfolio_companies
                    WHERE family_office_id = %s
                    ORDER BY investment_date DESC NULLS LAST
                    LIMIT %s OFFSET %s
                """, (office_id, limit, offset))
                rows = cur.fetchall()

        companies = [
            PortfolioCompany(
                id=row[0],
                family_office_id=row[1],
                company_name=row[2],
                sector=row[3],
                location=row[4],
                investment_date=row[5],
                investment_amount=float(row[6]) if row[6] else None,
                ownership_percentage=float(row[7]) if row[7] else None,
                current_valuation=float(row[8]) if row[8] else None,
                status=row[9],
                description=row[10]
            )
            for row in rows
        ]

        return companies, total

    @staticmethod
    def get_office_themes(office_id: int, db_id: str = None) -> List[InvestorTheme]:
        """
        Get investment themes for a family office.

        Args:
            office_id: ID of the family office
            db_id: Database configuration ID

        Returns:
            List of investor themes
        """
        db_id = db_id or FOCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        id, family_office_id, theme_name, theme_category,
                        allocation_target, priority, description, active
                    FROM investor_themes
                    WHERE family_office_id = %s
                    ORDER BY priority ASC NULLS LAST, theme_name ASC
                """, (office_id,))
                rows = cur.fetchall()

        return [
            InvestorTheme(
                id=row[0],
                family_office_id=row[1],
                theme_name=row[2],
                theme_category=row[3],
                allocation_target=float(row[4]) if row[4] else None,
                priority=row[5],
                description=row[6],
                active=row[7]
            )
            for row in rows
        ]

    @staticmethod
    def get_impact_analysis(office_id: int, db_id: str = None) -> Optional[ImpactAnalysis]:
        """
        Get the latest impact analysis for a family office.

        Args:
            office_id: ID of the family office
            db_id: Database configuration ID

        Returns:
            Impact analysis or None if not found
        """
        db_id = db_id or FOCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        id, family_office_id, analysis_date, esg_score,
                        environmental_score, social_score, governance_score,
                        impact_focus_areas, carbon_footprint, diversity_metrics,
                        reporting_framework, notes
                    FROM impact_analysis
                    WHERE family_office_id = %s
                    ORDER BY analysis_date DESC NULLS LAST
                    LIMIT 1
                """, (office_id,))
                row = cur.fetchone()

                if not row:
                    return None

        return ImpactAnalysis(
            id=row[0],
            family_office_id=row[1],
            analysis_date=row[2],
            esg_score=float(row[3]) if row[3] else None,
            environmental_score=float(row[4]) if row[4] else None,
            social_score=float(row[5]) if row[5] else None,
            governance_score=float(row[6]) if row[6] else None,
            impact_focus_areas=row[7],
            carbon_footprint=float(row[8]) if row[8] else None,
            diversity_metrics=row[9],
            reporting_framework=row[10],
            notes=row[11]
        )

    @staticmethod
    def get_stats(db_id: str = None) -> FOCollectionStats:
        """
        Get aggregate statistics for the FO collection.

        Args:
            db_id: Database configuration ID

        Returns:
            Collection statistics
        """
        db_id = db_id or FOCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                # Total offices
                cur.execute("SELECT COUNT(*) FROM family_offices")
                total_offices = cur.fetchone()[0]

                # Total contacts
                cur.execute("SELECT COUNT(*) FROM family_office_contacts")
                total_contacts = cur.fetchone()[0]

                # Total interactions
                cur.execute("SELECT COUNT(*) FROM family_office_interactions")
                total_interactions = cur.fetchone()[0]

                # Total co-investments
                cur.execute("SELECT COUNT(*) FROM co_investments")
                total_co_investments = cur.fetchone()[0]

                # Total portfolio companies
                cur.execute("SELECT COUNT(*) FROM portfolio_companies")
                total_portfolio_companies = cur.fetchone()[0]

                # Total AUM (assuming USD as default)
                cur.execute("""
                    SELECT
                        SUM(aum),
                        aum_currency
                    FROM family_offices
                    WHERE aum IS NOT NULL
                    GROUP BY aum_currency
                    ORDER BY SUM(aum) DESC
                    LIMIT 1
                """)
                aum_row = cur.fetchone()
                total_aum = float(aum_row[0]) if aum_row and aum_row[0] else None
                aum_currency = aum_row[1] if aum_row else None

                # Offices by type
                cur.execute("""
                    SELECT office_type, COUNT(*)
                    FROM family_offices
                    WHERE office_type IS NOT NULL
                    GROUP BY office_type
                    ORDER BY COUNT(*) DESC
                """)
                offices_by_type = {row[0]: row[1] for row in cur.fetchall()}

                # Offices by location
                cur.execute("""
                    SELECT headquarters, COUNT(*)
                    FROM family_offices
                    WHERE headquarters IS NOT NULL
                    GROUP BY headquarters
                    ORDER BY COUNT(*) DESC
                    LIMIT 20
                """)
                offices_by_location = {row[0]: row[1] for row in cur.fetchall()}

                # Offices by status
                cur.execute("""
                    SELECT status, COUNT(*)
                    FROM family_offices
                    WHERE status IS NOT NULL
                    GROUP BY status
                    ORDER BY COUNT(*) DESC
                """)
                offices_by_status = {row[0]: row[1] for row in cur.fetchall()}

        return FOCollectionStats(
            total_offices=total_offices,
            total_contacts=total_contacts,
            total_interactions=total_interactions,
            total_co_investments=total_co_investments,
            total_portfolio_companies=total_portfolio_companies,
            total_aum=total_aum,
            total_aum_currency=aum_currency,
            offices_by_type=offices_by_type,
            offices_by_location=offices_by_location,
            offices_by_status=offices_by_status
        )

    @staticmethod
    def office_exists(office_id: int, db_id: str = None) -> bool:
        """
        Check if a family office exists.

        Args:
            office_id: ID of the family office
            db_id: Database configuration ID

        Returns:
            True if office exists, False otherwise
        """
        db_id = db_id or FOCollectionService.DEFAULT_DB_ID

        with get_explorer_connection(db_id) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT EXISTS(SELECT 1 FROM family_offices WHERE id = %s)",
                    (office_id,)
                )
                return cur.fetchone()[0]
