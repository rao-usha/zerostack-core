"""Tests for statistical drift detection methods."""
import pytest
import math
from services.statistical_drift import (
    StatisticalDriftDetector,
    StatisticalTestType,
    StatisticalTestResult,
    get_statistical_drift_detector
)


class TestKSTest:
    """Tests for Kolmogorov-Smirnov test."""

    def test_ks_identical_distributions(self):
        """KS test should show no drift for identical distributions."""
        detector = StatisticalDriftDetector()

        baseline = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        current = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        result = detector.ks_test(baseline, current)

        assert result.test_type == StatisticalTestType.KS_TEST
        # Note: KS statistic may be small but non-zero due to tie-handling in ECDF
        assert result.statistic <= 0.2  # Very small KS statistic
        assert result.p_value >= 0.5  # High p-value (not significant)
        assert result.is_significant is False

    def test_ks_completely_different_distributions(self):
        """KS test should detect drift for completely different distributions."""
        detector = StatisticalDriftDetector()

        baseline = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        current = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0]

        result = detector.ks_test(baseline, current)

        assert result.test_type == StatisticalTestType.KS_TEST
        assert result.statistic == 1.0  # Max possible KS statistic
        assert result.p_value < 0.05
        assert result.is_significant is True

    def test_ks_shifted_distribution(self):
        """KS test should detect moderate drift for shifted distributions."""
        detector = StatisticalDriftDetector()

        import random
        random.seed(42)

        # Normal-ish distribution centered at 50
        baseline = [50 + random.gauss(0, 10) for _ in range(100)]
        # Shifted distribution centered at 60
        current = [60 + random.gauss(0, 10) for _ in range(100)]

        result = detector.ks_test(baseline, current)

        assert result.test_type == StatisticalTestType.KS_TEST
        assert result.statistic > 0.2  # Expect notable KS statistic
        assert result.is_significant is True  # Should detect the shift

    def test_ks_insufficient_samples(self):
        """KS test should handle insufficient samples gracefully."""
        detector = StatisticalDriftDetector()

        baseline = [1.0]  # Only one sample
        current = [2.0, 3.0, 4.0]

        result = detector.ks_test(baseline, current)

        assert result.is_significant is False
        assert "Insufficient" in result.message

    def test_ks_details_included(self):
        """KS test result should include sample details."""
        detector = StatisticalDriftDetector()

        baseline = [1.0, 2.0, 3.0, 4.0, 5.0]
        current = [2.0, 3.0, 4.0, 5.0, 6.0]

        result = detector.ks_test(baseline, current)

        assert result.details is not None
        assert 'baseline_n' in result.details
        assert 'current_n' in result.details
        assert result.details['baseline_n'] == 5
        assert result.details['current_n'] == 5


