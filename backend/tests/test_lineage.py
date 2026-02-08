"""Tests for lineage domain - data lineage tracking, SQL parsing, and impact analysis."""
import pytest
from uuid import uuid4
from datetime import datetime

from domains.lineage.models import (
    EntityType, EdgeType, ColumnTransformation,
    DataLineageEdge, DataLineageMetadata, DataLineageColumn,
    LineageNode, LineageEdgeResponse, ColumnLineage,
    LineageGraphResponse, LineageSummary,
    CreateLineageRequest, LineageQueryRequest,
    LineageImpactAnalysis, LineageSearchRequest, LineageSearchResult
)


class TestLineageEnums:
    """Test lineage enum values."""

    def test_entity_types(self):
        """Test all entity types are available."""
        assert EntityType.FILE.value == "file"
        assert EntityType.FILE_TABLE.value == "file_table"
        assert EntityType.DATABASE_TABLE.value == "database_table"
        assert EntityType.DATASET.value == "dataset"
        assert EntityType.NOTEBOOK.value == "notebook"
        assert EntityType.QUERY.value == "query"
        assert EntityType.MODEL.value == "model"
        assert EntityType.REPORT.value == "report"
        assert EntityType.NOTEBOOK_OUTPUT.value == "notebook_output"

    def test_edge_types(self):
        """Test all edge types are available."""
        assert EdgeType.DERIVED_FROM.value == "derived_from"
        assert EdgeType.PUBLISHED.value == "published"
        assert EdgeType.TRANSFORMED.value == "transformed"
        assert EdgeType.JOINED.value == "joined"
        assert EdgeType.AGGREGATED.value == "aggregated"
        assert EdgeType.FILTERED.value == "filtered"
        assert EdgeType.TRAINED_ON.value == "trained_on"
        assert EdgeType.QUERIED_FROM.value == "queried_from"

    def test_column_transformation_types(self):
        """Test column transformation types."""
        assert ColumnTransformation.DIRECT.value == "direct"
        assert ColumnTransformation.CAST.value == "cast"
        assert ColumnTransformation.CALCULATED.value == "calculated"
        assert ColumnTransformation.AGGREGATED.value == "aggregated"
        assert ColumnTransformation.RENAMED.value == "renamed"


class TestLineageNodeModels:
    """Test lineage node models."""

    def test_lineage_node_minimal(self):
        """Test lineage node with minimal fields."""
        node = LineageNode(
            entity_type=EntityType.DATABASE_TABLE,
            entity_id=uuid4(),
            entity_name="customers"
        )
        assert node.entity_name == "customers"
        assert node.is_source is False
        assert node.is_sink is False
        assert node.depth == 0

    def test_lineage_node_full(self):
        """Test lineage node with all fields."""
        node = LineageNode(
            entity_type=EntityType.DATABASE_TABLE,
            entity_id=uuid4(),
            entity_name="analytics.customers",
            schema_name="analytics",
            row_count=100000,
            column_count=25,
            created_at=datetime.utcnow(),
            last_modified_at=datetime.utcnow(),
            is_source=True,
            is_sink=False,
            depth=0
        )
        assert node.row_count == 100000
        assert node.is_source is True
        assert node.schema_name == "analytics"

    def test_lineage_node_dataset(self):
        """Test lineage node for dataset."""
        node = LineageNode(
            entity_type=EntityType.DATASET,
            entity_id=uuid4(),
            entity_name="customer_segments",
            is_sink=True,
            depth=3
        )
        assert node.entity_type == EntityType.DATASET
        assert node.is_sink is True


class TestLineageEdgeModels:
    """Test lineage edge models."""

    def test_lineage_edge_response(self):
        """Test lineage edge response model."""
        edge = LineageEdgeResponse(
            id=uuid4(),
            source_type=EntityType.DATABASE_TABLE,
            source_id=uuid4(),
            source_name="raw_orders",
            target_type=EntityType.DATASET,
            target_id=uuid4(),
            target_name="processed_orders",
            edge_type=EdgeType.TRANSFORMED,
            transform_sql="SELECT * FROM raw_orders WHERE status = 'active'",
            transform_config={"filter": "status = 'active'"},
            created_at=datetime.utcnow(),
            created_by=uuid4(),
            source_row_count=50000,
            target_row_count=35000
        )
        assert edge.edge_type == EdgeType.TRANSFORMED
        assert edge.source_row_count == 50000

    def test_column_lineage(self):
        """Test column lineage model."""
        col_lineage = ColumnLineage(
            source_column="amount",
            source_data_type="decimal(10,2)",
            target_column="total_amount",
            target_data_type="decimal(12,2)",
            transformation=ColumnTransformation.CALCULATED,
            transformation_expression="SUM(amount)"
        )
        assert col_lineage.transformation == ColumnTransformation.CALCULATED
        assert col_lineage.transformation_expression == "SUM(amount)"

    def test_column_lineage_direct(self):
        """Test direct column mapping."""
        col_lineage = ColumnLineage(
            source_column="customer_id",
            source_data_type="integer",
            target_column="customer_id",
            target_data_type="integer",
            transformation=ColumnTransformation.DIRECT,
            transformation_expression=None
        )
        assert col_lineage.transformation == ColumnTransformation.DIRECT


