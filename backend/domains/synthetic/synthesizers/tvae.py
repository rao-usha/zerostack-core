"""TVAE synthesizer implementation."""
import logging
import time
from typing import Dict, Any, Optional

import pandas as pd

from .base import BaseSynthesizer, SynthesizerResult

logger = logging.getLogger(__name__)


class TVAESynthesizer(BaseSynthesizer):
    """Tabular Variational Autoencoder synthesizer using SDV.
    
    TVAE uses a variational autoencoder architecture adapted for tabular data.
    It learns a latent representation of the data and generates new samples
    by sampling from the latent space.
    
    Compared to CTGAN:
    - More stable training
    - Faster convergence
    - Good for smaller datasets
    - May produce slightly less sharp distributions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._synthesizer = None
        self._sdv_metadata = None
    
    @property
    def name(self) -> str:
        return "TVAE"
    
    @property
    def synthesizer_type(self) -> str:
        return "tvae"
    
    def fit(self, data: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Fit the TVAE model to data.
        
        Args:
            data: Training data
            metadata: Optional column metadata
        """
        from sdv.single_table import TVAESynthesizer as SDVTVAE
        from sdv.metadata import SingleTableMetadata
        
        logger.info(f"Fitting TVAE on {len(data)} rows, {len(data.columns)} columns")
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
        encoder_dim = self.config.get('encoder_dim', (128, 128))
        decoder_dim = self.config.get('decoder_dim', (128, 128))
        l2_scale = self.config.get('l2_scale', 1e-5)
        loss_factor = self.config.get('loss_factor', 2)
        
        # Convert lists to tuples if needed
        if isinstance(encoder_dim, list):
            encoder_dim = tuple(encoder_dim)
        if isinstance(decoder_dim, list):
            decoder_dim = tuple(decoder_dim)
        
        # Create synthesizer
        self._synthesizer = SDVTVAE(
            metadata=self._sdv_metadata,
            epochs=epochs,
            batch_size=batch_size,
            compress_dims=encoder_dim,
            decompress_dims=decoder_dim,
            l2scale=l2_scale,
            loss_factor=loss_factor,
        )
        
        # Fit to data
        logger.info(f"Training TVAE for {epochs} epochs...")
        self._synthesizer.fit(data)
        self._fitted = True
        
        fit_time = time.time() - start_time
        logger.info(f"TVAE fitted in {fit_time:.2f}s")
    
    def sample(self, num_rows: int) -> SynthesizerResult:
        """Generate synthetic data using the fitted model.
        
        Args:
            num_rows: Number of rows to generate
            
        Returns:
            SynthesizerResult with synthetic data
        """
        self._validate_fitted()
        
        logger.info(f"Generating {num_rows} synthetic rows with TVAE")
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
            'id': 'tvae',
            'name': 'TVAE',
            'description': 'Tabular Variational Autoencoder with stable training and good results for mixed data types. A reliable alternative to CTGAN.',
            'speed': 'medium',
            'quality': 'very_good',
            'gpu_required': False,
            'gpu_recommended': True,
            'best_for': [
                'Stable training requirements',
                'Smaller datasets',
                'Mixed data types',
                'When CTGAN training is unstable',
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
                'encoder_dim': {
                    'type': 'array',
                    'default': [128, 128],
                    'description': 'Encoder network dimensions',
                },
                'decoder_dim': {
                    'type': 'array',
                    'default': [128, 128],
                    'description': 'Decoder network dimensions',
                },
                'l2_scale': {
                    'type': 'number',
                    'default': 1e-5,
                    'description': 'L2 regularization scale',
                },
                'loss_factor': {
                    'type': 'number',
                    'default': 2,
                    'description': 'Loss scaling factor',
                },
            },
        }
