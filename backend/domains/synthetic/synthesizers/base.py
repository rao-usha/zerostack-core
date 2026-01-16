"""Base synthesizer interface."""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class SynthesizerResult:
    """Result from synthesis operation."""
    synthetic_data: pd.DataFrame
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    fit_time_seconds: float = 0.0
    sample_time_seconds: float = 0.0


class BaseSynthesizer(ABC):
    """Abstract base class for all synthesizers.
    
    All synthesizers must implement:
    - fit(): Learn from real data
    - sample(): Generate synthetic data
    - get_info(): Return synthesizer information
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize synthesizer with optional config.
        
        Args:
            config: Synthesizer-specific configuration
        """
        self.config = config or {}
        self._fitted = False
        self._metadata = None
        self._columns = None
        self._dtypes = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable synthesizer name."""
        pass
    
    @property
    @abstractmethod
    def synthesizer_type(self) -> str:
        """Synthesizer type identifier."""
        pass
    
    @property
    def is_fitted(self) -> bool:
        """Check if synthesizer has been fitted."""
        return self._fitted
    
    @abstractmethod
    def fit(self, data: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Fit the synthesizer to real data.
        
        Args:
            data: Real data to learn from
            metadata: Optional metadata about columns (types, constraints, etc.)
        """
        pass
    
    @abstractmethod
    def sample(self, num_rows: int) -> SynthesizerResult:
        """Generate synthetic data.
        
        Args:
            num_rows: Number of rows to generate
            
        Returns:
            SynthesizerResult with synthetic data and metadata
        """
        pass
    
    @classmethod
    @abstractmethod
    def get_info(cls) -> Dict[str, Any]:
        """Get information about this synthesizer.
        
        Returns:
            Dict with name, description, speed, quality, etc.
        """
        pass
    
    def _validate_fitted(self) -> None:
        """Raise error if not fitted."""
        if not self._fitted:
            raise RuntimeError(f"{self.name} has not been fitted. Call fit() first.")
    
    def _store_metadata(self, data: pd.DataFrame) -> None:
        """Store column information from input data."""
        self._columns = list(data.columns)
        self._dtypes = {col: str(data[col].dtype) for col in data.columns}
    
    def _post_process(self, synthetic_df: pd.DataFrame) -> pd.DataFrame:
        """Post-process synthetic data to match original dtypes.
        
        Args:
            synthetic_df: Raw synthetic data
            
        Returns:
            Processed DataFrame with correct dtypes
        """
        # Ensure columns are in same order
        if self._columns:
            synthetic_df = synthetic_df[self._columns]
        
        # Try to restore original dtypes
        if self._dtypes:
            for col, dtype in self._dtypes.items():
                if col in synthetic_df.columns:
                    try:
                        if 'int' in dtype:
                            synthetic_df[col] = synthetic_df[col].round().astype(dtype)
                        elif 'float' in dtype:
                            synthetic_df[col] = synthetic_df[col].astype(dtype)
                    except (ValueError, TypeError):
                        # Keep the generated dtype if conversion fails
                        pass
        
        return synthetic_df
