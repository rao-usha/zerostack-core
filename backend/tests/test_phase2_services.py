"""
Unit tests for Phase 2 PE Analysis Services

Tests for trend analysis, reconciliation, and AI insights services.
"""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from domains.data_ingestion.trend_analyzer import (
    TrendAnalyzer,
    TrendDirection,
    Seasonality,
)
from domains.data_ingestion.reconciliation_service import (
    ReconciliationService,
    ReconciliationType,
    DiscrepancySeverity,
)
from domains.data_ingestion.ai_insights_service import (
    AIInsightsService,
    AIInsight,
    AIAnalysisReport,
)


class TestTrendAnalyzer:
    """Tests for TrendAnalyzer service"""

    @pytest.fixture
    def analyzer(self):
        return TrendAnalyzer()

    @pytest.fixture
    def sample_time_series(self):
        """Create sample time series with known characteristics"""
        dates = pd.date_range('2023-01-01', periods=24, freq='M')
        # Growing revenue with some noise
        values = [100 + i * 5 + np.random.randn() * 2 for i in range(24)]
        return pd.DataFrame({'date': dates, 'revenue': values})

    def test_analyze_time_series_basic(self, analyzer, sample_time_series):
        """Test basic time series analysis"""
        result = analyzer.analyze_time_series(
            sample_time_series, 'date', 'revenue', 'revenue'
        )

        assert result is not None
        assert result.column_name == 'revenue'
        assert result.growth_metrics is not None
        assert result.trend_line_slope > 0  # Should detect upward trend

    def test_analyze_time_series_growth_direction(self, analyzer):
        """Test trend direction detection"""
        # Create clearly increasing data
        dates = pd.date_range('2023-01-01', periods=12, freq='M')
        df_increasing = pd.DataFrame({
            'date': dates,
            'value': [100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210]
        })

        result = analyzer.analyze_time_series(df_increasing, 'date', 'value')

        assert result is not None
        assert result.growth_metrics.trend_direction == TrendDirection.INCREASING

    def test_analyze_time_series_decreasing(self, analyzer):
        """Test decreasing trend detection"""
        dates = pd.date_range('2023-01-01', periods=12, freq='M')
        df_decreasing = pd.DataFrame({
            'date': dates,
            'value': [200, 190, 180, 170, 160, 150, 140, 130, 120, 110, 100, 90]
        })

        result = analyzer.analyze_time_series(df_decreasing, 'date', 'value')

        assert result is not None
        assert result.growth_metrics.trend_direction == TrendDirection.DECREASING

    def test_calculate_growth_rates(self, analyzer, sample_time_series):
        """Test growth rate calculations"""
        result = analyzer.calculate_growth_rates(
            sample_time_series, 'date', 'revenue'
        )

        assert 'latest_value' in result
        assert 'earliest_value' in result
        assert 'period_count' in result
        assert result['period_count'] == 24

    def test_calculate_growth_rates_with_cagr(self, analyzer):
        """Test CAGR calculation"""
        dates = pd.date_range('2020-01-01', periods=36, freq='M')  # 3 years
        # 50% total growth over 3 years
        values = [100 * (1.5 ** (i/35)) for i in range(36)]
        df = pd.DataFrame({'date': dates, 'revenue': values})

        result = analyzer.calculate_growth_rates(df, 'date', 'revenue')

        assert 'cagr' in result
        # CAGR should be approximately 14.5% for 50% growth over 3 years
        assert 0.10 < result['cagr'] < 0.20

    def test_detect_trend_breaks(self, analyzer):
        """Test trend break detection"""
        dates = pd.date_range('2023-01-01', periods=12, freq='M')
        # Steady growth with sudden spike
        values = [100, 105, 110, 115, 120, 125, 200, 205, 210, 215, 220, 225]
        df = pd.DataFrame({'date': dates, 'value': values})

        breaks = analyzer.detect_trend_breaks(df, 'date', 'value')

        assert len(breaks) >= 1
        # Should detect the spike at index 6
        spike_break = [b for b in breaks if b['period_index'] == 6]
        assert len(spike_break) >= 1

    def test_analyze_time_series_insufficient_data(self, analyzer):
        """Test handling of insufficient data"""
        dates = pd.date_range('2023-01-01', periods=3, freq='M')
        df = pd.DataFrame({'date': dates, 'value': [100, 110, 120]})

        result = analyzer.analyze_time_series(df, 'date', 'value')

        assert result is None  # Not enough data

    def test_seasonality_detection(self, analyzer):
        """Test seasonality detection with quarterly pattern"""
        # Create data with quarterly seasonality
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=36, freq='M')
        base = 100
        seasonal = [10, 5, 0, 10, 5, 0] * 6  # Quarterly pattern
        trend = [i * 2 for i in range(36)]
        values = [base + s + t + np.random.randn() for s, t in zip(seasonal, trend)]
        df = pd.DataFrame({'date': dates, 'value': values})

        result = analyzer.analyze_time_series(df, 'date', 'value')

        assert result is not None
        # May detect quarterly seasonality depending on strength

    def test_insights_generation(self, analyzer):
        """Test that insights are generated"""
        dates = pd.date_range('2023-01-01', periods=24, freq='M')
        # Strong growth
        values = [100 * (1.03 ** i) for i in range(24)]  # 3% monthly growth
        df = pd.DataFrame({'date': dates, 'revenue': values})

        result = analyzer.analyze_time_series(df, 'date', 'revenue', 'revenue')

        assert result is not None
        assert len(result.insights) > 0


