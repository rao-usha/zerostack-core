"""Statistical tests for drift detection.

Provides statistical methods for detecting distribution drift between
baseline and current data samples.
"""
import math
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DataType(str, Enum):
    """Type of data being tested."""
    CONTINUOUS = "continuous"
    CATEGORICAL = "categorical"
    BINARY = "binary"


@dataclass
class TestResult:
    """Result of a statistical test."""
    test_name: str
    statistic: float
    p_value: float
    is_significant: bool
    threshold: float
    message: str

    def to_dict(self) -> dict:
        return {
            'test_name': self.test_name,
            'statistic': round(self.statistic, 6),
            'p_value': round(self.p_value, 6),
            'is_significant': self.is_significant,
            'threshold': self.threshold,
            'message': self.message
        }


@dataclass
class DriftResult:
    """Result of drift detection."""
    has_drift: bool
    drift_score: float  # 0-1 normalized
    test_results: List[TestResult]
    data_type: DataType
    message: str

    def to_dict(self) -> dict:
        return {
            'has_drift': self.has_drift,
            'drift_score': round(self.drift_score, 4),
            'test_results': [t.to_dict() for t in self.test_results],
            'data_type': self.data_type.value,
            'message': self.message
        }


def kolmogorov_smirnov_test(
    baseline: List[float],
    current: List[float],
    alpha: float = 0.05
) -> TestResult:
    """
    Perform two-sample Kolmogorov-Smirnov test.

    Tests whether two samples come from the same distribution.
    Works well for continuous data.

    Args:
        baseline: Baseline sample data
        current: Current sample data
        alpha: Significance level (default 0.05)

    Returns:
        TestResult with KS statistic and p-value
    """
    if len(baseline) < 2 or len(current) < 2:
        return TestResult(
            test_name="Kolmogorov-Smirnov",
            statistic=0.0,
            p_value=1.0,
            is_significant=False,
            threshold=alpha,
            message="Insufficient data for KS test"
        )

    try:
        from scipy import stats
        stat, p_value = stats.ks_2samp(baseline, current)
    except ImportError:
        # Fallback: manual KS test implementation
        stat, p_value = _manual_ks_test(baseline, current)

    is_significant = p_value < alpha

    if is_significant:
        message = f"Distributions differ significantly (KS={stat:.4f}, p={p_value:.4f})"
    else:
        message = f"No significant difference detected (KS={stat:.4f}, p={p_value:.4f})"

    return TestResult(
        test_name="Kolmogorov-Smirnov",
        statistic=stat,
        p_value=p_value,
        is_significant=is_significant,
        threshold=alpha,
        message=message
    )


def chi_squared_test(
    baseline: Dict[str, int],
    current: Dict[str, int],
    alpha: float = 0.05
) -> TestResult:
    """
    Perform chi-squared test for categorical data.

    Tests whether the distribution of categories has changed.

    Args:
        baseline: Category counts from baseline {category: count}
        current: Category counts from current {category: count}
        alpha: Significance level (default 0.05)

    Returns:
        TestResult with chi-squared statistic and p-value
    """
    # Get union of categories
    all_categories = set(baseline.keys()) | set(current.keys())

    if len(all_categories) < 2:
        return TestResult(
            test_name="Chi-Squared",
            statistic=0.0,
            p_value=1.0,
            is_significant=False,
            threshold=alpha,
            message="Insufficient categories for chi-squared test"
        )

    # Build observed and expected frequencies
    baseline_total = sum(baseline.values())
    current_total = sum(current.values())

    if baseline_total == 0 or current_total == 0:
        return TestResult(
            test_name="Chi-Squared",
            statistic=0.0,
            p_value=1.0,
            is_significant=False,
            threshold=alpha,
            message="Empty data for chi-squared test"
        )

    # Calculate chi-squared statistic
    chi_sq = 0.0
    degrees_freedom = len(all_categories) - 1

    for category in all_categories:
        observed = current.get(category, 0)
        # Expected based on baseline proportions
        baseline_prop = baseline.get(category, 0) / baseline_total
        expected = baseline_prop * current_total

        if expected > 0:
            chi_sq += ((observed - expected) ** 2) / expected

    # Calculate p-value
    try:
        from scipy import stats
        p_value = 1 - stats.chi2.cdf(chi_sq, degrees_freedom)
    except ImportError:
        # Fallback: approximate p-value
        p_value = _approximate_chi2_pvalue(chi_sq, degrees_freedom)

    is_significant = p_value < alpha

    if is_significant:
        message = f"Category distribution changed significantly (χ²={chi_sq:.4f}, p={p_value:.4f})"
    else:
        message = f"No significant category change (χ²={chi_sq:.4f}, p={p_value:.4f})"

    return TestResult(
        test_name="Chi-Squared",
        statistic=chi_sq,
        p_value=p_value,
        is_significant=is_significant,
        threshold=alpha,
        message=message
    )


