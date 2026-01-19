"""Privacy risk scoring for synthetic data."""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist

logger = logging.getLogger(__name__)


@dataclass
class PrivacyRiskReport:
    """Privacy risk assessment report."""
    overall_risk: str  # "low", "medium", "high"
    risk_score: float  # 0.0 to 1.0 (lower is better/safer)
    
    # Individual metrics
    uniqueness_risk: float  # Risk from unique/quasi-identifier columns
    similarity_risk: float  # Risk from synthetic records too similar to real
    outlier_risk: float  # Risk from outliers that might be identifiable
    
    # Details
    high_risk_columns: List[str] = field(default_factory=list)
    nearest_neighbor_distances: Optional[Dict[str, float]] = None
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class PrivacyRiskScorer:
    """Score privacy risk of synthetic data.
    
    Evaluates multiple privacy risks:
    1. Uniqueness risk - columns with high cardinality that could identify individuals
    2. Similarity risk - synthetic records too close to real records
    3. Outlier risk - extreme values that might be re-identifiable
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.1,
        uniqueness_threshold: float = 0.9,
        sample_size: int = 1000,
    ):
        """Initialize risk scorer.
        
        Args:
            similarity_threshold: Distance threshold for "too similar" records
            uniqueness_threshold: Ratio threshold for high-uniqueness columns
            sample_size: Max samples for distance calculations (performance)
        """
        self.similarity_threshold = similarity_threshold
        self.uniqueness_threshold = uniqueness_threshold
        self.sample_size = sample_size
    
    def score(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        pii_columns: Optional[List[str]] = None,
    ) -> PrivacyRiskReport:
        """Score the privacy risk of synthetic data.
        
        Args:
            real_data: Original real data
            synthetic_data: Generated synthetic data
            pii_columns: Known PII columns (already handled)
            
        Returns:
            PrivacyRiskReport with scores and recommendations
        """
        pii_columns = pii_columns or []
        
        # Calculate individual risk scores
        uniqueness_risk, high_unique_cols = self._calculate_uniqueness_risk(
            synthetic_data, exclude_cols=pii_columns
        )
        
        similarity_risk, nn_distances = self._calculate_similarity_risk(
            real_data, synthetic_data, exclude_cols=pii_columns
        )
        
        outlier_risk, outlier_cols = self._calculate_outlier_risk(
            real_data, synthetic_data, exclude_cols=pii_columns
        )
        
        # Calculate overall risk (weighted average)
        overall_score = (
            0.4 * similarity_risk +
            0.35 * uniqueness_risk +
            0.25 * outlier_risk
        )
        
        # Determine risk level
        if overall_score < 0.3:
            overall_risk = "low"
        elif overall_score < 0.6:
            overall_risk = "medium"
        else:
            overall_risk = "high"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            uniqueness_risk, similarity_risk, outlier_risk,
            high_unique_cols, outlier_cols
        )
        
        # Generate warnings
        warnings = []
        if similarity_risk > 0.5:
            warnings.append(
                "Some synthetic records are very similar to real records. "
                "Consider using differential privacy."
            )
        if uniqueness_risk > 0.7:
            warnings.append(
                f"Columns with high uniqueness detected: {', '.join(high_unique_cols[:3])}. "
                "These could be quasi-identifiers."
            )
        
        return PrivacyRiskReport(
            overall_risk=overall_risk,
            risk_score=round(overall_score, 3),
            uniqueness_risk=round(uniqueness_risk, 3),
            similarity_risk=round(similarity_risk, 3),
            outlier_risk=round(outlier_risk, 3),
            high_risk_columns=high_unique_cols + outlier_cols,
            nearest_neighbor_distances=nn_distances,
            recommendations=recommendations,
            warnings=warnings,
        )
    
    def _calculate_uniqueness_risk(
        self,
        df: pd.DataFrame,
        exclude_cols: List[str],
    ) -> Tuple[float, List[str]]:
        """Calculate risk from high-uniqueness columns.
        
        Columns where most values are unique can be quasi-identifiers.
        """
        high_unique_cols = []
        uniqueness_scores = []
        
        for col in df.columns:
            if col in exclude_cols:
                continue
            
            # Skip numeric columns with many values (likely continuous)
            if pd.api.types.is_numeric_dtype(df[col]):
                if df[col].nunique() > 100:
                    continue
            
            # Calculate uniqueness ratio
            uniqueness = df[col].nunique() / len(df) if len(df) > 0 else 0
            
            if uniqueness > self.uniqueness_threshold:
                high_unique_cols.append(col)
                uniqueness_scores.append(uniqueness)
        
        # Risk is based on how many high-uniqueness columns exist
        if not uniqueness_scores:
            return 0.0, []
        
        risk = min(1.0, len(uniqueness_scores) * 0.2 + max(uniqueness_scores) * 0.3)
        return risk, high_unique_cols
    
    def _calculate_similarity_risk(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        exclude_cols: List[str],
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate risk from synthetic records being too similar to real records.
        
        Uses nearest neighbor distance in numeric feature space.
        """
        # Get numeric columns only
        numeric_cols = [
            col for col in real_data.select_dtypes(include=[np.number]).columns
            if col not in exclude_cols
        ]
        
        if len(numeric_cols) < 2:
            return 0.0, {"message": "Not enough numeric columns for similarity analysis"}
        
        # Sample for performance
        real_sample = real_data[numeric_cols].dropna()
        synth_sample = synthetic_data[numeric_cols].dropna()
        
        if len(real_sample) > self.sample_size:
            real_sample = real_sample.sample(self.sample_size, random_state=42)
        if len(synth_sample) > self.sample_size:
            synth_sample = synth_sample.sample(self.sample_size, random_state=42)
        
        if len(real_sample) == 0 or len(synth_sample) == 0:
            return 0.0, {"message": "No valid samples for similarity calculation"}
        
        # Normalize data
        real_normalized = (real_sample - real_sample.mean()) / (real_sample.std() + 1e-10)
        synth_normalized = (synth_sample - real_sample.mean()) / (real_sample.std() + 1e-10)
        
        # Calculate pairwise distances
        try:
            distances = cdist(synth_normalized.values, real_normalized.values, metric='euclidean')
            
            # Get minimum distance for each synthetic record (to nearest real record)
            min_distances = distances.min(axis=1)
            
            # Calculate statistics
            mean_min_dist = float(np.mean(min_distances))
            min_min_dist = float(np.min(min_distances))
            pct_too_close = float(np.mean(min_distances < self.similarity_threshold))
            
            # Risk is based on how many synthetic records are "too close" to real ones
            risk = min(1.0, pct_too_close * 2 + (1 / (mean_min_dist + 0.1)) * 0.1)
            
            return risk, {
                "mean_nearest_distance": round(mean_min_dist, 4),
                "min_nearest_distance": round(min_min_dist, 4),
                "pct_below_threshold": round(pct_too_close, 4),
            }
        except Exception as e:
            logger.warning(f"Similarity calculation failed: {e}")
            return 0.0, {"error": str(e)}
    
    def _calculate_outlier_risk(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame,
        exclude_cols: List[str],
    ) -> Tuple[float, List[str]]:
        """Calculate risk from outliers in synthetic data.
        
        Outliers that match real outliers could be re-identifiable.
        """
        numeric_cols = [
            col for col in real_data.select_dtypes(include=[np.number]).columns
            if col not in exclude_cols
        ]
        
        outlier_cols = []
        
        for col in numeric_cols:
            real_col = real_data[col].dropna()
            synth_col = synthetic_data[col].dropna()
            
            if len(real_col) == 0 or len(synth_col) == 0:
                continue
            
            # Calculate IQR bounds from real data
            q1, q3 = real_col.quantile([0.25, 0.75])
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            
            # Check if synthetic has values outside real bounds
            synth_outliers = (synth_col < lower) | (synth_col > upper)
            real_outliers = (real_col < lower) | (real_col > upper)
            
            # Risk if synthetic reproduces similar extreme values
            if synth_outliers.any() and real_outliers.any():
                synth_extreme = synth_col[synth_outliers]
                real_extreme = real_col[real_outliers]
                
                # Check if any synthetic outliers are close to real outliers
                for sv in synth_extreme:
                    if any(abs(sv - rv) < 0.01 * abs(rv + 1e-10) for rv in real_extreme):
                        outlier_cols.append(col)
                        break
        
        # Risk based on number of columns with matching outliers
        risk = min(1.0, len(outlier_cols) * 0.25)
        return risk, list(set(outlier_cols))
    
    def _generate_recommendations(
        self,
        uniqueness_risk: float,
        similarity_risk: float,
        outlier_risk: float,
        high_unique_cols: List[str],
        outlier_cols: List[str],
    ) -> List[str]:
        """Generate recommendations based on risk scores."""
        recommendations = []
        
        if similarity_risk > 0.5:
            recommendations.append(
                "Consider enabling differential privacy to add noise and reduce "
                "similarity between synthetic and real records."
            )
        
        if uniqueness_risk > 0.5 and high_unique_cols:
            recommendations.append(
                f"High-uniqueness columns ({', '.join(high_unique_cols[:3])}) may act as "
                "quasi-identifiers. Consider generalizing or binning these values."
            )
        
        if outlier_risk > 0.3 and outlier_cols:
            recommendations.append(
                f"Columns with preserved outliers ({', '.join(outlier_cols[:3])}) could "
                "enable re-identification. Consider capping extreme values."
            )
        
        if not recommendations:
            recommendations.append(
                "Privacy risk is acceptable. The synthetic data appears safe for sharing."
            )
        
        return recommendations


def quick_privacy_check(
    real_data: pd.DataFrame,
    synthetic_data: pd.DataFrame,
) -> Dict[str, Any]:
    """Quick privacy check returning a simple summary.
    
    Args:
        real_data: Original data
        synthetic_data: Synthetic data
        
    Returns:
        Dict with risk level and key metrics
    """
    scorer = PrivacyRiskScorer()
    report = scorer.score(real_data, synthetic_data)
    
    return {
        "risk_level": report.overall_risk,
        "risk_score": report.risk_score,
        "safe_to_share": report.overall_risk in ["low", "medium"],
        "warnings": report.warnings,
        "recommendations": report.recommendations[:2],  # Top 2
    }
