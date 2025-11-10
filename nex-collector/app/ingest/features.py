"""Feature extraction for facets."""
from typing import Dict, Any, Optional
import re


class FeatureExtractor:
    """Extract structured features from context variants."""
    
    def extract(self, body_text: str, domain: Optional[str] = None, 
                persona: Optional[str] = None, task: Optional[str] = None,
                style: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract features from context.
        
        Returns:
            Dictionary of extracted features
        """
        features = {}
        
        # Domain detection (if not provided)
        if not domain:
            domain = self._detect_domain(body_text)
        features["domain"] = domain
        
        # Persona detection
        if not persona:
            persona = self._detect_persona(body_text)
        features["persona"] = persona
        
        # Task detection
        if not task:
            task = self._detect_task(body_text)
        features["task"] = task
        
        # Style detection
        if not style:
            style = self._detect_style(body_text)
        features["style"] = style
        
        # Additional features
        features["complexity"] = self._assess_complexity(body_text)
        features["formality"] = self._assess_formality(body_text)
        features["length_category"] = self._categorize_length(len(body_text))
        
        return features
    
    def _detect_domain(self, text: str) -> str:
        """Detect domain from text."""
        domain_keywords = {
            "finance": ["financial", "revenue", "profit", "investment", "budget"],
            "healthcare": ["patient", "medical", "diagnosis", "treatment", "health"],
            "legal": ["legal", "law", "contract", "compliance", "regulation"],
            "technology": ["software", "code", "system", "application", "technical"],
        }
        
        text_lower = text.lower()
        for domain, keywords in domain_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return domain
        
        return "general"
    
    def _detect_persona(self, text: str) -> str:
        """Detect persona from text."""
        persona_patterns = {
            "CFO": r"\b(CFO|chief financial|financial officer|revenue|profitability)\b",
            "doctor": r"\b(doctor|physician|medical professional|diagnosis|treatment)\b",
            "lawyer": r"\b(lawyer|attorney|legal counsel|compliance|regulation)\b",
            "engineer": r"\b(engineer|technical|implementation|system|architecture)\b",
        }
        
        text_lower = text.lower()
        for persona, pattern in persona_patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                return persona
        
        return "general"
    
    def _detect_task(self, text: str) -> str:
        """Detect task type from text."""
        task_patterns = {
            "explain": r"\b(explain|describe|clarify|elaborate)\b",
            "classify": r"\b(classify|categorize|identify|determine)\b",
            "generate": r"\b(generate|create|produce|write)\b",
            "analyze": r"\b(analyze|evaluate|assess|review)\b",
        }
        
        text_lower = text.lower()
        for task, pattern in task_patterns.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                return task
        
        return "general"
    
    def _detect_style(self, text: str) -> str:
        """Detect writing style."""
        # Check formality indicators
        formal_indicators = len(re.findall(r'\b(must|shall|therefore|furthermore)\b', text, re.IGNORECASE))
        casual_indicators = len(re.findall(r'\b(you|your|let\'s|we\'ll)\b', text, re.IGNORECASE))
        
        if formal_indicators > casual_indicators:
            return "formal"
        elif casual_indicators > formal_indicators:
            return "conversational"
        else:
            return "neutral"
    
    def _assess_complexity(self, text: str) -> str:
        """Assess complexity level."""
        avg_sentence_length = len(text.split()) / max(1, text.count('.') + text.count('!') + text.count('?'))
        
        if avg_sentence_length > 20:
            return "high"
        elif avg_sentence_length > 10:
            return "medium"
        else:
            return "low"
    
    def _assess_formality(self, text: str) -> float:
        """Assess formality score (0-1)."""
        formal_markers = len(re.findall(r'\b(must|shall|therefore|furthermore|consequently)\b', text, re.IGNORECASE))
        casual_markers = len(re.findall(r'\b(you|your|let\'s|gonna|wanna)\b', text, re.IGNORECASE))
        
        total = formal_markers + casual_markers
        if total == 0:
            return 0.5
        
        return formal_markers / total
    
    def _categorize_length(self, length: int) -> str:
        """Categorize text length."""
        if length < 500:
            return "short"
        elif length < 2000:
            return "medium"
        else:
            return "long"