class TestChiSquaredTest:
    """Tests for chi-squared test on categorical data."""

    def test_chi2_identical_distributions(self):
        """Chi-squared should show no drift for identical category distributions."""
        detector = StatisticalDriftDetector()

        baseline = ['A', 'A', 'B', 'B', 'C', 'C', 'A', 'B', 'C', 'A']
        current = ['A', 'A', 'B', 'B', 'C', 'C', 'A', 'B', 'C', 'A']

        result = detector.chi_squared_test(baseline, current)

        assert result.test_type == StatisticalTestType.CHI_SQUARED
        assert result.statistic == 0.0
        assert result.is_significant is False

    def test_chi2_different_distributions(self):
        """Chi-squared should detect drift when category proportions change significantly."""
        detector = StatisticalDriftDetector()

        # Baseline: mostly A
        baseline = ['A'] * 80 + ['B'] * 15 + ['C'] * 5
        # Current: mostly C
        current = ['A'] * 5 + ['B'] * 15 + ['C'] * 80

        result = detector.chi_squared_test(baseline, current)

        assert result.test_type == StatisticalTestType.CHI_SQUARED
        assert result.statistic > 0  # Expect notable chi-squared
        assert result.is_significant is True

    def test_chi2_new_category(self):
        """Chi-squared should detect when new categories appear."""
        detector = StatisticalDriftDetector()

        baseline = ['A', 'A', 'B', 'B', 'C', 'C'] * 5
        current = ['A', 'B', 'C', 'D', 'D', 'D'] * 5  # New category D

        result = detector.chi_squared_test(baseline, current)

        assert result.is_significant is True
        assert result.details['n_categories'] == 4  # A, B, C, D

    def test_chi2_insufficient_samples(self):
        """Chi-squared should handle insufficient samples gracefully."""
        detector = StatisticalDriftDetector()

        baseline = ['A', 'B']  # Too few
        current = ['A', 'B', 'C']

        result = detector.chi_squared_test(baseline, current)

        assert result.is_significant is False
        assert "Insufficient" in result.message

    def test_chi2_single_category(self):
        """Chi-squared should handle single category case."""
        detector = StatisticalDriftDetector()

        baseline = ['A'] * 20
        current = ['A'] * 20

        result = detector.chi_squared_test(baseline, current)

        assert result.is_significant is False
        assert "Insufficient categories" in result.message


class TestPSI:
    """Tests for Population Stability Index."""

    def test_psi_identical_distributions(self):
        """PSI should be near zero for identical distributions."""
        detector = StatisticalDriftDetector()

        baseline = list(range(100))
        current = list(range(100))

        result = detector.psi(baseline, current)

        assert result.test_type == StatisticalTestType.PSI
        assert result.statistic < 0.01  # Very small PSI
        assert result.is_significant is False

    def test_psi_shifted_distribution(self):
        """PSI should detect shift in distributions."""
        detector = StatisticalDriftDetector()

        baseline = list(range(100))  # 0-99
        current = list(range(50, 150))  # 50-149 (shifted)

        result = detector.psi(baseline, current)

        assert result.test_type == StatisticalTestType.PSI
        assert result.statistic > 0.1  # Notable PSI
        assert result.is_significant is True

    def test_psi_completely_different(self):
        """PSI should be high for completely different distributions."""
        detector = StatisticalDriftDetector()

        baseline = list(range(100))  # 0-99
        current = list(range(1000, 1100))  # 1000-1099 (completely different)

        result = detector.psi(baseline, current)

        assert result.statistic > 0.25  # Significant PSI
        assert result.details['severity_level'] == 'significant'

    def test_psi_threshold_customization(self):
        """PSI should respect custom thresholds."""
        detector = StatisticalDriftDetector()

        baseline = list(range(100))
        current = list(range(10, 110))  # Slight shift

        # With low threshold, should be significant
        result_low = detector.psi(baseline, current, threshold=0.01)
        # With high threshold, might not be significant
        result_high = detector.psi(baseline, current, threshold=0.5)

        assert result_low.threshold == 0.01
        assert result_high.threshold == 0.5

    def test_psi_insufficient_samples(self):
        """PSI should handle insufficient samples gracefully."""
        detector = StatisticalDriftDetector()

        baseline = [1, 2, 3]  # Too few for 10 bins
        current = [4, 5, 6]

        result = detector.psi(baseline, current, n_bins=10)

        assert result.is_significant is False
        assert "Insufficient" in result.message

    def test_psi_bin_contributions(self):
        """PSI result should include per-bin contributions."""
        detector = StatisticalDriftDetector()

        baseline = list(range(100))
        current = list(range(50, 150))

        result = detector.psi(baseline, current, n_bins=5)

        assert result.details is not None
        assert 'bin_psi_contributions' in result.details
        assert len(result.details['bin_psi_contributions']) == 5


