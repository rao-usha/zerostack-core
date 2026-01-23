"""
ML Model Training Data Tracking

Automatically detects and tracks queries used for ML model training,
feature extraction, and data science workflows.

Identifies:
- Feature extraction queries
- Training data preparation
- Model inference data sources
- A/B test datasets
"""
import re
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from .sql_parser import SQLLineageParser, QueryLineage


@dataclass
class MLFeature:
    """Represents a feature extracted from data"""
    feature_name: str
    source_table: str
    source_column: str
    transformation: str  # e.g., "LOG(amount)", "DATE_PART('day', date)"
    feature_type: str  # NUMERIC, CATEGORICAL, TEMPORAL, TEXT


@dataclass
class MLDataQuery:
    """Represents a query used for ML"""
    query_id: str
    query_type: str  # FEATURE_EXTRACTION, TRAINING_DATA, INFERENCE_DATA, VALIDATION_DATA
    sql: str
    features_extracted: List[MLFeature]
    source_tables: List[str]
    target_dataset: Optional[str]
    detected_patterns: List[str]
    confidence_score: float  # 0-1, how confident we are this is ML-related


class MLDataTracker:
    """
    Detects and tracks ML-related queries automatically.
    
    Detection patterns:
    - Feature engineering keywords (LAG, LEAD, window functions)
    - Statistical aggregations (STDDEV, PERCENTILE, VARIANCE)
    - Common ML table names (features, train, test, validation)
    - Train/test split patterns (RANDOM(), MOD())
    - Temporal features (DAY_OF_WEEK, HOUR, MONTH)
    """
    
    def __init__(self):
        self.parser = SQLLineageParser()
        
        # Keywords that suggest ML/feature engineering
        self.ml_keywords = {
            # Window functions (common in time series features)
            'LAG', 'LEAD', 'ROW_NUMBER', 'RANK', 'DENSE_RANK',
            'FIRST_VALUE', 'LAST_VALUE', 'NTH_VALUE',
            
            # Statistical functions
            'STDDEV', 'VARIANCE', 'PERCENTILE_CONT', 'PERCENTILE_DISC',
            'CORR', 'COVAR_POP', 'COVAR_SAMP',
            
            # Time-based features
            'DATE_PART', 'EXTRACT', 'DATE_TRUNC', 'AGE',
            
            # Randomization (train/test split)
            'RANDOM', 'MD5', 'HASH',
            
            # Array/JSON (feature vectors)
            'ARRAY_AGG', 'JSON_AGG', 'ARRAY', 'UNNEST'
        }
        
        # Table name patterns
        self.ml_table_patterns = [
            r'\bfeatures?\b',
            r'\btrain(?:ing)?(?:_data|_set)?\b',
            r'\btest(?:_data|_set)?\b',
            r'\bval(?:idation)?(?:_data|_set)?\b',
            r'\bml_\w+',
            r'\bmodel_\w+',
            r'\bprediction',
            r'\bscore',
            r'\binference'
        ]
        
        # Column name patterns (features)
        self.feature_name_patterns = [
            r'\bfeat_\w+',
            r'\b\w+_feat\b',
            r'\bfeature_\w+',
            r'\b\w+_transformed\b',
            r'\b\w+_encoded\b',
            r'\b\w+_normalized\b',
            r'\b\w+_scaled\b',
            r'\blabel\b',
            r'\btarget\b',
            r'\by_\w+',  # common ML convention
        ]
    
    def analyze_query(self, sql: str) -> Optional[MLDataQuery]:
        """
        Analyze if a query is ML-related and extract metadata.
        
        Args:
            sql: SQL query to analyze
            
        Returns:
            MLDataQuery if detected as ML-related, None otherwise
        """
        sql_upper = sql.upper()
        
        # Check for ML keywords
        detected_patterns = []
        confidence = 0.0
        
        # Score based on ML keywords
        ml_keyword_count = sum(1 for keyword in self.ml_keywords if keyword in sql_upper)
        if ml_keyword_count > 0:
            detected_patterns.append(f"{ml_keyword_count} ML keyword(s) found")
            confidence += min(ml_keyword_count * 0.15, 0.4)
        
        # Score based on table names
        for pattern in self.ml_table_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                detected_patterns.append(f"ML table pattern: {pattern}")
                confidence += 0.25
                break
        
        # Score based on column names (in SELECT clause)
        select_match = re.search(r'\bSELECT\s+(.*?)\s+FROM\b', sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)
            for pattern in self.feature_name_patterns:
                if re.search(pattern, select_clause, re.IGNORECASE):
                    detected_patterns.append(f"Feature column pattern: {pattern}")
                    confidence += 0.2
                    break
        
        # Check for train/test split pattern (random sampling or modulo)
        if re.search(r'\b(RANDOM|MD5|HASH)\s*\(\s*\)', sql, re.IGNORECASE):
            if re.search(r'\bWHERE\b.*\b(MOD|%)\b', sql, re.IGNORECASE):
                detected_patterns.append("Train/test split pattern detected")
                confidence += 0.3
        
        # Check for window functions (time series features)
        if re.search(r'\bOVER\s*\(', sql, re.IGNORECASE):
            detected_patterns.append("Window functions (time series features)")
            confidence += 0.2
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        # Only return if confidence >= 0.3
        if confidence < 0.3:
            return None
        
        # Parse SQL for lineage
        query_lineage = self.parser.parse(sql)
        
        # Determine query type
        query_type = self._determine_ml_query_type(sql, detected_patterns)
        
        # Extract features
        features = self._extract_features(sql, query_lineage)
        
        # Determine target dataset
        target_dataset = None
        if query_lineage.target_table:
            target_dataset = query_lineage.target_table.full_name
        
        return MLDataQuery(
            query_id=str(uuid4()),
            query_type=query_type,
            sql=sql,
            features_extracted=features,
            source_tables=[t.full_name for t in query_lineage.source_tables],
            target_dataset=target_dataset,
            detected_patterns=detected_patterns,
            confidence_score=confidence
        )
    
    def _determine_ml_query_type(self, sql: str, patterns: List[str]) -> str:
        """Determine the type of ML query"""
        sql_lower = sql.lower()
        
        if any('train' in pattern.lower() for pattern in patterns):
            return 'TRAINING_DATA'
        elif any('test' in pattern.lower() or 'validation' in pattern.lower() for pattern in patterns):
            return 'VALIDATION_DATA'
        elif 'inference' in sql_lower or 'prediction' in sql_lower or 'score' in sql_lower:
            return 'INFERENCE_DATA'
        else:
            return 'FEATURE_EXTRACTION'
    
    def _extract_features(self, sql: str, query_lineage: QueryLineage) -> List[MLFeature]:
        """Extract ML features from query"""
        features = []
        
        # Parse SELECT clause
        select_match = re.search(r'\bSELECT\s+(.*?)\s+FROM\b', sql, re.IGNORECASE | re.DOTALL)
        if not select_match:
            return []
        
        select_clause = select_match.group(1)
        
        # Split by commas (naive approach)
        column_exprs = select_clause.split(',')
        
        for expr in column_exprs:
            expr = expr.strip()
            
            # Check for AS alias
            as_match = re.search(r'\s+[Aa][Ss]\s+(["\']?(\w+)["\']?)\s*$', expr)
            if as_match:
                feature_name = as_match.group(2)
                source_expr = expr[:as_match.start()].strip()
            else:
                # Use expression as feature name
                feature_name = expr.split('.')[-1] if '.' in expr else expr
                source_expr = expr
            
            # Detect feature type
            feature_type = self._detect_feature_type(source_expr)
            
            # Extract source column
            col_match = re.search(r'(\w+)\.(\w+)', source_expr)
            if col_match:
                source_table = col_match.group(1)
                source_column = col_match.group(2)
            else:
                source_table = 'unknown'
                col_match = re.search(r'\b([a-zA-Z_]\w*)\b', source_expr)
                source_column = col_match.group(1) if col_match else 'unknown'
            
            features.append(MLFeature(
                feature_name=feature_name[:50],  # Limit length
                source_table=source_table,
                source_column=source_column,
                transformation=source_expr[:200],  # Limit length
                feature_type=feature_type
            ))
        
        return features
    
    def _detect_feature_type(self, expr: str) -> str:
        """Detect the type of feature"""
        expr_upper = expr.upper()
        
        # Temporal features
        if any(keyword in expr_upper for keyword in ['DATE', 'TIME', 'YEAR', 'MONTH', 'DAY', 'HOUR', 'EXTRACT']):
            return 'TEMPORAL'
        
        # Numeric transformations
        if any(keyword in expr_upper for keyword in ['LOG', 'SQRT', 'POWER', 'ABS', 'ROUND', 'SUM', 'AVG', 'COUNT']):
            return 'NUMERIC'
        
        # Text features
        if any(keyword in expr_upper for keyword in ['UPPER', 'LOWER', 'SUBSTRING', 'CONCAT', 'LENGTH', 'SPLIT']):
            return 'TEXT'
        
        # Categorical (CASE, COALESCE, etc.)
        if any(keyword in expr_upper for keyword in ['CASE', 'WHEN', 'COALESCE', 'NULLIF']):
            return 'CATEGORICAL'
        
        # Default
        return 'UNKNOWN'
    
    def track_ml_pipeline(
        self,
        feature_query: str,
        model_id: str,
        model_name: str,
        model_type: str
    ) -> Dict:
        """
        Track ML pipeline from feature extraction to model training.
        
        Args:
            feature_query: SQL query used to extract features
            model_id: ID of the ML model
            model_name: Name of the ML model
            model_type: Type of model (e.g., "random_forest", "xgboost")
            
        Returns:
            Dictionary with tracking information
        """
        ml_query = self.analyze_query(feature_query)
        
        if not ml_query:
            return {
                'tracked': False,
                'reason': 'Query does not appear to be ML-related'
            }
        
        return {
            'tracked': True,
            'model_id': model_id,
            'model_name': model_name,
            'model_type': model_type,
            'query_type': ml_query.query_type,
            'features_count': len(ml_query.features_extracted),
            'features': [
                {
                    'name': f.feature_name,
                    'type': f.feature_type,
                    'source': f"{f.source_table}.{f.source_column}"
                }
                for f in ml_query.features_extracted
            ],
            'source_tables': ml_query.source_tables,
            'confidence': ml_query.confidence_score,
            'detected_patterns': ml_query.detected_patterns
        }


# Convenience function
def analyze_ml_query(sql: str) -> Optional[MLDataQuery]:
    """
    Analyze if a query is ML-related.
    
    Example:
        result = analyze_ml_query('''
            SELECT 
                customer_id,
                LOG(amount) as log_amount,
                EXTRACT(hour FROM created_at) as hour_of_day,
                LAG(amount) OVER (PARTITION BY customer_id ORDER BY date) as prev_amount
            FROM sales
        ''')
        
        if result:
            print(f"ML Query Type: {result.query_type}")
            print(f"Features: {len(result.features_extracted)}")
            print(f"Confidence: {result.confidence_score:.2%}")
    """
    tracker = MLDataTracker()
    return tracker.analyze_query(sql)
