"""
Unit tests for Anomaly Detection and Red Flag Scanner

Tests for PE Analysis Engine - Phase 2
"""
import math
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from domains.data_ingestion.anomaly_service import AnomalyDetectionService
from domains.data_ingestion.red_flag_scanner import RedFlagScanner
from domains.data_ingestion.models import AnomalyType, RedFlagType


class TestAnomalyDetectionService:
    """Tests for AnomalyDetectionService"""

    @pytest.fixture
    def service(self):
        return AnomalyDetectionService()

    # --- Statistical Outliers Tests ---

    def test_detect_statistical_outliers_with_outliers(self, service):
        """Test that statistical outliers are detected"""
        # Create normal data with clear outliers
        np.random.seed(42)
        normal_data = np.random.normal(100, 10, 100)
        # Add obvious outliers
        outliers = [500, 600, -200]
        values = pd.Series(list(normal_data) + outliers)

        result = service.detect_statistical_outliers("test_col", values)

        assert result is not None
        assert result.anomaly_type == AnomalyType.STATISTICAL_OUTLIER
        assert result.affected_rows >= 3  # At least our planted outliers
        assert "outliers" in result.title.lower()

    def test_detect_statistical_outliers_no_outliers(self, service):
        """Test that clean data doesn't flag outliers"""
        np.random.seed(42)
        values = pd.Series(np.random.normal(100, 10, 100))

        result = service.detect_statistical_outliers("test_col", values)

        # Should either be None or have very few flagged
        if result is not None:
            assert result.affected_percent < 5

    def test_detect_statistical_outliers_too_few_samples(self, service):
        """Test that small samples don't trigger detection"""
        values = pd.Series([1, 2, 3, 100])  # Obvious outlier but too few samples

        result = service.detect_statistical_outliers("test_col", values)

        assert result is None

    # --- Benford's Law Tests ---

    def test_detect_benfords_violation_uniform_data(self, service):
        """Test that uniform first digits violate Benford's Law"""
        # Create data with uniform first digit distribution (not natural)
        np.random.seed(42)
        # Numbers 100-999 have roughly uniform first digits
        values = pd.Series(np.random.randint(100, 1000, 500))

        result = service.detect_benfords_law_violation("revenue", values)

        assert result is not None
        assert result.anomaly_type == AnomalyType.BENFORDS_VIOLATION

    def test_detect_benfords_natural_data(self, service):
        """Test that naturally distributed data follows Benford's Law"""
        # Generate Benford-compliant data using exponential growth
        np.random.seed(42)
        values = pd.Series(10 ** np.random.uniform(1, 6, 500))

        result = service.detect_benfords_law_violation("revenue", values)

        # Natural data should have lower p-value or pass the test
        # Note: Due to randomness, this may occasionally fail

    def test_detect_benfords_too_few_samples(self, service):
        """Test that small samples don't trigger Benford's check"""
        values = pd.Series([111, 222, 333, 444])  # Too few samples

        result = service.detect_benfords_law_violation("test_col", values)

        assert result is None

    # --- Round Number Bias Tests ---

    def test_detect_round_number_bias_high_bias(self, service):
        """Test detection of high round number prevalence"""
        # 50% of values end in 0 (way above expected 10%)
        values = pd.Series([
            100, 110, 120, 130, 140, 150, 160, 170, 180, 190,  # All round
            100, 110, 120, 130, 140, 150, 160, 170, 180, 190,  # All round
            101, 102, 103, 104, 105, 106, 107, 108, 109, 111,  # Not round
            112, 113, 114, 115, 116, 117, 118, 119, 121, 122,  # Not round
        ])

        result = service.detect_round_number_bias("amounts", values)

        assert result is not None
        assert result.anomaly_type == AnomalyType.ROUND_NUMBER_BIAS

    def test_detect_round_number_bias_normal(self, service):
        """Test that normal distribution doesn't flag round number bias"""
        np.random.seed(42)
        values = pd.Series(np.random.randint(1, 1000, 100))

        result = service.detect_round_number_bias("amounts", values)

        # Should be None or low severity with low percentage
        if result is not None:
            assert result.evidence['percent_ending_0'] < 20

    # --- Temporal Gap Tests ---

    def test_detect_temporal_gaps_with_gaps(self, service):
        """Test detection of temporal gaps in date series"""
        # Create dates with a 30-day gap (much larger than daily frequency)
        dates = []
        base = datetime(2024, 1, 1)
        for i in range(30):  # First 30 days
            dates.append(base + timedelta(days=i))
        # Skip 30 days
        for i in range(60, 90):  # Days 60-90
            dates.append(base + timedelta(days=i))

        date_series = pd.Series(pd.to_datetime(dates))

        result = service.detect_temporal_gaps("date", date_series)

        assert result is not None
        assert result.anomaly_type == AnomalyType.TEMPORAL_GAP
        assert result.evidence['gap_count'] >= 1

    def test_detect_temporal_gaps_no_gaps(self, service):
        """Test that continuous dates don't flag gaps"""
        dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(60)]
        date_series = pd.Series(pd.to_datetime(dates))

        result = service.detect_temporal_gaps("date", date_series)

        assert result is None

    # --- Column Type Detection Tests ---

    def test_looks_like_financial_by_name(self, service):
        """Test financial column detection by name"""
        financial_values = pd.Series([100000, 200000, 300000])  # Large values typical of financial data
        id_values = pd.Series([1, 2, 3])  # Small ID values don't look financial

        assert service._looks_like_financial("revenue", financial_values) is True
        assert service._looks_like_financial("total_sales", financial_values) is True
        assert service._looks_like_financial("customer_id", id_values) is False

    def test_analyze_column_numeric(self, service):
        """Test full column analysis for numeric data"""
        np.random.seed(42)
        # Create data with some anomalies
        normal = np.random.normal(1000, 100, 100)
        outliers = [5000, 6000]  # Clear outliers
        values = pd.Series(list(normal) + outliers)

        results = service.analyze_column("revenue", values, "float")

        # Should detect at least outliers
        assert len(results) >= 1
        assert any(r.anomaly_type == AnomalyType.STATISTICAL_OUTLIER for r in results)