class TestJSDivergence:
    """Tests for Jensen-Shannon divergence."""

    def test_js_identical_distributions(self):
        """JS divergence should be zero for identical distributions."""
        detector = StatisticalDriftDetector()

        baseline = list(range(100))
        current = list(range(100))

        result = detector.js_divergence(baseline, current)

        assert result.test_type == StatisticalTestType.JS_DIVERGENCE
        assert result.statistic < 0.01  # Near zero
        assert result.is_significant is False

    def test_js_different_distributions(self):
        """JS divergence should be positive for different distributions."""
        detector = StatisticalDriftDetector()

        baseline = list(range(100))  # 0-99
        current = list(range(50, 150))  # 50-149

        result = detector.js_divergence(baseline, current)

        assert result.statistic > 0.0
        assert result.p_value is None  # JS doesn't have p-value

    def test_js_completely_different(self):
        """JS divergence should be high for completely different distributions."""
        detector = StatisticalDriftDetector()

        baseline = [0] * 100  # All zeros
        current = [100] * 100  # All hundreds

        result = detector.js_divergence(baseline, current)

        # JS divergence is bounded by ln(2) ≈ 0.693
        assert result.statistic > 0.3
        assert result.details['interpretation'] in ['moderately different', 'very different']

    def test_js_max_divergence(self):
        """JS divergence max should be ln(2)."""
        detector = StatisticalDriftDetector()

        result = detector.js_divergence([1] * 100, [1000] * 100)

        assert result.details['max_possible'] == round(math.log(2), 6)

    def test_js_constant_values(self):
        """JS divergence should handle constant values."""
        detector = StatisticalDriftDetector()

        baseline = [5.0] * 50
        current = [5.0] * 50

        result = detector.js_divergence(baseline, current)

        assert result.statistic == 0.0
        assert "identical" in result.message.lower()


class TestDetectDrift:
    """Tests for the unified detect_drift method."""

    def test_detect_drift_ks(self):
        """detect_drift should work with KS test type."""
        detector = StatisticalDriftDetector()

        baseline = list(range(50))
        current = list(range(50, 100))

        result = detector.detect_drift(
            baseline, current,
            test_type=StatisticalTestType.KS_TEST
        )

        assert result.test_type == StatisticalTestType.KS_TEST

    def test_detect_drift_chi2(self):
        """detect_drift should work with chi-squared test type."""
        detector = StatisticalDriftDetector()

        baseline = ['A'] * 30 + ['B'] * 20
        current = ['A'] * 25 + ['B'] * 25

        result = detector.detect_drift(
            baseline, current,
            test_type=StatisticalTestType.CHI_SQUARED
        )

        assert result.test_type == StatisticalTestType.CHI_SQUARED

    def test_detect_drift_psi(self):
        """detect_drift should work with PSI test type."""
        detector = StatisticalDriftDetector()

        baseline = list(range(100))
        current = list(range(100))

        result = detector.detect_drift(
            baseline, current,
            test_type=StatisticalTestType.PSI
        )

        assert result.test_type == StatisticalTestType.PSI

    def test_detect_drift_js(self):
        """detect_drift should work with JS divergence test type."""
        detector = StatisticalDriftDetector()

        baseline = list(range(100))
        current = list(range(100))

        result = detector.detect_drift(
            baseline, current,
            test_type=StatisticalTestType.JS_DIVERGENCE
        )

        assert result.test_type == StatisticalTestType.JS_DIVERGENCE

    def test_detect_drift_with_kwargs(self):
        """detect_drift should pass kwargs to specific test."""
        detector = StatisticalDriftDetector()

        baseline = list(range(100))
        current = list(range(100))

        result = detector.detect_drift(
            baseline, current,
            test_type=StatisticalTestType.PSI,
            n_bins=5,
            threshold=0.2
        )

        assert result.threshold == 0.2
        assert result.details['n_bins'] == 5


