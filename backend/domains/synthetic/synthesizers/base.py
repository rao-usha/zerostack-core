"""Base synthesizer interface."""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from ..models import GenerationCondition

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

    def sample_with_conditions(
        self,
        num_rows: int,
        conditions: List["GenerationCondition"],
        max_tries_per_batch: int = 100,
        oversample_factor: float = 2.0,
    ) -> SynthesizerResult:
        """Generate synthetic data matching conditions.

        This method supports conditional sampling where generated rows must
        satisfy specified conditions. SDV synthesizers support exact-value
        conditions natively, while range conditions are handled via oversampling
        and post-filtering.

        Args:
            num_rows: Target number of rows to generate
            conditions: List of conditions to satisfy
            max_tries_per_batch: Max sampling attempts for SDV reject sampling
            oversample_factor: Factor to oversample for range conditions

        Returns:
            SynthesizerResult with synthetic data matching conditions

        Note:
            Not all synthesizers support all condition types efficiently.
            GaussianCopula has native support for conditional sampling.
            CTGAN/TVAE use reject sampling which may be slower.
        """
        # Default implementation: delegate to regular sample and apply filters
        # Subclasses should override for native conditional support
        from ..conditions import ConditionProcessor

        processor = ConditionProcessor()
        _, post_filter_conditions = processor.split_conditions(conditions)

        # If we have post-filter conditions, oversample
        target_rows = num_rows
        if post_filter_conditions:
            target_rows = int(num_rows * oversample_factor)

        # Generate data
        result = self.sample(target_rows)

        # Apply post-filters
        if post_filter_conditions:
            result.synthetic_data = processor.apply_post_filters(
                result.synthetic_data, post_filter_conditions
            )

            # Ensure we have enough rows
            if len(result.synthetic_data) < num_rows:
                result.warnings.append(
                    f"Only {len(result.synthetic_data)} rows matched conditions "
                    f"(requested {num_rows}). Try increasing oversample_factor."
                )
            else:
                # Trim to requested count
                result.synthetic_data = result.synthetic_data.head(num_rows)

        result.metadata['conditional'] = True
        result.metadata['conditions_count'] = len(conditions)

        return result
    
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
