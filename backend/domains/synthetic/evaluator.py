"""Quality evaluation for synthetic data."""
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class ColumnQuality:
    """Quality metrics for a single column."""
    column_name: str
    dtype: str
    ks_statistic: Optional[float] = None
    p_value: Optional[float] = None
    score: float = 0.0
    rating: str = "unknown"


@dataclass 
class QualityReport:
    """Complete quality evaluation report."""
    overall_score: float
    statistical_fidelity_score: float
    correlation_score: float
    column_scores: List[ColumnQuality] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Detailed metrics
    statistical_metrics: Dict[str, Any] = field(default_factory=dict)
    correlation_metrics: Dict[str, Any] = field(default_factory=dict)


class SyntheticDataEvaluator:
    """Evaluate quality of synthetic data compared to real data."""
    
    def evaluate(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
    ) -> QualityReport:
        """Evaluate synthetic data quality.
        
        Args:
            real_data: Original real data
            synthetic_data: Generated synthetic data
            
        Returns:
            QualityReport with scores and recommendations
        """
        logger.info(f"Evaluating synthetic data quality: {len(synthetic_data)} rows")
        
        # Ensure same columns
        common_cols = list(set(real_data.columns) & set(synthetic_data.columns))
        if not common_cols:
            raise ValueError("No common columns between real and synthetic data")
        
        real_data = real_data[common_cols]
        synthetic_data = synthetic_data[common_cols]
        
        # Evaluate each column
        column_scores = []
        for col in common_cols:
            col_score = self._evaluate_column(
                real_data[col],
                synthetic_data[col],
                col
            )
            column_scores.append(col_score)
        
        # Calculate statistical fidelity score (mean of column scores)
        valid_scores = [cs.score for cs in column_scores if cs.score > 0]
        statistical_fidelity_score = np.mean(valid_scores) if valid_scores else 0.0
        
        # Calculate correlation preservation
        correlation_score, correlation_metrics = self._evaluate_correlations(
            real_data, synthetic_data
        )
        
        # Overall score is weighted average
        overall_score = (0.6 * statistical_fidelity_score + 0.4 * correlation_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            column_scores, 
            correlation_score,
            statistical_fidelity_score
        )
        
        # Check for warnings
        warnings = self._check_warnings(real_data, synthetic_data, column_scores)
        
        return QualityReport(
            overall_score=round(overall_score, 3),
            statistical_fidelity_score=round(statistical_fidelity_score, 3),
            correlation_score=round(correlation_score, 3),
            column_scores=column_scores,
            recommendations=recommendations,
            warnings=warnings,
            correlation_metrics=correlation_metrics,
        )
    
    def _evaluate_column(
        self,
        real_col: pd.Series,
        synth_col: pd.Series,
        col_name: str,
    ) -> ColumnQuality:
        """Evaluate a single column."""
        dtype = str(real_col.dtype)
        
        # Handle different data types
        if pd.api.types.is_numeric_dtype(real_col):
            return self._evaluate_numeric_column(real_col, synth_col, col_name, dtype)
        elif pd.api.types.is_categorical_dtype(real_col) or real_col.dtype == object:
            return self._evaluate_categorical_column(real_col, synth_col, col_name, dtype)
        elif pd.api.types.is_datetime64_any_dtype(real_col):
            return self._evaluate_datetime_column(real_col, synth_col, col_name, dtype)
        else:
            return ColumnQuality(
                column_name=col_name,
                dtype=dtype,
                score=0.5,
                rating="unknown"
            )
    
    def _evaluate_numeric_column(
        self,
        real_col: pd.Series,
        synth_col: pd.Series,
        col_name: str,
        dtype: str,
    ) -> ColumnQuality:
        """Evaluate numeric column using KS test."""
        # Remove NaN values
        real_clean = real_col.dropna()
        synth_clean = synth_col.dropna()
        
        if len(real_clean) == 0 or len(synth_clean) == 0:
            return ColumnQuality(
                column_name=col_name,
                dtype=dtype,
                score=0.0,
                rating="poor"
            )
        
        # Kolmogorov-Smirnov test
        ks_stat, p_value = stats.ks_2samp(real_clean, synth_clean)
        
        # Convert KS statistic to score (lower is better)
        # KS stat ranges from 0 to 1, we want 1 to be good
        score = 1.0 - ks_stat
        
        # Determine rating
        if ks_stat < 0.05:
            rating = "excellent"
        elif ks_stat < 0.1:
            rating = "good"
        elif ks_stat < 0.2:
            rating = "fair"
        else:
            rating = "poor"
        
        return ColumnQuality(
            column_name=col_name,
            dtype=dtype,
            ks_statistic=round(ks_stat, 4),
            p_value=round(p_value, 4),
            score=round(score, 3),
            rating=rating,
        )
    
    def _evaluate_categorical_column(
        self,
        real_col: pd.Series,
        synth_col: pd.Series,
        col_name: str,
        dtype: str,
    ) -> ColumnQuality:
        """Evaluate categorical column using total variation distance."""
        # Get value distributions
        real_dist = real_col.value_counts(normalize=True)
        synth_dist = synth_col.value_counts(normalize=True)
        
        # Align on all categories
        all_categories = set(real_dist.index) | set(synth_dist.index)
        real_probs = [real_dist.get(cat, 0) for cat in all_categories]
        synth_probs = [synth_dist.get(cat, 0) for cat in all_categories]
        
        # Total variation distance
        tvd = 0.5 * sum(abs(r - s) for r, s in zip(real_probs, synth_probs))
        
        # Convert to score
        score = 1.0 - tvd
        
        # Rating
        if tvd < 0.05:
            rating = "excellent"
        elif tvd < 0.1:
            rating = "good"
        elif tvd < 0.2:
            rating = "fair"
        else:
            rating = "poor"
        
        return ColumnQuality(
            column_name=col_name,
            dtype=dtype,
            ks_statistic=round(tvd, 4),  # Using TVD instead of KS
            score=round(score, 3),
            rating=rating,
        )
    
    def _evaluate_datetime_column(
        self,
        real_col: pd.Series,
        synth_col: pd.Series,
        col_name: str,
        dtype: str,
    ) -> ColumnQuality:
        """Evaluate datetime column by converting to numeric."""
        # Convert to numeric (unix timestamp)
        real_numeric = pd.to_numeric(real_col.dropna())
        synth_numeric = pd.to_numeric(synth_col.dropna())
        
        return self._evaluate_numeric_column(
            real_numeric, synth_numeric, col_name, dtype
        )
    
    def _evaluate_correlations(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
    ) -> Tuple[float, Dict[str, Any]]:
        """Evaluate correlation preservation."""
        # Get numeric columns only
        numeric_cols = real_data.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            return 1.0, {"message": "Not enough numeric columns for correlation analysis"}
        
        # Calculate correlation matrices
        real_corr = real_data[numeric_cols].corr()
        synth_corr = synthetic_data[numeric_cols].corr()
        
        # Calculate difference
        corr_diff = np.abs(real_corr.values - synth_corr.values)
        
        # Mean absolute difference (excluding diagonal)
        mask = ~np.eye(len(numeric_cols), dtype=bool)
        mean_diff = np.mean(corr_diff[mask])
        
        # Convert to score
        score = 1.0 - min(mean_diff, 1.0)
        
        return round(score, 3), {
            "mean_correlation_difference": round(mean_diff, 4),
            "numeric_columns_analyzed": len(numeric_cols),
        }
    
    def _generate_recommendations(
        self,
        column_scores: List[ColumnQuality],
        correlation_score: float,
        statistical_score: float,
    ) -> List[str]:
        """Generate recommendations based on scores."""
        recommendations = []
        
        # Check for poor columns
        poor_columns = [cs for cs in column_scores if cs.rating == "poor"]
        if poor_columns:
            col_names = ", ".join(cs.column_name for cs in poor_columns[:3])
            recommendations.append(
                f"Columns with poor distribution match: {col_names}. "
                "Consider using CTGAN for better capture of complex distributions."
            )
        
        # Correlation issues
        if correlation_score < 0.7:
            recommendations.append(
                "Correlation preservation is below 70%. "
                "The synthetic data may not capture relationships between columns well. "
                "Try CTGAN or TVAE for better correlation preservation."
            )
        
        # Overall quality
        if statistical_score < 0.8:
            recommendations.append(
                "Consider increasing training epochs for deep learning synthesizers "
                "or using a larger sample of source data."
            )
        
        if not recommendations:
            recommendations.append(
                "Synthetic data quality is good! Ready for use."
            )
        
        return recommendations
    
    def _check_warnings(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        column_scores: List[ColumnQuality],
    ) -> List[str]:
        """Check for potential issues and warnings."""
        warnings = []
        
        # Check for columns with very different row counts after NaN removal
        for col in real_data.columns:
            real_valid = real_data[col].dropna()
            synth_valid = synthetic_data[col].dropna()
            
            real_null_pct = 1 - len(real_valid) / len(real_data)
            synth_null_pct = 1 - len(synth_valid) / len(synthetic_data)
            
            if abs(real_null_pct - synth_null_pct) > 0.1:
                warnings.append(
                    f"Column '{col}' has different null rates: "
                    f"real={real_null_pct:.1%}, synthetic={synth_null_pct:.1%}"
                )
        
        # Check for unexpected values in categorical columns
        for col in real_data.select_dtypes(include=['object', 'category']).columns:
            real_values = set(real_data[col].dropna().unique())
            synth_values = set(synthetic_data[col].dropna().unique())
            
            new_values = synth_values - real_values
            if new_values:
                warnings.append(
                    f"Column '{col}' has synthetic values not in original: "
                    f"{list(new_values)[:3]}"
                )
        
        return warnings
