"""Tests for insights domain - insight generation, persistence, and analytics."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock, patch

from services.insights import InsightsGenerator
from domains.insights.models import (
    InsightGenerateRequest, InsightReportResponse, InsightListItem,
    InsightListResponse, InsightType, Insight, InsightCreate, InsightReport
)
from domains.insights.db_models import InsightReport as InsightReportDB


class TestInsightsGenerator:
    """Test the core InsightsGenerator analytics engine."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        np.random.seed(42)
        return pd.DataFrame({
            'revenue': np.random.uniform(1000, 5000, 100),
            'cost': np.random.uniform(500, 2000, 100),
            'units': np.random.randint(10, 100, 100),
            'margin': np.random.uniform(0.1, 0.5, 100),
            'category': np.random.choice(['A', 'B', 'C'], 100),
        })

    @pytest.fixture
    def generator(self):
        """Create InsightsGenerator instance."""
        return InsightsGenerator()

    def test_generate_returns_all_insight_types(self, generator, sample_df):
        """Test that generate returns all expected insight types."""
        result = generator.generate(sample_df, "retail")

        expected_keys = [
            'summary', 'trends', 'anomalies', 'correlations',
            'recommendations', 'key_metrics', 'executive_kpis',
            'trend_data', 'distribution_data', 'growth_metrics',
            'risk_indicators', 'performance_score'
        ]

        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_generate_summary(self, generator, sample_df):
        """Test summary generation."""
        result = generator.generate(sample_df)

        assert 'summary' in result
        assert '100 rows' in result['summary']
        assert '5 columns' in result['summary']

    def test_identify_trends(self, generator, sample_df):
        """Test trend identification."""
        result = generator.generate(sample_df)

        assert 'trends' in result
        assert isinstance(result['trends'], list)

        if result['trends']:
            trend = result['trends'][0]
            assert 'column' in trend
            assert 'direction' in trend
            assert trend['direction'] in ['increasing', 'decreasing']
            assert 'average_change' in trend

    def test_detect_anomalies(self, generator, sample_df):
        """Test anomaly detection using IQR method."""
        result = generator.generate(sample_df)

        assert 'anomalies' in result
        assert isinstance(result['anomalies'], list)

        for anomaly in result['anomalies']:
            assert 'column' in anomaly
            assert 'outlier_count' in anomaly
            assert 'percentage' in anomaly
            assert anomaly['percentage'] >= 0

    def test_find_correlations(self, generator, sample_df):
        """Test correlation finding."""
        result = generator.generate(sample_df)

        assert 'correlations' in result
        assert isinstance(result['correlations'], list)

        for corr in result['correlations']:
            assert 'column1' in corr
            assert 'column2' in corr
            assert 'correlation' in corr
            assert -1 <= corr['correlation'] <= 1
            assert 'strength' in corr
            assert corr['strength'] in ['moderate', 'strong']

    def test_generate_recommendations(self, generator, sample_df):
        """Test recommendation generation."""
        result = generator.generate(sample_df, "healthcare")

        assert 'recommendations' in result
        assert isinstance(result['recommendations'], list)
        assert len(result['recommendations']) <= 5

    def test_calculate_key_metrics(self, generator, sample_df):
        """Test key metrics calculation."""
        result = generator.generate(sample_df)

        assert 'key_metrics' in result
        assert isinstance(result['key_metrics'], dict)

        for col, metrics in result['key_metrics'].items():
            assert 'mean' in metrics
            assert 'median' in metrics
            assert 'std' in metrics
            assert 'min' in metrics
            assert 'max' in metrics

    def test_calculate_executive_kpis(self, generator, sample_df):
        """Test executive KPI calculation."""
        result = generator.generate(sample_df)

        assert 'executive_kpis' in result
        assert isinstance(result['executive_kpis'], list)
        assert len(result['executive_kpis']) <= 4  # Max 4 KPIs

        for kpi in result['executive_kpis']:
            assert 'name' in kpi
            assert 'value' in kpi
            assert 'trend' in kpi
            assert 'trend_direction' in kpi
            assert kpi['trend_direction'] in ['up', 'down']

    def test_prepare_trend_data(self, generator, sample_df):
        """Test trend data preparation for visualization."""
        result = generator.generate(sample_df)

        assert 'trend_data' in result
        assert isinstance(result['trend_data'], list)
        assert len(result['trend_data']) <= 50  # Max 50 data points

        if result['trend_data']:
            data_point = result['trend_data'][0]
            assert 'index' in data_point

    def test_prepare_distribution_data(self, generator, sample_df):
        """Test distribution data preparation."""
        result = generator.generate(sample_df)

        assert 'distribution_data' in result
        assert isinstance(result['distribution_data'], dict)

        for col, dist in result['distribution_data'].items():
            assert isinstance(dist, list)
            for bucket in dist:
                assert 'range' in bucket
                assert 'count' in bucket
                assert 'percentage' in bucket

    def test_calculate_growth_metrics(self, generator, sample_df):
        """Test growth metrics calculation."""
        result = generator.generate(sample_df)

        assert 'growth_metrics' in result
        assert isinstance(result['growth_metrics'], dict)

        for col, metrics in result['growth_metrics'].items():
            assert 'growth_rate' in metrics
            assert 'cagr' in metrics
            assert 'momentum' in metrics
            assert metrics['momentum'] in ['accelerating', 'decelerating']

    def test_calculate_risk_indicators(self, generator, sample_df):
        """Test risk indicator calculation."""
        result = generator.generate(sample_df)

        assert 'risk_indicators' in result
        assert isinstance(result['risk_indicators'], list)

        for risk in result['risk_indicators']:
            assert 'metric' in risk
            assert 'volatility' in risk
            assert 'outlier_percentage' in risk
            assert 'risk_level' in risk
            assert risk['risk_level'] in ['low', 'medium', 'high']

    def test_calculate_performance_score(self, generator, sample_df):
        """Test performance score calculation."""
        result = generator.generate(sample_df)

        assert 'performance_score' in result
        score = result['performance_score']

        assert 'overall_score' in score
        assert 0 <= score['overall_score'] <= 100
        assert 'health' in score
        assert score['health'] in ['excellent', 'good', 'fair', 'needs attention']
        assert 'data_quality' in score
        assert 'consistency' in score
        assert 'growth' in score

    def test_empty_dataframe(self, generator):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()
        result = generator.generate(empty_df)

        assert result['performance_score']['overall_score'] == 0
        assert result['performance_score']['health'] == 'unknown'

    def test_single_row_dataframe(self, generator):
        """Test handling of single-row DataFrame."""
        single_df = pd.DataFrame({'value': [100]})
        result = generator.generate(single_df)

        assert 'summary' in result
        assert '1 rows' in result['summary']

    def test_non_numeric_only_dataframe(self, generator):
        """Test handling of DataFrame with only non-numeric columns."""
        text_df = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'category': ['A', 'B', 'C']
        })
        result = generator.generate(text_df)

        # Should handle gracefully
        assert 'summary' in result
        assert result['key_metrics'] == {}

    def test_dataframe_with_nulls(self, generator):
        """Test handling of DataFrame with null values."""
        null_df = pd.DataFrame({
            'value': [1.0, 2.0, None, 4.0, None],
            'count': [10, None, 30, 40, 50]
        })
        result = generator.generate(null_df)

        # Should handle nulls gracefully
        assert 'summary' in result
        assert 'recommendations' in result
        # Should recommend addressing missing data
        assert any('missing' in rec.lower() for rec in result['recommendations'])