def population_stability_index(
    baseline: List[float],
    current: List[float],
    buckets: int = 10
) -> float:
    """
    Calculate Population Stability Index (PSI).

    PSI measures how much a distribution has shifted over time.
    Common thresholds:
    - PSI < 0.1: No significant shift
    - 0.1 <= PSI < 0.2: Moderate shift
    - PSI >= 0.2: Significant shift

    Args:
        baseline: Baseline sample data
        current: Current sample data
        buckets: Number of buckets for binning (default 10)

    Returns:
        PSI value (0 = identical, higher = more different)
    """
    if len(baseline) < buckets or len(current) < buckets:
        return 0.0

    # Create bucket boundaries from baseline
    baseline_sorted = sorted(baseline)
    bucket_size = len(baseline_sorted) // buckets

    boundaries = [float('-inf')]
    for i in range(1, buckets):
        idx = i * bucket_size
        if idx < len(baseline_sorted):
            boundaries.append(baseline_sorted[idx])
    boundaries.append(float('inf'))

    # Count items in each bucket
    baseline_counts = [0] * buckets
    current_counts = [0] * buckets

    for val in baseline:
        for i in range(buckets):
            if boundaries[i] <= val < boundaries[i + 1]:
                baseline_counts[i] += 1
                break

    for val in current:
        for i in range(buckets):
            if boundaries[i] <= val < boundaries[i + 1]:
                current_counts[i] += 1
                break

    # Calculate PSI
    baseline_total = len(baseline)
    current_total = len(current)

    psi = 0.0
    for i in range(buckets):
        baseline_pct = max(baseline_counts[i] / baseline_total, 0.0001)
        current_pct = max(current_counts[i] / current_total, 0.0001)

        psi += (current_pct - baseline_pct) * math.log(current_pct / baseline_pct)

    return psi


def jensen_shannon_divergence(
    baseline: List[float],
    current: List[float],
    buckets: int = 10
) -> float:
    """
    Calculate Jensen-Shannon Divergence.

    Symmetric measure of distribution difference (0-1 range).

    Args:
        baseline: Baseline sample data
        current: Current sample data
        buckets: Number of buckets for binning

    Returns:
        JS divergence (0 = identical, 1 = completely different)
    """
    if len(baseline) < buckets or len(current) < buckets:
        return 0.0

    # Create bucket boundaries from combined data
    combined = baseline + current
    combined_sorted = sorted(combined)
    bucket_size = len(combined_sorted) // buckets

    boundaries = [float('-inf')]
    for i in range(1, buckets):
        idx = i * bucket_size
        if idx < len(combined_sorted):
            boundaries.append(combined_sorted[idx])
    boundaries.append(float('inf'))

    # Build probability distributions
    p = [0.0] * buckets  # baseline
    q = [0.0] * buckets  # current

    for val in baseline:
        for i in range(buckets):
            if boundaries[i] <= val < boundaries[i + 1]:
                p[i] += 1
                break

    for val in current:
        for i in range(buckets):
            if boundaries[i] <= val < boundaries[i + 1]:
                q[i] += 1
                break

    # Normalize
    p_sum = sum(p)
    q_sum = sum(q)

    if p_sum == 0 or q_sum == 0:
        return 0.0

    p = [x / p_sum for x in p]
    q = [x / q_sum for x in q]

    # Calculate M = (P + Q) / 2
    m = [(p[i] + q[i]) / 2 for i in range(buckets)]

    # Calculate KL divergences
    def kl_divergence(p_dist, q_dist):
        kl = 0.0
        for i in range(len(p_dist)):
            if p_dist[i] > 0 and q_dist[i] > 0:
                kl += p_dist[i] * math.log(p_dist[i] / q_dist[i])
        return kl

    js = (kl_divergence(p, m) + kl_divergence(q, m)) / 2

    # Convert to 0-1 range (sqrt for JS distance)
    return math.sqrt(js) if js > 0 else 0.0