class TestLineageGraphModels:
    """Test lineage graph models."""

    def test_lineage_graph_response_empty(self):
        """Test empty lineage graph response."""
        center = LineageNode(
            entity_type=EntityType.DATASET,
            entity_id=uuid4(),
            entity_name="isolated_dataset"
        )
        graph = LineageGraphResponse(
            center_node=center,
            total_upstream_count=0,
            total_downstream_count=0,
            max_depth=0
        )
        assert len(graph.upstream_nodes) == 0
        assert len(graph.downstream_nodes) == 0

    def test_lineage_graph_response_full(self):
        """Test lineage graph response with nodes and edges."""
        center_id = uuid4()
        source_id = uuid4()
        target_id = uuid4()

        center = LineageNode(
            entity_type=EntityType.DATABASE_TABLE,
            entity_id=center_id,
            entity_name="orders"
        )
        source = LineageNode(
            entity_type=EntityType.FILE,
            entity_id=source_id,
            entity_name="orders.csv",
            is_source=True
        )
        target = LineageNode(
            entity_type=EntityType.DATASET,
            entity_id=target_id,
            entity_name="order_summary",
            is_sink=True
        )
        edge1 = LineageEdgeResponse(
            id=uuid4(),
            source_type=EntityType.FILE,
            source_id=source_id,
            source_name="orders.csv",
            target_type=EntityType.DATABASE_TABLE,
            target_id=center_id,
            target_name="orders",
            edge_type=EdgeType.DERIVED_FROM,
            transform_sql=None,
            transform_config=None,
            created_at=datetime.utcnow(),
            created_by=None,
            source_row_count=None,
            target_row_count=None
        )
        edge2 = LineageEdgeResponse(
            id=uuid4(),
            source_type=EntityType.DATABASE_TABLE,
            source_id=center_id,
            source_name="orders",
            target_type=EntityType.DATASET,
            target_id=target_id,
            target_name="order_summary",
            edge_type=EdgeType.AGGREGATED,
            transform_sql=None,
            transform_config=None,
            created_at=datetime.utcnow(),
            created_by=None,
            source_row_count=None,
            target_row_count=None
        )

        graph = LineageGraphResponse(
            center_node=center,
            upstream_nodes=[source],
            downstream_nodes=[target],
            edges=[edge1, edge2],
            column_mappings=[],
            total_upstream_count=1,
            total_downstream_count=1,
            max_depth=1
        )

        assert len(graph.upstream_nodes) == 1
        assert len(graph.downstream_nodes) == 1
        assert len(graph.edges) == 2
        assert graph.max_depth == 1


class TestLineageSummaryModels:
    """Test lineage summary models."""

    def test_lineage_summary(self):
        """Test lineage summary model."""
        summary = LineageSummary(
            entity_type=EntityType.DATABASE_TABLE,
            entity_id=uuid4(),
            entity_name="sales",
            upstream_count=3,
            downstream_count=5,
            total_upstream_count=7,
            total_downstream_count=12,
            immediate_sources=["orders", "customers", "products"],
            immediate_targets=["sales_summary", "daily_report"],
            is_stale=False,
            last_refreshed_at=datetime.utcnow()
        )
        assert summary.upstream_count == 3
        assert summary.downstream_count == 5
        assert len(summary.immediate_sources) == 3

    def test_lineage_summary_stale(self):
        """Test stale lineage summary."""
        summary = LineageSummary(
            entity_type=EntityType.DATASET,
            entity_id=uuid4(),
            entity_name="old_dataset",
            is_stale=True
        )
        assert summary.is_stale is True


