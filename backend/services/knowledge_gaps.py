import pandas as pd
import numpy as np
from typing import Dict, Any, List

class KnowledgeGapIdentifier:
    """Identify gaps in knowledge and data coverage"""
    
    def identify(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify knowledge gaps in the dataset"""
        return {
            "temporal_gaps": self._identify_temporal_gaps(df),
            "feature_gaps": self._identify_feature_gaps(df),
            "coverage_gaps": self._identify_coverage_gaps(df),
            "relationship_gaps": self._identify_relationship_gaps(df),
            "data_diversity": self._assess_diversity(df),
            "recommendations": self._gap_recommendations(df)
        }
    
    def _identify_temporal_gaps(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify gaps in time-series data"""
        date_cols = df.select_dtypes(include=['datetime64']).columns
        
        gaps = {
            "has_temporal_data": len(date_cols) > 0,
            "date_columns": [col for col in date_cols]
        }
        
        if len(date_cols) > 0:
            date_col = date_cols[0]
            date_range = df[date_col].max() - df[date_col].min()
            gaps["time_span_days"] = date_range.days if hasattr(date_range, 'days') else None
            gaps["total_periods"] = len(df)
        
        return gaps
    
    def _identify_feature_gaps(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify missing important features"""
        gaps = []
        suggestions = []
        
        # Check for common important features
        col_names_lower = [col.lower() for col in df.columns]
        
        if "date" not in " ".join(col_names_lower) and "time" not in " ".join(col_names_lower):
            gaps.append("temporal_dimension")
            suggestions.append("Consider adding date/time columns for trend analysis")
        
        if not any("id" in col.lower() or "key" in col.lower() for col in df.columns):
            gaps.append("identifier")
            suggestions.append("Unique identifiers help with data tracking and joins")
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            gaps.append("numeric_features")
            suggestions.append("More numeric features enable correlation and predictive analysis")
        
        categorical_cols = df.select_dtypes(exclude=[np.number]).columns
        if len(categorical_cols) == 0:
            gaps.append("categorical_features")
            suggestions.append("Categorical features help with segmentation and grouping")
        
        return {
            "identified_gaps": gaps,
            "suggestions": suggestions,
            "severity": "high" if len(gaps) >= 2 else "medium"
        }
    
    def _identify_coverage_gaps(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify gaps in data coverage"""
        gaps = []
        
        # Check for missing value patterns
        missing_per_col = df.isnull().sum()
        high_missing = missing_per_col[missing_per_col > len(df) * 0.2]
        
        if len(high_missing) > 0:
            gaps.append({
                "type": "high_missing_data",
                "columns": high_missing.index.tolist(),
                "impact": "May affect analysis reliability"
            })
        
        # Check for low diversity
        low_diversity_cols = []
        for col in df.columns:
            if df[col].nunique() < 3 and len(df) > 10:
                low_diversity_cols.append(col)
        
        if len(low_diversity_cols) > 0:
            gaps.append({
                "type": "low_diversity",
                "columns": low_diversity_cols,
                "impact": "Limited variation may reduce analytical value"
            })
        
        # Check sample size
        if len(df) < 50:
            gaps.append({
                "type": "small_sample_size",
                "sample_count": len(df),
                "impact": "Small sample size may limit statistical significance"
            })
        
        return {
            "gaps": gaps,
            "severity": "high" if len(gaps) >= 2 else "medium" if len(gaps) == 1 else "low"
        }
    
    def _identify_relationship_gaps(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify gaps in understanding relationships"""
        numeric_df = df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) < 2:
            return {
                "can_analyze_relationships": False,
                "reason": "Need at least 2 numeric columns for relationship analysis"
            }
        
        corr_matrix = numeric_df.corr().abs()
        strong_correlations = (corr_matrix > 0.7) & (corr_matrix < 1.0)
        strong_pairs = strong_correlations.sum().sum() / 2
        
        return {
            "can_analyze_relationships": True,
            "strong_relationships_found": int(strong_pairs),
            "recommendation": "Explore feature engineering for better predictive power" if strong_pairs < 3 else "Good relationship coverage"
        }
    
    def _assess_diversity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data diversity"""
        diversity_scores = {}
        
        for col in df.columns:
            unique_count = df[col].nunique()
            total_count = len(df)
            diversity_ratio = unique_count / total_count if total_count > 0 else 0
            diversity_scores[col] = {
                "unique_values": int(unique_count),
                "diversity_ratio": round(diversity_ratio, 3),
                "assessment": "high" if diversity_ratio > 0.8 else "medium" if diversity_ratio > 0.3 else "low"
            }
        
        return diversity_scores
    
    def _gap_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate recommendations to address knowledge gaps"""
        recommendations = []
        
        # Temporal recommendations
        date_cols = df.select_dtypes(include=['datetime64']).columns
        if len(date_cols) == 0:
            recommendations.append("Add temporal dimension to enable time-series analysis and trend detection")
        
        # Sample size recommendations
        if len(df) < 100:
            recommendations.append("Consider collecting more samples for more reliable statistical analysis")
        
        # Feature recommendations
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 3:
            recommendations.append("Add more numeric features to enable advanced analytics and modeling")
        
        # Missing data recommendations
        if df.isnull().sum().sum() > 0:
            recommendations.append("Address missing data to improve data quality and completeness")
        
        # Relationship recommendations
        if len(numeric_cols) >= 2:
            recommendations.append("Explore feature interactions and create derived features for better insights")
        
        return recommendations

