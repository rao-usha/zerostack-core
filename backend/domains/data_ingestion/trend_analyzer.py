"""
Trend Analysis Service

Analyzes time-series data for growth rates, seasonality, and cohort patterns.
Used for PE due diligence to identify trends and forecast reliability.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats


class TrendDirection(str, Enum):
    """Direction of trend"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


class Seasonality(str, Enum):
    """Detected seasonality pattern"""
    NONE = "none"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


@dataclass
class GrowthMetrics:
    """Growth rate calculations"""
    period_over_period: Optional[float]  # Most recent period vs prior
    mom_avg: Optional[float]  # Average month-over-month
    qoq_avg: Optional[float]  # Average quarter-over-quarter
    yoy_avg: Optional[float]  # Average year-over-year
    cagr: Optional[float]  # Compound annual growth rate
    trend_direction: TrendDirection
    acceleration: Optional[float]  # Is growth accelerating or decelerating


@dataclass
class TrendResult:
    """Result from trend analysis"""
    column_name: str
    metric_type: str  # revenue, customers, etc.
    growth_metrics: GrowthMetrics
    seasonality: Seasonality
    seasonality_strength: float  # 0-1 scale
    trend_line_slope: float
    trend_line_r_squared: float
    forecast_next_period: Optional[float]
    anomaly_periods: List[str]  # Periods that deviate from trend
    insights: List[str]


@dataclass
class CohortResult:
    """Result from cohort analysis"""
    cohort_column: str
    metric_column: str
    retention_matrix: Dict[str, Dict[str, float]]  # cohort -> period -> retention
    avg_retention_by_period: Dict[str, float]
    best_cohort: str
    worst_cohort: str
    insights: List[str]