def detect_drift(
    baseline_data: List,
    current_data: List,
    data_type: str = "auto",
    alpha: float = 0.05,
    psi_threshold: float = 0.1
) -> DriftResult:
    """
    High-level drift detection function.

    Automatically selects appropriate tests based on data type.

    Args:
        baseline_data: Baseline sample
        current_data: Current sample
        data_type: "continuous", "categorical", "binary", or "auto"
        alpha: Significance level for statistical tests
        psi_threshold: Threshold for PSI (default 0.1)

    Returns:
        DriftResult with comprehensive drift analysis
    """
    # Auto-detect data type if needed
    if data_type == "auto":
        data_type = _detect_data_type(baseline_data)

    try:
        dtype = DataType(data_type)
    except ValueError:
        dtype = DataType.CONTINUOUS

    test_results = []
    drift_scores = []

    if dtype == DataType.CONTINUOUS:
        # Use KS test and PSI for continuous data
        baseline_floats = [float(x) for x in baseline_data if x is not None]
        current_floats = [float(x) for x in current_data if x is not None]

        # Kolmogorov-Smirnov test
        ks_result = kolmogorov_smirnov_test(baseline_floats, current_floats, alpha)
        test_results.append(ks_result)
        drift_scores.append(1.0 if ks_result.is_significant else 0.0)

        # PSI
        psi = population_stability_index(baseline_floats, current_floats)
        psi_significant = psi >= psi_threshold
        test_results.append(TestResult(
            test_name="Population Stability Index",
            statistic=psi,
            p_value=0.0,  # PSI doesn't have p-value
            is_significant=psi_significant,
            threshold=psi_threshold,
            message=f"PSI={psi:.4f} ({'significant' if psi_significant else 'acceptable'})"
        ))
        drift_scores.append(min(psi / 0.2, 1.0))  # Normalize PSI to 0-1

        # Jensen-Shannon divergence for additional insight
        js = jensen_shannon_divergence(baseline_floats, current_floats)
        test_results.append(TestResult(
            test_name="Jensen-Shannon Divergence",
            statistic=js,
            p_value=0.0,
            is_significant=js > 0.3,
            threshold=0.3,
            message=f"JS divergence={js:.4f}"
        ))
        drift_scores.append(js)

    elif dtype in (DataType.CATEGORICAL, DataType.BINARY):
        # Use chi-squared for categorical data
        baseline_counts = _count_values(baseline_data)
        current_counts = _count_values(current_data)

        chi_result = chi_squared_test(baseline_counts, current_counts, alpha)
        test_results.append(chi_result)
        drift_scores.append(1.0 if chi_result.is_significant else 0.0)

        # Calculate category shift
        shift = _calculate_category_shift(baseline_counts, current_counts)
        test_results.append(TestResult(
            test_name="Category Shift",
            statistic=shift,
            p_value=0.0,
            is_significant=shift > 0.1,
            threshold=0.1,
            message=f"Total category shift={shift:.4f}"
        ))
        drift_scores.append(min(shift, 1.0))

    # Aggregate results
    avg_drift_score = sum(drift_scores) / len(drift_scores) if drift_scores else 0.0
    has_drift = any(r.is_significant for r in test_results)

    if has_drift:
        message = f"Drift detected with score {avg_drift_score:.2f}"
    else:
        message = f"No significant drift (score={avg_drift_score:.2f})"

    return DriftResult(
        has_drift=has_drift,
        drift_score=avg_drift_score,
        test_results=test_results,
        data_type=dtype,
        message=message
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _detect_data_type(data: List) -> str:
    """Auto-detect data type from sample."""
    if not data:
        return "continuous"

    # Check for numeric
    numeric_count = 0
    unique_values = set()

    for val in data[:1000]:  # Sample first 1000
        if val is None:
            continue
        unique_values.add(val)
        try:
            float(val)
            numeric_count += 1
        except (ValueError, TypeError):
            pass

    sample_size = min(len(data), 1000)

    if numeric_count < sample_size * 0.9:
        return "categorical"

    # Check cardinality for numeric data
    if len(unique_values) <= 2:
        return "binary"
    elif len(unique_values) <= 20 and len(unique_values) < sample_size * 0.1:
        return "categorical"

    return "continuous"


def _count_values(data: List) -> Dict[str, int]:
    """Count occurrences of each value."""
    counts = {}
    for val in data:
        key = str(val) if val is not None else "__null__"
        counts[key] = counts.get(key, 0) + 1
    return counts


def _calculate_category_shift(
    baseline: Dict[str, int],
    current: Dict[str, int]
) -> float:
    """Calculate total proportion shift between category distributions."""
    all_categories = set(baseline.keys()) | set(current.keys())

    baseline_total = sum(baseline.values())
    current_total = sum(current.values())

    if baseline_total == 0 or current_total == 0:
        return 0.0

    total_shift = 0.0
    for cat in all_categories:
        baseline_pct = baseline.get(cat, 0) / baseline_total
        current_pct = current.get(cat, 0) / current_total
        total_shift += abs(current_pct - baseline_pct)

    return total_shift / 2  # Divide by 2 since shifts sum to max 2


def _manual_ks_test(sample1: List[float], sample2: List[float]) -> Tuple[float, float]:
    """
    Manual implementation of KS test when scipy is not available.

    Returns (statistic, approximate p-value)
    """
    n1 = len(sample1)
    n2 = len(sample2)

    # Combine and sort
    combined = [(val, 1) for val in sample1] + [(val, 2) for val in sample2]
    combined.sort(key=lambda x: x[0])

    # Calculate empirical CDFs
    cdf1 = 0.0
    cdf2 = 0.0
    max_diff = 0.0

    for val, group in combined:
        if group == 1:
            cdf1 += 1.0 / n1
        else:
            cdf2 += 1.0 / n2
        max_diff = max(max_diff, abs(cdf1 - cdf2))

    # Approximate p-value using asymptotic formula
    n_eff = (n1 * n2) / (n1 + n2)
    lambda_val = max_diff * math.sqrt(n_eff)

    # Kolmogorov distribution approximation
    p_value = 2 * math.exp(-2 * lambda_val ** 2)
    p_value = min(max(p_value, 0.0), 1.0)

    return max_diff, p_value


def _approximate_chi2_pvalue(chi_sq: float, df: int) -> float:
    """
    Approximate chi-squared p-value when scipy is not available.

    Uses Wilson-Hilferty approximation.
    """
    if df <= 0 or chi_sq <= 0:
        return 1.0

    # Wilson-Hilferty transformation
    h = 2.0 / (9.0 * df)
    z = ((chi_sq / df) ** (1.0/3.0) - (1 - h)) / math.sqrt(h)

    # Standard normal approximation
    # Using logistic approximation to normal CDF
    p_value = 1.0 / (1.0 + math.exp(-1.7 * z))
    p_value = 1 - p_value  # Upper tail

    return min(max(p_value, 0.0), 1.0)
