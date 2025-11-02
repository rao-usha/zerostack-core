import pandas as pd
import numpy as np
from typing import Dict, Any, List

class DataQualityAnalyzer:
    """Analyze and report on data quality"""
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive data quality analysis"""
        return {
            "overall_score": self._calculate_overall_score(df),
            "completeness": self._analyze_completeness(df),
            "accuracy": self._analyze_accuracy(df),
            "consistency": self._analyze_consistency(df),
            "validity": self._analyze_validity(df),
            "issues": self._identify_issues(df),
            "recommendations": self._quality_recommendations(df)
        }
    
    def _calculate_overall_score(self, df: pd.DataFrame) -> float:
        """Calculate overall data quality score (0-100)"""
        completeness_score = self._completeness_score(df)
        consistency_score = self._consistency_score(df)
        
        overall = (completeness_score * 0.6 + consistency_score * 0.4)
        return round(overall, 2)
    
    def _completeness_score(self, df: pd.DataFrame) -> float:
        """Calculate completeness score"""
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        completeness = (1 - missing_cells / total_cells) * 100 if total_cells > 0 else 100
        return max(0, min(100, completeness))
    
    def _consistency_score(self, df: pd.DataFrame) -> float:
        """Calculate consistency score based on duplicate rows and data type consistency"""
        duplicate_ratio = len(df[df.duplicated()]) / len(df) if len(df) > 0 else 0
        consistency = (1 - duplicate_ratio) * 100
        return max(0, min(100, consistency))
    
    def _analyze_completeness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data completeness"""
        missing_per_col = df.isnull().sum()
        missing_percent = (missing_per_col / len(df) * 100).round(2)
        
        columns_with_missing = missing_per_col[missing_per_col > 0]
        
        return {
            "total_missing": int(df.isnull().sum().sum()),
            "total_cells": int(len(df) * len(df.columns)),
            "completeness_percentage": float(self._completeness_score(df)),
            "columns_with_missing": {
                col: {
                    "missing_count": int(count),
                    "missing_percentage": float(missing_percent[col])
                }
                for col, count in columns_with_missing.items()
            }
        }
    
    def _analyze_accuracy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data accuracy (outliers, invalid values)"""
        accuracy_issues = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            # Check for outliers using IQR
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)]
            
            if len(outliers) > 0:
                accuracy_issues.append({
                    "column": col,
                    "issue_type": "outliers",
                    "count": int(len(outliers)),
                    "percentage": float(len(outliers) / len(df) * 100)
                })
        
        return {
            "accuracy_score": max(0, 100 - len(accuracy_issues) * 10),
            "issues": accuracy_issues
        }
    
    def _analyze_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data consistency"""
        duplicate_rows = len(df[df.duplicated()])
        duplicate_percentage = (duplicate_rows / len(df) * 100) if len(df) > 0 else 0
        
        # Check for inconsistent data types in columns
        type_consistency = {}
        for col in df.columns:
            try:
                # Try to detect mixed types
                unique_types = df[col].dropna().apply(type).unique()
                if len(unique_types) > 1:
                    type_consistency[col] = "mixed_types"
            except:
                pass
        
        return {
            "duplicate_rows": int(duplicate_rows),
            "duplicate_percentage": round(duplicate_percentage, 2),
            "consistency_score": float(self._consistency_score(df)),
            "type_issues": type_consistency
        }
    
    def _analyze_validity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data validity"""
        validity_issues = []
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            # Check for negative values where they shouldn't exist
            if col.lower() in ['age', 'price', 'revenue', 'sales']:
                negative_count = len(df[df[col] < 0])
                if negative_count > 0:
                    validity_issues.append({
                        "column": col,
                        "issue": "negative_values",
                        "count": int(negative_count)
                    })
        
        return {
            "validity_score": max(0, 100 - len(validity_issues) * 15),
            "issues": validity_issues
        }
    
    def _identify_issues(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify all data quality issues"""
        issues = []
        
        # Missing data issues
        missing_per_col = df.isnull().sum()
        high_missing = missing_per_col[missing_per_col > len(df) * 0.1]
        for col, count in high_missing.items():
            issues.append({
                "severity": "high",
                "type": "missing_data",
                "column": col,
                "description": f"{col} has {count} missing values ({count/len(df)*100:.1f}%)",
                "recommendation": "Consider imputation or data collection"
            })
        
        # Duplicate issues
        duplicates = len(df[df.duplicated()])
        if duplicates > 0:
            issues.append({
                "severity": "medium",
                "type": "duplicates",
                "description": f"{duplicates} duplicate rows found",
                "recommendation": "Review and remove duplicate records if not intentional"
            })
        
        # Outlier issues
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols[:5]:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)]
            if len(outliers) > len(df) * 0.05:  # More than 5% outliers
                issues.append({
                    "severity": "medium",
                    "type": "outliers",
                    "column": col,
                    "description": f"{len(outliers)} outliers detected in {col}",
                    "recommendation": "Investigate outliers for data entry errors or special cases"
                })
        
        return issues
    
    def _quality_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate data quality improvement recommendations"""
        recommendations = []
        
        missing_per_col = df.isnull().sum()
        if missing_per_col.sum() > 0:
            recommendations.append("Address missing data through imputation or data collection")
        
        if len(df[df.duplicated()]) > 0:
            recommendations.append("Remove or investigate duplicate records")
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            recommendations.append("Consider including numeric columns for more advanced analysis")
        
        if len(df) < 100:
            recommendations.append("Dataset may benefit from more samples for reliable analysis")
        
        return recommendations