class TrendAnalyzer:
    """Service for analyzing trends in time-series data"""

    # Minimum data points for various analyses
    MIN_POINTS_TREND = 4
    MIN_POINTS_SEASONALITY = 12
    MIN_POINTS_COHORT = 3

    def analyze_time_series(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        metric_type: str = "value",
    ) -> Optional[TrendResult]:
        """
        Perform comprehensive trend analysis on a time series.

        Args:
            df: DataFrame with time series data
            date_column: Name of date/period column
            value_column: Name of value column to analyze
            metric_type: Type of metric (revenue, customers, etc.)

        Returns:
            TrendResult with growth metrics, seasonality, and insights
        """
        if date_column not in df.columns or value_column not in df.columns:
            return None

        # Prepare data
        ts_df = df[[date_column, value_column]].copy()
        ts_df[date_column] = pd.to_datetime(ts_df[date_column], errors='coerce')
        ts_df[value_column] = pd.to_numeric(ts_df[value_column], errors='coerce')
        ts_df = ts_df.dropna().sort_values(date_column)

        if len(ts_df) < self.MIN_POINTS_TREND:
            return None

        values = ts_df[value_column].values
        dates = ts_df[date_column].values

        # Calculate growth metrics
        growth_metrics = self._calculate_growth_metrics(ts_df, date_column, value_column)

        # Detect seasonality
        seasonality, seasonality_strength = self._detect_seasonality(values)

        # Fit trend line
        slope, r_squared = self._fit_trend_line(values)

        # Forecast next period
        forecast = self._forecast_next_period(values, slope)

        # Find anomaly periods
        anomaly_periods = self._find_anomaly_periods(ts_df, date_column, value_column)

        # Generate insights
        insights = self._generate_trend_insights(
            growth_metrics, seasonality, slope, r_squared, metric_type
        )

        return TrendResult(
            column_name=value_column,
            metric_type=metric_type,
            growth_metrics=growth_metrics,
            seasonality=seasonality,
            seasonality_strength=seasonality_strength,
            trend_line_slope=slope,
            trend_line_r_squared=r_squared,
            forecast_next_period=forecast,
            anomaly_periods=anomaly_periods,
            insights=insights,
        )

    def calculate_growth_rates(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
    ) -> Dict[str, Any]:
        """
        Calculate various growth rate metrics.

        Returns dict with MoM, QoQ, YoY growth rates and CAGR.
        """
        ts_df = df[[date_column, value_column]].copy()
        ts_df[date_column] = pd.to_datetime(ts_df[date_column], errors='coerce')
        ts_df[value_column] = pd.to_numeric(ts_df[value_column], errors='coerce')
        ts_df = ts_df.dropna().sort_values(date_column)

        if len(ts_df) < 2:
            return {}

        values = ts_df[value_column].values
        dates = ts_df[date_column]

        result = {
            'latest_value': float(values[-1]),
            'earliest_value': float(values[0]),
            'period_count': len(values),
        }

        # Period over period (most recent)
        if len(values) >= 2 and values[-2] != 0:
            result['pop_growth'] = float((values[-1] - values[-2]) / values[-2])

        # Calculate all period-over-period growth rates
        pct_changes = pd.Series(values).pct_change().dropna()
        if len(pct_changes) > 0:
            result['avg_growth'] = float(pct_changes.mean())
            result['median_growth'] = float(pct_changes.median())
            result['growth_volatility'] = float(pct_changes.std())

        # CAGR
        if len(values) >= 2 and values[0] > 0 and values[-1] > 0:
            years = (dates.iloc[-1] - dates.iloc[0]).days / 365.25
            if years > 0:
                result['cagr'] = float((values[-1] / values[0]) ** (1 / years) - 1)

        # Try to calculate MoM, QoQ, YoY based on date frequency
        result.update(self._calculate_periodic_growth(ts_df, date_column, value_column))

        return result

    def analyze_cohorts(
        self,
        df: pd.DataFrame,
        cohort_column: str,
        period_column: str,
        metric_column: str,
        base_metric_column: Optional[str] = None,
    ) -> Optional[CohortResult]:
        """
        Perform cohort analysis for retention/behavior tracking.

        Args:
            df: DataFrame with cohort data
            cohort_column: Column identifying the cohort (e.g., signup_month)
            period_column: Column identifying the measurement period
            metric_column: Column with the metric to track
            base_metric_column: Column with base value for retention calc (optional)

        Returns:
            CohortResult with retention matrix and insights
        """
        required_cols = [cohort_column, period_column, metric_column]
        if not all(col in df.columns for col in required_cols):
            return None

        cohort_df = df[required_cols].copy()
        if base_metric_column and base_metric_column in df.columns:
            cohort_df[base_metric_column] = df[base_metric_column]

        # Get unique cohorts
        cohorts = cohort_df[cohort_column].unique()
        if len(cohorts) < self.MIN_POINTS_COHORT:
            return None

        # Build retention matrix
        retention_matrix = {}
        cohort_performance = {}

        for cohort in cohorts:
            cohort_data = cohort_df[cohort_df[cohort_column] == cohort].sort_values(period_column)
            if len(cohort_data) < 2:
                continue

            base_value = cohort_data[metric_column].iloc[0]
            if base_value == 0:
                continue

            cohort_key = str(cohort)
            retention_matrix[cohort_key] = {}

            for i, (_, row) in enumerate(cohort_data.iterrows()):
                period_key = f"period_{i}"
                retention = row[metric_column] / base_value
                retention_matrix[cohort_key][period_key] = round(retention, 4)

            # Track overall cohort performance (retention at last period)
            cohort_performance[cohort_key] = retention

        if not retention_matrix:
            return None

        # Calculate average retention by period
        avg_retention = self._calculate_avg_retention(retention_matrix)

        # Find best/worst cohorts
        best_cohort = max(cohort_performance, key=cohort_performance.get)
        worst_cohort = min(cohort_performance, key=cohort_performance.get)

        # Generate insights
        insights = self._generate_cohort_insights(
            retention_matrix, avg_retention, best_cohort, worst_cohort, cohort_performance
        )

        return CohortResult(
            cohort_column=cohort_column,
            metric_column=metric_column,
            retention_matrix=retention_matrix,
            avg_retention_by_period=avg_retention,
            best_cohort=best_cohort,
            worst_cohort=worst_cohort,
            insights=insights,
        )

    def detect_trend_breaks(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        sensitivity: float = 2.0,
    ) -> List[Dict[str, Any]]:
        """
        Detect significant trend breaks/changes in time series.

        Args:
            df: DataFrame with time series
            date_column: Date column name
            value_column: Value column name
            sensitivity: Z-score threshold for detecting breaks

        Returns:
            List of detected trend breaks with details
        """
        ts_df = df[[date_column, value_column]].copy()
        ts_df[date_column] = pd.to_datetime(ts_df[date_column], errors='coerce')
        ts_df[value_column] = pd.to_numeric(ts_df[value_column], errors='coerce')
        ts_df = ts_df.dropna().sort_values(date_column).reset_index(drop=True)

        if len(ts_df) < 6:
            return []

        values = ts_df[value_column].values
        dates = ts_df[date_column].values

        # Calculate period-over-period changes
        changes = np.diff(values)
        if len(changes) < 3:
            return []

        # Calculate rolling statistics
        mean_change = np.mean(changes)
        std_change = np.std(changes)

        if std_change == 0:
            return []

        trend_breaks = []
        for i, change in enumerate(changes):
            z_score = (change - mean_change) / std_change
            if abs(z_score) > sensitivity:
                period_idx = i + 1
                trend_breaks.append({
                    'period_index': period_idx,
                    'date': str(dates[period_idx])[:10],
                    'previous_value': float(values[i]),
                    'new_value': float(values[period_idx]),
                    'change': float(change),
                    'change_percent': float(change / values[i] * 100) if values[i] != 0 else None,
                    'z_score': round(float(z_score), 2),
                    'direction': 'increase' if change > 0 else 'decrease',
                })

        return trend_breaks

    def _calculate_growth_metrics(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
    ) -> GrowthMetrics:
        """Calculate comprehensive growth metrics"""
        values = df[value_column].values
        dates = df[date_column]

        # Period over period
        pop = None
        if len(values) >= 2 and values[-2] != 0:
            pop = float((values[-1] - values[-2]) / values[-2])

        # Average growth
        pct_changes = pd.Series(values).pct_change().dropna()
        avg_growth = float(pct_changes.mean()) if len(pct_changes) > 0 else None

        # CAGR
        cagr = None
        if len(values) >= 2 and values[0] > 0 and values[-1] > 0:
            years = (dates.iloc[-1] - dates.iloc[0]).days / 365.25
            if years > 0:
                cagr = float((values[-1] / values[0]) ** (1 / years) - 1)

        # Determine trend direction
        if len(pct_changes) >= 2:
            recent_changes = pct_changes.tail(3)
            if recent_changes.mean() > 0.02:
                direction = TrendDirection.INCREASING
            elif recent_changes.mean() < -0.02:
                direction = TrendDirection.DECREASING
            elif recent_changes.std() > 0.1:
                direction = TrendDirection.VOLATILE
            else:
                direction = TrendDirection.STABLE
        else:
            direction = TrendDirection.STABLE

        # Acceleration (is growth speeding up or slowing down)
        acceleration = None
        if len(pct_changes) >= 4:
            first_half = pct_changes.iloc[:len(pct_changes)//2].mean()
            second_half = pct_changes.iloc[len(pct_changes)//2:].mean()
            acceleration = float(second_half - first_half)

        # Get periodic growth rates
        periodic = self._calculate_periodic_growth(df, date_column, value_column)

        return GrowthMetrics(
            period_over_period=pop,
            mom_avg=periodic.get('mom_avg'),
            qoq_avg=periodic.get('qoq_avg'),
            yoy_avg=periodic.get('yoy_avg'),
            cagr=cagr,
            trend_direction=direction,
            acceleration=acceleration,
        )

    def _calculate_periodic_growth(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
    ) -> Dict[str, float]:
        """Calculate MoM, QoQ, YoY growth rates"""
        result = {}
        df = df.copy()
        df['_date'] = pd.to_datetime(df[date_column])
        df = df.sort_values('_date')

        values = df[value_column].values
        dates = df['_date']

        if len(df) < 2:
            return result

        # Detect frequency
        avg_days = (dates.iloc[-1] - dates.iloc[0]).days / (len(dates) - 1)

        if avg_days <= 35:  # Monthly data
            # MoM is just period over period
            pct_changes = pd.Series(values).pct_change().dropna()
            if len(pct_changes) > 0:
                result['mom_avg'] = float(pct_changes.mean())

            # QoQ (every 3 periods)
            if len(values) >= 4:
                qoq_changes = []
                for i in range(3, len(values)):
                    if values[i-3] != 0:
                        qoq_changes.append((values[i] - values[i-3]) / values[i-3])
                if qoq_changes:
                    result['qoq_avg'] = float(np.mean(qoq_changes))

            # YoY (every 12 periods)
            if len(values) >= 13:
                yoy_changes = []
                for i in range(12, len(values)):
                    if values[i-12] != 0:
                        yoy_changes.append((values[i] - values[i-12]) / values[i-12])
                if yoy_changes:
                    result['yoy_avg'] = float(np.mean(yoy_changes))

        elif avg_days <= 95:  # Quarterly data
            pct_changes = pd.Series(values).pct_change().dropna()
            if len(pct_changes) > 0:
                result['qoq_avg'] = float(pct_changes.mean())

            # YoY (every 4 periods)
            if len(values) >= 5:
                yoy_changes = []
                for i in range(4, len(values)):
                    if values[i-4] != 0:
                        yoy_changes.append((values[i] - values[i-4]) / values[i-4])
                if yoy_changes:
                    result['yoy_avg'] = float(np.mean(yoy_changes))

        else:  # Annual data
            pct_changes = pd.Series(values).pct_change().dropna()
            if len(pct_changes) > 0:
                result['yoy_avg'] = float(pct_changes.mean())

        return result

    def _detect_seasonality(self, values: np.ndarray) -> Tuple[Seasonality, float]:
        """Detect seasonality pattern in time series"""
        if len(values) < self.MIN_POINTS_SEASONALITY:
            return Seasonality.NONE, 0.0

        # Try autocorrelation at different lags
        best_seasonality = Seasonality.NONE
        best_strength = 0.0

        # Check monthly (lag 1 for monthly data, looking for patterns)
        # Check quarterly (lag 3)
        # Check annual (lag 12)

        for lag, season_type in [(3, Seasonality.QUARTERLY), (12, Seasonality.ANNUAL)]:
            if len(values) > lag * 2:
                autocorr = self._autocorrelation(values, lag)
                if autocorr > best_strength and autocorr > 0.3:
                    best_strength = autocorr
                    best_seasonality = season_type

        return best_seasonality, round(best_strength, 3)

    def _autocorrelation(self, values: np.ndarray, lag: int) -> float:
        """Calculate autocorrelation at given lag"""
        if len(values) <= lag:
            return 0.0

        n = len(values)
        mean = np.mean(values)
        var = np.var(values)

        if var == 0:
            return 0.0

        autocorr = np.sum((values[:-lag] - mean) * (values[lag:] - mean)) / (n * var)
        return float(autocorr)

    def _fit_trend_line(self, values: np.ndarray) -> Tuple[float, float]:
        """Fit linear trend line and return slope and R-squared"""
        x = np.arange(len(values))
        slope, intercept, r_value, _, _ = stats.linregress(x, values)
        return round(float(slope), 4), round(float(r_value ** 2), 4)

    def _forecast_next_period(self, values: np.ndarray, slope: float) -> Optional[float]:
        """Simple linear forecast for next period"""
        if len(values) < 2:
            return None

        # Use last value + trend
        forecast = values[-1] + slope
        return round(float(forecast), 2)

    def _find_anomaly_periods(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
    ) -> List[str]:
        """Find periods that deviate significantly from trend"""
        values = df[value_column].values
        dates = df[date_column].values

        if len(values) < 4:
            return []

        # Fit trend
        x = np.arange(len(values))
        slope, intercept, _, _, _ = stats.linregress(x, values)
        predicted = intercept + slope * x

        # Calculate residuals
        residuals = values - predicted
        std_residual = np.std(residuals)

        if std_residual == 0:
            return []

        # Find anomalies (>2 std from trend)
        anomalies = []
        for i, (residual, date) in enumerate(zip(residuals, dates)):
            if abs(residual) > 2 * std_residual:
                anomalies.append(str(date)[:10])

        return anomalies[:5]  # Limit to top 5

    def _calculate_avg_retention(
        self,
        retention_matrix: Dict[str, Dict[str, float]],
    ) -> Dict[str, float]:
        """Calculate average retention by period across cohorts"""
        period_retentions = {}

        for cohort_data in retention_matrix.values():
            for period, retention in cohort_data.items():
                if period not in period_retentions:
                    period_retentions[period] = []
                period_retentions[period].append(retention)

        return {
            period: round(np.mean(values), 4)
            for period, values in period_retentions.items()
        }

    def _generate_trend_insights(
        self,
        growth: GrowthMetrics,
        seasonality: Seasonality,
        slope: float,
        r_squared: float,
        metric_type: str,
    ) -> List[str]:
        """Generate human-readable insights from trend analysis"""
        insights = []

        # Growth direction
        if growth.trend_direction == TrendDirection.INCREASING:
            if growth.cagr and growth.cagr > 0.25:
                insights.append(f"{metric_type.title()} showing strong growth (CAGR: {growth.cagr*100:.1f}%)")
            else:
                insights.append(f"{metric_type.title()} trending upward")
        elif growth.trend_direction == TrendDirection.DECREASING:
            insights.append(f"Warning: {metric_type.title()} trending downward")
        elif growth.trend_direction == TrendDirection.VOLATILE:
            insights.append(f"{metric_type.title()} showing high volatility - investigate causes")

        # Acceleration
        if growth.acceleration is not None:
            if growth.acceleration > 0.05:
                insights.append("Growth is accelerating")
            elif growth.acceleration < -0.05:
                insights.append("Growth is decelerating")

        # Seasonality
        if seasonality != Seasonality.NONE:
            insights.append(f"Detected {seasonality.value} seasonality pattern")

        # Trend fit
        if r_squared > 0.8:
            insights.append("Strong linear trend - forecasts likely reliable")
        elif r_squared < 0.3:
            insights.append("Weak linear trend - high variability in data")

        return insights

    def _generate_cohort_insights(
        self,
        retention_matrix: Dict[str, Dict[str, float]],
        avg_retention: Dict[str, float],
        best_cohort: str,
        worst_cohort: str,
        cohort_performance: Dict[str, float],
    ) -> List[str]:
        """Generate insights from cohort analysis"""
        insights = []

        # Overall retention trend
        periods = sorted(avg_retention.keys())
        if len(periods) >= 2:
            first_retention = avg_retention[periods[1]] if len(periods) > 1 else 1.0
            last_retention = avg_retention[periods[-1]]

            if last_retention < 0.5:
                insights.append(f"Warning: Low retention ({last_retention*100:.0f}%) by final period")
            elif last_retention > 0.8:
                insights.append(f"Strong retention ({last_retention*100:.0f}%) maintained")

        # Best/worst cohort comparison
        if best_cohort != worst_cohort:
            best_perf = cohort_performance[best_cohort]
            worst_perf = cohort_performance[worst_cohort]
            if best_perf - worst_perf > 0.2:
                insights.append(
                    f"Significant cohort variance: {best_cohort} ({best_perf*100:.0f}%) vs "
                    f"{worst_cohort} ({worst_perf*100:.0f}%)"
                )

        return insights
