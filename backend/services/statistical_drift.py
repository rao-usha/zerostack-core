"""Statistical drift detection methods.

Provides statistical tests for detecting distribution drift in ML models:
- KS-test (Kolmogorov-Smirnov) for continuous numerical data
- Chi-squared test for categorical data
- PSI (Population Stability Index) for distribution stability
- Jensen-Shannon divergence for distribution similarity

These tests compare two distributions (baseline vs current) and return
a p-value or score indicating whether significant drift has occurred.
"""
import logging
import math
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StatisticalTestType(str, Enum):
    """Types of statistical drift tests."""
    KS_TEST = "ks_test"  # Kolmogorov-Smirnov test
    CHI_SQUARED = "chi_squared"  # Chi-squared test
    PSI = "psi"  # Population Stability Index
    JS_DIVERGENCE = "js_divergence"  # Jensen-Shannon divergence


@dataclass
class StatisticalTestResult:
    """Result of a statistical drift test."""
    test_type: StatisticalTestType
    statistic: float  # Test statistic (KS statistic, chi2, PSI, or JS divergence)
    p_value: Optional[float]  # P-value (None for PSI/JS which don't have p-values)
    is_significant: bool  # Whether drift is statistically significant
    threshold: float  # Threshold used for significance
    message: str
    details: Optional[Dict] = None

    def to_dict(self) -> dict:
        return {
            'test_type': self.test_type.value,
            'statistic': self.statistic,
            'p_value': self.p_value,
            'is_significant': self.is_significant,
            'threshold': self.threshold,
            'message': self.message,
            'details': self.details
        }