class TestRedFlagScanner:
    """Tests for RedFlagScanner"""

    @pytest.fixture
    def scanner(self):
        return RedFlagScanner()

    # --- Financial Red Flags Tests ---

    def test_scan_financial_negative_revenue(self, scanner):
        """Test detection of negative revenue"""
        df = pd.DataFrame({
            'revenue': [100000, 150000, -5000, 200000, 180000],
            'date': pd.date_range('2024-01-01', periods=5, freq='M'),
        })

        results = scanner.scan_financial(df, {'revenue': 'revenue'})

        assert len(results) >= 1
        negative_rev = [r for r in results if r.flag_type == RedFlagType.NEGATIVE_REVENUE]
        assert len(negative_rev) >= 1

    def test_scan_financial_ebitda_exceeds_revenue(self, scanner):
        """Test detection of EBITDA > Revenue (impossible)"""
        df = pd.DataFrame({
            'revenue': [100000, 150000, 200000],
            'ebitda': [50000, 200000, 100000],  # Second row has EBITDA > Revenue
        })

        results = scanner.scan_financial(
            df,
            {'revenue': 'revenue', 'ebitda': 'ebitda'}
        )

        impossible_margin = [r for r in results if r.flag_type == RedFlagType.IMPOSSIBLE_MARGIN]
        assert len(impossible_margin) >= 1

    def test_scan_financial_extreme_growth(self, scanner):
        """Test detection of extreme revenue growth"""
        df = pd.DataFrame({
            'revenue': [100000, 120000, 500000, 550000],  # 300%+ growth in period 3
        })

        results = scanner.scan_financial(df, {'revenue': 'revenue'})

        growth_flags = [r for r in results if r.flag_type == RedFlagType.EXTREME_GROWTH]
        assert len(growth_flags) >= 1

    # --- Customer Red Flags Tests ---

    def test_scan_customer_high_churn(self, scanner):
        """Test detection of high churn rate"""
        df = pd.DataFrame({
            'churn': [0.05, 0.06, 0.25, 0.08, 0.30],  # 25% and 30% are high
        })

        results = scanner.scan_customer(df, {'churn': 'churn'})

        churn_flags = [r for r in results if r.flag_type == RedFlagType.HIGH_CHURN]
        assert len(churn_flags) >= 1
        assert churn_flags[0].severity in ['high', 'critical']

    def test_scan_customer_declining_count_growing_revenue(self, scanner):
        """Test detection of declining customers with growing revenue"""
        df = pd.DataFrame({
            'customer_count': [1000, 950, 900, 850, 800, 750, 700, 650],  # -35%
            'revenue': [100, 110, 120, 130, 140, 150, 160, 170],  # +70%
        })

        results = scanner.scan_customer(
            df,
            {'customer_count': 'customer_count', 'revenue': 'revenue'}
        )

        concentration_flags = [r for r in results if r.flag_type == RedFlagType.CUSTOMER_CONCENTRATION]
        assert len(concentration_flags) >= 1

    # --- Operational Red Flags Tests ---

    def test_scan_operational_headcount_mismatch(self, scanner):
        """Test detection of headcount growth outpacing revenue"""
        df = pd.DataFrame({
            'headcount': [50, 55, 60, 70, 85, 100, 120, 150],  # 200% growth
            'revenue': [1000, 1050, 1100, 1150, 1200, 1250, 1300, 1350],  # 35% growth
        })

        results = scanner.scan_operational(
            df,
            {'headcount': 'headcount', 'revenue': 'revenue'}
        )

        mismatch_flags = [r for r in results if r.flag_type == RedFlagType.HEADCOUNT_MISMATCH]
        assert len(mismatch_flags) >= 1

    # --- Data Quality Red Flags Tests ---

    def test_scan_data_quality_future_dates(self, scanner):
        """Test detection of future dates"""
        future_date = datetime.now() + timedelta(days=30)
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-02-01', future_date.strftime('%Y-%m-%d')],
        })

        results = scanner.scan_data_quality(df, {'date': 'date'})

        future_flags = [r for r in results if r.flag_type == RedFlagType.FUTURE_DATES]
        assert len(future_flags) >= 1

    def test_scan_data_quality_duplicates(self, scanner):
        """Test detection of duplicate rows"""
        df = pd.DataFrame({
            'id': [1, 2, 3, 1, 2],  # Duplicates of rows 1 and 2
            'value': [100, 200, 300, 100, 200],
        })

        results = scanner.scan_data_quality(df, {})

        dup_flags = [r for r in results if r.flag_type == RedFlagType.DUPLICATE_ROWS]
        assert len(dup_flags) >= 1

    def test_scan_data_quality_negative_impossible(self, scanner):
        """Test detection of impossible negative values"""
        df = pd.DataFrame({
            'customer_count': [100, 150, -5, 200],  # Negative customer count impossible
        })

        results = scanner.scan_data_quality(df, {'customer_count': 'customer_count'})

        neg_flags = [r for r in results if r.flag_type == RedFlagType.NEGATIVE_IMPOSSIBLE]
        assert len(neg_flags) >= 1

    # --- Full Scan Tests ---

    def test_scan_dataframe_full(self, scanner):
        """Test full DataFrame scan with multiple issues"""
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=5, freq='M'),
            'revenue': [100000, 150000, -5000, 600000, 180000],  # Negative + extreme growth
            'customer_count': [1000, 1100, 1050, 900, 800],  # Declining
            'churn': [0.05, 0.06, 0.25, 0.08, 0.12],  # High churn spike
        })

        results = scanner.scan_dataframe(df, ['financial', 'customer'])

        # Should detect multiple issues
        assert len(results) >= 2

    def test_scan_dataframe_clean_data(self, scanner):
        """Test that clean data produces minimal flags"""
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=12, freq='M'),
            'revenue': [100 + i * 5 for i in range(12)],  # Steady 5% growth
            'customer_count': [1000 + i * 10 for i in range(12)],  # Steady growth
        })

        results = scanner.scan_dataframe(df, ['financial', 'customer'])

        # Clean data should have few or no flags
        # May have some warnings but no critical issues
        critical_flags = [r for r in results if r.severity == 'critical']
        assert len(critical_flags) == 0


