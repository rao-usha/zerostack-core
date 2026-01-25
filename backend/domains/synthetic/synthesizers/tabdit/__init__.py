"""TabDiT - Tabular Diffusion Transformer synthesizer module.

TabDiT is a state-of-the-art synthetic data generator that combines:
1. VAE (Variational Autoencoder) - Compresses tabular rows to latent vectors
2. Diffusion Transformer - Learns to generate latent vectors via denoising

This module provides:
- TabDiTSynthesizer: Main synthesizer class
- TabDiTConfig: Configuration dataclasses
- TabularTokenizer: Handles mixed data types
- TabularVAE: Encoder-decoder for latent space
- DiffusionTransformer: Denoising model
- NoiseScheduler: DDPM/DDIM schedulers
"""

from .config import (
    TabDiTConfig,
    VAEConfig,
    DiffusionConfig,
    TokenizerConfig,
)
from .tokenizer import TabularTokenizer, ColumnInfo
from .synthesizer import TabDiTSynthesizer

# Optional imports (require PyTorch)
try:
    from .vae import (
        TabularVAE,
        VAETrainer,
        VAELoss,
        Encoder,
        Decoder,
        load_vae_from_checkpoint,
    )
    from .diffusion import (
        DiffusionTransformer,
        DiffusionTrainer,
        EMA,
        TransformerBlock,
        load_diffusion_from_checkpoint,
    )
    from .scheduler import (
        NoiseScheduler,
        DDIMScheduler,
        create_scheduler,
    )
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

__all__ = [
    # Main synthesizer
    "TabDiTSynthesizer",
    # Configuration
    "TabDiTConfig",
    "VAEConfig",
    "DiffusionConfig",
    "TokenizerConfig",
    # Tokenizer
    "TabularTokenizer",
    "ColumnInfo",
    # Flag
    "TORCH_AVAILABLE",
]

# Add PyTorch-dependent exports if available
if TORCH_AVAILABLE:
    __all__.extend([
        # VAE
        "TabularVAE",
        "VAETrainer",
        "VAELoss",
        "Encoder",
        "Decoder",
        "load_vae_from_checkpoint",
        # Diffusion
        "DiffusionTransformer",
        "DiffusionTrainer",
        "EMA",
        "TransformerBlock",
        "load_diffusion_from_checkpoint",
        # Scheduler
        "NoiseScheduler",
        "DDIMScheduler",
        "create_scheduler",
    ])
