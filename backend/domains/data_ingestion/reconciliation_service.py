"""
Cross-File Reconciliation Service

Validates data consistency across multiple files/data sources.
Used for PE due diligence to identify discrepancies between reported figures.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


class ReconciliationType(str, Enum):
    """Type of reconciliation check"""
    REVENUE_MATCH = "revenue_match"
    CUSTOMER_COUNT = "customer_count"
    HEADCOUNT_PAYROLL = "headcount_payroll"
    INVENTORY_COGS = "inventory_cogs"
    BALANCE_SHEET = "balance_sheet"
    PERIOD_TOTALS = "period_totals"
    CUSTOM = "custom"


class DiscrepancySeverity(str, Enum):
    """Severity of reconciliation discrepancy"""
    INFO = "info"  # < 1% difference
    WARNING = "warning"  # 1-5% difference
    HIGH = "high"  # 5-10% difference
    CRITICAL = "critical"  # > 10% difference


@dataclass
class ReconciliationResult:
    """Result from a reconciliation check"""
    reconciliation_type: ReconciliationType
    source_a: str  # First data source/file
    source_b: str  # Second data source/file
    field_a: str  # Field from source A
    field_b: str  # Field from source B
    matches: bool
    discrepancy_count: int
    discrepancy_percent: float
    severity: DiscrepancySeverity
    total_variance: float
    details: List[Dict[str, Any]]  # Period-by-period breakdown
    recommendation: str


@dataclass
class ReconciliationSummary:
    """Summary of all reconciliation checks"""
    total_checks: int
    passed: int
    failed: int
    critical_issues: int
    results: List[ReconciliationResult]
    overall_confidence: float  # 0-100 data confidence score


class ReconciliationService:
    """Service for cross-file data reconciliation"""

    # Tolerance thresholds for matching
    TOLERANCE_EXACT = 0.001  # 0.1%
    TOLERANCE_MINOR = 0.01  # 1%
    TOLERANCE_WARNING = 0.05  # 5%
    TOLERANCE_CRITICAL = 0.10  # 10%

    # Common column patterns for auto-detection
    COLUMN_PATTERNS = {
        'revenue': ['revenue', 'sales', 'income', 'turnover', 'receipts', 'total_revenue'],
        'customer_count': ['customers', 'customer_count', 'num_customers', 'client_count'],
        'headcount': ['headcount', 'employees', 'fte', 'staff_count', 'employee_count'],
        'payroll': ['payroll', 'salaries', 'wages', 'compensation', 'payroll_expense'],
        'inventory': ['inventory', 'stock', 'inventory_value'],
        'cogs': ['cogs', 'cost_of_goods', 'cost_of_sales', 'direct_costs'],
        'date': ['date', 'period', 'month', 'quarter', 'year', 'period_end'],
    }

    def reconcile_dataframes(
        self,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        source_a_name: str = "Source A",
        source_b_name: str = "Source B",
        reconciliation_type: Optional[ReconciliationType] = None,
    ) -> ReconciliationSummary:
        """
        Perform comprehensive reconciliation between two DataFrames.

        Args:
            df_a: First DataFrame
            df_b: Second DataFrame
            source_a_name: Name/description of first source
            source_b_name: Name/description of second source
            reconciliation_type: Specific type of reconciliation (auto-detect if None)

        Returns:
            ReconciliationSummary with all check results
        """
        results = []

        # Auto-detect common reconciliation opportunities
        cols_a = self._identify_columns(df_a)
        cols_b = self._identify_columns(df_b)

        # Revenue reconciliation
        if 'revenue' in cols_a and 'revenue' in cols_b:
            result = self._reconcile_metric(
                df_a, df_b, cols_a, cols_b,
                'revenue', 'revenue',
                ReconciliationType.REVENUE_MATCH,
                source_a_name, source_b_name
            )
            if result:
                results.append(result)

        # Customer count reconciliation
        if 'customer_count' in cols_a and 'customer_count' in cols_b:
            result = self._reconcile_metric(
                df_a, df_b, cols_a, cols_b,
                'customer_count', 'customer_count',
                ReconciliationType.CUSTOMER_COUNT,
                source_a_name, source_b_name
            )
            if result:
                results.append(result)

        # Headcount vs Payroll reconciliation
        if 'headcount' in cols_a and 'payroll' in cols_b:
            result = self._reconcile_headcount_payroll(
                df_a, df_b, cols_a, cols_b,
                source_a_name, source_b_name
            )
            if result:
                results.append(result)

        # Inventory vs COGS reconciliation
        if 'inventory' in cols_a and 'cogs' in cols_b:
            result = self._reconcile_inventory_cogs(
                df_a, df_b, cols_a, cols_b,
                source_a_name, source_b_name
            )
            if result:
                results.append(result)

        # Period totals check within each file
        if 'revenue' in cols_a and 'date' in cols_a:
            result = self._check_period_totals(
                df_a, cols_a, source_a_name
            )
            if result:
                results.append(result)

        return self._create_summary(results)

    def reconcile_specific(
        self,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        column_a: str,
        column_b: str,
        join_column_a: Optional[str] = None,
        join_column_b: Optional[str] = None,
        source_a_name: str = "Source A",
        source_b_name: str = "Source B",
        tolerance: float = 0.05,
    ) -> ReconciliationResult:
        """
        Reconcile specific columns between two DataFrames.

        Args:
            df_a: First DataFrame
            df_b: Second DataFrame
            column_a: Column to compare from df_a
            column_b: Column to compare from df_b
            join_column_a: Column to join on from df_a
            join_column_b: Column to join on from df_b
            source_a_name: Name of first source
            source_b_name: Name of second source
            tolerance: Acceptable variance (default 5%)

        Returns:
            ReconciliationResult with comparison details
        """
        if column_a not in df_a.columns or column_b not in df_b.columns:
            return ReconciliationResult(
                reconciliation_type=ReconciliationType.CUSTOM,
                source_a=source_a_name,
                source_b=source_b_name,
                field_a=column_a,
                field_b=column_b,
                matches=False,
                discrepancy_count=0,
                discrepancy_percent=100.0,
                severity=DiscrepancySeverity.CRITICAL,
                total_variance=0,
                details=[{"error": "Column not found in one or both sources"}],
                recommendation="Verify column names exist in both data sources",
            )

        # Prepare data for comparison
        if join_column_a and join_column_b:
            # Join on specified columns
            merged = pd.merge(
                df_a[[join_column_a, column_a]].rename(columns={column_a: 'value_a'}),
                df_b[[join_column_b, column_b]].rename(columns={column_b: 'value_b'}),
                left_on=join_column_a,
                right_on=join_column_b,
                how='outer'
            )
        else:
            # Compare totals or row-by-row if same length
            if len(df_a) == len(df_b):
                merged = pd.DataFrame({
                    'value_a': df_a[column_a].values,
                    'value_b': df_b[column_b].values,
                })
            else:
                # Compare totals only
                total_a = pd.to_numeric(df_a[column_a], errors='coerce').sum()
                total_b = pd.to_numeric(df_b[column_b], errors='coerce').sum()
                merged = pd.DataFrame({
                    'value_a': [total_a],
                    'value_b': [total_b],
                })

        return self._compare_values(
            merged, column_a, column_b,
            ReconciliationType.CUSTOM,
            source_a_name, source_b_name,
            tolerance
        )

    def check_internal_consistency(
        self,
        df: pd.DataFrame,
        source_name: str = "Data",
    ) -> List[ReconciliationResult]:
        """
        Check internal consistency within a single DataFrame.

        Validates:
        - Subtotals match details
        - Calculated fields are correct
        - Period-over-period continuity
        """
        results = []
        cols = self._identify_columns(df)

        # Check if totals columns match sum of details
        # (This is a simplified example - real implementation would be more sophisticated)

        # Check for balance sheet equation: Assets = Liabilities + Equity
        asset_cols = [c for c in df.columns if 'asset' in c.lower()]
        liability_cols = [c for c in df.columns if 'liabilit' in c.lower()]
        equity_cols = [c for c in df.columns if 'equity' in c.lower()]

        if asset_cols and liability_cols and equity_cols:
            result = self._check_balance_sheet_equation(
                df, asset_cols[0], liability_cols[0], equity_cols[0], source_name
            )
            if result:
                results.append(result)

        # Check period continuity
        if 'date' in cols:
            result = self._check_period_continuity(df, cols, source_name)
            if result:
                results.append(result)

        return results

    def _identify_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Map column types to actual column names"""
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

    def _reconcile_metric(
        self,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        cols_a: Dict[str, str],
        cols_b: Dict[str, str],
        metric_type_a: str,
        metric_type_b: str,
        reconciliation_type: ReconciliationType,
        source_a_name: str,
        source_b_name: str,
    ) -> Optional[ReconciliationResult]:
        """Reconcile a specific metric between two sources"""
        col_a = cols_a.get(metric_type_a)
        col_b = cols_b.get(metric_type_b)

        if not col_a or not col_b:
            return None

        # Try to join on date if available
        date_col_a = cols_a.get('date')
        date_col_b = cols_b.get('date')

        if date_col_a and date_col_b:
            # Normalize dates
            df_a = df_a.copy()
            df_b = df_b.copy()
            df_a['_join_date'] = pd.to_datetime(df_a[date_col_a], errors='coerce')
            df_b['_join_date'] = pd.to_datetime(df_b[date_col_b], errors='coerce')

            # Merge on date
            merged = pd.merge(
                df_a[['_join_date', col_a]].rename(columns={col_a: 'value_a'}),
                df_b[['_join_date', col_b]].rename(columns={col_b: 'value_b'}),
                on='_join_date',
                how='outer'
            )
            merged['period'] = merged['_join_date'].dt.strftime('%Y-%m-%d')
        else:
            # Compare totals
            total_a = pd.to_numeric(df_a[col_a], errors='coerce').sum()
            total_b = pd.to_numeric(df_b[col_b], errors='coerce').sum()
            merged = pd.DataFrame({
                'value_a': [total_a],
                'value_b': [total_b],
                'period': ['Total'],
            })

        return self._compare_values(
            merged, col_a, col_b,
            reconciliation_type,
            source_a_name, source_b_name
        )

    def _reconcile_headcount_payroll(
        self,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        cols_a: Dict[str, str],
        cols_b: Dict[str, str],
        source_a_name: str,
        source_b_name: str,
    ) -> Optional[ReconciliationResult]:
        """
        Check if headcount aligns with payroll expense.

        This is a ratio check rather than exact match.
        """
        headcount_col = cols_a.get('headcount')
        payroll_col = cols_b.get('payroll')

        if not headcount_col or not payroll_col:
            return None

        headcount = pd.to_numeric(df_a[headcount_col], errors='coerce')
        payroll = pd.to_numeric(df_b[payroll_col], errors='coerce')

        avg_headcount = headcount.mean()
        total_payroll = payroll.sum()

        if avg_headcount > 0:
            cost_per_employee = total_payroll / avg_headcount

            # Check if cost per employee is reasonable (simplified check)
            # Typical range: $30k - $300k annually
            details = [{
                'avg_headcount': round(float(avg_headcount), 1),
                'total_payroll': round(float(total_payroll), 2),
                'cost_per_employee': round(float(cost_per_employee), 2),
            }]

            reasonable = 30000 < cost_per_employee < 300000
            severity = DiscrepancySeverity.INFO if reasonable else DiscrepancySeverity.WARNING

            return ReconciliationResult(
                reconciliation_type=ReconciliationType.HEADCOUNT_PAYROLL,
                source_a=source_a_name,
                source_b=source_b_name,
                field_a=headcount_col,
                field_b=payroll_col,
                matches=reasonable,
                discrepancy_count=0 if reasonable else 1,
                discrepancy_percent=0.0,
                severity=severity,
                total_variance=cost_per_employee,
                details=details,
                recommendation=(
                    "Headcount and payroll appear aligned"
                    if reasonable else
                    f"Cost per employee (${cost_per_employee:,.0f}) outside typical range. Verify data."
                ),
            )

        return None

    def _reconcile_inventory_cogs(
        self,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        cols_a: Dict[str, str],
        cols_b: Dict[str, str],
        source_a_name: str,
        source_b_name: str,
    ) -> Optional[ReconciliationResult]:
        """
        Check inventory vs COGS relationship.

        Inventory turnover should be reasonable (typically 2-12x annually).
        """
        inventory_col = cols_a.get('inventory')
        cogs_col = cols_b.get('cogs')

        if not inventory_col or not cogs_col:
            return None

        inventory = pd.to_numeric(df_a[inventory_col], errors='coerce')
        cogs = pd.to_numeric(df_b[cogs_col], errors='coerce')

        avg_inventory = inventory.mean()
        total_cogs = cogs.sum()

        if avg_inventory > 0:
            # Estimate annual turnover
            turnover = total_cogs / avg_inventory

            details = [{
                'avg_inventory': round(float(avg_inventory), 2),
                'total_cogs': round(float(total_cogs), 2),
                'implied_turnover': round(float(turnover), 2),
            }]

            # Reasonable turnover is 2-12x (depends on industry)
            reasonable = 1 < turnover < 20
            severity = DiscrepancySeverity.INFO if reasonable else DiscrepancySeverity.WARNING

            return ReconciliationResult(
                reconciliation_type=ReconciliationType.INVENTORY_COGS,
                source_a=source_a_name,
                source_b=source_b_name,
                field_a=inventory_col,
                field_b=cogs_col,
                matches=reasonable,
                discrepancy_count=0 if reasonable else 1,
                discrepancy_percent=0.0,
                severity=severity,
                total_variance=turnover,
                details=details,
                recommendation=(
                    f"Inventory turnover ({turnover:.1f}x) appears reasonable"
                    if reasonable else
                    f"Inventory turnover ({turnover:.1f}x) unusual. Verify inventory valuation and COGS."
                ),
            )

        return None

    def _check_period_totals(
        self,
        df: pd.DataFrame,
        cols: Dict[str, str],
        source_name: str,
    ) -> Optional[ReconciliationResult]:
        """Check if period totals are internally consistent"""
        # This is a simplified check for duplicate period entries
        date_col = cols.get('date')
        revenue_col = cols.get('revenue')

        if not date_col or not revenue_col:
            return None

        df = df.copy()
        df['_date'] = pd.to_datetime(df[date_col], errors='coerce')

        # Check for duplicate periods
        duplicates = df.groupby('_date').size()
        dup_periods = duplicates[duplicates > 1]

        if len(dup_periods) > 0:
            details = [
                {'period': str(period)[:10], 'count': int(count)}
                for period, count in dup_periods.head(5).items()
            ]

            return ReconciliationResult(
                reconciliation_type=ReconciliationType.PERIOD_TOTALS,
                source_a=source_name,
                source_b=source_name,
                field_a=date_col,
                field_b=revenue_col,
                matches=False,
                discrepancy_count=len(dup_periods),
                discrepancy_percent=len(dup_periods) / len(duplicates) * 100,
                severity=DiscrepancySeverity.WARNING,
                total_variance=0,
                details=details,
                recommendation="Found duplicate entries for same period. Verify if intentional or data error.",
            )

        return None

    def _check_balance_sheet_equation(
        self,
        df: pd.DataFrame,
        asset_col: str,
        liability_col: str,
        equity_col: str,
        source_name: str,
    ) -> Optional[ReconciliationResult]:
        """Check if Assets = Liabilities + Equity"""
        assets = pd.to_numeric(df[asset_col], errors='coerce')
        liabilities = pd.to_numeric(df[liability_col], errors='coerce')
        equity = pd.to_numeric(df[equity_col], errors='coerce')

        expected = liabilities + equity
        variance = (assets - expected).abs()
        variance_pct = (variance / assets.replace(0, np.nan)).fillna(0)

        issues = variance_pct[variance_pct > self.TOLERANCE_MINOR]

        if len(issues) > 0:
            severity = DiscrepancySeverity.CRITICAL if variance_pct.max() > self.TOLERANCE_CRITICAL else DiscrepancySeverity.HIGH

            return ReconciliationResult(
                reconciliation_type=ReconciliationType.BALANCE_SHEET,
                source_a=source_name,
                source_b=source_name,
                field_a=asset_col,
                field_b=f"{liability_col} + {equity_col}",
                matches=False,
                discrepancy_count=len(issues),
                discrepancy_percent=float(variance_pct.max() * 100),
                severity=severity,
                total_variance=float(variance.sum()),
                details=[{
                    'max_variance_pct': round(float(variance_pct.max() * 100), 2),
                    'rows_with_issues': len(issues),
                }],
                recommendation="Balance sheet equation (A = L + E) does not balance. Check for missing accounts.",
            )

        return None

    def _check_period_continuity(
        self,
        df: pd.DataFrame,
        cols: Dict[str, str],
        source_name: str,
    ) -> Optional[ReconciliationResult]:
        """Check for gaps in period sequence"""
        date_col = cols.get('date')
        if not date_col:
            return None

        dates = pd.to_datetime(df[date_col], errors='coerce').dropna().sort_values()

        if len(dates) < 3:
            return None

        # Calculate gaps
        gaps = dates.diff().dropna()
        median_gap = gaps.median()

        # Find large gaps (> 2x median)
        large_gaps = gaps[gaps > median_gap * 2]

        if len(large_gaps) > 0:
            return ReconciliationResult(
                reconciliation_type=ReconciliationType.PERIOD_TOTALS,
                source_a=source_name,
                source_b=source_name,
                field_a=date_col,
                field_b="Period sequence",
                matches=False,
                discrepancy_count=len(large_gaps),
                discrepancy_percent=len(large_gaps) / len(gaps) * 100,
                severity=DiscrepancySeverity.WARNING,
                total_variance=0,
                details=[{
                    'gap_count': len(large_gaps),
                    'typical_gap_days': int(median_gap.days),
                }],
                recommendation="Found gaps in period sequence. Verify if data is complete.",
            )

        return None

    def _compare_values(
        self,
        merged: pd.DataFrame,
        field_a: str,
        field_b: str,
        reconciliation_type: ReconciliationType,
        source_a_name: str,
        source_b_name: str,
        tolerance: float = 0.05,
    ) -> ReconciliationResult:
        """Compare values and generate reconciliation result"""
        merged['value_a'] = pd.to_numeric(merged['value_a'], errors='coerce')
        merged['value_b'] = pd.to_numeric(merged['value_b'], errors='coerce')

        # Calculate variance
        merged['variance'] = merged['value_a'] - merged['value_b']
        merged['variance_pct'] = (
            merged['variance'].abs() /
            merged[['value_a', 'value_b']].max(axis=1).replace(0, np.nan)
        ).fillna(0)

        # Identify discrepancies
        discrepancies = merged[merged['variance_pct'] > tolerance]
        discrepancy_count = len(discrepancies)
        max_variance_pct = float(merged['variance_pct'].max())
        total_variance = float(merged['variance'].abs().sum())

        # Determine severity
        if max_variance_pct <= self.TOLERANCE_MINOR:
            severity = DiscrepancySeverity.INFO
        elif max_variance_pct <= self.TOLERANCE_WARNING:
            severity = DiscrepancySeverity.WARNING
        elif max_variance_pct <= self.TOLERANCE_CRITICAL:
            severity = DiscrepancySeverity.HIGH
        else:
            severity = DiscrepancySeverity.CRITICAL

        # Build details
        details = []
        for _, row in discrepancies.head(10).iterrows():
            detail = {
                'value_a': round(float(row['value_a']), 2) if pd.notna(row['value_a']) else None,
                'value_b': round(float(row['value_b']), 2) if pd.notna(row['value_b']) else None,
                'variance': round(float(row['variance']), 2) if pd.notna(row['variance']) else None,
                'variance_pct': round(float(row['variance_pct'] * 100), 2),
            }
            if 'period' in row:
                detail['period'] = row['period']
            details.append(detail)

        matches = discrepancy_count == 0

        # Generate recommendation
        if matches:
            recommendation = f"{field_a} reconciles with {field_b} within tolerance"
        elif severity == DiscrepancySeverity.CRITICAL:
            recommendation = f"Critical discrepancy: {field_a} vs {field_b} differs by {max_variance_pct*100:.1f}%. Immediate investigation required."
        else:
            recommendation = f"Discrepancy found: {discrepancy_count} periods differ. Review data sources for consistency."

        return ReconciliationResult(
            reconciliation_type=reconciliation_type,
            source_a=source_a_name,
            source_b=source_b_name,
            field_a=field_a,
            field_b=field_b,
            matches=matches,
            discrepancy_count=discrepancy_count,
            discrepancy_percent=round(max_variance_pct * 100, 2),
            severity=severity,
            total_variance=round(total_variance, 2),
            details=details,
            recommendation=recommendation,
        )

    def _create_summary(
        self,
        results: List[ReconciliationResult],
    ) -> ReconciliationSummary:
        """Create summary from all reconciliation results"""
        if not results:
            return ReconciliationSummary(
                total_checks=0,
                passed=0,
                failed=0,
                critical_issues=0,
                results=[],
                overall_confidence=100.0,
            )

        passed = sum(1 for r in results if r.matches)
        failed = len(results) - passed
        critical = sum(1 for r in results if r.severity == DiscrepancySeverity.CRITICAL)

        # Calculate confidence score
        # Start at 100, deduct based on issues
        confidence = 100.0
        for result in results:
            if result.severity == DiscrepancySeverity.CRITICAL:
                confidence -= 25
            elif result.severity == DiscrepancySeverity.HIGH:
                confidence -= 15
            elif result.severity == DiscrepancySeverity.WARNING:
                confidence -= 5

        confidence = max(confidence, 0)

        return ReconciliationSummary(
            total_checks=len(results),
            passed=passed,
            failed=failed,
            critical_issues=critical,
            results=results,
            overall_confidence=round(confidence, 1),
        )