class TestInsightModels:
    """Test Pydantic models for insights."""

    def test_insight_generate_request_minimal(self):
        """Test minimal insight generate request."""
        request = InsightGenerateRequest(dataset_id=uuid4())

        assert request.context == "general business"
        assert request.title is None
        assert request.persist is True

    def test_insight_generate_request_full(self):
        """Test full insight generate request."""
        dataset_id = uuid4()
        request = InsightGenerateRequest(
            dataset_id=dataset_id,
            context="healthcare analytics",
            title="Q4 Health Report",
            persist=False
        )

        assert request.dataset_id == dataset_id
        assert request.context == "healthcare analytics"
        assert request.title == "Q4 Health Report"
        assert request.persist is False

    def test_insight_report_response(self):
        """Test insight report response model."""
        now = datetime.utcnow()
        response = InsightReportResponse(
            id=uuid4(),
            dataset_id=uuid4(),
            title="Test Report",
            context="retail",
            performance_score={"overall_score": 85, "health": "good"},
            executive_kpis=[{"name": "revenue", "value": 1000, "trend": 5.2}],
            trend_data=[{"index": 0, "revenue": 100}],
            growth_metrics={"revenue": {"growth_rate": 10.5}},
            risk_indicators=[{"metric": "revenue", "risk_level": "low"}],
            distribution_data={"revenue": [{"range": "0-100", "count": 10}]},
            recommendations=["Monitor trends", "Expand dataset"],
            summary="Test summary",
            trends=[{"column": "revenue", "direction": "up"}],
            anomalies=[{"column": "cost", "outlier_count": 5}],
            correlations=[{"column1": "revenue", "column2": "units", "correlation": 0.8}],
            key_metrics={"revenue": {"mean": 100}},
            created_at=now,
            updated_at=now
        )

        assert response.title == "Test Report"
        assert response.performance_score["overall_score"] == 85
        assert len(response.recommendations) == 2

    def test_insight_list_item(self):
        """Test insight list item model."""
        item = InsightListItem(
            id=uuid4(),
            dataset_id=uuid4(),
            title="Monthly Report",
            context="finance",
            summary="Financial analysis for Q4",
            created_at=datetime.utcnow()
        )

        assert item.title == "Monthly Report"
        assert item.context == "finance"

    def test_insight_list_response(self):
        """Test insight list response model."""
        response = InsightListResponse(
            items=[],
            total=0,
            page=1,
            page_size=20
        )

        assert response.total == 0
        assert response.page == 1

    def test_insight_type_values(self):
        """Test insight type constants."""
        assert InsightType.SUMMARY == "summary"
        assert InsightType.TREND == "trend"
        assert InsightType.ANOMALY == "anomaly"
        assert InsightType.CORRELATION == "correlation"
        assert InsightType.PREDICTION == "prediction"

    def test_legacy_insight_model(self):
        """Test legacy Insight model for backward compatibility."""
        insight = Insight(
            id=uuid4(),
            name="Revenue Trend",
            description="Monthly revenue analysis",
            insight_type="trend",
            dataset_id=uuid4(),
            data={"direction": "up", "change": 10.5},
            metadata={"source": "auto-generated"},
            created_at=datetime.utcnow()
        )

        assert insight.insight_type == "trend"
        assert insight.data["direction"] == "up"

    def test_legacy_insight_create_model(self):
        """Test legacy InsightCreate model."""
        create = InsightCreate(
            name="Anomaly Detection",
            insight_type="anomaly",
            dataset_id=uuid4(),
            config={"threshold": 0.05}
        )

        assert create.name == "Anomaly Detection"
        assert create.config["threshold"] == 0.05

    def test_legacy_insight_report_model(self):
        """Test legacy InsightReport model."""
        report = InsightReport(
            id=uuid4(),
            title="Quarterly Report",
            insights=[],
            summary={"key_finding": "Growth is positive"},
            created_at=datetime.utcnow()
        )

        assert report.title == "Quarterly Report"
        assert report.summary["key_finding"] == "Growth is positive"


