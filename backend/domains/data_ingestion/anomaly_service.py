"""
Anomaly Detection Service

Statistical anomaly detection for PE due diligence data analysis.
Implements Z-score outliers, Benford's Law, round number bias, and temporal gap detection.
"""
import math
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from domains.data_ingestion.models import AnomalyResult, AnomalyType


class AnomalyDetectionService:
    """Service for detecting statistical anomalies in data columns"""

    # Thresholds for anomaly detection
    MODIFIED_ZSCORE_THRESHOLD = 3.5
    ROUND_NUMBER_WARNING_THRESHOLD = 0.25  # 25% round numbers
    ROUND_NUMBER_CRITICAL_THRESHOLD = 0.40  # 40% round numbers
    BENFORDS_P_VALUE_THRESHOLD = 0.01
    MIN_SAMPLE_SIZE = 30  # Minimum samples for statistical tests
    TEMPORAL_GAP_MULTIPLIER = 3  # Gap > 3x median gap is flagged

    def analyze_column(
        self,
        col_name: str,
        values: pd.Series,
        inferred_type: str,
    ) -> List[AnomalyResult]:
        """
        Run all applicable anomaly checks on a column.

        Args:
            col_name: Column name
            values: Column values as pandas Series
            inferred_type: Inferred data type from schema detection

        Returns:
            List of detected anomalies
        """
        anomalies = []
        non_null = values.dropna()

        if len(non_null) < self.MIN_SAMPLE_SIZE:
            return anomalies

        # Run checks based on data type
        numeric_types = ['integer', 'float', 'currency', 'percentage']
        date_types = ['date', 'datetime']

        if inferred_type in numeric_types:
            # Convert to numeric, handling currency symbols
            numeric_vals = self._to_numeric(non_null)
            if numeric_vals is not None and len(numeric_vals) >= self.MIN_SAMPLE_SIZE:
                # Statistical outliers
                outlier_result = self.detect_statistical_outliers(col_name, numeric_vals)
                if outlier_result:
                    anomalies.append(outlier_result)

                # Benford's Law (for financial-looking data)
                if self._looks_like_financial(col_name, numeric_vals):
                    benfords_result = self.detect_benfords_law_violation(col_name, numeric_vals)
                    if benfords_result:
                        anomalies.append(benfords_result)

                # Round number bias
                round_result = self.detect_round_number_bias(col_name, numeric_vals)
                if round_result:
                    anomalies.append(round_result)

        elif inferred_type in date_types:
            # Try parsing dates
            date_series = pd.to_datetime(non_null, errors='coerce')
            valid_dates = date_series.dropna()
            if len(valid_dates) >= self.MIN_SAMPLE_SIZE:
                gap_result = self.detect_temporal_gaps(col_name, valid_dates)
                if gap_result:
                    anomalies.append(gap_result)

        return anomalies

    def detect_statistical_outliers(
        self,
        col_name: str,
        values: pd.Series,
    ) -> Optional[AnomalyResult]:
        """
        Detect outliers using modified Z-score (more robust than standard Z-score).

        Modified Z-score uses median and MAD instead of mean and std dev,
        making it robust to skewed distributions common in financial data.

        Formula: Modified_Z = 0.6745 * (x - median) / MAD
        Flag if |Modified_Z| > 3.5
        """
        if len(values) < self.MIN_SAMPLE_SIZE:
            return None

        median = values.median()
        mad = np.median(np.abs(values - median))

        if mad == 0:
            # All values are the same
            return None

        # Calculate modified Z-scores
        modified_z = 0.6745 * (values - median) / mad
        outlier_mask = np.abs(modified_z) > self.MODIFIED_ZSCORE_THRESHOLD
        outlier_count = outlier_mask.sum()

        if outlier_count == 0:
            return None

        outlier_percent = (outlier_count / len(values)) * 100
        outlier_values = values[outlier_mask].head(5).tolist()

        # Determine severity based on count and percentage
        if outlier_percent > 10:
            severity = "high"
        elif outlier_percent > 5:
            severity = "medium"
        else:
            severity = "low"

        return AnomalyResult(
            anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
            severity=severity,
            column_name=col_name,
            title=f"Statistical outliers detected in '{col_name}'",
            description=(
                f"Found {outlier_count} values ({outlier_percent:.1f}%) that deviate "
                f"significantly from the distribution (modified Z-score > {self.MODIFIED_ZSCORE_THRESHOLD}). "
                f"These may be data entry errors, exceptional cases, or legitimate extreme values."
            ),
            evidence={
                "outlier_count": int(outlier_count),
                "outlier_percent": round(outlier_percent, 2),
                "median": float(median),
                "mad": float(mad),
                "threshold": self.MODIFIED_ZSCORE_THRESHOLD,
                "example_outliers": [float(v) for v in outlier_values],
            },
            recommendation=(
                "Review the flagged values to determine if they are data entry errors, "
                "exceptional business cases, or legitimate outliers. Consider verifying "
                "against source documents."
            ),
            affected_rows=int(outlier_count),
            affected_percent=round(outlier_percent, 2),
        )

    def detect_benfords_law_violation(
        self,
        col_name: str,
        values: pd.Series,
    ) -> Optional[AnomalyResult]:
        """
        Check if first-digit distribution follows Benford's Law.

        Benford's Law predicts that in naturally occurring datasets,
        the leading digit d occurs with probability P(d) = log10(1 + 1/d).

        Violations can indicate data manipulation or fabrication.
        """
        if len(values) < 100:  # Need larger sample for Benford's
            return None

        # Get absolute values (Benford's applies to magnitudes)
        abs_vals = values.abs()
        abs_vals = abs_vals[abs_vals > 0]  # Remove zeros

        if len(abs_vals) < 100:
            return None

        # Extract first digits
        first_digits = abs_vals.apply(lambda x: int(str(abs(x)).lstrip('0').lstrip('.')[0])
                                       if str(abs(x)).lstrip('0').lstrip('.') else 0)
        first_digits = first_digits[first_digits > 0]

        if len(first_digits) < 100:
            return None

        # Count observed frequencies
        observed = first_digits.value_counts().sort_index()
        observed_counts = [observed.get(d, 0) for d in range(1, 10)]
        total = sum(observed_counts)

        if total < 100:
            return None

        # Expected Benford distribution
        expected_probs = [math.log10(1 + 1/d) for d in range(1, 10)]
        expected_counts = [p * total for p in expected_probs]

        # Chi-squared test
        chi2, p_value = stats.chisquare(observed_counts, expected_counts)

        if p_value >= self.BENFORDS_P_VALUE_THRESHOLD:
            return None  # No significant deviation

        # Calculate deviation details
        deviations = {}
        for d in range(1, 10):
            obs_pct = (observed_counts[d-1] / total) * 100
            exp_pct = expected_probs[d-1] * 100
            deviations[str(d)] = {
                "observed": round(obs_pct, 1),
                "expected": round(exp_pct, 1),
                "difference": round(obs_pct - exp_pct, 1),
            }

        # Severity based on p-value
        if p_value < 0.001:
            severity = "high"
        elif p_value < 0.005:
            severity = "medium"
        else:
            severity = "low"

        return AnomalyResult(
            anomaly_type=AnomalyType.BENFORDS_VIOLATION,
            severity=severity,
            column_name=col_name,
            title=f"Benford's Law violation in '{col_name}'",
            description=(
                f"The first-digit distribution significantly deviates from Benford's Law "
                f"(chi-squared test p-value: {p_value:.4f}). Natural financial data typically "
                f"follows Benford's Law. Deviations may indicate data manipulation, fabrication, "
                f"rounding, or simply that this data type doesn't follow Benford's Law naturally."
            ),
            evidence={
                "chi_squared": round(float(chi2), 2),
                "p_value": round(float(p_value), 6),
                "sample_size": int(total),
                "first_digit_distribution": deviations,
            },
            recommendation=(
                "Investigate whether the deviation is due to legitimate business factors "
                "(e.g., price points at $9.99, $19.99) or potential data issues. Compare "
                "against source documents for verification."
            ),
        )

    def detect_round_number_bias(
        self,
        col_name: str,
        values: pd.Series,
    ) -> Optional[AnomalyResult]:
        """
        Detect suspicious prevalence of round numbers.

        High frequency of round numbers (ending in 0, 00, 000) can indicate
        estimates, guesses, or fabricated data rather than actual measurements.
        """
        if len(values) < self.MIN_SAMPLE_SIZE:
            return None

        # Check different levels of rounding
        values_int = values.apply(lambda x: int(round(x)) if pd.notna(x) and x != 0 else 0)
        values_int = values_int[values_int != 0]

        if len(values_int) < self.MIN_SAMPLE_SIZE:
            return None

        # Count round numbers at different levels
        ends_in_0 = (values_int % 10 == 0).sum()
        ends_in_00 = (values_int % 100 == 0).sum()
        ends_in_000 = (values_int % 1000 == 0).sum()

        total = len(values_int)
        pct_ends_0 = ends_in_0 / total
        pct_ends_00 = ends_in_00 / total
        pct_ends_000 = ends_in_000 / total

        # Expected by chance: 10% end in 0, 1% end in 00, 0.1% end in 000
        # Flag if significantly higher

        issues = []
        if pct_ends_0 > 0.20:  # More than 20% (vs expected 10%)
            issues.append(f"{pct_ends_0*100:.1f}% end in 0 (expected ~10%)")
        if pct_ends_00 > 0.05:  # More than 5% (vs expected 1%)
            issues.append(f"{pct_ends_00*100:.1f}% end in 00 (expected ~1%)")
        if pct_ends_000 > 0.02:  # More than 2% (vs expected 0.1%)
            issues.append(f"{pct_ends_000*100:.1f}% end in 000 (expected ~0.1%)")

        if not issues:
            return None

        # Calculate overall round number percentage for severity
        round_pct = pct_ends_0

        if round_pct >= self.ROUND_NUMBER_CRITICAL_THRESHOLD:
            severity = "high"
        elif round_pct >= self.ROUND_NUMBER_WARNING_THRESHOLD:
            severity = "medium"
        else:
            severity = "low"

        return AnomalyResult(
            anomaly_type=AnomalyType.ROUND_NUMBER_BIAS,
            severity=severity,
            column_name=col_name,
            title=f"Round number bias in '{col_name}'",
            description=(
                f"Unusually high prevalence of round numbers detected: {'; '.join(issues)}. "
                f"This pattern may indicate estimates, manual data entry, or fabricated values "
                f"rather than actual measurements or calculations."
            ),
            evidence={
                "percent_ending_0": round(pct_ends_0 * 100, 2),
                "percent_ending_00": round(pct_ends_00 * 100, 2),
                "percent_ending_000": round(pct_ends_000 * 100, 2),
                "count_ending_0": int(ends_in_0),
                "count_ending_00": int(ends_in_00),
                "count_ending_000": int(ends_in_000),
                "total_values": int(total),
            },
            recommendation=(
                "Verify that round numbers reflect actual values from source documents. "
                "If this column represents estimates or budgets, round numbers may be expected. "
                "If it represents actuals (revenue, transactions), investigate further."
            ),
            affected_rows=int(ends_in_0),
            affected_percent=round(pct_ends_0 * 100, 2),
        )

    def detect_temporal_gaps(
        self,
        col_name: str,
        date_series: pd.Series,
    ) -> Optional[AnomalyResult]:
        """
        Find missing dates/periods in time series data.

        Identifies gaps that are significantly larger than the typical interval,
        which may indicate missing data or reporting gaps.
        """
        if len(date_series) < self.MIN_SAMPLE_SIZE:
            return None

        # Sort dates
        sorted_dates = date_series.sort_values()

        # Calculate gaps between consecutive dates
        gaps = sorted_dates.diff().dropna()

        if len(gaps) == 0:
            return None

        # Convert to days
        gap_days = gaps.dt.total_seconds() / (24 * 3600)
        gap_days = gap_days[gap_days > 0]  # Remove zero/negative gaps

        if len(gap_days) < 10:
            return None

        # Find median gap and flag large deviations
        median_gap = gap_days.median()
        if median_gap == 0:
            return None

        threshold = median_gap * self.TEMPORAL_GAP_MULTIPLIER
        large_gaps = gap_days[gap_days > threshold]

        if len(large_gaps) == 0:
            return None

        # Get the actual gap periods
        gap_details = []
        gap_indices = gap_days[gap_days > threshold].index
        for idx in list(gap_indices)[:5]:  # Top 5 gaps
            loc = sorted_dates.index.get_loc(idx)
            if loc > 0:
                start_date = sorted_dates.iloc[loc - 1]
                end_date = sorted_dates.iloc[loc]
                gap_size = (end_date - start_date).days
                gap_details.append({
                    "from": start_date.strftime('%Y-%m-%d'),
                    "to": end_date.strftime('%Y-%m-%d'),
                    "gap_days": int(gap_size),
                })

        # Severity based on number and size of gaps
        if len(large_gaps) > 5 or large_gaps.max() > median_gap * 10:
            severity = "high"
        elif len(large_gaps) > 2 or large_gaps.max() > median_gap * 5:
            severity = "medium"
        else:
            severity = "low"

        return AnomalyResult(
            anomaly_type=AnomalyType.TEMPORAL_GAP,
            severity=severity,
            column_name=col_name,
            title=f"Temporal gaps detected in '{col_name}'",
            description=(
                f"Found {len(large_gaps)} significant gaps in the date sequence. "
                f"The typical interval is {median_gap:.1f} days, but gaps of "
                f"{large_gaps.min():.0f}-{large_gaps.max():.0f} days were found. "
                f"This may indicate missing data periods."
            ),
            evidence={
                "gap_count": int(len(large_gaps)),
                "median_interval_days": round(float(median_gap), 1),
                "threshold_days": round(float(threshold), 1),
                "largest_gap_days": round(float(large_gaps.max()), 1),
                "gap_periods": gap_details,
            },
            recommendation=(
                "Investigate the identified gap periods. Verify if data was not collected, "
                "was lost, or represents legitimate business gaps (e.g., seasonal closures). "
                "Request complete data from the source if gaps are unexplained."
            ),
            affected_rows=int(len(large_gaps)),
        )

    def detect_distribution_shift(
        self,
        col_name: str,
        current: pd.Series,
        baseline: pd.Series,
    ) -> Optional[AnomalyResult]:
        """
        Detect significant distribution shifts between two datasets.

        Uses Kolmogorov-Smirnov test and Population Stability Index (PSI).
        Useful for comparing periods (e.g., YoY) or against benchmarks.
        """
        if len(current) < self.MIN_SAMPLE_SIZE or len(baseline) < self.MIN_SAMPLE_SIZE:
            return None

        # KS Test
        ks_stat, ks_pvalue = stats.ks_2samp(current, baseline)

        # PSI calculation
        psi = self._calculate_psi(baseline, current)

        # Neither significant
        if ks_pvalue >= 0.05 and psi < 0.1:
            return None

        # Determine severity
        if psi >= 0.25 or ks_pvalue < 0.001:
            severity = "high"
        elif psi >= 0.1 or ks_pvalue < 0.01:
            severity = "medium"
        else:
            severity = "low"

        return AnomalyResult(
            anomaly_type=AnomalyType.DISTRIBUTION_SHIFT,
            severity=severity,
            column_name=col_name,
            title=f"Distribution shift detected in '{col_name}'",
            description=(
                f"The distribution has shifted significantly compared to baseline. "
                f"KS test p-value: {ks_pvalue:.4f}, PSI: {psi:.3f}. "
                f"PSI > 0.25 indicates significant population shift."
            ),
            evidence={
                "ks_statistic": round(float(ks_stat), 4),
                "ks_pvalue": round(float(ks_pvalue), 6),
                "psi": round(float(psi), 4),
                "current_mean": round(float(current.mean()), 4),
                "baseline_mean": round(float(baseline.mean()), 4),
                "current_std": round(float(current.std()), 4),
                "baseline_std": round(float(baseline.std()), 4),
            },
            recommendation=(
                "Investigate the cause of the distribution shift. This could indicate "
                "business changes, data collection issues, or market shifts."
            ),
        )

    def _calculate_psi(
        self,
        expected: pd.Series,
        actual: pd.Series,
        buckets: int = 10,
    ) -> float:
        """Calculate Population Stability Index"""
        breakpoints = np.percentile(expected, np.linspace(0, 100, buckets + 1))
        breakpoints[0] = -np.inf
        breakpoints[-1] = np.inf

        expected_counts = np.histogram(expected, breakpoints)[0]
        actual_counts = np.histogram(actual, breakpoints)[0]

        expected_pct = expected_counts / len(expected)
        actual_pct = actual_counts / len(actual)

        # Avoid division by zero
        expected_pct = np.where(expected_pct == 0, 0.0001, expected_pct)
        actual_pct = np.where(actual_pct == 0, 0.0001, actual_pct)

        psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
        return float(psi)

    def _to_numeric(self, series: pd.Series) -> Optional[pd.Series]:
        """Convert series to numeric, handling currency symbols"""
        try:
            # Remove common currency symbols and commas
            cleaned = series.astype(str).str.replace(r'[\$,€£¥%]', '', regex=True)
            return pd.to_numeric(cleaned, errors='coerce').dropna()
        except Exception:
            return None

    def _looks_like_financial(self, col_name: str, values: pd.Series) -> bool:
        """Check if column likely contains financial data based on name and values"""
        financial_keywords = [
            'revenue', 'sales', 'profit', 'cost', 'expense', 'income',
            'price', 'amount', 'total', 'balance', 'payment', 'fee',
            'margin', 'ebitda', 'cash', 'spend'
        ]
        col_lower = col_name.lower()

        # Check column name
        if any(kw in col_lower for kw in financial_keywords):
            return True

        # Check if values look financial (large range, positive, decimal places)
        if len(values) > 0:
            min_val = values.min()
            max_val = values.max()
            # Financial data often has wide range and mostly positive values
            if max_val > 100 and (min_val >= 0 or abs(min_val) < max_val * 0.5):
                return True

        return False