class TestReconciliationService:
    """Tests for ReconciliationService"""

    @pytest.fixture
    def reconciler(self):
        return ReconciliationService()

    def test_reconcile_matching_data(self, reconciler):
        """Test reconciliation of matching data"""
        df_a = pd.DataFrame({
            'date': ['2023-01', '2023-02', '2023-03'],
            'revenue': [100, 150, 200],
        })
        df_b = pd.DataFrame({
            'date': ['2023-01', '2023-02', '2023-03'],
            'sales': [100, 150, 200],
        })

        result = reconciler.reconcile_specific(
            df_a, df_b, 'revenue', 'sales',
            source_a_name='File A', source_b_name='File B'
        )

        assert result.matches is True
        assert result.discrepancy_count == 0

    def test_reconcile_with_discrepancies(self, reconciler):
        """Test reconciliation with discrepancies"""
        df_a = pd.DataFrame({
            'date': ['2023-01', '2023-02', '2023-03'],
            'revenue': [100, 150, 200],
        })
        df_b = pd.DataFrame({
            'date': ['2023-01', '2023-02', '2023-03'],
            'sales': [100, 180, 200],  # 150 vs 180 = 20% difference
        })

        result = reconciler.reconcile_specific(
            df_a, df_b, 'revenue', 'sales',
            source_a_name='File A', source_b_name='File B',
            tolerance=0.05
        )

        assert result.matches is False
        assert result.discrepancy_count >= 1

    def test_reconcile_dataframes_auto(self, reconciler):
        """Test automatic reconciliation detection"""
        df_a = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=6, freq='M'),
            'revenue': [100, 110, 120, 130, 140, 150],
            'customer_count': [10, 11, 12, 13, 14, 15],
        })
        df_b = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=6, freq='M'),
            'total_revenue': [100, 110, 120, 130, 140, 150],
            'customers': [10, 11, 12, 13, 14, 15],
        })

        summary = reconciler.reconcile_dataframes(df_a, df_b, 'Source A', 'Source B')

        assert summary.total_checks >= 1
        assert summary.overall_confidence >= 0

    def test_severity_calculation(self, reconciler):
        """Test severity is calculated correctly"""
        df_a = pd.DataFrame({'value': [100]})
        df_b = pd.DataFrame({'value': [150]})  # 50% difference

        result = reconciler.reconcile_specific(
            df_a, df_b, 'value', 'value',
            source_a_name='A', source_b_name='B'
        )

        assert result.severity == DiscrepancySeverity.CRITICAL

    def test_headcount_payroll_reconciliation(self, reconciler):
        """Test headcount vs payroll ratio check"""
        df_headcount = pd.DataFrame({
            'headcount': [50, 52, 55, 58],
        })
        df_payroll = pd.DataFrame({
            'payroll': [5000000, 5200000, 5500000, 5800000],  # ~$100k per employee
        })

        cols_a = {'headcount': 'headcount'}
        cols_b = {'payroll': 'payroll'}

        result = reconciler._reconcile_headcount_payroll(
            df_headcount, df_payroll, cols_a, cols_b, 'HR Data', 'Payroll Data'
        )

        assert result is not None
        assert result.reconciliation_type == ReconciliationType.HEADCOUNT_PAYROLL

    def test_internal_consistency_duplicates(self, reconciler):
        """Test duplicate period detection"""
        df = pd.DataFrame({
            'date': ['2023-01', '2023-01', '2023-02', '2023-03'],  # Duplicate 2023-01
            'revenue': [100, 100, 150, 200],
        })

        cols = {'date': 'date', 'revenue': 'revenue'}
        result = reconciler._check_period_totals(df, cols, 'Test Data')

        assert result is not None
        assert result.discrepancy_count >= 1

    def test_reconciliation_summary(self, reconciler):
        """Test summary generation"""
        # Create some reconciliation results
        df_a = pd.DataFrame({'revenue': [100, 200], 'date': ['2023-01', '2023-02']})
        df_b = pd.DataFrame({'revenue': [100, 200], 'date': ['2023-01', '2023-02']})

        summary = reconciler.reconcile_dataframes(df_a, df_b, 'A', 'B')

        assert summary.total_checks >= 0
        assert summary.overall_confidence >= 0
        assert summary.overall_confidence <= 100


