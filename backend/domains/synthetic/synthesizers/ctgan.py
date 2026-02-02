"""CTGAN synthesizer implementation."""
import logging
import time
from typing import Dict, Any, Optional, List, TYPE_CHECKING

import pandas as pd

from .base import BaseSynthesizer, SynthesizerResult

if TYPE_CHECKING:
    from ..models import GenerationCondition

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

    def sample_with_conditions(
        self,
        num_rows: int,
        conditions: List["GenerationCondition"],
        max_tries_per_batch: int = 100,
        oversample_factor: float = 2.0,
    ) -> SynthesizerResult:
        """Generate synthetic data matching conditions.

        CTGAN supports conditional sampling via SDV's sample_from_conditions,
        but uses reject sampling which can be slower than GaussianCopula.

        Args:
            num_rows: Target number of rows to generate
            conditions: List of conditions to satisfy
            max_tries_per_batch: Max sampling attempts per batch
            oversample_factor: Factor to oversample for range conditions

        Returns:
            SynthesizerResult with synthetic data matching conditions
        """
        self._validate_fitted()

        from ..conditions import ConditionProcessor

        logger.info(f"Generating {num_rows} conditional rows with CTGAN")
        start_time = time.time()

        processor = ConditionProcessor()
        sdv_conditions, post_filter_conditions = processor.split_conditions(conditions)

        warnings = []
        warnings.append(
            "CTGAN uses reject sampling for conditions which may be slow. "
            "Consider GaussianCopula for faster conditional generation."
        )

        # Determine how many rows to generate
        target_rows = num_rows
        if post_filter_conditions:
            target_rows = int(num_rows * oversample_factor)

        # Generate with SDV conditions if we have any
        if sdv_conditions:
            merged = processor.merge_sdv_conditions(target_rows, sdv_conditions)

            if merged:
                logger.info(f"Using merged condition for {len(sdv_conditions)} columns")
                try:
                    synthetic_df = self._synthesizer.sample_from_conditions(
                        conditions=[merged],
                        max_tries_per_batch=max_tries_per_batch,
                    )
                except Exception as e:
                    logger.warning(f"Conditional sampling failed: {e}, falling back to regular sampling")
                    warnings.append(f"Conditional sampling failed: {str(e)}")
                    synthetic_df = self._synthesizer.sample(target_rows)
            else:
                sdv_conds = processor.build_sdv_conditions(target_rows, sdv_conditions)
                logger.info(f"Using {len(sdv_conds)} SDV conditions")
                try:
                    synthetic_df = self._synthesizer.sample_from_conditions(
                        conditions=sdv_conds,
                        max_tries_per_batch=max_tries_per_batch,
                    )
                except Exception as e:
                    logger.warning(f"Conditional sampling failed: {e}, falling back to regular sampling")
                    warnings.append(f"Conditional sampling failed: {str(e)}")
                    synthetic_df = self._synthesizer.sample(target_rows)
        else:
            synthetic_df = self._synthesizer.sample(target_rows)

        # Apply post-filters for range conditions
        if post_filter_conditions:
            synthetic_df = processor.apply_post_filters(synthetic_df, post_filter_conditions)

            if len(synthetic_df) < num_rows:
                warnings.append(
                    f"Only {len(synthetic_df)} rows matched conditions "
                    f"(requested {num_rows}). Try increasing oversample_factor."
                )
            else:
                synthetic_df = synthetic_df.head(num_rows)

        # Post-process to restore dtypes
        synthetic_df = self._post_process(synthetic_df)

        sample_time = time.time() - start_time
        logger.info(f"Generated {len(synthetic_df)} conditional rows in {sample_time:.2f}s")

        return SynthesizerResult(
            synthetic_data=synthetic_df,
            metadata={
                'synthesizer': self.synthesizer_type,
                'num_rows': len(synthetic_df),
                'num_columns': len(synthetic_df.columns),
                'conditional': True,
                'conditions_count': len(conditions),
                'sdv_conditions_count': len(sdv_conditions),
                'post_filter_conditions_count': len(post_filter_conditions),
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
