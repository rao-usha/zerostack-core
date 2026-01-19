"""CTGAN synthesizer implementation."""
import logging
import time
from typing import Dict, Any, Optional

import pandas as pd

from .base import BaseSynthesizer, SynthesizerResult

logger = logging.getLogger(__name__)


class CTGANSynthesizer(BaseSynthesizer):
    """Conditional Tabular GAN synthesizer using SDV.
    
    CTGAN uses a conditional generator that can handle mixed data types
    (numeric and categorical) effectively. It uses mode-specific normalization
    to capture complex distributions.
    
    This synthesizer produces the highest quality synthetic data but:
    - Requires more training time
    - Benefits significantly from GPU acceleration
    - May require hyperparameter tuning for best results
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._synthesizer = None
        self._sdv_metadata = None
    
    @property
    def name(self) -> str:
        return "CTGAN"
    
    @property
    def synthesizer_type(self) -> str:
        return "ctgan"
    
    def fit(self, data: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Fit the CTGAN model to data.
        
        Args:
            data: Training data
            metadata: Optional column metadata
        """
        from sdv.single_table import CTGANSynthesizer as SDVCtgan
        from sdv.metadata import SingleTableMetadata
        
        logger.info(f"Fitting CTGAN on {len(data)} rows, {len(data.columns)} columns")
        start_time = time.time()
        
        # Store column info
        self._store_metadata(data)
        
        # Create SDV metadata
        self._sdv_metadata = SingleTableMetadata()
        self._sdv_metadata.detect_from_dataframe(data)
        
        # Apply any metadata overrides
        if metadata:
            for col, col_meta in metadata.items():
                if col in data.columns and 'sdtype' in col_meta:
                    self._sdv_metadata.update_column(
                        column_name=col,
                        sdtype=col_meta['sdtype']
                    )
        
        # Get config options with defaults
        epochs = self.config.get('epochs', 300)
        batch_size = self.config.get('batch_size', 500)
        generator_dim = self.config.get('generator_dim', (256, 256))
        discriminator_dim = self.config.get('discriminator_dim', (256, 256))
        generator_lr = self.config.get('generator_lr', 2e-4)
        discriminator_lr = self.config.get('discriminator_lr', 2e-4)
        discriminator_steps = self.config.get('discriminator_steps', 1)
        verbose = self.config.get('verbose', False)
        
        # Convert lists to tuples if needed
        if isinstance(generator_dim, list):
            generator_dim = tuple(generator_dim)
        if isinstance(discriminator_dim, list):
            discriminator_dim = tuple(discriminator_dim)
        
        # Create synthesizer
        self._synthesizer = SDVCtgan(
            metadata=self._sdv_metadata,
            epochs=epochs,
            batch_size=batch_size,
            generator_dim=generator_dim,
            discriminator_dim=discriminator_dim,
            generator_lr=generator_lr,
            discriminator_lr=discriminator_lr,
            discriminator_steps=discriminator_steps,
            verbose=verbose,
        )
        
        # Fit to data
        logger.info(f"Training CTGAN for {epochs} epochs (this may take a while)...")
        self._synthesizer.fit(data)
        self._fitted = True
        
        fit_time = time.time() - start_time
        logger.info(f"CTGAN fitted in {fit_time:.2f}s")
    
    def sample(self, num_rows: int) -> SynthesizerResult:
        """Generate synthetic data using the fitted model.
        
        Args:
            num_rows: Number of rows to generate
            
        Returns:
            SynthesizerResult with synthetic data
        """
        self._validate_fitted()
        
        logger.info(f"Generating {num_rows} synthetic rows with CTGAN")
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
            'id': 'ctgan',
            'name': 'CTGAN',
            'description': 'Conditional Tabular GAN that excels at capturing complex distributions in mixed-type data. Produces highest quality results but requires more training time.',
            'speed': 'slow',
            'quality': 'excellent',
            'gpu_required': False,  # Works without GPU but much faster with
            'gpu_recommended': True,
            'best_for': [
                'Complex distributions',
                'Mixed numeric/categorical data',
                'High-quality requirements',
                'Production datasets',
            ],
            'config_schema': {
                'epochs': {
                    'type': 'integer',
                    'default': 300,
                    'min': 1,
                    'max': 1000,
                    'description': 'Number of training epochs',
                },
                'batch_size': {
                    'type': 'integer',
                    'default': 500,
                    'min': 10,
                    'max': 10000,
                    'description': 'Training batch size',
                },
                'generator_dim': {
                    'type': 'array',
                    'default': [256, 256],
                    'description': 'Generator network dimensions',
                },
                'discriminator_dim': {
                    'type': 'array',
                    'default': [256, 256],
                    'description': 'Discriminator network dimensions',
                },
            },
        }
