"""Tabular tokenizer for mixed data types."""
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from .config import TokenizerConfig

logger = logging.getLogger(__name__)


@dataclass
class ColumnInfo:
    """Information about a column for tokenization."""
    name: str
    dtype: str  # "numeric", "categorical", "datetime"
    original_dtype: str
    n_categories: int = 0
    categories: Optional[List[Any]] = None
    bin_edges: Optional[np.ndarray] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    has_missing: bool = False
    missing_indicator_idx: Optional[int] = None


class TabularTokenizer:
    """Tokenizer for mixed tabular data types.

    Converts tabular data with numeric, categorical, and datetime columns
    into a unified representation suitable for neural network processing.

    Features:
    - Numeric: Standardization + optional binning for embedding lookup
    - Categorical: Integer encoding with vocabulary
    - Datetime: Decomposition into components (year, month, day, etc.)
    - Missing values: Indicator tokens or imputation
    """

    def __init__(self, config: Optional[TokenizerConfig] = None):
        """Initialize tokenizer.

        Args:
            config: Tokenizer configuration
        """
        self.config = config or TokenizerConfig()
        self._fitted = False
        self._columns: List[ColumnInfo] = []
        self._column_order: List[str] = []
        self._input_dim: int = 0
        self._embedding_dims: Dict[str, int] = {}

    @property
    def is_fitted(self) -> bool:
        """Check if tokenizer has been fitted."""
        return self._fitted

    @property
    def input_dim(self) -> int:
        """Get total input dimension after tokenization."""
        return self._input_dim

    @property
    def column_info(self) -> Dict[str, ColumnInfo]:
        """Get column information dict."""
        return {col.name: col for col in self._columns}

    def fit(self, df: pd.DataFrame) -> "TabularTokenizer":
        """Fit tokenizer to data.

        Args:
            df: Training data

        Returns:
            Self for chaining
        """
        self._columns = []
        self._column_order = list(df.columns)
        total_dim = 0

        for col_name in df.columns:
            col = df[col_name]
            col_info = self._analyze_column(col_name, col)
            self._columns.append(col_info)

            # Calculate dimension contribution
            if col_info.dtype == "numeric":
                # Continuous value + optional missing indicator
                dim = 1 + (1 if col_info.has_missing else 0)
            elif col_info.dtype == "categorical":
                # One-hot or embedding dimension
                dim = min(col_info.n_categories + 1, self.config.max_cardinality + 2)
            elif col_info.dtype == "datetime":
                # Date components
                dim = len(self.config.date_components)
            else:
                dim = 1

            self._embedding_dims[col_name] = dim
            total_dim += dim

        self._input_dim = total_dim
        self._fitted = True

        logger.info(
            f"Fitted tokenizer: {len(self._columns)} columns, "
            f"input_dim={self._input_dim}"
        )

        return self

    def _analyze_column(self, name: str, col: pd.Series) -> ColumnInfo:
        """Analyze a single column and create ColumnInfo."""
        original_dtype = str(col.dtype)
        has_missing = col.isna().any()

        # Detect column type
        if pd.api.types.is_numeric_dtype(col):
            return self._analyze_numeric(name, col, original_dtype, has_missing)
        elif pd.api.types.is_datetime64_any_dtype(col):
            return self._analyze_datetime(name, col, original_dtype, has_missing)
        else:
            return self._analyze_categorical(name, col, original_dtype, has_missing)

    def _analyze_numeric(
        self,
        name: str,
        col: pd.Series,
        original_dtype: str,
        has_missing: bool,
    ) -> ColumnInfo:
        """Analyze numeric column."""
        clean_col = col.dropna()

        mean_val = float(clean_col.mean()) if len(clean_col) > 0 else 0.0
        std_val = float(clean_col.std()) if len(clean_col) > 1 else 1.0
        std_val = max(std_val, 1e-8)  # Avoid division by zero

        min_val = float(clean_col.min()) if len(clean_col) > 0 else 0.0
        max_val = float(clean_col.max()) if len(clean_col) > 0 else 1.0

        # Compute bin edges if using binning
        bin_edges = None
        if self.config.num_bins > 0 and len(clean_col) > self.config.num_bins:
            if self.config.use_quantile_binning:
                percentiles = np.linspace(0, 100, self.config.num_bins + 1)
                bin_edges = np.percentile(clean_col, percentiles)
                bin_edges = np.unique(bin_edges)  # Remove duplicates
            else:
                bin_edges = np.linspace(min_val, max_val, self.config.num_bins + 1)

        return ColumnInfo(
            name=name,
            dtype="numeric",
            original_dtype=original_dtype,
            mean=mean_val,
            std=std_val,
            min_val=min_val,
            max_val=max_val,
            bin_edges=bin_edges,
            has_missing=has_missing,
        )

    def _analyze_categorical(
        self,
        name: str,
        col: pd.Series,
        original_dtype: str,
        has_missing: bool,
    ) -> ColumnInfo:
        """Analyze categorical column."""
        # Get value counts, sorted by frequency
        value_counts = col.value_counts()
        categories = list(value_counts.index)

        # Truncate if too many categories
        if len(categories) > self.config.max_cardinality:
            logger.warning(
                f"Column '{name}' has {len(categories)} categories, "
                f"truncating to {self.config.max_cardinality}"
            )
            categories = categories[:self.config.max_cardinality]

        return ColumnInfo(
            name=name,
            dtype="categorical",
            original_dtype=original_dtype,
            n_categories=len(categories),
            categories=categories,
            has_missing=has_missing,
        )

    def _analyze_datetime(
        self,
        name: str,
        col: pd.Series,
        original_dtype: str,
        has_missing: bool,
    ) -> ColumnInfo:
        """Analyze datetime column."""
        return ColumnInfo(
            name=name,
            dtype="datetime",
            original_dtype=original_dtype,
            has_missing=has_missing,
        )

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transform data to tokenized representation.

        Args:
            df: Data to transform

        Returns:
            Numpy array of shape (n_rows, input_dim)
        """
        if not self._fitted:
            raise RuntimeError("Tokenizer must be fitted before transform")

        arrays = []

        for col_info in self._columns:
            col = df[col_info.name] if col_info.name in df.columns else None

            if col is None:
                # Handle missing column
                dim = self._embedding_dims.get(col_info.name, 1)
                arrays.append(np.zeros((len(df), dim)))
                continue

            if col_info.dtype == "numeric":
                arr = self._transform_numeric(col, col_info)
            elif col_info.dtype == "categorical":
                arr = self._transform_categorical(col, col_info)
            elif col_info.dtype == "datetime":
                arr = self._transform_datetime(col, col_info)
            else:
                arr = np.zeros((len(df), 1))

            arrays.append(arr)

        return np.hstack(arrays).astype(np.float32)

    def _transform_numeric(
        self,
        col: pd.Series,
        col_info: ColumnInfo,
    ) -> np.ndarray:
        """Transform numeric column."""
        values = col.values.astype(np.float64)
        mask = np.isnan(values)

        # Fill missing with mean for standardization
        values[mask] = col_info.mean

        # Standardize
        standardized = (values - col_info.mean) / col_info.std

        if col_info.has_missing:
            # Add missing indicator
            missing_indicator = mask.astype(np.float32).reshape(-1, 1)
            return np.column_stack([standardized, missing_indicator])
        else:
            return standardized.reshape(-1, 1)

    def _transform_categorical(
        self,
        col: pd.Series,
        col_info: ColumnInfo,
    ) -> np.ndarray:
        """Transform categorical column to one-hot encoding."""
        n_cats = len(col_info.categories) + 1  # +1 for unknown
        if col_info.has_missing:
            n_cats += 1  # +1 for missing

        # Create category to index mapping
        cat_to_idx = {cat: i + 1 for i, cat in enumerate(col_info.categories)}

        # Map values to indices
        indices = np.zeros(len(col), dtype=np.int32)
        for i, val in enumerate(col.values):
            if pd.isna(val):
                if col_info.has_missing:
                    indices[i] = n_cats - 1  # Missing index is last
                else:
                    indices[i] = 0  # Unknown
            else:
                indices[i] = cat_to_idx.get(val, 0)  # 0 for unknown

        # One-hot encode
        one_hot = np.zeros((len(col), n_cats), dtype=np.float32)
        one_hot[np.arange(len(col)), indices] = 1.0

        return one_hot

    def _transform_datetime(
        self,
        col: pd.Series,
        col_info: ColumnInfo,
    ) -> np.ndarray:
        """Transform datetime column to components."""
        # Convert to datetime if needed
        dt_col = pd.to_datetime(col, errors="coerce")

        components = []
        for comp in self.config.date_components:
            if comp == "year":
                vals = dt_col.dt.year.fillna(2000).values
                # Normalize years to reasonable range
                vals = (vals - 2000) / 50.0
            elif comp == "month":
                vals = dt_col.dt.month.fillna(1).values / 12.0
            elif comp == "day":
                vals = dt_col.dt.day.fillna(1).values / 31.0
            elif comp == "dayofweek":
                vals = dt_col.dt.dayofweek.fillna(0).values / 6.0
            elif comp == "hour":
                vals = dt_col.dt.hour.fillna(0).values / 23.0
            else:
                vals = np.zeros(len(col))

            components.append(vals.reshape(-1, 1))

        return np.hstack(components).astype(np.float32)

    def inverse_transform(self, arr: np.ndarray) -> pd.DataFrame:
        """Convert tokenized representation back to DataFrame.

        Args:
            arr: Tokenized array of shape (n_rows, input_dim)

        Returns:
            DataFrame with original column types
        """
        if not self._fitted:
            raise RuntimeError("Tokenizer must be fitted before inverse_transform")

        data = {}
        col_idx = 0

        for col_info in self._columns:
            dim = self._embedding_dims[col_info.name]
            col_arr = arr[:, col_idx:col_idx + dim]
            col_idx += dim

            if col_info.dtype == "numeric":
                data[col_info.name] = self._inverse_numeric(col_arr, col_info)
            elif col_info.dtype == "categorical":
                data[col_info.name] = self._inverse_categorical(col_arr, col_info)
            elif col_info.dtype == "datetime":
                data[col_info.name] = self._inverse_datetime(col_arr, col_info)

        return pd.DataFrame(data)

    def _inverse_numeric(
        self,
        arr: np.ndarray,
        col_info: ColumnInfo,
    ) -> np.ndarray:
        """Inverse transform numeric column."""
        # First column is standardized value
        standardized = arr[:, 0]

        # Unstandardize
        values = standardized * col_info.std + col_info.mean

        # Apply missing mask if present
        if col_info.has_missing and arr.shape[1] > 1:
            missing_mask = arr[:, 1] > 0.5
            values = values.astype(np.float64)
            values[missing_mask] = np.nan

        # Clip to original range
        if col_info.min_val is not None and col_info.max_val is not None:
            values = np.clip(values, col_info.min_val, col_info.max_val)

        return values

    def _inverse_categorical(
        self,
        arr: np.ndarray,
        col_info: ColumnInfo,
    ) -> np.ndarray:
        """Inverse transform categorical column."""
        # Get argmax indices
        indices = np.argmax(arr, axis=1)

        # Map back to categories
        values = []
        n_cats = len(col_info.categories)

        for idx in indices:
            if idx == 0:
                # Unknown - pick random category
                values.append(
                    col_info.categories[np.random.randint(n_cats)]
                    if n_cats > 0 else None
                )
            elif idx <= n_cats:
                values.append(col_info.categories[idx - 1])
            else:
                # Missing
                values.append(None)

        return np.array(values, dtype=object)

    def _inverse_datetime(
        self,
        arr: np.ndarray,
        col_info: ColumnInfo,
    ) -> np.ndarray:
        """Inverse transform datetime column."""
        # Extract components
        comp_idx = 0
        year = month = day = None

        for comp in self.config.date_components:
            val = arr[:, comp_idx]
            comp_idx += 1

            if comp == "year":
                year = (val * 50.0 + 2000).astype(int)
            elif comp == "month":
                month = np.clip((val * 12.0).astype(int), 1, 12)
            elif comp == "day":
                day = np.clip((val * 31.0).astype(int), 1, 28)  # Safe day

        # Construct dates
        if year is not None and month is not None and day is not None:
            dates = []
            for y, m, d in zip(year, month, day):
                try:
                    dates.append(pd.Timestamp(year=y, month=m, day=d))
                except (ValueError, OverflowError):
                    dates.append(pd.NaT)
            return np.array(dates)
        else:
            return np.array([pd.NaT] * len(arr))

    def save(self, path: Union[str, Path]) -> None:
        """Save tokenizer to file.

        Args:
            path: Path to save to (JSON format)
        """
        path = Path(path)

        state = {
            "config": self.config.to_dict(),
            "fitted": self._fitted,
            "column_order": self._column_order,
            "input_dim": self._input_dim,
            "embedding_dims": self._embedding_dims,
            "columns": [
                {
                    "name": c.name,
                    "dtype": c.dtype,
                    "original_dtype": c.original_dtype,
                    "n_categories": c.n_categories,
                    "categories": c.categories,
                    "bin_edges": c.bin_edges.tolist() if c.bin_edges is not None else None,
                    "mean": c.mean,
                    "std": c.std,
                    "min_val": c.min_val,
                    "max_val": c.max_val,
                    "has_missing": c.has_missing,
                }
                for c in self._columns
            ],
        }

        with open(path, "w") as f:
            json.dump(state, f, indent=2)

        logger.info(f"Saved tokenizer to {path}")

    @classmethod
    def load(cls, path: Union[str, Path]) -> "TabularTokenizer":
        """Load tokenizer from file.

        Args:
            path: Path to load from

        Returns:
            Loaded tokenizer
        """
        path = Path(path)

        with open(path, "r") as f:
            state = json.load(f)

        tokenizer = cls(TokenizerConfig.from_dict(state["config"]))
        tokenizer._fitted = state["fitted"]
        tokenizer._column_order = state["column_order"]
        tokenizer._input_dim = state["input_dim"]
        tokenizer._embedding_dims = state["embedding_dims"]

        tokenizer._columns = [
            ColumnInfo(
                name=c["name"],
                dtype=c["dtype"],
                original_dtype=c["original_dtype"],
                n_categories=c.get("n_categories", 0),
                categories=c.get("categories"),
                bin_edges=np.array(c["bin_edges"]) if c.get("bin_edges") else None,
                mean=c.get("mean"),
                std=c.get("std"),
                min_val=c.get("min_val"),
                max_val=c.get("max_val"),
                has_missing=c.get("has_missing", False),
            )
            for c in state["columns"]
        ]

        logger.info(f"Loaded tokenizer from {path}")
        return tokenizer
