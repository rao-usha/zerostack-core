"""Configuration dataclasses for TabDiT synthesizer."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TokenizerConfig:
    """Configuration for the tabular tokenizer.

    The tokenizer handles conversion of mixed tabular data types
    (numeric, categorical, dates) to a unified representation.
    """
    # Numeric column handling
    num_bins: int = 100  # Number of bins for discretization
    use_quantile_binning: bool = True  # Use quantile vs uniform bins

    # Categorical handling
    max_cardinality: int = 50  # Max categories before treating as high-cardinality
    unknown_token_id: int = 0  # Token ID for unknown categories
    pad_token_id: int = -1  # Token ID for padding

    # Date handling
    date_components: List[str] = field(
        default_factory=lambda: ["year", "month", "day", "dayofweek"]
    )

    # Missing value handling
    handle_missing: str = "indicator"  # "indicator", "mean", "mode", "drop"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "num_bins": self.num_bins,
            "use_quantile_binning": self.use_quantile_binning,
            "max_cardinality": self.max_cardinality,
            "unknown_token_id": self.unknown_token_id,
            "pad_token_id": self.pad_token_id,
            "date_components": self.date_components,
            "handle_missing": self.handle_missing,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TokenizerConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class VAEConfig:
    """Configuration for the Variational Autoencoder phase.

    The VAE compresses tabular rows into a continuous latent space,
    enabling the diffusion model to operate on fixed-size vectors.
    """
    # Architecture
    latent_dim: int = 128  # Dimension of latent space
    encoder_layers: List[int] = field(default_factory=lambda: [512, 256, 128])
    decoder_layers: List[int] = field(default_factory=lambda: [128, 256, 512])
    activation: str = "gelu"  # "relu", "gelu", "silu"
    dropout: float = 0.1

    # Training
    epochs: int = 100
    batch_size: int = 512
    learning_rate: float = 1e-3
    weight_decay: float = 1e-5

    # Loss weights
    reconstruction_weight: float = 1.0
    kl_weight: float = 0.1  # Beta for KL divergence
    kl_annealing: bool = True  # Anneal KL weight during training

    # Checkpointing
    checkpoint_interval: int = 10
    early_stopping_patience: int = 10

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "latent_dim": self.latent_dim,
            "encoder_layers": self.encoder_layers,
            "decoder_layers": self.decoder_layers,
            "activation": self.activation,
            "dropout": self.dropout,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "reconstruction_weight": self.reconstruction_weight,
            "kl_weight": self.kl_weight,
            "kl_annealing": self.kl_annealing,
            "checkpoint_interval": self.checkpoint_interval,
            "early_stopping_patience": self.early_stopping_patience,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "VAEConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class DiffusionConfig:
    """Configuration for the Diffusion Transformer phase.

    The diffusion transformer learns to denoise latent vectors,
    enabling generation of new synthetic data.
    """
    # Architecture
    num_layers: int = 6
    hidden_dim: int = 256
    num_heads: int = 8
    mlp_ratio: float = 4.0
    dropout: float = 0.1

    # Diffusion process
    num_train_timesteps: int = 1000  # Total diffusion steps for training
    num_inference_steps: int = 50  # Steps for generation (DDIM)
    beta_schedule: str = "cosine"  # "linear", "cosine", "squaredcos_cap_v2"
    beta_start: float = 0.0001
    beta_end: float = 0.02
    prediction_type: str = "epsilon"  # "epsilon", "v_prediction", "sample"

    # Training
    epochs: int = 200
    batch_size: int = 256
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    warmup_steps: int = 500

    # EMA for generation
    use_ema: bool = True
    ema_decay: float = 0.9999

    # Conditioning (optional)
    use_class_conditioning: bool = False
    num_classes: int = 0

    # Checkpointing
    checkpoint_interval: int = 20
    early_stopping_patience: int = 20

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "num_layers": self.num_layers,
            "hidden_dim": self.hidden_dim,
            "num_heads": self.num_heads,
            "mlp_ratio": self.mlp_ratio,
            "dropout": self.dropout,
            "num_train_timesteps": self.num_train_timesteps,
            "num_inference_steps": self.num_inference_steps,
            "beta_schedule": self.beta_schedule,
            "beta_start": self.beta_start,
            "beta_end": self.beta_end,
            "prediction_type": self.prediction_type,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "weight_decay": self.weight_decay,
            "warmup_steps": self.warmup_steps,
            "use_ema": self.use_ema,
            "ema_decay": self.ema_decay,
            "use_class_conditioning": self.use_class_conditioning,
            "num_classes": self.num_classes,
            "checkpoint_interval": self.checkpoint_interval,
            "early_stopping_patience": self.early_stopping_patience,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DiffusionConfig":
        """Create from dictionary."""
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class TabDiTConfig:
    """Complete configuration for TabDiT synthesizer."""
    vae: VAEConfig = field(default_factory=VAEConfig)
    diffusion: DiffusionConfig = field(default_factory=DiffusionConfig)
    tokenizer: TokenizerConfig = field(default_factory=TokenizerConfig)

    # General settings
    random_seed: Optional[int] = None
    device: str = "auto"  # "auto", "cuda", "cpu"
    mixed_precision: bool = True  # Use fp16/bf16

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "vae": self.vae.to_dict(),
            "diffusion": self.diffusion.to_dict(),
            "tokenizer": self.tokenizer.to_dict(),
            "random_seed": self.random_seed,
            "device": self.device,
            "mixed_precision": self.mixed_precision,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TabDiTConfig":
        """Create from dictionary."""
        return cls(
            vae=VAEConfig.from_dict(d.get("vae", {})),
            diffusion=DiffusionConfig.from_dict(d.get("diffusion", {})),
            tokenizer=TokenizerConfig.from_dict(d.get("tokenizer", {})),
            random_seed=d.get("random_seed"),
            device=d.get("device", "auto"),
            mixed_precision=d.get("mixed_precision", True),
        )

    @classmethod
    def default(cls) -> "TabDiTConfig":
        """Create default configuration."""
        return cls()

    @classmethod
    def small(cls) -> "TabDiTConfig":
        """Create configuration for smaller datasets (<10K rows)."""
        return cls(
            vae=VAEConfig(
                latent_dim=64,
                encoder_layers=[256, 128],
                decoder_layers=[128, 256],
                epochs=50,
                batch_size=256,
            ),
            diffusion=DiffusionConfig(
                num_layers=4,
                hidden_dim=128,
                num_heads=4,
                epochs=100,
                batch_size=128,
                num_inference_steps=25,
            ),
        )

    @classmethod
    def large(cls) -> "TabDiTConfig":
        """Create configuration for larger datasets (>100K rows)."""
        return cls(
            vae=VAEConfig(
                latent_dim=256,
                encoder_layers=[1024, 512, 256],
                decoder_layers=[256, 512, 1024],
                epochs=150,
                batch_size=1024,
            ),
            diffusion=DiffusionConfig(
                num_layers=8,
                hidden_dim=512,
                num_heads=16,
                epochs=300,
                batch_size=512,
                num_inference_steps=100,
            ),
        )
