"""
File Parser for Investor Data Ingestion

Parses CSV and Excel files for FO/LP data import.
"""
from io import BytesIO
from typing import List, Tuple, Any, Dict

import pandas as pd
import numpy as np


class FileParser:
    """Parses uploaded files into DataFrames."""

    @staticmethod
    def parse_file(
        file_content: bytes,
        filename: str,
        file_type: str = None
    ) -> List[Tuple[str, pd.DataFrame]]:
        """
        Parse file content into list of (sheet_name, DataFrame) tuples.

        Args:
            file_content: Raw file bytes
            filename: Original filename
            file_type: MIME type or extension (optional)

        Returns:
            List of (sheet_name, DataFrame) tuples
        """
        buffer = BytesIO(file_content)
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        file_type = file_type or ''

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
                raise ValueError(f"Unsupported file type: {file_type or ext}")

    @staticmethod
    def get_column_preview(df: pd.DataFrame, max_samples: int = 5) -> List[Dict[str, Any]]:
        """
        Get preview information for each column.

        Args:
            df: DataFrame to analyze
            max_samples: Maximum sample values to include

        Returns:
            List of column preview dictionaries
        """
        previews = []

        for col_name in df.columns:
            col = df[col_name]

            # Infer type
            dtype = col.dtype
            if pd.api.types.is_integer_dtype(dtype):
                inferred_type = "integer"
            elif pd.api.types.is_float_dtype(dtype):
                inferred_type = "float"
            elif pd.api.types.is_bool_dtype(dtype):
                inferred_type = "boolean"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                inferred_type = "datetime"
            else:
                inferred_type = "string"

            # Get sample values
            non_null = col.dropna()
            samples = [
                FileParser._make_serializable(v)
                for v in non_null.unique()[:max_samples]
            ]

            previews.append({
                "name": str(col_name),
                "inferred_type": inferred_type,
                "sample_values": samples,
                "null_count": int(col.isnull().sum()),
                "unique_count": int(col.nunique())
            })

        return previews

    @staticmethod
    def get_sample_data(df: pd.DataFrame, max_rows: int = 10) -> List[Dict[str, Any]]:
        """
        Get sample rows from the DataFrame.

        Args:
            df: DataFrame to sample
            max_rows: Maximum rows to return

        Returns:
            List of row dictionaries
        """
        sample_df = df.head(max_rows).copy()

        # Convert to JSON-serializable format
        for col in sample_df.columns:
            sample_df[col] = sample_df[col].apply(FileParser._make_serializable)

        return sample_df.to_dict(orient='records')

    @staticmethod
    def _make_serializable(val: Any) -> Any:
        """Convert value to JSON-serializable format."""
        if pd.isna(val):
            return None
        if isinstance(val, (np.integer, np.floating)):
            return float(val)
        if isinstance(val, np.bool_):
            return bool(val)
        if isinstance(val, pd.Timestamp):
            return val.isoformat()
        return str(val) if not isinstance(val, (str, int, float, bool, type(None))) else val
