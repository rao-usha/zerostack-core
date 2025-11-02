import pandas as pd
import numpy as np
from typing import Dict, Any, List

class InsightsGenerator:
    """Generate strategic insights from data"""
    
    def generate(self, df: pd.DataFrame, context: str = "general business") -> Dict[str, Any]:
        """Generate comprehensive insights"""
        insights = {
            "summary": self._generate_summary(df),
            "trends": self._identify_trends(df),
            "anomalies": self._detect_anomalies(df),
            "correlations": self._find_correlations(df),
            "recommendations": self._generate_recommendations(df, context),
            "key_metrics": self._calculate_key_metrics(df),
            "executive_kpis": self._calculate_executive_kpis(df),
            "trend_data": self._prepare_trend_data(df),
            "distribution_data": self._prepare_distribution_data(df),
            "growth_metrics": self._calculate_growth_metrics(df),
            "risk_indicators": self._calculate_risk_indicators(df),
            "performance_score": self._calculate_performance_score(df)
        }
        return insights
    
    def _generate_summary(self, df: pd.DataFrame) -> str:
        """Generate summary insights"""
        summary_parts = [
            f"Dataset contains {len(df)} rows and {len(df.columns)} columns.",
        ]
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            summary_parts.append(f"Key numeric metrics available: {', '.join(numeric_cols[:5])}")
        
        return " ".join(summary_parts)
    
    def _identify_trends(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify trends in the data"""
        trends = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols[:5]:  # Limit to 5 columns
            if len(df) > 1:
                trend_direction = "increasing" if df[col].iloc[-1] > df[col].iloc[0] else "decreasing"
                avg_change = (df[col].iloc[-1] - df[col].iloc[0]) / len(df)
                trends.append({
                    "column": col,
                    "direction": trend_direction,
                    "average_change": float(avg_change),
                    "description": f"{col} shows {trend_direction} trend"
                })
        
        return trends
    
    def _detect_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies using IQR method"""
        anomalies = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols[:5]:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_count = len(df[(df[col] < lower_bound) | (df[col] > upper_bound)])
            if outlier_count > 0:
                anomalies.append({
                    "column": col,
                    "outlier_count": int(outlier_count),
                    "percentage": float(outlier_count / len(df) * 100),
                    "description": f"{outlier_count} outliers detected in {col}"
                })
        
        return anomalies
    
    def _find_correlations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find strong correlations between numeric columns"""
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) < 2:
            return []
        
        corr_matrix = numeric_df.corr()
        correlations = []
        
        for i, col1 in enumerate(corr_matrix.columns):
            for col2 in corr_matrix.columns[i+1:]:
                corr_value = corr_matrix.loc[col1, col2]
                if abs(corr_value) > 0.5:  # Strong correlation threshold
                    correlations.append({
                        "column1": col1,
                        "column2": col2,
                        "correlation": float(corr_value),
                        "strength": "strong" if abs(corr_value) > 0.7 else "moderate"
                    })
        
        return sorted(correlations, key=lambda x: abs(x["correlation"]), reverse=True)[:10]
    
    def _generate_recommendations(self, df: pd.DataFrame, context: str) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []
        
        # Check for missing data
        missing_data = df.isnull().sum()
        high_missing = missing_data[missing_data > len(df) * 0.1]
        if len(high_missing) > 0:
            recommendations.append(
                f"Consider addressing data quality issues: {', '.join(high_missing.index[:3])} have significant missing values"
            )
        
        # Check for data diversity
        for col in df.columns[:5]:
            if df[col].nunique() == 1:
                recommendations.append(f"{col} has no variation - may not be useful for analysis")
        
        # General recommendations
        recommendations.append("Monitor key metrics regularly for early trend detection")
        recommendations.append("Consider expanding dataset with additional features for better predictive power")
        
        return recommendations[:5]
    
    def _calculate_key_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate key business metrics"""
        metrics = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols[:10]:  # Limit to 10 columns
            metrics[col] = {
                "mean": float(df[col].mean()),
                "median": float(df[col].median()),
                "std": float(df[col].std()),
                "min": float(df[col].min()),
                "max": float(df[col].max())
            }
        
        return metrics
    
    def _calculate_executive_kpis(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Calculate executive-level KPIs"""
        kpis = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols[:4]:  # Top 4 metrics
            current_value = float(df[col].mean())
            min_val = float(df[col].min())
            max_val = float(df[col].max())
            
            # Calculate trend (growth from first to last value)
            if len(df) > 1:
                trend = ((df[col].iloc[-1] - df[col].iloc[0]) / df[col].iloc[0] * 100) if df[col].iloc[0] != 0 else 0
            else:
                trend = 0
            
            kpis.append({
                "name": col,
                "value": current_value,
                "trend": float(trend),
                "trend_direction": "up" if trend > 0 else "down",
                "min": min_val,
                "max": max_val
            })
        
        return kpis
    
    def _prepare_trend_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Prepare time series data for trend visualization"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return []
        
        # Take up to 50 data points for smooth visualization
        step = max(1, len(df) // 50)
        sample_df = df.iloc[::step]
        
        trend_data = []
        for idx, row in sample_df.iterrows():
            data_point = {"index": int(idx)}
            for col in numeric_cols[:5]:  # Top 5 metrics
                data_point[col] = float(row[col]) if pd.notna(row[col]) else 0
            trend_data.append(data_point)
        
        return trend_data
    
    def _prepare_distribution_data(self, df: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
        """Prepare distribution data for bar charts"""
        distributions = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols[:3]:  # Top 3 metrics
            # Create bins for distribution
            bins = 10
            hist, bin_edges = np.histogram(df[col].dropna(), bins=bins)
            
            dist_data = []
            for i in range(len(hist)):
                dist_data.append({
                    "range": f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}",
                    "count": int(hist[i]),
                    "percentage": float(hist[i] / len(df) * 100)
                })
            
            distributions[col] = dist_data
        
        return distributions
    
    def _calculate_growth_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate growth metrics for CEO dashboard"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0 or len(df) < 2:
            return {}
        
        growth_metrics = {}
        
        for col in numeric_cols[:3]:
            # Calculate period-over-period growth
            first_half = df[col].iloc[:len(df)//2].mean()
            second_half = df[col].iloc[len(df)//2:].mean()
            
            growth_rate = ((second_half - first_half) / first_half * 100) if first_half != 0 else 0
            
            # Calculate CAGR (approximation)
            if df[col].iloc[0] != 0:
                cagr = ((df[col].iloc[-1] / df[col].iloc[0]) ** (1/max(1, len(df)/12)) - 1) * 100
            else:
                cagr = 0
            
            growth_metrics[col] = {
                "growth_rate": float(growth_rate),
                "cagr": float(cagr),
                "momentum": "accelerating" if growth_rate > 0 else "decelerating"
            }
        
        return growth_metrics
    
    def _calculate_risk_indicators(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Calculate risk indicators for executive review"""
        risks = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols[:5]:
            # Calculate volatility (coefficient of variation)
            cv = (df[col].std() / df[col].mean() * 100) if df[col].mean() != 0 else 0
            
            # Calculate outlier percentage
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outlier_pct = len(df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)]) / len(df) * 100
            
            risk_level = "high" if cv > 50 or outlier_pct > 10 else "medium" if cv > 25 or outlier_pct > 5 else "low"
            
            risks.append({
                "metric": col,
                "volatility": float(cv),
                "outlier_percentage": float(outlier_pct),
                "risk_level": risk_level
            })
        
        return risks
    
    def _calculate_performance_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate overall performance score"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return {"overall_score": 0, "health": "unknown"}
        
        # Calculate data quality score
        completeness = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        
        # Calculate consistency score (lower CV is better)
        cvs = []
        for col in numeric_cols:
            if df[col].mean() != 0:
                cvs.append(df[col].std() / df[col].mean())
        consistency = max(0, 100 - np.mean(cvs) * 100) if cvs else 50
        
        # Calculate growth score
        growth_scores = []
        for col in numeric_cols[:3]:
            if len(df) > 1 and df[col].iloc[0] != 0:
                growth = (df[col].iloc[-1] - df[col].iloc[0]) / df[col].iloc[0] * 100
                growth_scores.append(min(100, max(0, 50 + growth)))
        growth_score = np.mean(growth_scores) if growth_scores else 50
        
        # Overall score (weighted average)
        overall = (completeness * 0.3 + consistency * 0.3 + growth_score * 0.4)
        
        health = "excellent" if overall >= 80 else "good" if overall >= 60 else "fair" if overall >= 40 else "needs attention"
        
        return {
            "overall_score": float(overall),
            "health": health,
            "data_quality": float(completeness),
            "consistency": float(consistency),
            "growth": float(growth_score)
        }