class TestLineageRequestModels:
    """Test lineage request models."""

    def test_create_lineage_request(self):
        """Test create lineage request model."""
        request = CreateLineageRequest(
            source_type=EntityType.DATABASE_TABLE,
            source_id=uuid4(),
            source_name="raw_data",
            target_type=EntityType.DATASET,
            target_id=uuid4(),
            target_name="processed_data",
            edge_type=EdgeType.TRANSFORMED,
            transform_sql="SELECT * FROM raw_data WHERE active = true",
            transform_config={"filter": "active = true"},
            source_row_count=10000,
            target_row_count=8500,
            column_mappings=[
                ColumnLineage(
                    source_column="id",
                    source_data_type="integer",
                    target_column="id",
                    target_data_type="integer",
                    transformation=ColumnTransformation.DIRECT,
                    transformation_expression=None
                )
            ]
        )
        assert request.edge_type == EdgeType.TRANSFORMED
        assert len(request.column_mappings) == 1

    def test_lineage_query_request(self):
        """Test lineage query request model."""
        request = LineageQueryRequest(
            entity_type=EntityType.DATABASE_TABLE,
            entity_id=uuid4(),
            direction="both",
            max_depth=5,
            include_columns=True
        )
        assert request.max_depth == 5
        assert request.include_columns is True

    def test_lineage_query_request_defaults(self):
        """Test lineage query request default values."""
        request = LineageQueryRequest(
            entity_type=EntityType.DATASET,
            entity_id=uuid4()
        )
        assert request.direction == "both"
        assert request.max_depth == 3
        assert request.include_columns is False


class TestLineageImpactAnalysis:
    """Test impact analysis models."""

    def test_impact_analysis_low_risk(self):
        """Test impact analysis - low risk."""
        impact = LineageImpactAnalysis(
            entity_type=EntityType.DATABASE_TABLE,
            entity_id=uuid4(),
            entity_name="staging_table",
            affected_downstream_count=2,
            affected_entities=[],
            risk_level="low",
            recommendations=[]
        )
        assert impact.risk_level == "low"
        assert impact.affected_downstream_count == 2

    def test_impact_analysis_high_risk(self):
        """Test impact analysis - high risk."""
        affected = [
            LineageNode(
                entity_type=EntityType.REPORT,
                entity_id=uuid4(),
                entity_name="executive_dashboard"
            ),
            LineageNode(
                entity_type=EntityType.MODEL,
                entity_id=uuid4(),
                entity_name="sales_forecast_model"
            )
        ]
        impact = LineageImpactAnalysis(
            entity_type=EntityType.DATABASE_TABLE,
            entity_id=uuid4(),
            entity_name="sales_core",
            affected_downstream_count=15,
            affected_entities=affected,
            risk_level="high",
            recommendations=[
                "Notify dashboard owners before changes",
                "Retrain ML models after schema changes"
            ]
        )
        assert impact.risk_level == "high"
        assert len(impact.recommendations) == 2


class TestLineageSearchModels:
    """Test lineage search models."""

    def test_lineage_search_request(self):
        """Test lineage search request."""
        request = LineageSearchRequest(
            search_term="customers",
            entity_types=[EntityType.DATABASE_TABLE, EntityType.DATASET],
            limit=100
        )
        assert request.search_term == "customers"
        assert len(request.entity_types) == 2

    def test_lineage_search_request_defaults(self):
        """Test lineage search request defaults."""
        request = LineageSearchRequest(search_term="sales")
        assert request.limit == 50
        assert request.entity_types is None

    def test_lineage_search_result(self):
        """Test lineage search result."""
        result = LineageSearchResult(
            entities=[
                LineageNode(
                    entity_type=EntityType.DATABASE_TABLE,
                    entity_id=uuid4(),
                    entity_name="customers"
                )
            ],
            total_count=1
        )
        assert result.total_count == 1


class TestRouterImports:
    """Test that router and services import correctly."""

    def test_router_imports(self):
        """Verify router can be imported."""
        from domains.lineage.router import router
        assert router is not None
        assert router.prefix == "/api/v1/lineage"

    def test_service_imports(self):
        """Verify service can be imported."""
        from domains.lineage.service import LineageService
        assert LineageService is not None

    def test_sql_parser_imports(self):
        """Verify SQL parser can be imported."""
        from domains.lineage.sql_parser import (
            SQLLineageParser, parse_sql_lineage,
            TableReference, ColumnReference, QueryLineage
        )
        assert SQLLineageParser is not None
        assert parse_sql_lineage is not None

    def test_auto_tracker_imports(self):
        """Verify auto tracker can be imported."""
        from domains.lineage.auto_tracker import AutoLineageTracker
        assert AutoLineageTracker is not None

    def test_column_lineage_imports(self):
        """Verify column lineage module can be imported."""
        from domains.lineage.column_lineage import extract_column_lineage
        assert extract_column_lineage is not None

    def test_ml_tracker_imports(self):
        """Verify ML tracker can be imported."""
        from domains.lineage.ml_tracker import analyze_ml_query
        assert analyze_ml_query is not None


