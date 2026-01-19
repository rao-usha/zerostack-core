"""PII (Personally Identifiable Information) detection service."""
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class PIIType(str, Enum):
    """Types of PII that can be detected."""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    NAME = "name"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    ADDRESS = "address"
    CITY = "city"
    STATE = "state"
    ZIP_CODE = "zip_code"
    DATE_OF_BIRTH = "date_of_birth"
    IP_ADDRESS = "ip_address"
    URL = "url"
    USERNAME = "username"


@dataclass
class PIIDetectionResult:
    """Result of PII detection for a column."""
    column_name: str
    pii_type: Optional[PIIType]
    confidence: float  # 0.0 to 1.0
    detection_method: str  # "pattern", "column_name", "content_analysis"
    sample_matches: List[str] = field(default_factory=list)
    

class PIIDetector:
    """Detect PII in dataframes using patterns and heuristics.
    
    Detection methods:
    1. Column name matching (e.g., "email", "phone_number")
    2. Content pattern matching (regex)
    3. Statistical analysis (uniqueness, format consistency)
    """
    
    # Regex patterns for content detection
    PATTERNS = {
        PIIType.EMAIL: re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        ),
        PIIType.PHONE: re.compile(
            r'^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$'
        ),
        PIIType.SSN: re.compile(
            r'^\d{3}-?\d{2}-?\d{4}$'
        ),
        PIIType.CREDIT_CARD: re.compile(
            r'^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$'
        ),
        PIIType.ZIP_CODE: re.compile(
            r'^\d{5}(-\d{4})?$'
        ),
        PIIType.IP_ADDRESS: re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        ),
        PIIType.URL: re.compile(
            r'^https?://[^\s]+$'
        ),
        PIIType.DATE_OF_BIRTH: re.compile(
            r'^(0?[1-9]|1[0-2])[-/](0?[1-9]|[12][0-9]|3[01])[-/](19|20)\d{2}$|^(19|20)\d{2}[-/](0?[1-9]|1[0-2])[-/](0?[1-9]|[12][0-9]|3[01])$'
        ),
    }
    
    # Column name patterns (case-insensitive)
    COLUMN_NAME_PATTERNS = {
        PIIType.EMAIL: [
            r'e[-_]?mail', r'email[-_]?addr', r'user[-_]?email'
        ],
        PIIType.PHONE: [
            r'phone', r'mobile', r'cell', r'tel', r'fax', r'contact[-_]?num'
        ],
        PIIType.SSN: [
            r'ssn', r'social[-_]?sec', r'tax[-_]?id', r'sin'  # SIN for Canada
        ],
        PIIType.CREDIT_CARD: [
            r'credit[-_]?card', r'card[-_]?num', r'cc[-_]?num', r'pan'
        ],
        PIIType.NAME: [
            r'^name$', r'full[-_]?name', r'customer[-_]?name', r'user[-_]?name',
            r'person[-_]?name', r'contact[-_]?name'
        ],
        PIIType.FIRST_NAME: [
            r'first[-_]?name', r'fname', r'given[-_]?name', r'forename'
        ],
        PIIType.LAST_NAME: [
            r'last[-_]?name', r'lname', r'surname', r'family[-_]?name'
        ],
        PIIType.ADDRESS: [
            r'address', r'street', r'addr[-_]?line', r'mailing[-_]?addr'
        ],
        PIIType.CITY: [
            r'^city$', r'town', r'municipality'
        ],
        PIIType.STATE: [
            r'^state$', r'province', r'region'
        ],
        PIIType.ZIP_CODE: [
            r'zip', r'postal', r'postcode'
        ],
        PIIType.DATE_OF_BIRTH: [
            r'dob', r'birth[-_]?date', r'date[-_]?of[-_]?birth', r'birthday'
        ],
        PIIType.IP_ADDRESS: [
            r'ip[-_]?addr', r'^ip$', r'client[-_]?ip', r'user[-_]?ip'
        ],
        PIIType.USERNAME: [
            r'user[-_]?name', r'login', r'user[-_]?id', r'account[-_]?name'
        ],
    }
    
    # Common name lists for name detection
    COMMON_FIRST_NAMES = {
        'james', 'john', 'robert', 'michael', 'william', 'david', 'richard', 'joseph',
        'mary', 'patricia', 'jennifer', 'linda', 'elizabeth', 'barbara', 'susan', 'jessica',
        'sarah', 'karen', 'nancy', 'lisa', 'margaret', 'betty', 'sandra', 'ashley',
        'matthew', 'christopher', 'daniel', 'anthony', 'mark', 'donald', 'steven', 'paul',
        'emma', 'olivia', 'ava', 'sophia', 'isabella', 'mia', 'charlotte', 'amelia',
        'liam', 'noah', 'oliver', 'elijah', 'lucas', 'mason', 'logan', 'alexander'
    }
    
    def __init__(self, sample_size: int = 100, confidence_threshold: float = 0.5):
        """Initialize PII detector.
        
        Args:
            sample_size: Number of values to sample for content analysis
            confidence_threshold: Minimum confidence to report as PII
        """
        self.sample_size = sample_size
        self.confidence_threshold = confidence_threshold
    
    def detect(self, df: pd.DataFrame) -> Dict[str, PIIDetectionResult]:
        """Detect PII in all columns of a dataframe.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dict mapping column names to detection results
        """
        results = {}
        
        for col in df.columns:
            result = self._detect_column(df[col], col)
            if result.pii_type and result.confidence >= self.confidence_threshold:
                results[col] = result
                logger.info(
                    f"Detected PII in column '{col}': {result.pii_type.value} "
                    f"(confidence: {result.confidence:.2f}, method: {result.detection_method})"
                )
        
        return results
    
    def _detect_column(self, series: pd.Series, col_name: str) -> PIIDetectionResult:
        """Detect PII in a single column."""
        # First, try column name matching (fastest)
        name_result = self._detect_by_column_name(col_name)
        if name_result and name_result.confidence >= 0.7:
            return name_result
        
        # Then try content pattern matching
        content_result = self._detect_by_content(series, col_name)
        
        # Combine results - prefer higher confidence
        if name_result and content_result:
            if name_result.pii_type == content_result.pii_type:
                # Same type detected by both methods - high confidence
                return PIIDetectionResult(
                    column_name=col_name,
                    pii_type=name_result.pii_type,
                    confidence=min(0.95, name_result.confidence + content_result.confidence * 0.3),
                    detection_method="column_name+content",
                    sample_matches=content_result.sample_matches,
                )
            elif content_result.confidence > name_result.confidence:
                return content_result
            else:
                return name_result
        
        return content_result or name_result or PIIDetectionResult(
            column_name=col_name,
            pii_type=None,
            confidence=0.0,
            detection_method="none",
        )
    
    def _detect_by_column_name(self, col_name: str) -> Optional[PIIDetectionResult]:
        """Detect PII type based on column name."""
        col_lower = col_name.lower().replace(' ', '_')
        
        for pii_type, patterns in self.COLUMN_NAME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, col_lower, re.IGNORECASE):
                    return PIIDetectionResult(
                        column_name=col_name,
                        pii_type=pii_type,
                        confidence=0.8,
                        detection_method="column_name",
                    )
        
        return None
    
    def _detect_by_content(self, series: pd.Series, col_name: str) -> Optional[PIIDetectionResult]:
        """Detect PII type based on content patterns."""
        # Only analyze string columns
        if not pd.api.types.is_string_dtype(series) and series.dtype != object:
            # Check if it might be a date column
            if pd.api.types.is_datetime64_any_dtype(series):
                col_lower = col_name.lower()
                if any(kw in col_lower for kw in ['birth', 'dob', 'born']):
                    return PIIDetectionResult(
                        column_name=col_name,
                        pii_type=PIIType.DATE_OF_BIRTH,
                        confidence=0.7,
                        detection_method="content_analysis",
                    )
            return None
        
        # Sample non-null values
        non_null = series.dropna()
        if len(non_null) == 0:
            return None
        
        sample = non_null.head(self.sample_size).astype(str)
        
        # Try each pattern
        best_match = None
        best_score = 0.0
        best_samples = []
        
        for pii_type, pattern in self.PATTERNS.items():
            matches = sample.apply(lambda x: bool(pattern.match(str(x).strip())))
            match_rate = matches.mean()
            
            if match_rate > best_score and match_rate >= 0.5:
                best_match = pii_type
                best_score = match_rate
                best_samples = sample[matches].head(3).tolist()
        
        # Special case: name detection (no regex, use heuristics)
        if best_match is None:
            name_result = self._detect_names(sample, col_name)
            if name_result:
                return name_result
        
        if best_match:
            return PIIDetectionResult(
                column_name=col_name,
                pii_type=best_match,
                confidence=min(0.9, best_score),
                detection_method="content_pattern",
                sample_matches=best_samples,
            )
        
        return None
    
    def _detect_names(self, sample: pd.Series, col_name: str) -> Optional[PIIDetectionResult]:
        """Detect if column contains names using heuristics."""
        # Check if values look like names:
        # - Mostly alphabetic
        # - Title case or all caps
        # - Some match common first names
        
        def is_name_like(val: str) -> bool:
            val = str(val).strip()
            if not val or len(val) < 2:
                return False
            # Check if mostly alphabetic
            alpha_ratio = sum(c.isalpha() or c.isspace() for c in val) / len(val)
            if alpha_ratio < 0.8:
                return False
            # Check case pattern (Title Case or ALL CAPS)
            words = val.split()
            if len(words) == 0:
                return False
            return all(w.istitle() or w.isupper() for w in words if len(w) > 1)
        
        name_like_rate = sample.apply(is_name_like).mean()
        
        # Check for common first names
        first_words = sample.apply(lambda x: str(x).split()[0].lower() if str(x).strip() else '')
        common_name_rate = first_words.isin(self.COMMON_FIRST_NAMES).mean()
        
        # Determine if it's a name column
        if name_like_rate >= 0.7:
            # Try to determine if it's first name, last name, or full name
            avg_words = sample.apply(lambda x: len(str(x).split())).mean()
            
            if common_name_rate >= 0.3:
                if avg_words < 1.5:
                    pii_type = PIIType.FIRST_NAME
                else:
                    pii_type = PIIType.NAME
            elif avg_words < 1.5:
                # Single words, likely last names
                pii_type = PIIType.LAST_NAME
            else:
                pii_type = PIIType.NAME
            
            return PIIDetectionResult(
                column_name=col_name,
                pii_type=pii_type,
                confidence=min(0.8, name_like_rate * 0.9 + common_name_rate * 0.2),
                detection_method="content_analysis",
                sample_matches=sample.head(3).tolist(),
            )
        
        return None
    
    def get_pii_summary(self, results: Dict[str, PIIDetectionResult]) -> Dict[str, Any]:
        """Get a summary of detected PII."""
        if not results:
            return {
                "total_pii_columns": 0,
                "pii_types": {},
                "high_risk_columns": [],
                "recommendations": ["No PII detected in the dataset."],
            }
        
        # Count by type
        type_counts = {}
        for result in results.values():
            if result.pii_type:
                type_name = result.pii_type.value
                type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # Identify high-risk columns (SSN, credit card)
        high_risk = [
            r.column_name for r in results.values()
            if r.pii_type in [PIIType.SSN, PIIType.CREDIT_CARD]
        ]
        
        recommendations = []
        if high_risk:
            recommendations.append(
                f"High-risk PII detected in columns: {', '.join(high_risk)}. "
                "These will be replaced with fake data."
            )
        if PIIType.EMAIL.value in type_counts:
            recommendations.append("Email addresses will be replaced with fake emails.")
        if PIIType.NAME.value in type_counts or PIIType.FIRST_NAME.value in type_counts:
            recommendations.append("Names will be replaced with fake names.")
        
        return {
            "total_pii_columns": len(results),
            "pii_types": type_counts,
            "high_risk_columns": high_risk,
            "columns": {
                col: {
                    "type": r.pii_type.value if r.pii_type else None,
                    "confidence": r.confidence,
                    "method": r.detection_method,
                }
                for col, r in results.items()
            },
            "recommendations": recommendations,
        }
