"""
Data Ingestion Service

Analyzes uploaded CSV/Excel files with schema detection optimized for PE due diligence.
"""
import re
import time
from io import BytesIO
from typing import Any, List, Optional, Tuple

import pandas as pd
import numpy as np

from domains.data_ingestion.models import (
    ColumnAnalysis,
    DataQualityFlag,
    FileAnalysisResponse,
    InferredDataType,
    SheetAnalysis,
)
from domains.data_ingestion.anomaly_service import AnomalyDetectionService
from domains.data_ingestion.red_flag_scanner import RedFlagScanner


class DataIngestionService:
    """Service for analyzing uploaded data files"""

    # Patterns for type detection
    EMAIL_PATTERN = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
    PHONE_PATTERN = re.compile(r'^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$')
    URL_PATTERN = re.compile(r'^https?://[^\s]+$')
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
    CURRENCY_PATTERN = re.compile(r'^[\$\€\£\¥]?\s*-?[\d,]+\.?\d*$')
    PERCENTAGE_PATTERN = re.compile(r'^-?\d+\.?\d*\s*%$')
    DATE_PATTERNS = [
        re.compile(r'^\d{4}-\d{2}-\d{2}$'),  # YYYY-MM-DD
        re.compile(r'^\d{2}/\d{2}/\d{4}$'),  # MM/DD/YYYY
        re.compile(r'^\d{2}-\d{2}-\d{4}$'),  # DD-MM-YYYY
    ]

    # PE-relevant column name patterns
    PE_CATEGORIES = {
        'financial': ['revenue', 'sales', 'profit', 'ebitda', 'margin', 'cost', 'expense', 'income', 'cash', 'debt', 'equity', 'asset', 'liability', 'balance'],
        'customer': ['customer', 'client', 'account', 'subscriber', 'user', 'buyer', 'churn', 'retention', 'ltv', 'arpu', 'mrr', 'arr'],
        'operational': ['employee', 'headcount', 'fte', 'productivity', 'efficiency', 'capacity', 'utilization'],
        'sales': ['deal', 'pipeline', 'opportunity', 'quota', 'booking', 'contract', 'order', 'lead'],
        'hr': ['salary', 'compensation', 'tenure', 'turnover', 'hire', 'termination', 'department', 'title'],
        'inventory': ['sku', 'inventory', 'stock', 'warehouse', 'shipment', 'fulfillment'],
    }

    def analyze_file(
        self,
        file_content: bytes,
        filename: str,
        file_type: str,
    ) -> FileAnalysisResponse:
        """
        Analyze an uploaded file and return schema + quality analysis.

        Args:
            file_content: Raw file bytes
            filename: Original filename
            file_type: MIME type or extension

        Returns:
            FileAnalysisResponse with full analysis
        """
        start_time = time.time()

        # Parse file into DataFrames
        sheets = self._parse_file(file_content, filename, file_type)

        # Analyze each sheet
        sheet_analyses = []
        total_rows = 0
        total_columns = 0
        all_quality_issues = []
        detected_categories = set()

        for sheet_name, df in sheets:
            analysis = self._analyze_sheet(sheet_name, df)
            sheet_analyses.append(analysis)
            total_rows += analysis.row_count
            total_columns += analysis.column_count
            all_quality_issues.extend(analysis.quality_issues)

            # Detect PE-relevant categories
            for col in analysis.columns:
                categories = self._detect_pe_categories(col.name)
                detected_categories.update(categories)

        # Calculate overall quality score
        if sheet_analyses:
            overall_quality = sum(s.quality_score for s in sheet_analyses) / len(sheet_analyses)
        else:
            overall_quality = 0

        # Generate PE-specific insights
        potential_issues = self._identify_pe_issues(sheet_analyses)
        recommendations = self._generate_recommendations(sheet_analyses, detected_categories)

        # Generate summary
        summary = self._generate_summary(
            filename, total_rows, total_columns,
            len(sheet_analyses), detected_categories, overall_quality
        )

        duration_ms = int((time.time() - start_time) * 1000)

        return FileAnalysisResponse(
            filename=filename,
            file_size_bytes=len(file_content),
            file_type=file_type,
            sheets=sheet_analyses,
            total_rows=total_rows,
            total_columns=total_columns,
            analysis_duration_ms=duration_ms,
            overall_quality_score=round(overall_quality, 1),
            summary=summary,
            detected_data_categories=list(detected_categories),
            potential_issues=potential_issues,
            recommendations=recommendations,
        )

    def _parse_file(
        self,
        file_content: bytes,
        filename: str,
        file_type: str,
    ) -> List[Tuple[str, pd.DataFrame]]:
        """Parse file content into list of (sheet_name, DataFrame) tuples"""
        buffer = BytesIO(file_content)
        ext = filename.lower().split('.')[-1] if '.' in filename else ''

        if ext == 'csv' or 'csv' in file_type:
            df = pd.read_csv(buffer)
            return [(filename.rsplit('.', 1)[0], df)]

        elif ext == 'tsv' or 'tab-separated' in file_type:
            df = pd.read_csv(buffer, sep='\t')
            return [(filename.rsplit('.', 1)[0], df)]

        elif ext in ['xlsx', 'xls'] or 'excel' in file_type or 'spreadsheet' in file_type:
            excel = pd.ExcelFile(buffer)
            sheets = []
            for sheet_name in excel.sheet_names:
                df = pd.read_excel(excel, sheet_name=sheet_name)
                if not df.empty:
                    sheets.append((sheet_name, df))
            return sheets

        else:
            # Try CSV as fallback
            try:
                df = pd.read_csv(buffer)
                return [(filename.rsplit('.', 1)[0] if '.' in filename else filename, df)]
            except Exception:
                raise ValueError(f"Unsupported file type: {file_type}")

    def _analyze_sheet(self, sheet_name: str, df: pd.DataFrame) -> SheetAnalysis:
        """Analyze a single sheet/DataFrame"""
        columns = []
        quality_issues = []

        for col_name in df.columns:
            col_analysis = self._analyze_column(df[col_name], str(col_name))
            columns.append(col_analysis)

            # Collect quality issues
            for flag in col_analysis.quality_flags:
                quality_issues.append(f"{col_name}: {flag.value}")

        # Calculate quality score
        quality_score = self._calculate_quality_score(columns, len(df))

        # Get sample data (first 10 rows, convert to JSON-serializable format)
        sample_df = df.head(10).copy()
        for col in sample_df.columns:
            sample_df[col] = sample_df[col].apply(self._make_serializable)
        sample_data = sample_df.values.tolist()

        # Run anomaly detection
        anomalies = []
        try:
            anomaly_service = AnomalyDetectionService()
            for col in columns:
                col_anomalies = anomaly_service.analyze_column(
                    col.name, df[col.name], col.inferred_type.value
                )
                for anomaly in col_anomalies:
                    anomalies.append(anomaly.model_dump())
                    quality_issues.append(f"ANOMALY: {anomaly.title}")
        except Exception:
            pass  # Don't fail analysis if anomaly detection fails

        # Detect PE-relevant categories for red flag scanning
        detected_categories = set()
        for col in columns:
            categories = self._detect_pe_categories(col.name)
            detected_categories.update(categories)

        # Run red flag scanner
        red_flags = []
        try:
            red_flag_scanner = RedFlagScanner()
            rf_results = red_flag_scanner.scan_dataframe(df, list(detected_categories))
            for rf in rf_results:
                red_flags.append(rf.model_dump())
                quality_issues.append(f"RED FLAG: {rf.title}")
        except Exception:
            pass  # Don't fail analysis if red flag scanning fails

        return SheetAnalysis(
            sheet_name=sheet_name,
            row_count=len(df),
            column_count=len(df.columns),
            columns=columns,
            sample_data=sample_data,
            quality_score=round(quality_score, 1),
            quality_issues=quality_issues[:30],  # Increased limit to accommodate anomalies/red flags
            anomalies=anomalies,
            red_flags=red_flags,
        )

    def _analyze_column(self, series: pd.Series, col_name: str) -> ColumnAnalysis:
        """Analyze a single column"""
        # Basic stats
        null_count = series.isnull().sum()
        null_percent = (null_count / len(series) * 100) if len(series) > 0 else 0
        unique_count = series.nunique()
        unique_percent = (unique_count / len(series) * 100) if len(series) > 0 else 0

        # Infer type
        inferred_type = self._infer_column_type(series)

        # Quality flags
        quality_flags = []

        if null_percent > 50:
            quality_flags.append(DataQualityFlag.MISSING_VALUES)
        if null_percent == 100:
            quality_flags.append(DataQualityFlag.EMPTY_COLUMN)
        if unique_percent > 95 and len(series) > 10:
            quality_flags.append(DataQualityFlag.HIGH_CARDINALITY)
        if unique_count <= 2 and len(series) > 10:
            quality_flags.append(DataQualityFlag.LOW_CARDINALITY)

        # Get example values
        non_null = series.dropna()
        examples = [str(v) for v in non_null.unique()[:5]]

        # Type-specific stats
        min_val = max_val = mean_val = std_dev = None
        min_len = max_len = avg_len = None

        if inferred_type in [InferredDataType.INTEGER, InferredDataType.FLOAT, InferredDataType.CURRENCY]:
            try:
                numeric = pd.to_numeric(non_null.astype(str).str.replace(r'[\$,€£¥%]', '', regex=True), errors='coerce')
                if not numeric.empty:
                    min_val = str(numeric.min())
                    max_val = str(numeric.max())
                    mean_val = float(numeric.mean())
                    std_dev = float(numeric.std()) if len(numeric) > 1 else None

                    # Check for outliers using IQR
                    q1 = numeric.quantile(0.25)
                    q3 = numeric.quantile(0.75)
                    iqr = q3 - q1
                    outlier_count = ((numeric < q1 - 1.5 * iqr) | (numeric > q3 + 1.5 * iqr)).sum()
                    if outlier_count > len(numeric) * 0.05:
                        quality_flags.append(DataQualityFlag.OUTLIERS)
            except Exception:
                pass

        elif inferred_type == InferredDataType.STRING:
            try:
                lengths = non_null.astype(str).str.len()
                if not lengths.empty:
                    min_len = int(lengths.min())
                    max_len = int(lengths.max())
                    avg_len = float(lengths.mean())
            except Exception:
                pass

        return ColumnAnalysis(
            name=col_name,
            inferred_type=inferred_type,
            nullable=null_count > 0,
            null_count=int(null_count),
            null_percent=round(null_percent, 2),
            unique_count=int(unique_count),
            unique_percent=round(unique_percent, 2),
            example_values=examples,
            min_value=min_val,
            max_value=max_val,
            mean_value=round(mean_val, 4) if mean_val is not None else None,
            std_dev=round(std_dev, 4) if std_dev is not None else None,
            min_length=min_len,
            max_length=max_len,
            avg_length=round(avg_len, 2) if avg_len is not None else None,
            quality_flags=quality_flags,
        )

    def _infer_column_type(self, series: pd.Series) -> InferredDataType:
        """Infer the semantic type of a column"""
        non_null = series.dropna()
        if len(non_null) == 0:
            return InferredDataType.STRING

        # Sample for pattern matching (performance)
        sample = non_null.head(100).astype(str)

        # Check for specific patterns first
        if sample.apply(lambda x: bool(self.EMAIL_PATTERN.match(x))).mean() > 0.8:
            return InferredDataType.EMAIL

        if sample.apply(lambda x: bool(self.UUID_PATTERN.match(x))).mean() > 0.8:
            return InferredDataType.UUID

        if sample.apply(lambda x: bool(self.URL_PATTERN.match(x))).mean() > 0.8:
            return InferredDataType.URL

        if sample.apply(lambda x: bool(self.PERCENTAGE_PATTERN.match(x))).mean() > 0.8:
            return InferredDataType.PERCENTAGE

        if sample.apply(lambda x: bool(self.CURRENCY_PATTERN.match(x.replace(',', '')))).mean() > 0.8:
            # Check if it's actually currency (has symbol or column name suggests it)
            if sample.str.contains(r'[\$€£¥]').any():
                return InferredDataType.CURRENCY

        if sample.apply(lambda x: bool(self.PHONE_PATTERN.match(x.replace(' ', '')))).mean() > 0.5:
            return InferredDataType.PHONE

        # Check for dates
        for pattern in self.DATE_PATTERNS:
            if sample.apply(lambda x: bool(pattern.match(x))).mean() > 0.8:
                return InferredDataType.DATE

        # Try pandas datetime parsing
        try:
            pd.to_datetime(sample, errors='raise')
            return InferredDataType.DATETIME
        except Exception:
            pass

        # Check pandas dtype
        dtype = series.dtype
        if pd.api.types.is_integer_dtype(dtype):
            return InferredDataType.INTEGER
        if pd.api.types.is_float_dtype(dtype):
            return InferredDataType.FLOAT
        if pd.api.types.is_bool_dtype(dtype):
            return InferredDataType.BOOLEAN

        # Try numeric conversion
        try:
            numeric = pd.to_numeric(non_null, errors='raise')
            if (numeric % 1 == 0).all():
                return InferredDataType.INTEGER
            return InferredDataType.FLOAT
        except Exception:
            pass

        return InferredDataType.STRING

    def _calculate_quality_score(self, columns: List[ColumnAnalysis], row_count: int) -> float:
        """Calculate overall quality score for a sheet"""
        if not columns or row_count == 0:
            return 0

        scores = []

        for col in columns:
            col_score = 100

            # Penalize missing values
            col_score -= min(col.null_percent * 0.5, 30)

            # Penalize quality flags
            col_score -= len(col.quality_flags) * 5

            scores.append(max(col_score, 0))

        return sum(scores) / len(scores) if scores else 0

    def _detect_pe_categories(self, col_name: str) -> List[str]:
        """Detect PE-relevant data categories from column name"""
        col_lower = col_name.lower()
        categories = []

        for category, keywords in self.PE_CATEGORIES.items():
            for keyword in keywords:
                if keyword in col_lower:
                    categories.append(category)
                    break

        return categories

    def _identify_pe_issues(self, sheets: List[SheetAnalysis]) -> List[str]:
        """Identify potential issues relevant to PE due diligence"""
        issues = []

        for sheet in sheets:
            # Check for data completeness
            high_null_cols = [c.name for c in sheet.columns if c.null_percent > 30]
            if high_null_cols:
                issues.append(f"{sheet.sheet_name}: High missing data in {', '.join(high_null_cols[:3])}")

            # Check for small datasets
            if sheet.row_count < 12:
                issues.append(f"{sheet.sheet_name}: Limited data ({sheet.row_count} rows) - may not show trends")

            # Check for outliers in numeric columns
            outlier_cols = [c.name for c in sheet.columns if DataQualityFlag.OUTLIERS in c.quality_flags]
            if outlier_cols:
                issues.append(f"{sheet.sheet_name}: Potential outliers in {', '.join(outlier_cols[:3])}")

        return issues[:10]

    def _generate_recommendations(
        self,
        sheets: List[SheetAnalysis],
        categories: set,
    ) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []

        # Category-specific recommendations
        if 'financial' in categories:
            recommendations.append("Financial data detected - verify currency and date formats are consistent")
        if 'customer' in categories:
            recommendations.append("Customer data detected - check for PII and consider anonymization")
        if 'hr' in categories:
            recommendations.append("HR/compensation data detected - ensure confidentiality requirements are met")

        # Quality-based recommendations
        for sheet in sheets:
            if sheet.quality_score < 70:
                recommendations.append(f"{sheet.sheet_name}: Data quality below threshold - review before analysis")

        return recommendations[:5]

    def _generate_summary(
        self,
        filename: str,
        total_rows: int,
        total_columns: int,
        sheet_count: int,
        categories: set,
        quality_score: float,
    ) -> str:
        """Generate a human-readable summary"""
        parts = [f"Analyzed '{filename}': {total_rows:,} rows across {total_columns} columns"]

        if sheet_count > 1:
            parts.append(f" in {sheet_count} sheets")

        if categories:
            parts.append(f". Detected data categories: {', '.join(categories)}")

        parts.append(f". Overall quality score: {quality_score:.0f}/100")

        return ''.join(parts)

    def _make_serializable(self, val: Any) -> Any:
        """Convert value to JSON-serializable format"""
        if pd.isna(val):
            return None
        if isinstance(val, (np.integer, np.floating)):
            return float(val)
        if isinstance(val, np.bool_):
            return bool(val)
        if isinstance(val, pd.Timestamp):
            return val.isoformat()
        return str(val) if not isinstance(val, (str, int, float, bool, type(None))) else val