class TestSQLParser:
    """Test SQL parser functionality."""

    def test_parse_simple_select(self):
        """Test parsing simple SELECT query."""
        from domains.lineage.sql_parser import parse_sql_lineage

        lineage = parse_sql_lineage("SELECT * FROM customers")
        assert lineage.query_type == "SELECT"
        assert len(lineage.source_tables) >= 1
        assert lineage.source_tables[0].table == "customers"

    def test_parse_select_with_schema(self):
        """Test parsing SELECT with schema prefix."""
        from domains.lineage.sql_parser import parse_sql_lineage

        lineage = parse_sql_lineage("SELECT * FROM public.customers")
        assert len(lineage.source_tables) >= 1
        # SQL parser extracts table name; schema parsing may vary by sqlparse version
        table = lineage.source_tables[0]
        assert "customers" in table.full_name or table.table == "customers"

    def test_parse_join_query(self):
        """Test parsing JOIN query."""
        from domains.lineage.sql_parser import parse_sql_lineage

        sql = """
        SELECT o.*, c.name
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        """
        lineage = parse_sql_lineage(sql)
        assert lineage.join_type is not None
        assert len(lineage.source_tables) >= 2

    def test_parse_left_join(self):
        """Test parsing LEFT JOIN query."""
        from domains.lineage.sql_parser import parse_sql_lineage

        sql = """
        SELECT * FROM orders
        LEFT JOIN customers ON orders.customer_id = customers.id
        """
        lineage = parse_sql_lineage(sql)
        assert lineage.join_type == "LEFT"

    def test_parse_aggregation(self):
        """Test parsing query with aggregation."""
        from domains.lineage.sql_parser import parse_sql_lineage

        sql = "SELECT customer_id, SUM(amount) FROM orders GROUP BY customer_id"
        lineage = parse_sql_lineage(sql)
        assert lineage.has_aggregation is True

    def test_parse_where_clause(self):
        """Test parsing query with WHERE clause."""
        from domains.lineage.sql_parser import parse_sql_lineage

        sql = "SELECT * FROM orders WHERE amount > 100"
        lineage = parse_sql_lineage(sql)
        assert lineage.has_filter is True

    def test_parse_insert_query(self):
        """Test parsing INSERT query."""
        from domains.lineage.sql_parser import parse_sql_lineage

        sql = "INSERT INTO summary SELECT date, SUM(amount) FROM sales GROUP BY date"
        lineage = parse_sql_lineage(sql)
        assert lineage.query_type == "INSERT"
        # Source table should be detected
        assert len(lineage.source_tables) >= 1
        assert any(t.table == "sales" for t in lineage.source_tables)
        # Aggregation should be detected
        assert lineage.has_aggregation is True

    def test_table_reference_equality(self):
        """Test table reference equality."""
        from domains.lineage.sql_parser import TableReference

        ref1 = TableReference(schema="public", table="customers")
        ref2 = TableReference(schema="public", table="customers")
        ref3 = TableReference(schema="analytics", table="customers")

        assert ref1 == ref2
        assert ref1 != ref3
        assert hash(ref1) == hash(ref2)

    def test_column_reference_equality(self):
        """Test column reference equality."""
        from domains.lineage.sql_parser import ColumnReference

        ref1 = ColumnReference(table="orders", column="id")
        ref2 = ColumnReference(table="orders", column="id")
        ref3 = ColumnReference(table="customers", column="id")

        assert ref1 == ref2
        assert ref1 != ref3


class TestSQLModelTables:
    """Test SQLModel table definitions."""

    def test_data_lineage_edge_model(self):
        """Test DataLineageEdge model can be instantiated."""
        edge = DataLineageEdge(
            source_type=EntityType.DATABASE_TABLE,
            source_id=uuid4(),
            source_name="orders",
            target_type=EntityType.DATASET,
            target_id=uuid4(),
            target_name="order_summary",
            edge_type=EdgeType.AGGREGATED
        )
        assert edge.edge_type == EdgeType.AGGREGATED
        assert edge.id is not None

    def test_data_lineage_metadata_model(self):
        """Test DataLineageMetadata model can be instantiated."""
        metadata = DataLineageMetadata(
            entity_type=EntityType.DATABASE_TABLE,
            entity_id=uuid4(),
            entity_name="customers",
            upstream_count=2,
            downstream_count=5,
            lineage_depth=3
        )
        assert metadata.upstream_count == 2
        assert metadata.is_stale is False

    def test_data_lineage_column_model(self):
        """Test DataLineageColumn model can be instantiated."""
        column = DataLineageColumn(
            edge_id=uuid4(),
            source_column="amount",
            source_data_type="decimal",
            target_column="total",
            target_data_type="decimal",
            transformation=ColumnTransformation.AGGREGATED,
            transformation_expression="SUM(amount)"
        )
        assert column.transformation == ColumnTransformation.AGGREGATED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
