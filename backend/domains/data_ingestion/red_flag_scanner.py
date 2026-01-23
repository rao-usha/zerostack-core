"""
Red Flag Scanner

PE-specific red flag detection for due diligence data analysis.
Implements financial, customer, operational, and data quality red flags.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from domains.data_ingestion.models import RedFlagResult, RedFlagType


class RedFlagScanner:
    """Scanner for PE-specific red flags in uploaded data"""

    # Column name patterns for detecting data categories
    COLUMN_PATTERNS = {
        'revenue': ['revenue', 'sales', 'income', 'turnover', 'receipts'],
        'ebitda': ['ebitda', 'operating_income', 'operating_profit'],
        'gross_margin': ['gross_margin', 'gm', 'gross_profit_margin'],
        'profit': ['profit', 'net_income', 'earnings', 'net_profit'],
        'cost': ['cost', 'expense', 'cogs', 'opex'],
        'customer_count': ['customer_count', 'customers', 'num_customers', 'client_count', 'accounts'],
        'churn': ['churn', 'churn_rate', 'attrition'],
        'mrr': ['mrr', 'monthly_recurring', 'recurring_revenue'],
        'arr': ['arr', 'annual_recurring', 'annualized'],
        'headcount': ['headcount', 'employees', 'fte', 'staff_count', 'team_size'],
        'date': ['date', 'period', 'month', 'quarter', 'year'],
        'customer_revenue': ['customer_revenue', 'revenue_per_customer', 'arpu', 'revenue_concentration'],
    }

    # Thresholds for red flags
    THRESHOLDS = {
        # Financial
        'extreme_growth_warning': 1.5,  # 150% YoY
        'extreme_growth_critical': 3.0,  # 300% YoY
        'extreme_decline_warning': 0.3,  # 30% decline
        'extreme_decline_critical': 0.5,  # 50% decline
        'gross_margin_low': 0.20,  # Below 20%
        'gross_margin_high': 0.80,  # Above 80%

        # Customer
        'monthly_churn_warning': 0.10,  # 10%
        'monthly_churn_critical': 0.20,  # 20%
        'concentration_warning': 0.25,  # Top customer > 25%
        'concentration_critical': 0.40,  # Top customer > 40%

        # Operational
        'headcount_vs_revenue_warning': 1.5,  # Headcount growing 1.5x faster
        'headcount_vs_revenue_critical': 2.0,  # Headcount growing 2x faster

        # Data quality
        'period_end_spike_warning': 0.30,  # >30% in last week
        'period_end_spike_critical': 0.50,  # >50% in last week
        'duplicate_row_warning': 0.01,  # >1% duplicates
        'duplicate_row_critical': 0.05,  # >5% duplicates
    }

    def scan_dataframe(
        self,
        df: pd.DataFrame,
        detected_categories: List[str],
    ) -> List[RedFlagResult]:
        """
        Run all applicable red flag checks on a DataFrame.

        Args:
            df: DataFrame to scan
            detected_categories: List of detected PE data categories

        Returns:
            List of detected red flags
        """
        red_flags = []

        # Identify relevant columns
        col_mapping = self._identify_columns(df)

        # Data quality checks (always run)
        red_flags.extend(self.scan_data_quality(df, col_mapping))

        # Financial checks
        if 'financial' in detected_categories or self._has_financial_columns(col_mapping):
            red_flags.extend(self.scan_financial(df, col_mapping))

        # Customer checks
        if 'customer' in detected_categories or self._has_customer_columns(col_mapping):
            red_flags.extend(self.scan_customer(df, col_mapping))

        # Operational checks
        if 'operational' in detected_categories or self._has_operational_columns(col_mapping):
            red_flags.extend(self.scan_operational(df, col_mapping))

        return red_flags

    def scan_financial(
        self,
        df: pd.DataFrame,
        col_mapping: Dict[str, str],
    ) -> List[RedFlagResult]:
        """
        Scan for financial red flags.

        Checks:
        - Negative revenue/EBITDA
        - EBITDA > Revenue (impossible)
        - Gross margin > 100% or < 0%
        - Extreme revenue growth/decline
        """
        red_flags = []

        # Check for negative revenue
        revenue_col = col_mapping.get('revenue')
        if revenue_col and revenue_col in df.columns:
            revenue = pd.to_numeric(df[revenue_col], errors='coerce')
            negative_count = (revenue < 0).sum()
            if negative_count > 0:
                red_flags.append(RedFlagResult(
                    flag_type=RedFlagType.NEGATIVE_REVENUE,
                    severity="critical" if negative_count > 1 else "high",
                    category="financial",
                    title="Negative revenue values detected",
                    description=(
                        f"Found {negative_count} rows with negative revenue. "
                        f"Revenue should never be negative. This may indicate data errors, "
                        f"returns/refunds miscategorized, or data manipulation."
                    ),
                    evidence={
                        "negative_count": int(negative_count),
                        "negative_percent": round((negative_count / len(revenue)) * 100, 2),
                        "negative_values": revenue[revenue < 0].head(5).tolist(),
                    },
                    recommendation=(
                        "Verify negative values against source documents. If these represent "
                        "refunds or credits, they should be categorized separately from revenue."
                    ),
                    affected_columns=[revenue_col],
                ))

        # Check for EBITDA > Revenue
        ebitda_col = col_mapping.get('ebitda')
        if revenue_col and ebitda_col and revenue_col in df.columns and ebitda_col in df.columns:
            revenue = pd.to_numeric(df[revenue_col], errors='coerce')
            ebitda = pd.to_numeric(df[ebitda_col], errors='coerce')
            impossible = (ebitda > revenue) & (revenue > 0)
            impossible_count = impossible.sum()
            if impossible_count > 0:
                red_flags.append(RedFlagResult(
                    flag_type=RedFlagType.IMPOSSIBLE_MARGIN,
                    severity="critical",
                    category="financial",
                    title="EBITDA exceeds revenue",
                    description=(
                        f"Found {impossible_count} rows where EBITDA exceeds revenue. "
                        f"This is mathematically impossible - EBITDA cannot be greater than "
                        f"the revenue it's derived from. This indicates data errors."
                    ),
                    evidence={
                        "impossible_count": int(impossible_count),
                        "sample_rows": df[impossible][
                            [revenue_col, ebitda_col]
                        ].head(5).to_dict('records'),
                    },
                    recommendation=(
                        "Review data definitions and verify calculations. EBITDA should always "
                        "be less than revenue. Check for unit mismatches or data entry errors."
                    ),
                    affected_columns=[revenue_col, ebitda_col],
                ))

        # Check gross margin bounds
        margin_col = col_mapping.get('gross_margin')
        if margin_col and margin_col in df.columns:
            margin = pd.to_numeric(df[margin_col], errors='coerce')
            # Detect if values are percentages (0-100) or decimals (0-1)
            if margin.max() > 1.5:  # Likely percentage format
                margin = margin / 100

            invalid_low = (margin < 0).sum()
            invalid_high = (margin > 1).sum()
            suspicious_low = ((margin >= 0) & (margin < self.THRESHOLDS['gross_margin_low'])).sum()
            suspicious_high = ((margin <= 1) & (margin > self.THRESHOLDS['gross_margin_high'])).sum()

            if invalid_low > 0 or invalid_high > 0:
                red_flags.append(RedFlagResult(
                    flag_type=RedFlagType.IMPOSSIBLE_MARGIN,
                    severity="critical",
                    category="financial",
                    title="Invalid gross margin values",
                    description=(
                        f"Found gross margins outside valid range: {invalid_low} below 0%, "
                        f"{invalid_high} above 100%. Gross margin must be between 0-100%."
                    ),
                    evidence={
                        "below_zero_count": int(invalid_low),
                        "above_100_count": int(invalid_high),
                        "min_value": round(float(margin.min()) * 100, 2),
                        "max_value": round(float(margin.max()) * 100, 2),
                    },
                    recommendation=(
                        "Verify margin calculations. Negative margins are only possible if "
                        "selling below cost (unusual). Margins over 100% indicate calculation errors."
                    ),
                    affected_columns=[margin_col],
                ))

        # Check for extreme growth/decline
        if revenue_col and revenue_col in df.columns:
            revenue = pd.to_numeric(df[revenue_col], errors='coerce').dropna()
            if len(revenue) >= 2:
                growth_results = self._check_growth_rates(revenue, "revenue")
                red_flags.extend(growth_results)

        return red_flags

    def scan_customer(
        self,
        df: pd.DataFrame,
        col_mapping: Dict[str, str],
    ) -> List[RedFlagResult]:
        """
        Scan for customer-related red flags.

        Checks:
        - High churn rate
        - Customer concentration
        - Declining customer count with growing revenue
        """
        red_flags = []

        # Check churn rate
        churn_col = col_mapping.get('churn')
        if churn_col and churn_col in df.columns:
            churn = pd.to_numeric(df[churn_col], errors='coerce')
            # Convert if percentage format
            if churn.max() > 1.5:
                churn = churn / 100

            high_churn = churn[churn > self.THRESHOLDS['monthly_churn_warning']]
            if len(high_churn) > 0:
                max_churn = churn.max()
                severity = "critical" if max_churn > self.THRESHOLDS['monthly_churn_critical'] else "high"

                red_flags.append(RedFlagResult(
                    flag_type=RedFlagType.HIGH_CHURN,
                    severity=severity,
                    category="customer",
                    title="High customer churn rate",
                    description=(
                        f"Churn rate exceeds {self.THRESHOLDS['monthly_churn_warning']*100:.0f}% "
                        f"in {len(high_churn)} periods. Maximum churn: {max_churn*100:.1f}%. "
                        f"High churn significantly impacts customer lifetime value and growth."
                    ),
                    evidence={
                        "high_churn_periods": int(len(high_churn)),
                        "max_churn_percent": round(float(max_churn) * 100, 2),
                        "avg_churn_percent": round(float(churn.mean()) * 100, 2),
                        "warning_threshold": self.THRESHOLDS['monthly_churn_warning'] * 100,
                    },
                    recommendation=(
                        "Investigate root causes of churn. Review customer satisfaction, "
                        "competitive positioning, and product-market fit. Consider cohort analysis "
                        "to identify problematic customer segments."
                    ),
                    affected_columns=[churn_col],
                ))

        # Check for declining customers with growing revenue
        customer_col = col_mapping.get('customer_count')
        revenue_col = col_mapping.get('revenue')
        date_col = col_mapping.get('date')

        if all(col and col in df.columns for col in [customer_col, revenue_col]):
            customers = pd.to_numeric(df[customer_col], errors='coerce')
            revenue = pd.to_numeric(df[revenue_col], errors='coerce')

            if len(customers) >= 4:  # Need enough data points
                # Compare first half vs second half
                mid = len(customers) // 2
                early_customers = customers.iloc[:mid].mean()
                late_customers = customers.iloc[mid:].mean()
                early_revenue = revenue.iloc[:mid].mean()
                late_revenue = revenue.iloc[mid:].mean()

                customer_change = (late_customers - early_customers) / early_customers if early_customers else 0
                revenue_change = (late_revenue - early_revenue) / early_revenue if early_revenue else 0

                if customer_change < -0.1 and revenue_change > 0.1:
                    red_flags.append(RedFlagResult(
                        flag_type=RedFlagType.CUSTOMER_CONCENTRATION,
                        severity="high",
                        category="customer",
                        title="Customer count declining while revenue grows",
                        description=(
                            f"Customer count decreased {abs(customer_change)*100:.1f}% while "
                            f"revenue increased {revenue_change*100:.1f}%. This suggests increasing "
                            f"concentration on fewer, larger customers - a significant risk factor."
                        ),
                        evidence={
                            "customer_change_percent": round(customer_change * 100, 2),
                            "revenue_change_percent": round(revenue_change * 100, 2),
                            "early_period_avg_customers": round(float(early_customers), 0),
                            "late_period_avg_customers": round(float(late_customers), 0),
                        },
                        recommendation=(
                            "Analyze customer concentration. Request top 10 customer revenue breakdown. "
                            "High dependence on few customers is a significant acquisition risk."
                        ),
                        affected_columns=[customer_col, revenue_col],
                    ))

        return red_flags

    def scan_operational(
        self,
        df: pd.DataFrame,
        col_mapping: Dict[str, str],
    ) -> List[RedFlagResult]:
        """
        Scan for operational red flags.

        Checks:
        - Headcount growth >> revenue growth
        - Revenue per employee declining
        """
        red_flags = []

        headcount_col = col_mapping.get('headcount')
        revenue_col = col_mapping.get('revenue')

        if headcount_col and revenue_col and headcount_col in df.columns and revenue_col in df.columns:
            headcount = pd.to_numeric(df[headcount_col], errors='coerce')
            revenue = pd.to_numeric(df[revenue_col], errors='coerce')

            if len(headcount) >= 4:
                # Compare first quarter vs last quarter
                q = len(headcount) // 4
                if q > 0:
                    early_headcount = headcount.iloc[:q].mean()
                    late_headcount = headcount.iloc[-q:].mean()
                    early_revenue = revenue.iloc[:q].mean()
                    late_revenue = revenue.iloc[-q:].mean()

                    hc_growth = (late_headcount - early_headcount) / early_headcount if early_headcount else 0
                    rev_growth = (late_revenue - early_revenue) / early_revenue if early_revenue else 0

                    # Check if headcount growth significantly exceeds revenue growth
                    if hc_growth > 0.1 and rev_growth > 0:  # Both growing
                        ratio = hc_growth / rev_growth if rev_growth > 0 else float('inf')

                        if ratio > self.THRESHOLDS['headcount_vs_revenue_warning']:
                            severity = "high" if ratio > self.THRESHOLDS['headcount_vs_revenue_critical'] else "medium"

                            red_flags.append(RedFlagResult(
                                flag_type=RedFlagType.HEADCOUNT_MISMATCH,
                                severity=severity,
                                category="operational",
                                title="Headcount growth outpacing revenue growth",
                                description=(
                                    f"Headcount grew {hc_growth*100:.1f}% while revenue grew only "
                                    f"{rev_growth*100:.1f}% ({ratio:.1f}x ratio). This suggests "
                                    f"declining operational efficiency and potential overstaffing."
                                ),
                                evidence={
                                    "headcount_growth_percent": round(hc_growth * 100, 2),
                                    "revenue_growth_percent": round(rev_growth * 100, 2),
                                    "growth_ratio": round(ratio, 2),
                                    "early_headcount": round(float(early_headcount), 0),
                                    "late_headcount": round(float(late_headcount), 0),
                                    "early_revenue": round(float(early_revenue), 2),
                                    "late_revenue": round(float(late_revenue), 2),
                                },
                                recommendation=(
                                    "Review hiring plans and productivity metrics. Understand the "
                                    "investment thesis - are hires in advance of expected growth? "
                                    "Calculate revenue per employee trends."
                                ),
                                affected_columns=[headcount_col, revenue_col],
                            ))

                    # Check revenue per employee trend
                    rev_per_emp_early = early_revenue / early_headcount if early_headcount else 0
                    rev_per_emp_late = late_revenue / late_headcount if late_headcount else 0

                    if rev_per_emp_early > 0:
                        rpe_change = (rev_per_emp_late - rev_per_emp_early) / rev_per_emp_early
                        if rpe_change < -0.15:  # More than 15% decline
                            red_flags.append(RedFlagResult(
                                flag_type=RedFlagType.HEADCOUNT_MISMATCH,
                                severity="medium",
                                category="operational",
                                title="Declining revenue per employee",
                                description=(
                                    f"Revenue per employee declined {abs(rpe_change)*100:.1f}% "
                                    f"from ${rev_per_emp_early:,.0f} to ${rev_per_emp_late:,.0f}. "
                                    f"This indicates decreasing workforce productivity."
                                ),
                                evidence={
                                    "early_rev_per_employee": round(float(rev_per_emp_early), 2),
                                    "late_rev_per_employee": round(float(rev_per_emp_late), 2),
                                    "change_percent": round(rpe_change * 100, 2),
                                },
                                recommendation=(
                                    "Investigate productivity drivers. Consider if this reflects "
                                    "investment phase (hiring ahead of revenue) or structural issues."
                                ),
                                affected_columns=[headcount_col, revenue_col],
                            ))

        return red_flags

    def scan_data_quality(
        self,
        df: pd.DataFrame,
        col_mapping: Dict[str, str],
    ) -> List[RedFlagResult]:
        """
        Scan for data quality red flags.

        Checks:
        - Future dates
        - Duplicate rows
        - Period-end revenue spikes
        """
        red_flags = []

        # Check for future dates
        date_col = col_mapping.get('date')
        if date_col and date_col in df.columns:
            try:
                dates = pd.to_datetime(df[date_col], errors='coerce')
                today = pd.Timestamp.now()
                future_dates = dates[dates > today]

                if len(future_dates) > 0:
                    red_flags.append(RedFlagResult(
                        flag_type=RedFlagType.FUTURE_DATES,
                        severity="high",
                        category="data_quality",
                        title="Future dates detected",
                        description=(
                            f"Found {len(future_dates)} rows with dates in the future. "
                            f"Historical data should not contain future dates. This may indicate "
                            f"data entry errors, forecasts mixed with actuals, or timezone issues."
                        ),
                        evidence={
                            "future_date_count": int(len(future_dates)),
                            "earliest_future": future_dates.min().strftime('%Y-%m-%d'),
                            "latest_future": future_dates.max().strftime('%Y-%m-%d'),
                        },
                        recommendation=(
                            "Verify if future-dated records are forecasts (should be separate) "
                            "or data entry errors. Check for timezone conversion issues."
                        ),
                        affected_columns=[date_col],
                    ))
            except Exception:
                pass

        # Check for duplicate rows
        if len(df) > 0:
            dup_count = df.duplicated().sum()
            dup_percent = dup_count / len(df)

            if dup_percent > self.THRESHOLDS['duplicate_row_warning']:
                severity = "high" if dup_percent > self.THRESHOLDS['duplicate_row_critical'] else "medium"

                red_flags.append(RedFlagResult(
                    flag_type=RedFlagType.DUPLICATE_ROWS,
                    severity=severity,
                    category="data_quality",
                    title="Duplicate rows detected",
                    description=(
                        f"Found {dup_count} duplicate rows ({dup_percent*100:.2f}%). "
                        f"Duplicate data can inflate metrics and distort analysis."
                    ),
                    evidence={
                        "duplicate_count": int(dup_count),
                        "duplicate_percent": round(dup_percent * 100, 2),
                        "total_rows": int(len(df)),
                    },
                    recommendation=(
                        "Remove duplicate rows before analysis. Investigate the source of "
                        "duplicates - this may indicate data processing or extraction issues."
                    ),
                    affected_columns=list(df.columns[:5]),  # First 5 columns
                ))

        # Check for period-end spikes (hockey stick pattern)
        revenue_col = col_mapping.get('revenue')
        date_col = col_mapping.get('date')

        if revenue_col and date_col and revenue_col in df.columns and date_col in df.columns:
            result = self._check_period_end_spikes(df, revenue_col, date_col)
            if result:
                red_flags.append(result)

        # Check for negative values in columns that shouldn't be negative
        negative_impossible_cols = ['revenue', 'customer_count', 'headcount', 'mrr', 'arr']
        for col_type in negative_impossible_cols:
            col_name = col_mapping.get(col_type)
            if col_name and col_name in df.columns:
                values = pd.to_numeric(df[col_name], errors='coerce')
                negative_count = (values < 0).sum()
                if negative_count > 0 and col_type != 'revenue':  # Revenue already checked
                    red_flags.append(RedFlagResult(
                        flag_type=RedFlagType.NEGATIVE_IMPOSSIBLE,
                        severity="high",
                        category="data_quality",
                        title=f"Negative values in '{col_name}'",
                        description=(
                            f"Found {negative_count} negative values in '{col_name}'. "
                            f"This column type should not contain negative values."
                        ),
                        evidence={
                            "negative_count": int(negative_count),
                            "column_type": col_type,
                            "example_values": values[values < 0].head(5).tolist(),
                        },
                        recommendation=(
                            "Verify data source. Negative values here likely indicate "
                            "data entry errors or incorrect calculations."
                        ),
                        affected_columns=[col_name],
                    ))

        return red_flags

    def _identify_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Map column types to actual column names in the DataFrame"""
        mapping = {}
        df_cols_lower = {col.lower(): col for col in df.columns}

        for col_type, patterns in self.COLUMN_PATTERNS.items():
            for pattern in patterns:
                for col_lower, col_original in df_cols_lower.items():
                    if pattern in col_lower:
                        mapping[col_type] = col_original
                        break
                if col_type in mapping:
                    break

        return mapping

    def _has_financial_columns(self, col_mapping: Dict[str, str]) -> bool:
        """Check if financial columns are present"""
        financial_cols = ['revenue', 'ebitda', 'gross_margin', 'profit', 'cost']
        return any(col in col_mapping for col in financial_cols)

    def _has_customer_columns(self, col_mapping: Dict[str, str]) -> bool:
        """Check if customer columns are present"""
        customer_cols = ['customer_count', 'churn', 'mrr', 'arr']
        return any(col in col_mapping for col in customer_cols)

    def _has_operational_columns(self, col_mapping: Dict[str, str]) -> bool:
        """Check if operational columns are present"""
        return 'headcount' in col_mapping

    def _check_growth_rates(self, values: pd.Series, metric_name: str) -> List[RedFlagResult]:
        """Check for extreme growth or decline rates"""
        red_flags = []

        if len(values) < 2:
            return red_flags

        # Calculate period-over-period growth
        pct_change = values.pct_change().dropna()

        if len(pct_change) == 0:
            return red_flags

        # Check for extreme growth
        extreme_growth = pct_change[pct_change > self.THRESHOLDS['extreme_growth_warning']]
        if len(extreme_growth) > 0:
            max_growth = pct_change.max()
            severity = "high" if max_growth > self.THRESHOLDS['extreme_growth_critical'] else "medium"

            red_flags.append(RedFlagResult(
                flag_type=RedFlagType.EXTREME_GROWTH,
                severity=severity,
                category="financial",
                title=f"Extreme {metric_name} growth detected",
                description=(
                    f"Found {len(extreme_growth)} periods with growth exceeding "
                    f"{self.THRESHOLDS['extreme_growth_warning']*100:.0f}%. "
                    f"Maximum growth: {max_growth*100:.1f}%. Verify this is organic growth "
                    f"and not due to acquisitions, one-time events, or data issues."
                ),
                evidence={
                    "extreme_growth_periods": int(len(extreme_growth)),
                    "max_growth_percent": round(float(max_growth) * 100, 2),
                    "warning_threshold": self.THRESHOLDS['extreme_growth_warning'] * 100,
                },
                recommendation=(
                    "Investigate the cause of extreme growth. Verify if due to M&A, "
                    "large contract wins, or organic growth. Request supporting documentation."
                ),
                affected_columns=[],
            ))

        # Check for extreme decline
        extreme_decline = pct_change[pct_change < -self.THRESHOLDS['extreme_decline_warning']]
        if len(extreme_decline) > 0:
            max_decline = abs(pct_change.min())
            severity = "critical" if max_decline > self.THRESHOLDS['extreme_decline_critical'] else "high"

            red_flags.append(RedFlagResult(
                flag_type=RedFlagType.EXTREME_GROWTH,
                severity=severity,
                category="financial",
                title=f"Significant {metric_name} decline detected",
                description=(
                    f"Found {len(extreme_decline)} periods with decline exceeding "
                    f"{self.THRESHOLDS['extreme_decline_warning']*100:.0f}%. "
                    f"Maximum decline: {max_decline*100:.1f}%. This requires immediate attention."
                ),
                evidence={
                    "decline_periods": int(len(extreme_decline)),
                    "max_decline_percent": round(float(max_decline) * 100, 2),
                    "warning_threshold": self.THRESHOLDS['extreme_decline_warning'] * 100,
                },
                recommendation=(
                    "Urgently investigate the cause of decline. Review customer losses, "
                    "market conditions, and competitive dynamics. This is a critical risk factor."
                ),
                affected_columns=[],
            ))

        return red_flags

    def _check_period_end_spikes(
        self,
        df: pd.DataFrame,
        revenue_col: str,
        date_col: str,
    ) -> Optional[RedFlagResult]:
        """Check for suspicious period-end revenue spikes (hockey stick pattern)"""
        try:
            df_copy = df.copy()
            df_copy['_date'] = pd.to_datetime(df_copy[date_col], errors='coerce')
            df_copy['_revenue'] = pd.to_numeric(df_copy[revenue_col], errors='coerce')
            df_copy = df_copy.dropna(subset=['_date', '_revenue'])

            if len(df_copy) < 10:
                return None

            # Group by month and check if last week has disproportionate revenue
            df_copy['_month'] = df_copy['_date'].dt.to_period('M')
            df_copy['_day'] = df_copy['_date'].dt.day

            spike_months = []
            for month, group in df_copy.groupby('_month'):
                if len(group) < 5:
                    continue

                total_revenue = group['_revenue'].sum()
                if total_revenue <= 0:
                    continue

                # Last week of month (days 25-31)
                last_week = group[group['_day'] >= 25]['_revenue'].sum()
                last_week_pct = last_week / total_revenue

                if last_week_pct > self.THRESHOLDS['period_end_spike_warning']:
                    spike_months.append({
                        'month': str(month),
                        'last_week_percent': round(last_week_pct * 100, 1),
                    })

            if len(spike_months) >= 2:  # At least 2 months with spikes
                max_spike = max(m['last_week_percent'] for m in spike_months)
                severity = "high" if max_spike > self.THRESHOLDS['period_end_spike_critical'] * 100 else "medium"

                return RedFlagResult(
                    flag_type=RedFlagType.PERIOD_END_SPIKE,
                    severity=severity,
                    category="data_quality",
                    title="Period-end revenue spikes detected",
                    description=(
                        f"Found {len(spike_months)} months where >30% of revenue occurred in the "
                        f"last week. This 'hockey stick' pattern may indicate channel stuffing, "
                        f"aggressive end-of-period sales tactics, or revenue timing manipulation."
                    ),
                    evidence={
                        "spike_month_count": len(spike_months),
                        "spike_details": spike_months[:5],
                        "max_last_week_percent": round(max_spike, 1),
                    },
                    recommendation=(
                        "Review revenue recognition policies. Analyze deal timing patterns. "
                        "High period-end concentration may indicate sustainability risks or "
                        "aggressive sales practices."
                    ),
                    affected_columns=[revenue_col, date_col],
                )

        except Exception:
            pass

        return None
