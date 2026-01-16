"""Gaussian Copula synthesizer implementation."""
import logging
import time
from typing import Dict, Any, Optional

import pandas as pd

from .base import BaseSynthesizer, SynthesizerResult

logger = logging.getLogger(__name__)


class GaussianCopulaSynthesizer(BaseSynthesizer):
    """Gaussian Copula synthesizer using SDV.
    
    This is the recommended default synthesizer for most tabular data.
    It's fast, preserves correlations well, and doesn't require GPU.
    
    How it works:
    1. Transform each column to uniform distribution (using CDF)
    2. Fit multivariate Gaussian to capture correlations
    3. Sample from multivariate Gaussian
    4. Inverse transform back to original distributions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._synthesizer = None
        self._sdv_metadata = None
    
    @property
    def name(self) -> str:
        return "Gaussian Copula"
    
    @property
    def synthesizer_type(self) -> str:
        return "gaussian_copula"
    
    def fit(self, data: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Fit the Gaussian Copula model to data.
        
        Args:
            data: Training data
            metadata: Optional column metadata
        """
        from sdv.single_table import GaussianCopulaSynthesizer as SDVCopula
        from sdv.metadata import SingleTableMetadata
        
        logger.info(f"Fitting Gaussian Copula on {len(data)} rows, {len(data.columns)} columns")
        start_time = time.time()
        
        # Store column info
        self._store_metadata(data)
        
        # Create SDV metadata
        self._sdv_metadata = SingleTableMetadata()
        self._sdv_metadata.detect_from_dataframe(data)
        
        # Apply any metadata overrides from config
        if metadata:
            for col, col_meta in metadata.items():
                if col in data.columns:
                    if 'sdtype' in col_meta:
                        self._sdv_metadata.update_column(
                            column_name=col,
                            sdtype=col_meta['sdtype']
                        )
        
        # Get config options
        enforce_min_max = self.config.get('enforce_min_max', True)
        enforce_rounding = self.config.get('enforce_rounding', True)
        numerical_distributions = self.config.get('numerical_distributions', None)
        
        # Create synthesizer
        self._synthesizer = SDVCopula(
            metadata=self._sdv_metadata,
            enforce_min_max_values=enforce_min_max,
            enforce_rounding=enforce_rounding,
            numerical_distributions=numerical_distributions,
        )
        
        # Fit to data
        self._synthesizer.fit(data)
        self._fitted = True
        
        fit_time = time.time() - start_time
        logger.info(f"Gaussian Copula fitted in {fit_time:.2f}s")
    
    def sample(self, num_rows: int) -> SynthesizerResult:
        """Generate synthetic data using the fitted model.
        
        Args:
            num_rows: Number of rows to generate
            
        Returns:
            SynthesizerResult with synthetic data
        """
        self._validate_fitted()
        
        logger.info(f"Generating {num_rows} synthetic rows with Gaussian Copula")
        start_time = time.time()
        
        warnings = []
        
        # Generate synthetic data
        synthetic_df = self._synthesizer.sample(num_rows)
        
        # Post-process to restore dtypes
        synthetic_df = self._post_process(synthetic_df)
        
        sample_time = time.time() - start_time
        logger.info(f"Generated {len(synthetic_df)} rows in {sample_time:.2f}s")
        
        return SynthesizerResult(
            synthetic_data=synthetic_df,
            metadata={
                'synthesizer': self.synthesizer_type,
                'num_rows': len(synthetic_df),
                'num_columns': len(synthetic_df.columns),
            },
            warnings=warnings,
            sample_time_seconds=sample_time,
        )
    
    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        """Get synthesizer information."""
        return {
            'id': 'gaussian_copula',
            'name': 'Gaussian Copula',
            'description': 'Fast statistical synthesizer that preserves correlations using Gaussian copulas. Best default choice for most tabular data.',
            'speed': 'fast',
            'quality': 'good',
            'gpu_required': False,
            'best_for': [
                'Most tabular datasets',
                'Quick iteration',
                'Numeric-heavy data',
                'Datasets with clear correlations',
            ],
            'config_schema': {
                'enforce_min_max': {
                    'type': 'boolean',
                    'default': True,
                    'description': 'Enforce min/max values from original data',
                },
                'enforce_rounding': {
                    'type': 'boolean',
                    'default': True,
                    'description': 'Round numeric columns to match original precision',
                },
            },
        }
