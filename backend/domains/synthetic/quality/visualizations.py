"""Visualization data generation for synthetic data quality.

Generates data structures suitable for frontend chart rendering.
Does NOT generate actual images - returns JSON-serializable data.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class HistogramData:
    """Data for a histogram comparison."""
    column_name: str
    dtype: str
    bins: List[float]
    real_counts: List[int]
    synthetic_counts: List[int]
    real_density: List[float]
    synthetic_density: List[float]
    statistics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CategoryData:
    """Data for categorical column comparison."""
    column_name: str
    categories: List[str]
    real_counts: List[int]
    synthetic_counts: List[int]
    real_percentages: List[float]
    synthetic_percentages: List[float]


@dataclass
class DistributionComparison:
    """Complete distribution comparison data."""
    numeric_columns: List[HistogramData] = field(default_factory=list)
    categorical_columns: List[CategoryData] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CorrelationComparison:
    """Correlation matrix comparison data."""
    columns: List[str]
    real_correlation: List[List[float]]  # 2D matrix
    synthetic_correlation: List[List[float]]
    difference: List[List[float]]
    summary: Dict[str, Any] = field(default_factory=dict)


class QualityVisualizer:
    """Generate visualization data for quality comparison.
    
    Produces JSON-serializable data structures that frontends can use
    to render charts (histograms, bar charts, heatmaps, etc.)
    """
    
    def __init__(self, max_bins: int = 30, max_categories: int = 20):
        """Initialize visualizer.
        
        Args:
            max_bins: Maximum number of histogram bins
            max_categories: Maximum categories to show (rest grouped as "Other")
        """
        self.max_bins = max_bins
        self.max_categories = max_categories
    
    def generate_distribution_comparison(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ) -> DistributionComparison:
        """Generate distribution comparison data for all columns.
        
        Args:
            real_data: Original real data
            synthetic_data: Generated synthetic data
            columns: Specific columns to compare (None = all)
            
        Returns:
            DistributionComparison with histogram and category data
        """
        if columns is None:
            columns = list(set(real_data.columns) & set(synthetic_data.columns))
        
        numeric_columns = []
        categorical_columns = []
        
        for col in columns:
            if col not in real_data.columns or col not in synthetic_data.columns:
                continue
            
            real_col = real_data[col]
            synth_col = synthetic_data[col]
            
            if pd.api.types.is_numeric_dtype(real_col):
                hist_data = self._generate_histogram(real_col, synth_col, col)
                if hist_data:
                    numeric_columns.append(hist_data)
            else:
                cat_data = self._generate_category_comparison(real_col, synth_col, col)
                if cat_data:
                    categorical_columns.append(cat_data)
        
        summary = {
            "total_columns": len(columns),
            "numeric_columns": len(numeric_columns),
            "categorical_columns": len(categorical_columns),
        }
        
        return DistributionComparison(
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
            summary=summary,
        )
    
    def generate_correlation_comparison(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        columns: Optional[List[str]] = None,
    ) -> CorrelationComparison:
        """Generate correlation matrix comparison.
        
        Args:
            real_data: Original real data
            synthetic_data: Generated synthetic data
            columns: Specific numeric columns (None = auto-detect)
            
        Returns:
            CorrelationComparison with matrices
        """
        # Get numeric columns
        if columns is None:
            real_numeric = real_data.select_dtypes(include=[np.number]).columns
            synth_numeric = synthetic_data.select_dtypes(include=[np.number]).columns
            columns = list(set(real_numeric) & set(synth_numeric))
        
        if len(columns) < 2:
            return CorrelationComparison(
                columns=[],
                real_correlation=[],
                synthetic_correlation=[],
                difference=[],
                summary={"error": "Not enough numeric columns for correlation analysis"},
            )
        
        # Limit columns for readability
        if len(columns) > 15:
            # Keep columns with highest variance
            variances = [(col, real_data[col].var()) for col in columns]
            variances.sort(key=lambda x: x[1], reverse=True)
            columns = [v[0] for v in variances[:15]]
        
        # Calculate correlations
        real_corr = real_data[columns].corr()
        synth_corr = synthetic_data[columns].corr()
        
        # Calculate difference
        diff_corr = real_corr - synth_corr
        
        # Convert to lists (for JSON serialization)
        real_matrix = self._corr_to_list(real_corr)
        synth_matrix = self._corr_to_list(synth_corr)
        diff_matrix = self._corr_to_list(diff_corr)
        
        # Summary statistics
        diff_values = diff_corr.values[np.triu_indices_from(diff_corr.values, k=1)]
        
        summary = {
            "num_columns": len(columns),
            "mean_absolute_difference": round(np.mean(np.abs(diff_values)), 4),
            "max_absolute_difference": round(np.max(np.abs(diff_values)), 4),
            "correlation_pairs": len(diff_values),
        }
        
        return CorrelationComparison(
            columns=columns,
            real_correlation=real_matrix,
            synthetic_correlation=synth_matrix,
            difference=diff_matrix,
            summary=summary,
        )
    
    def _generate_histogram(
        self,
        real_col: pd.Series,
        synth_col: pd.Series,
        col_name: str,
    ) -> Optional[HistogramData]:
        """Generate histogram comparison for numeric column."""
        try:
            real_clean = real_col.dropna()
            synth_clean = synth_col.dropna()
            
            if len(real_clean) == 0 or len(synth_clean) == 0:
                return None
            
            # Determine bin edges from combined data
            all_data = pd.concat([real_clean, synth_clean])
            
            # Use fewer bins for discrete data
            unique_values = all_data.nunique()
            n_bins = min(self.max_bins, max(10, unique_values))
            
            # Calculate histogram
            bins = np.linspace(all_data.min(), all_data.max(), n_bins + 1)
            real_counts, _ = np.histogram(real_clean, bins=bins)
            synth_counts, _ = np.histogram(synth_clean, bins=bins)
            
            # Calculate density (normalized)
            real_density = real_counts / (len(real_clean) * (bins[1] - bins[0]))
            synth_density = synth_counts / (len(synth_clean) * (bins[1] - bins[0]))
            
            # Statistics
            statistics = {
                "real": {
                    "mean": round(float(real_clean.mean()), 4),
                    "std": round(float(real_clean.std()), 4),
                    "min": round(float(real_clean.min()), 4),
                    "max": round(float(real_clean.max()), 4),
                    "median": round(float(real_clean.median()), 4),
                },
                "synthetic": {
                    "mean": round(float(synth_clean.mean()), 4),
                    "std": round(float(synth_clean.std()), 4),
                    "min": round(float(synth_clean.min()), 4),
                    "max": round(float(synth_clean.max()), 4),
                    "median": round(float(synth_clean.median()), 4),
                },
            }
            
            return HistogramData(
                column_name=col_name,
                dtype=str(real_col.dtype),
                bins=[round(b, 4) for b in bins.tolist()],
                real_counts=real_counts.tolist(),
                synthetic_counts=synth_counts.tolist(),
                real_density=[round(d, 6) for d in real_density.tolist()],
                synthetic_density=[round(d, 6) for d in synth_density.tolist()],
                statistics=statistics,
            )
            
        except Exception as e:
            logger.warning(f"Histogram generation failed for {col_name}: {e}")
            return None
    
    def _generate_category_comparison(
        self,
        real_col: pd.Series,
        synth_col: pd.Series,
        col_name: str,
    ) -> Optional[CategoryData]:
        """Generate category comparison for categorical column."""
        try:
            real_counts = real_col.value_counts()
            synth_counts = synth_col.value_counts()
            
            # Get all categories
            all_categories = list(set(real_counts.index) | set(synth_counts.index))
            
            # Limit categories
            if len(all_categories) > self.max_categories:
                # Keep top categories by combined count
                combined = {}
                for cat in all_categories:
                    combined[cat] = real_counts.get(cat, 0) + synth_counts.get(cat, 0)
                top_cats = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:self.max_categories - 1]
                all_categories = [c[0] for c in top_cats] + ["__other__"]
                
                # Aggregate others
                other_real = sum(real_counts.get(c, 0) for c in set(real_counts.index) - set(all_categories))
                other_synth = sum(synth_counts.get(c, 0) for c in set(synth_counts.index) - set(all_categories))
                real_counts["__other__"] = other_real
                synth_counts["__other__"] = other_synth
            
            # Sort by real counts
            all_categories = sorted(all_categories, key=lambda c: real_counts.get(c, 0), reverse=True)
            
            real_count_list = [int(real_counts.get(c, 0)) for c in all_categories]
            synth_count_list = [int(synth_counts.get(c, 0)) for c in all_categories]
            
            real_total = sum(real_count_list)
            synth_total = sum(synth_count_list)
            
            real_pct = [round(c / real_total * 100, 2) if real_total > 0 else 0 for c in real_count_list]
            synth_pct = [round(c / synth_total * 100, 2) if synth_total > 0 else 0 for c in synth_count_list]
            
            # Convert categories to strings
            all_categories = [str(c) for c in all_categories]
            
            return CategoryData(
                column_name=col_name,
                categories=all_categories,
                real_counts=real_count_list,
                synthetic_counts=synth_count_list,
                real_percentages=real_pct,
                synthetic_percentages=synth_pct,
            )
            
        except Exception as e:
            logger.warning(f"Category comparison failed for {col_name}: {e}")
            return None
    
    def _corr_to_list(self, corr_matrix: pd.DataFrame) -> List[List[float]]:
        """Convert correlation matrix to nested list."""
        return [
            [round(float(v), 4) if not pd.isna(v) else 0.0 for v in row]
            for row in corr_matrix.values
        ]
    
    def generate_summary_stats(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
    ) -> Dict[str, Any]:
        """Generate summary statistics comparison.
        
        Returns a dict suitable for display in a summary table.
        """
        stats = []
        
        for col in real_data.columns:
            if col not in synthetic_data.columns:
                continue
            
            real_col = real_data[col]
            synth_col = synthetic_data[col]
            
            col_stats = {
                "column": col,
                "dtype": str(real_col.dtype),
            }
            
            if pd.api.types.is_numeric_dtype(real_col):
                col_stats.update({
                    "real_mean": round(real_col.mean(), 4) if not pd.isna(real_col.mean()) else None,
                    "synth_mean": round(synth_col.mean(), 4) if not pd.isna(synth_col.mean()) else None,
                    "real_std": round(real_col.std(), 4) if not pd.isna(real_col.std()) else None,
                    "synth_std": round(synth_col.std(), 4) if not pd.isna(synth_col.std()) else None,
                    "real_null_pct": round(real_col.isna().mean() * 100, 2),
                    "synth_null_pct": round(synth_col.isna().mean() * 100, 2),
                })
            else:
                col_stats.update({
                    "real_unique": int(real_col.nunique()),
                    "synth_unique": int(synth_col.nunique()),
                    "real_mode": str(real_col.mode().iloc[0]) if len(real_col.mode()) > 0 else None,
                    "synth_mode": str(synth_col.mode().iloc[0]) if len(synth_col.mode()) > 0 else None,
                    "real_null_pct": round(real_col.isna().mean() * 100, 2),
                    "synth_null_pct": round(synth_col.isna().mean() * 100, 2),
                })
            
            stats.append(col_stats)
        
        return {
            "columns": stats,
            "total_columns": len(stats),
            "real_rows": len(real_data),
            "synthetic_rows": len(synthetic_data),
        }