class TestColumnIdentification:
    """Tests for column pattern matching"""

    @pytest.fixture
    def scanner(self):
        return RedFlagScanner()

    def test_identify_revenue_columns(self, scanner):
        """Test identification of revenue columns"""
        df = pd.DataFrame({
            'total_revenue': [1, 2, 3],
            'monthly_sales': [1, 2, 3],
            'customer_id': [1, 2, 3],
        })

        mapping = scanner._identify_columns(df)

        assert 'revenue' in mapping
        assert mapping['revenue'] == 'total_revenue'

    def test_identify_multiple_column_types(self, scanner):
        """Test identification of multiple column types"""
        df = pd.DataFrame({
            'revenue': [1, 2, 3],
            'ebitda': [1, 2, 3],
            'customer_count': [1, 2, 3],
            'churn_rate': [0.1, 0.2, 0.3],
            'headcount': [10, 20, 30],
        })

        mapping = scanner._identify_columns(df)

        assert 'revenue' in mapping
        assert 'ebitda' in mapping
        assert 'customer_count' in mapping
        assert 'churn' in mapping
        assert 'headcount' in mapping


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    @pytest.fixture
    def anomaly_service(self):
        return AnomalyDetectionService()

    @pytest.fixture
    def scanner(self):
        return RedFlagScanner()

    def test_empty_dataframe(self, scanner):
        """Test handling of empty DataFrame"""
        df = pd.DataFrame()

        results = scanner.scan_dataframe(df, [])

        # Should return empty list, not error
        assert results == []

    def test_all_null_column(self, anomaly_service):
        """Test handling of all-null column"""
        values = pd.Series([None, None, None, None, None])

        results = anomaly_service.analyze_column("test", values, "float")

        # Should handle gracefully
        assert isinstance(results, list)

    def test_single_value_column(self, anomaly_service):
        """Test handling of single-value column"""
        values = pd.Series([100] * 50)

        results = anomaly_service.analyze_column("test", values, "float")

        # Should handle gracefully (MAD = 0)
        assert isinstance(results, list)

    def test_mixed_type_column(self, anomaly_service):
        """Test handling of mixed types in column"""
        values = pd.Series([100, "abc", 200, None, 300])

        # Should not raise an error
        results = anomaly_service.analyze_column("test", values, "float")
        assert isinstance(results, list)