class StatisticalDriftDetector:
    """Performs statistical tests for distribution drift."""

    # Default significance levels and thresholds
    DEFAULT_ALPHA = 0.05  # p-value threshold for statistical significance
    DEFAULT_PSI_THRESHOLD = 0.1  # PSI < 0.1 = no drift, 0.1-0.25 = moderate, > 0.25 = significant
    DEFAULT_JS_THRESHOLD = 0.1  # JS divergence threshold

    def ks_test(
        self,
        baseline: List[float],
        current: List[float],
        alpha: float = DEFAULT_ALPHA
    ) -> StatisticalTestResult:
        """
        Perform two-sample Kolmogorov-Smirnov test.

        Tests whether two samples come from the same continuous distribution.
        Good for detecting shifts in numerical feature distributions.

        Args:
            baseline: Baseline distribution samples
            current: Current distribution samples
            alpha: Significance level (default 0.05)

        Returns:
            StatisticalTestResult with KS statistic and p-value
        """
        if len(baseline) < 2 or len(current) < 2:
            return StatisticalTestResult(
                test_type=StatisticalTestType.KS_TEST,
                statistic=0.0,
                p_value=1.0,
                is_significant=False,
                threshold=alpha,
                message="Insufficient samples for KS test (need at least 2 per distribution)"
            )

        # Sort both distributions
        baseline_sorted = sorted(baseline)
        current_sorted = sorted(current)

        n1, n2 = len(baseline_sorted), len(current_sorted)

        # Compute empirical CDFs and find max difference
        ks_statistic = self._compute_ks_statistic(baseline_sorted, current_sorted)

        # Compute approximate p-value using the asymptotic formula
        # For large samples, KS statistic * sqrt(n1*n2/(n1+n2)) follows Kolmogorov distribution
        en = math.sqrt(n1 * n2 / (n1 + n2))
        p_value = self._ks_p_value(ks_statistic * en)

        is_significant = p_value < alpha

        if is_significant:
            message = f"Significant distribution drift detected (KS={ks_statistic:.4f}, p={p_value:.4f} < {alpha})"
        else:
            message = f"No significant drift (KS={ks_statistic:.4f}, p={p_value:.4f})"

        return StatisticalTestResult(
            test_type=StatisticalTestType.KS_TEST,
            statistic=round(ks_statistic, 6),
            p_value=round(p_value, 6),
            is_significant=is_significant,
            threshold=alpha,
            message=message,
            details={
                'baseline_n': n1,
                'current_n': n2,
                'baseline_mean': round(sum(baseline) / n1, 4),
                'current_mean': round(sum(current) / n2, 4)
            }
        )

    def _compute_ks_statistic(self, sorted1: List[float], sorted2: List[float]) -> float:
        """Compute the KS statistic (max difference between ECDFs)."""
        n1, n2 = len(sorted1), len(sorted2)

        # Merge both sorted arrays and track which distribution each value came from
        all_values = []
        for v in sorted1:
            all_values.append((v, 1, 0))  # (value, from_dist1, from_dist2)
        for v in sorted2:
            all_values.append((v, 0, 1))
        all_values.sort(key=lambda x: x[0])

        # Walk through and compute ECDF difference at each point
        cdf1, cdf2 = 0, 0
        max_diff = 0.0

        for _, d1, d2 in all_values:
            cdf1 += d1 / n1
            cdf2 += d2 / n2
            diff = abs(cdf1 - cdf2)
            if diff > max_diff:
                max_diff = diff

        return max_diff

    def _ks_p_value(self, z: float) -> float:
        """
        Compute approximate p-value for KS test using asymptotic formula.

        Uses the Kolmogorov distribution approximation:
        P(D > z) ≈ 2 * sum_{k=1}^{inf} (-1)^{k-1} * exp(-2*k^2*z^2)
        """
        if z <= 0:
            return 1.0
        if z > 3:
            return 0.0  # Essentially zero for large z

        # Compute using first few terms of the series
        p = 0.0
        for k in range(1, 101):
            term = ((-1) ** (k - 1)) * math.exp(-2 * k * k * z * z)
            p += term
            if abs(term) < 1e-10:
                break

        return min(1.0, max(0.0, 2 * p))

    def chi_squared_test(
        self,
        baseline: List[Union[str, int]],
        current: List[Union[str, int]],
        alpha: float = DEFAULT_ALPHA
    ) -> StatisticalTestResult:
        """
        Perform chi-squared test for categorical distributions.

        Tests whether the distribution of categories has changed significantly.
        Good for categorical features like gender, region, product_type, etc.

        Args:
            baseline: Baseline category samples
            current: Current category samples
            alpha: Significance level (default 0.05)

        Returns:
            StatisticalTestResult with chi-squared statistic and p-value
        """
        if len(baseline) < 5 or len(current) < 5:
            return StatisticalTestResult(
                test_type=StatisticalTestType.CHI_SQUARED,
                statistic=0.0,
                p_value=1.0,
                is_significant=False,
                threshold=alpha,
                message="Insufficient samples for chi-squared test (need at least 5 per distribution)"
            )

        # Count frequencies
        baseline_counts = self._count_frequencies(baseline)
        current_counts = self._count_frequencies(current)

        # Get all unique categories
        all_categories = set(baseline_counts.keys()) | set(current_counts.keys())

        # Total counts
        n_baseline = len(baseline)
        n_current = len(current)
        n_total = n_baseline + n_current

        # Compute chi-squared statistic
        chi2 = 0.0
        df = len(all_categories) - 1  # degrees of freedom

        if df < 1:
            return StatisticalTestResult(
                test_type=StatisticalTestType.CHI_SQUARED,
                statistic=0.0,
                p_value=1.0,
                is_significant=False,
                threshold=alpha,
                message="Insufficient categories for chi-squared test (need at least 2)"
            )

        for cat in all_categories:
            o_baseline = baseline_counts.get(cat, 0)
            o_current = current_counts.get(cat, 0)
            observed_total = o_baseline + o_current

            # Expected counts under null hypothesis (same distribution)
            e_baseline = observed_total * (n_baseline / n_total)
            e_current = observed_total * (n_current / n_total)

            # Add to chi-squared (with continuity correction for small counts)
            if e_baseline > 0:
                chi2 += ((o_baseline - e_baseline) ** 2) / e_baseline
            if e_current > 0:
                chi2 += ((o_current - e_current) ** 2) / e_current

        # Compute p-value using chi-squared distribution approximation
        p_value = self._chi2_p_value(chi2, df)

        is_significant = p_value < alpha

        if is_significant:
            message = f"Significant category distribution drift (χ²={chi2:.4f}, df={df}, p={p_value:.4f} < {alpha})"
        else:
            message = f"No significant drift (χ²={chi2:.4f}, df={df}, p={p_value:.4f})"

        return StatisticalTestResult(
            test_type=StatisticalTestType.CHI_SQUARED,
            statistic=round(chi2, 6),
            p_value=round(p_value, 6),
            is_significant=is_significant,
            threshold=alpha,
            message=message,
            details={
                'degrees_of_freedom': df,
                'n_categories': len(all_categories),
                'baseline_n': n_baseline,
                'current_n': n_current,
                'baseline_distribution': {k: round(v/n_baseline, 4) for k, v in baseline_counts.items()},
                'current_distribution': {k: round(v/n_current, 4) for k, v in current_counts.items()}
            }
        )

    def _count_frequencies(self, values: List[Union[str, int]]) -> Dict[Union[str, int], int]:
        """Count frequency of each unique value."""
        counts = {}
        for v in values:
            counts[v] = counts.get(v, 0) + 1
        return counts

    def _chi2_p_value(self, chi2: float, df: int) -> float:
        """
        Compute approximate p-value for chi-squared distribution.

        Uses Wilson-Hilferty transformation for approximation.
        """
        if chi2 <= 0 or df <= 0:
            return 1.0

        # Wilson-Hilferty approximation
        # Transform chi2/df to approximately normal
        if df > 100:
            # For large df, use normal approximation
            z = (chi2 - df) / math.sqrt(2 * df)
            return 1 - self._normal_cdf(z)

        # For smaller df, use a more accurate approximation
        # based on incomplete gamma function approximation
        x = chi2 / 2
        k = df / 2

        # Use regularized incomplete gamma function approximation
        return 1 - self._regularized_gamma_p(k, x)

    def _normal_cdf(self, z: float) -> float:
        """Compute standard normal CDF using error function approximation."""
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))

    def _regularized_gamma_p(self, a: float, x: float) -> float:
        """
        Compute regularized lower incomplete gamma function P(a, x).

        Uses series expansion for small x, continued fraction for large x.
        """
        if x < 0 or a <= 0:
            return 0.0
        if x == 0:
            return 0.0
        if x > 100 + a:
            return 1.0  # Essentially complete for large x

        # Use series expansion: P(a,x) = gamma(a,x) / Gamma(a)
        # gamma(a,x) = x^a * e^(-x) * sum_{n=0}^{inf} x^n / (a * (a+1) * ... * (a+n))
        if x < a + 1:
            # Series expansion
            sum_val = 1.0 / a
            term = 1.0 / a
            for n in range(1, 200):
                term *= x / (a + n)
                sum_val += term
                if abs(term) < 1e-10:
                    break
            return sum_val * math.exp(-x + a * math.log(x) - math.lgamma(a))
        else:
            # For large x, P(a,x) ≈ 1
            return 1 - self._regularized_gamma_q(a, x)

    def _regularized_gamma_q(self, a: float, x: float) -> float:
        """Compute upper incomplete gamma Q(a,x) = 1 - P(a,x)."""
        # Continued fraction approximation for Q(a,x)
        # Using Lentz's method
        if x < a + 1:
            return 1 - self._regularized_gamma_p(a, x)

        # Continued fraction
        b = x + 1 - a
        c = 1.0 / 1e-30
        d = 1.0 / b
        h = d

        for i in range(1, 200):
            an = -i * (i - a)
            b += 2
            d = an * d + b
            if abs(d) < 1e-30:
                d = 1e-30
            c = b + an / c
            if abs(c) < 1e-30:
                c = 1e-30
            d = 1.0 / d
            delta = d * c
            h *= delta
            if abs(delta - 1) < 1e-10:
                break

        return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h

    def psi(
        self,
        baseline: List[float],
        current: List[float],
        n_bins: int = 10,
        threshold: float = DEFAULT_PSI_THRESHOLD
    ) -> StatisticalTestResult:
        """
        Calculate Population Stability Index (PSI).

        PSI measures how much a distribution has shifted from baseline.
        Common interpretation:
        - PSI < 0.1: No significant shift
        - 0.1 <= PSI < 0.25: Moderate shift, monitor
        - PSI >= 0.25: Significant shift, action required

        Args:
            baseline: Baseline distribution samples
            current: Current distribution samples
            n_bins: Number of bins for discretization (default 10)
            threshold: PSI threshold for significance (default 0.1)

        Returns:
            StatisticalTestResult with PSI value
        """
        if len(baseline) < n_bins or len(current) < n_bins:
            return StatisticalTestResult(
                test_type=StatisticalTestType.PSI,
                statistic=0.0,
                p_value=None,
                is_significant=False,
                threshold=threshold,
                message=f"Insufficient samples for PSI (need at least {n_bins} per distribution)"
            )

        # Create bins based on baseline quantiles
        baseline_sorted = sorted(baseline)
        n = len(baseline_sorted)
        bin_edges = [baseline_sorted[0] - 1e-10]  # Start slightly below min

        for i in range(1, n_bins):
            idx = int(n * i / n_bins)
            bin_edges.append(baseline_sorted[idx])
        bin_edges.append(baseline_sorted[-1] + 1e-10)  # End slightly above max

        # Count baseline and current in each bin
        baseline_counts = self._bin_counts(baseline, bin_edges)
        current_counts = self._bin_counts(current, bin_edges)

        # Calculate PSI
        n_baseline = len(baseline)
        n_current = len(current)
        psi_value = 0.0
        bin_psi = []

        for i in range(n_bins):
            # Proportions with small epsilon to avoid log(0)
            p_baseline = (baseline_counts[i] + 0.5) / (n_baseline + n_bins * 0.5)
            p_current = (current_counts[i] + 0.5) / (n_current + n_bins * 0.5)

            # PSI for this bin
            bin_contribution = (p_current - p_baseline) * math.log(p_current / p_baseline)
            psi_value += bin_contribution
            bin_psi.append(round(bin_contribution, 6))

        is_significant = psi_value >= threshold

        if psi_value < 0.1:
            severity = "minimal"
        elif psi_value < 0.25:
            severity = "moderate"
        else:
            severity = "significant"

        message = f"PSI = {psi_value:.4f} ({severity} shift)"
        if is_significant:
            message += f" - exceeds threshold {threshold}"

        return StatisticalTestResult(
            test_type=StatisticalTestType.PSI,
            statistic=round(psi_value, 6),
            p_value=None,  # PSI doesn't have a p-value
            is_significant=is_significant,
            threshold=threshold,
            message=message,
            details={
                'n_bins': n_bins,
                'baseline_n': n_baseline,
                'current_n': n_current,
                'bin_psi_contributions': bin_psi,
                'severity_level': severity
            }
        )

    def _bin_counts(self, values: List[float], bin_edges: List[float]) -> List[int]:
        """Count values in each bin."""
        n_bins = len(bin_edges) - 1
        counts = [0] * n_bins

        for v in values:
            for i in range(n_bins):
                if bin_edges[i] <= v < bin_edges[i + 1]:
                    counts[i] += 1
                    break
            else:
                # Value equals last edge
                counts[n_bins - 1] += 1

        return counts

    def js_divergence(
        self,
        baseline: List[float],
        current: List[float],
        n_bins: int = 10,
        threshold: float = DEFAULT_JS_THRESHOLD
    ) -> StatisticalTestResult:
        """
        Calculate Jensen-Shannon divergence.

        JS divergence is a symmetric measure of similarity between distributions.
        It's the average of KL divergences: JS(P||Q) = 0.5 * KL(P||M) + 0.5 * KL(Q||M)
        where M = 0.5 * (P + Q).

        Range: [0, ln(2)] ≈ [0, 0.693]
        - 0 means identical distributions
        - Higher values indicate more dissimilar distributions

        Args:
            baseline: Baseline distribution samples
            current: Current distribution samples
            n_bins: Number of bins for discretization (default 10)
            threshold: JS divergence threshold for significance (default 0.1)

        Returns:
            StatisticalTestResult with JS divergence value
        """
        if len(baseline) < n_bins or len(current) < n_bins:
            return StatisticalTestResult(
                test_type=StatisticalTestType.JS_DIVERGENCE,
                statistic=0.0,
                p_value=None,
                is_significant=False,
                threshold=threshold,
                message=f"Insufficient samples for JS divergence (need at least {n_bins} per distribution)"
            )

        # Create bins based on combined data range
        all_values = baseline + current
        min_val, max_val = min(all_values), max(all_values)
        bin_width = (max_val - min_val) / n_bins

        if bin_width == 0:
            # All values are the same
            return StatisticalTestResult(
                test_type=StatisticalTestType.JS_DIVERGENCE,
                statistic=0.0,
                p_value=None,
                is_significant=False,
                threshold=threshold,
                message="All values are identical, JS divergence = 0"
            )

        bin_edges = [min_val + i * bin_width for i in range(n_bins + 1)]
        bin_edges[-1] += 1e-10  # Ensure max value is included

        # Get probability distributions
        baseline_counts = self._bin_counts(baseline, bin_edges)
        current_counts = self._bin_counts(current, bin_edges)

        n_baseline = len(baseline)
        n_current = len(current)

        # Convert to probabilities with smoothing
        p = [(c + 0.5) / (n_baseline + n_bins * 0.5) for c in baseline_counts]
        q = [(c + 0.5) / (n_current + n_bins * 0.5) for c in current_counts]

        # Compute mixture distribution M = 0.5 * (P + Q)
        m = [0.5 * (p[i] + q[i]) for i in range(n_bins)]

        # Compute JS divergence = 0.5 * KL(P||M) + 0.5 * KL(Q||M)
        js_div = 0.0
        for i in range(n_bins):
            if p[i] > 0 and m[i] > 0:
                js_div += 0.5 * p[i] * math.log(p[i] / m[i])
            if q[i] > 0 and m[i] > 0:
                js_div += 0.5 * q[i] * math.log(q[i] / m[i])

        # Convert to JS distance (square root of divergence) - optional
        # js_distance = math.sqrt(js_div)

        is_significant = js_div >= threshold

        # Interpret the divergence
        max_js = math.log(2)  # Maximum JS divergence
        relative_div = js_div / max_js

        if relative_div < 0.1:
            interpretation = "very similar"
        elif relative_div < 0.3:
            interpretation = "somewhat similar"
        elif relative_div < 0.5:
            interpretation = "moderately different"
        else:
            interpretation = "very different"

        message = f"JS divergence = {js_div:.4f} ({interpretation})"
        if is_significant:
            message += f" - exceeds threshold {threshold}"

        return StatisticalTestResult(
            test_type=StatisticalTestType.JS_DIVERGENCE,
            statistic=round(js_div, 6),
            p_value=None,  # JS divergence doesn't have a p-value
            is_significant=is_significant,
            threshold=threshold,
            message=message,
            details={
                'n_bins': n_bins,
                'baseline_n': n_baseline,
                'current_n': n_current,
                'max_possible': round(max_js, 6),
                'relative_divergence': round(relative_div, 4),
                'interpretation': interpretation
            }
        )

    def detect_drift(
        self,
        baseline: List[Union[float, str, int]],
        current: List[Union[float, str, int]],
        test_type: StatisticalTestType = StatisticalTestType.KS_TEST,
        **kwargs
    ) -> StatisticalTestResult:
        """
        Run the specified drift detection test.

        Args:
            baseline: Baseline distribution samples
            current: Current distribution samples
            test_type: Which statistical test to use
            **kwargs: Additional arguments for the specific test

        Returns:
            StatisticalTestResult
        """
        if test_type == StatisticalTestType.KS_TEST:
            return self.ks_test(baseline, current, **kwargs)
        elif test_type == StatisticalTestType.CHI_SQUARED:
            return self.chi_squared_test(baseline, current, **kwargs)
        elif test_type == StatisticalTestType.PSI:
            return self.psi(baseline, current, **kwargs)
        elif test_type == StatisticalTestType.JS_DIVERGENCE:
            return self.js_divergence(baseline, current, **kwargs)
        else:
            raise ValueError(f"Unknown test type: {test_type}")


# Singleton instance
_statistical_detector: Optional[StatisticalDriftDetector] = None


def get_statistical_drift_detector() -> StatisticalDriftDetector:
    """Get singleton statistical drift detector instance."""
    global _statistical_detector
    if _statistical_detector is None:
        _statistical_detector = StatisticalDriftDetector()
    return _statistical_detector