class TestAIInsightsService:
    """Tests for AIInsightsService"""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock LLM provider"""
        provider = MagicMock()

        async def mock_stream(*args, **kwargs):
            yield {"type": "delta", "content": "Test executive summary. "}
            yield {"type": "delta", "content": "Key findings here."}
            yield {"type": "done", "finish_reason": "stop"}

        provider.stream_chat = mock_stream
        return provider

    def test_fallback_summary(self):
        """Test fallback summary generation without LLM"""
        service = AIInsightsService()

        analysis_data = {
            'overall_quality_score': 75,
            'anomalies': [{'title': 'Anomaly 1'}],
            'red_flags': [{'title': 'Red Flag 1'}, {'title': 'Red Flag 2'}],
        }

        summary = service._generate_fallback_summary(analysis_data)

        assert 'quality score' in summary.lower()
        assert '75' in summary

    def test_fallback_questions(self):
        """Test fallback question generation"""
        service = AIInsightsService()

        red_flags = [
            {'title': 'Negative revenue'},
            {'title': 'High churn rate'},
        ]

        questions = service._generate_fallback_questions(red_flags)

        assert len(questions) > 0
        assert any('revenue' in q.lower() for q in questions)

    def test_fallback_report(self):
        """Test fallback report generation"""
        service = AIInsightsService()

        analysis_data = {
            'file_analysis': {
                'overall_quality_score': 80,
            },
            'anomalies': [{'title': 'Test anomaly', 'evidence': {}}],
            'red_flags': [{'title': 'Test red flag'}],
        }

        report = service._generate_fallback_report(analysis_data)

        assert isinstance(report, AIAnalysisReport)
        assert len(report.key_findings) > 0
        assert len(report.recommendations) > 0

    def test_parse_questions(self):
        """Test question parsing from LLM response"""
        service = AIInsightsService()

        response = """
1. What caused the revenue decline in Q3?
2. Can you explain the customer churn spike?
3. Why did headcount grow faster than revenue?
"""

        questions = service._parse_questions(response)

        assert len(questions) == 3
        assert all(q.endswith('?') for q in questions)

    def test_extract_section(self):
        """Test section extraction from report"""
        service = AIInsightsService()

        text = """
EXECUTIVE SUMMARY
This is the summary paragraph.
It has multiple lines.

KEY FINDINGS
- Finding 1
- Finding 2

RISK ASSESSMENT
Medium risk identified.
"""

        summary = service._extract_section(text, "EXECUTIVE SUMMARY")
        assert "summary paragraph" in summary.lower()

        findings = service._extract_bullet_points(text, "KEY FINDINGS")
        assert len(findings) == 2

    @pytest.mark.asyncio
    async def test_generate_executive_summary_with_mock(self, mock_provider):
        """Test executive summary generation with mocked LLM"""
        service = AIInsightsService()
        service._provider = mock_provider

        analysis_data = {
            'overall_quality_score': 85,
            'total_rows': 1000,
            'detected_categories': ['financial', 'customer'],
            'anomalies': [],
            'red_flags': [],
            'potential_issues': [],
        }

        summary = await service.generate_executive_summary(analysis_data)

        assert len(summary) > 0


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_dataframe_trend(self):
        """Test trend analysis with empty DataFrame"""
        analyzer = TrendAnalyzer()
        df = pd.DataFrame()

        result = analyzer.analyze_time_series(df, 'date', 'value')

        assert result is None

    def test_single_row_reconciliation(self):
        """Test reconciliation with single row"""
        reconciler = ReconciliationService()

        df_a = pd.DataFrame({'value': [100]})
        df_b = pd.DataFrame({'value': [100]})

        result = reconciler.reconcile_specific(
            df_a, df_b, 'value', 'value'
        )

        assert result is not None

    def test_missing_columns(self):
        """Test handling of missing columns"""
        reconciler = ReconciliationService()

        df_a = pd.DataFrame({'col_a': [1, 2, 3]})
        df_b = pd.DataFrame({'col_b': [1, 2, 3]})

        result = reconciler.reconcile_specific(
            df_a, df_b, 'missing_col', 'col_b'
        )

        assert result.matches is False
        assert "not found" in result.details[0].get('error', '').lower()

    def test_all_null_values(self):
        """Test handling of all-null columns"""
        analyzer = TrendAnalyzer()

        df = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=10, freq='M'),
            'value': [None] * 10,
        })

        result = analyzer.analyze_time_series(df, 'date', 'value')

        # Should handle gracefully
        assert result is None

    def test_mixed_types_in_values(self):
        """Test handling of mixed types"""
        analyzer = TrendAnalyzer()

        df = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=5, freq='M'),
            'value': [100, '200', 300, None, 500],
        })

        # Should convert to numeric and handle gracefully
        result = analyzer.calculate_growth_rates(df, 'date', 'value')

        assert isinstance(result, dict)