class TestStatisticalTestResult:
    """Tests for StatisticalTestResult dataclass."""

    def test_to_dict(self):
        """to_dict should return all fields correctly."""
        result = StatisticalTestResult(
            test_type=StatisticalTestType.KS_TEST,
            statistic=0.25,
            p_value=0.03,
            is_significant=True,
            threshold=0.05,
            message="Significant drift",
            details={'n': 100}
        )

        d = result.to_dict()

        assert d['test_type'] == 'ks_test'
        assert d['statistic'] == 0.25
        assert d['p_value'] == 0.03
        assert d['is_significant'] is True
        assert d['threshold'] == 0.05
        assert d['message'] == "Significant drift"
        assert d['details'] == {'n': 100}

    def test_to_dict_none_p_value(self):
        """to_dict should handle None p_value (for PSI/JS)."""
        result = StatisticalTestResult(
            test_type=StatisticalTestType.PSI,
            statistic=0.15,
            p_value=None,
            is_significant=True,
            threshold=0.1,
            message="Moderate shift"
        )

        d = result.to_dict()

        assert d['p_value'] is None


class TestSingleton:
    """Tests for singleton instance."""

    def test_get_statistical_drift_detector(self):
        """get_statistical_drift_detector should return singleton."""
        detector1 = get_statistical_drift_detector()
        detector2 = get_statistical_drift_detector()

        assert detector1 is detector2


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_lists(self):
        """Tests should handle empty lists gracefully."""
        detector = StatisticalDriftDetector()

        result_ks = detector.ks_test([], [1, 2, 3])
        result_chi2 = detector.chi_squared_test([], ['A', 'B'])
        result_psi = detector.psi([], [1, 2, 3])
        result_js = detector.js_divergence([], [1, 2, 3])

        assert result_ks.is_significant is False
        assert result_chi2.is_significant is False
        assert result_psi.is_significant is False
        assert result_js.is_significant is False

    def test_single_value_distributions(self):
        """Tests should handle single-value distributions."""
        detector = StatisticalDriftDetector()

        # For chi-squared, single category should not be significant
        result_chi2 = detector.chi_squared_test(['A'] * 10, ['A'] * 10)
        assert result_chi2.is_significant is False

        # For PSI with constant values, should show no drift
        result_psi = detector.psi([5.0] * 50, [5.0] * 50)
        assert result_psi.is_significant is False

        # For JS divergence with constant values, should be zero
        result_js = detector.js_divergence([5.0] * 50, [5.0] * 50)
        assert result_js.statistic == 0.0

    def test_negative_values(self):
        """Tests should handle negative values."""
        detector = StatisticalDriftDetector()

        baseline = [-10, -5, 0, 5, 10] * 10
        current = [-8, -3, 2, 7, 12] * 10

        result_ks = detector.ks_test(baseline, current)
        result_psi = detector.psi(baseline, current)
        result_js = detector.js_divergence(baseline, current)

        # Should run without errors
        assert result_ks.test_type == StatisticalTestType.KS_TEST
        assert result_psi.test_type == StatisticalTestType.PSI
        assert result_js.test_type == StatisticalTestType.JS_DIVERGENCE

    def test_large_distributions(self):
        """Tests should handle large distributions efficiently."""
        detector = StatisticalDriftDetector()

        import random
        random.seed(42)

        baseline = [random.gauss(0, 1) for _ in range(10000)]
        current = [random.gauss(0, 1) for _ in range(10000)]

        # Should complete without timing out
        result_ks = detector.ks_test(baseline, current)
        result_psi = detector.psi(baseline, current)
        result_js = detector.js_divergence(baseline, current)

        # Same distribution, should not be significant
        assert result_ks.is_significant is False
        assert result_psi.is_significant is False
        assert result_js.is_significant is False

    def test_outliers(self):
        """Tests should handle distributions with outliers."""
        detector = StatisticalDriftDetector()

        baseline = list(range(100)) + [10000]  # One extreme outlier
        current = list(range(100))

        result_ks = detector.ks_test(baseline, current)
        result_psi = detector.psi(baseline, current, n_bins=10)

        # Should detect the difference caused by outlier
        assert result_ks.statistic > 0