class TestInsightDBModels:
    """Test database models for insights."""

    def test_insight_report_db_model(self):
        """Test InsightReport SQLModel."""
        report = InsightReportDB(
            dataset_id=uuid4(),
            title="Test Report",
            context="test context",
            performance_score={"overall_score": 75},
            executive_kpis=[{"name": "metric1", "value": 100}],
            trend_data=[],
            growth_metrics={},
            risk_indicators=[],
            distribution_data={},
            recommendations=["Recommendation 1"],
            summary="Test summary",
            trends=[],
            anomalies=[],
            correlations=[],
            key_metrics={}
        )

        assert report.title == "Test Report"
        assert report.performance_score["overall_score"] == 75
        assert report.recommendations == ["Recommendation 1"]


class TestInsightsService:
    """Test InsightsService with mocked dependencies."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = MagicMock()
        session.add = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock()
        session.get = MagicMock(return_value=None)
        session.exec = MagicMock()
        session.execute = MagicMock()
        session.delete = MagicMock()
        return session

    def test_service_imports(self):
        """Test that service can be imported."""
        from domains.insights.service import InsightsService
        assert InsightsService is not None

    def test_service_initialization(self):
        """Test service initialization."""
        from domains.insights.service import InsightsService
        service = InsightsService()
        assert service.generator is not None

    @pytest.mark.asyncio
    async def test_get_insight_not_found(self, mock_session):
        """Test getting non-existent insight."""
        from domains.insights.service import InsightsService

        mock_session.get.return_value = None

        service = InsightsService()
        result = service.get_insight(uuid4(), mock_session)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_insight_not_found(self, mock_session):
        """Test deleting non-existent insight."""
        from domains.insights.service import InsightsService

        mock_session.get.return_value = None

        service = InsightsService()
        result = service.delete_insight(uuid4(), mock_session)

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_insight_success(self, mock_session):
        """Test successful insight deletion."""
        from domains.insights.service import InsightsService

        # Mock existing report
        mock_report = MagicMock()
        mock_session.get.return_value = mock_report

        service = InsightsService()
        result = service.delete_insight(uuid4(), mock_session)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_report)
        mock_session.commit.assert_called_once()


class TestRouterImports:
    """Test that router and related modules import correctly."""

    def test_router_imports(self):
        """Verify router can be imported."""
        from domains.insights.router import router
        assert router is not None
        assert router.prefix == "/insights"

    def test_service_imports(self):
        """Verify service can be imported."""
        from domains.insights.service import InsightsService
        assert InsightsService is not None

    def test_generator_imports(self):
        """Verify InsightsGenerator can be imported."""
        from services.insights import InsightsGenerator
        assert InsightsGenerator is not None

    def test_db_models_imports(self):
        """Verify db models can be imported."""
        from domains.insights.db_models import InsightReport
        assert InsightReport is not None

    def test_models_imports(self):
        """Verify Pydantic models can be imported."""
        from domains.insights.models import (
            InsightGenerateRequest,
            InsightReportResponse,
            InsightListResponse
        )
        assert InsightGenerateRequest is not None
        assert InsightReportResponse is not None
        assert InsightListResponse is not None


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def generator(self):
        return InsightsGenerator()

    def test_dataframe_with_inf_values(self, generator):
        """Test handling of infinite values.

        Note: DataFrames with inf values will raise ValueError in histogram.
        This is a known limitation - data should be cleaned before analysis.
        """
        inf_df = pd.DataFrame({
            'value': [1.0, 2.0, np.inf, 4.0, -np.inf]
        })
        # Infinite values cause numpy histogram to fail
        with pytest.raises(ValueError, match="not finite"):
            generator.generate(inf_df)

    def test_dataframe_with_large_numbers(self, generator):
        """Test handling of very large numbers."""
        large_df = pd.DataFrame({
            'value': [1e15, 2e15, 3e15, 4e15, 5e15]
        })
        result = generator.generate(large_df)
        assert 'key_metrics' in result

    def test_dataframe_with_negative_values(self, generator):
        """Test handling of negative values."""
        neg_df = pd.DataFrame({
            'profit': [-100, -50, 0, 50, 100],
            'loss': [-200, -150, -100, -50, 0]
        })
        result = generator.generate(neg_df)
        assert 'performance_score' in result

    def test_dataframe_with_constant_column(self, generator):
        """Test handling of columns with no variation."""
        const_df = pd.DataFrame({
            'constant': [5, 5, 5, 5, 5],
            'varying': [1, 2, 3, 4, 5]
        })
        result = generator.generate(const_df)
        # Should flag constant column in recommendations
        assert any('no variation' in rec.lower() for rec in result['recommendations'])

    def test_dataframe_with_datetime_column(self, generator):
        """Test handling of datetime columns."""
        date_df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10),
            'value': np.random.uniform(0, 100, 10)
        })
        result = generator.generate(date_df)
        # Should process numeric column only
        assert 'value' in result['key_metrics']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
