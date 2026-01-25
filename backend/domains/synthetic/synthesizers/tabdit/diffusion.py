"""Diffusion Transformer for latent space generation."""
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    nn = None

from .config import DiffusionConfig

logger = logging.getLogger(__name__)


class SinusoidalPositionEmbedding(nn.Module):
    """Sinusoidal embeddings for timestep encoding."""

    def __init__(self, dim: int):
        """Initialize embedding.

        Args:
            dim: Embedding dimension
        """
        super().__init__()
        self.dim = dim

    def forward(self, t: "torch.Tensor") -> "torch.Tensor":
        """Compute timestep embedding.

        Args:
            t: Timestep tensor of shape (batch,)

        Returns:
            Embedding tensor of shape (batch, dim)
        """
        device = t.device
        half_dim = self.dim // 2
        embeddings = math.log(10000) / (half_dim - 1)
        embeddings = torch.exp(torch.arange(half_dim, device=device) * -embeddings)
        embeddings = t[:, None] * embeddings[None, :]
        embeddings = torch.cat([torch.sin(embeddings), torch.cos(embeddings)], dim=-1)
        return embeddings


class TimestepEmbedding(nn.Module):
    """MLP for timestep embedding."""

    def __init__(self, time_dim: int, hidden_dim: int):
        """Initialize timestep embedding.

        Args:
            time_dim: Input timestep embedding dimension
            hidden_dim: Output dimension
        """
        super().__init__()
        self.mlp = nn.Sequential(
            nn.Linear(time_dim, hidden_dim),
            nn.SiLU(),
            nn.Linear(hidden_dim, hidden_dim),
        )

    def forward(self, t: "torch.Tensor") -> "torch.Tensor":
        """Forward pass."""
        return self.mlp(t)


class MLPBlock(nn.Module):
    """MLP block with GELU activation."""

    def __init__(
        self,
        hidden_dim: int,
        mlp_dim: int,
        dropout: float = 0.1,
    ):
        """Initialize MLP block.

        Args:
            hidden_dim: Input/output dimension
            mlp_dim: Hidden dimension (typically 4x hidden_dim)
            dropout: Dropout rate
        """
        super().__init__()
        self.fc1 = nn.Linear(hidden_dim, mlp_dim)
        self.fc2 = nn.Linear(mlp_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        self.act = nn.GELU()

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":
        """Forward pass."""
        x = self.fc1(x)
        x = self.act(x)
        x = self.dropout(x)
        x = self.fc2(x)
        x = self.dropout(x)
        return x


class TransformerBlock(nn.Module):
    """Transformer block with self-attention and time conditioning."""

    def __init__(
        self,
        hidden_dim: int,
        num_heads: int,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1,
    ):
        """Initialize transformer block.

        Args:
            hidden_dim: Hidden dimension
            num_heads: Number of attention heads
            mlp_ratio: MLP hidden dim ratio
            dropout: Dropout rate
        """
        super().__init__()

        self.norm1 = nn.LayerNorm(hidden_dim)
        self.attn = nn.MultiheadAttention(
            hidden_dim,
            num_heads,
            dropout=dropout,
            batch_first=True,
        )

        self.norm2 = nn.LayerNorm(hidden_dim)
        mlp_dim = int(hidden_dim * mlp_ratio)
        self.mlp = MLPBlock(hidden_dim, mlp_dim, dropout)

        # AdaLN-Zero modulation
        self.adaLN_modulation = nn.Sequential(
            nn.SiLU(),
            nn.Linear(hidden_dim, 6 * hidden_dim),
        )

    def forward(
        self,
        x: "torch.Tensor",
        t_emb: "torch.Tensor",
    ) -> "torch.Tensor":
        """Forward pass with time conditioning.

        Args:
            x: Input tensor of shape (batch, seq_len, hidden_dim)
            t_emb: Time embedding of shape (batch, hidden_dim)

        Returns:
            Output tensor of same shape as input
        """
        # Get modulation parameters (AdaLN-Zero)
        modulation = self.adaLN_modulation(t_emb)
        shift_msa, scale_msa, gate_msa, shift_mlp, scale_mlp, gate_mlp = modulation.chunk(6, dim=-1)

        # Self-attention with modulation
        x_norm = self.norm1(x)
        x_norm = x_norm * (1 + scale_msa.unsqueeze(1)) + shift_msa.unsqueeze(1)
        attn_out, _ = self.attn(x_norm, x_norm, x_norm)
        x = x + gate_msa.unsqueeze(1) * attn_out

        # MLP with modulation
        x_norm = self.norm2(x)
        x_norm = x_norm * (1 + scale_mlp.unsqueeze(1)) + shift_mlp.unsqueeze(1)
        mlp_out = self.mlp(x_norm)
        x = x + gate_mlp.unsqueeze(1) * mlp_out

        return x


class DiffusionTransformer(nn.Module):
    """Diffusion Transformer for latent space generation.

    This model learns to predict noise added to latent vectors,
    enabling iterative denoising for generation.
    """

    def __init__(
        self,
        latent_dim: int,
        config: Optional[DiffusionConfig] = None,
    ):
        """Initialize diffusion transformer.

        Args:
            latent_dim: Dimension of latent vectors (from VAE)
            config: Diffusion configuration
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for DiffusionTransformer")

        super().__init__()

        self.config = config or DiffusionConfig()
        self.latent_dim = latent_dim
        self.hidden_dim = self.config.hidden_dim

        # Input projection
        self.input_proj = nn.Linear(latent_dim, self.hidden_dim)

        # Timestep embedding
        time_dim = self.hidden_dim
        self.time_embed = nn.Sequential(
            SinusoidalPositionEmbedding(time_dim),
            TimestepEmbedding(time_dim, self.hidden_dim),
        )

        # Optional class conditioning
        self.class_embed = None
        if self.config.use_class_conditioning and self.config.num_classes > 0:
            self.class_embed = nn.Embedding(self.config.num_classes, self.hidden_dim)

        # Transformer blocks
        self.blocks = nn.ModuleList([
            TransformerBlock(
                hidden_dim=self.hidden_dim,
                num_heads=self.config.num_heads,
                mlp_ratio=self.config.mlp_ratio,
                dropout=self.config.dropout,
            )
            for _ in range(self.config.num_layers)
        ])

        # Final normalization and output
        self.final_norm = nn.LayerNorm(self.hidden_dim)
        self.output_proj = nn.Linear(self.hidden_dim, latent_dim)

        # Initialize output projection to zero (important for training stability)
        nn.init.zeros_(self.output_proj.weight)
        nn.init.zeros_(self.output_proj.bias)

    def forward(
        self,
        x: "torch.Tensor",
        t: "torch.Tensor",
        class_labels: Optional["torch.Tensor"] = None,
    ) -> "torch.Tensor":
        """Forward pass to predict noise.

        Args:
            x: Noisy latent vectors of shape (batch, latent_dim)
            t: Timesteps of shape (batch,)
            class_labels: Optional class labels of shape (batch,)

        Returns:
            Predicted noise of shape (batch, latent_dim)
        """
        # Input projection
        h = self.input_proj(x)

        # Add sequence dimension for transformer
        h = h.unsqueeze(1)  # (batch, 1, hidden_dim)

        # Time embedding
        t_emb = self.time_embed(t)  # (batch, hidden_dim)

        # Add class conditioning if provided
        if class_labels is not None and self.class_embed is not None:
            c_emb = self.class_embed(class_labels)
            t_emb = t_emb + c_emb

        # Transformer blocks
        for block in self.blocks:
            h = block(h, t_emb)

        # Final projection
        h = self.final_norm(h)
        h = h.squeeze(1)  # (batch, hidden_dim)
        output = self.output_proj(h)  # (batch, latent_dim)

        return output


class EMA:
    """Exponential Moving Average for model parameters."""

    def __init__(self, model: nn.Module, decay: float = 0.9999):
        """Initialize EMA.

        Args:
            model: Model to track
            decay: EMA decay rate
        """
        self.decay = decay
        self.shadow = {}
        self.backup = {}

        # Initialize shadow parameters
        for name, param in model.named_parameters():
            if param.requires_grad:
                self.shadow[name] = param.data.clone()

    def update(self, model: nn.Module) -> None:
        """Update shadow parameters."""
        for name, param in model.named_parameters():
            if param.requires_grad and name in self.shadow:
                self.shadow[name] = (
                    self.decay * self.shadow[name]
                    + (1 - self.decay) * param.data
                )

    def apply_shadow(self, model: nn.Module) -> None:
        """Apply shadow parameters to model."""
        for name, param in model.named_parameters():
            if param.requires_grad and name in self.shadow:
                self.backup[name] = param.data.clone()
                param.data = self.shadow[name]

    def restore(self, model: nn.Module) -> None:
        """Restore original parameters."""
        for name, param in model.named_parameters():
            if param.requires_grad and name in self.backup:
                param.data = self.backup[name]
        self.backup = {}


class DiffusionTrainer:
    """Trainer for DiffusionTransformer."""

    def __init__(
        self,
        model: DiffusionTransformer,
        scheduler: "NoiseScheduler",  # Will be imported from scheduler.py
        config: Optional[DiffusionConfig] = None,
        device: Optional[str] = None,
    ):
        """Initialize trainer.

        Args:
            model: Diffusion model to train
            scheduler: Noise scheduler
            config: Training configuration
            device: Device to train on
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for DiffusionTrainer")

        self.model = model
        self.scheduler = scheduler
        self.config = config or model.config

        # Set device
        if device == "auto" or device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.model.to(self.device)

        # Initialize optimizer
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
        )

        # Learning rate scheduler with warmup
        self.lr_scheduler = self._get_lr_scheduler()

        # EMA
        self.ema = EMA(model, self.config.ema_decay) if self.config.use_ema else None

        # Training state
        self.current_epoch = 0
        self.global_step = 0
        self.best_loss = float("inf")
        self.patience_counter = 0

    def _get_lr_scheduler(self):
        """Get learning rate scheduler with warmup."""
        def lr_lambda(step):
            if step < self.config.warmup_steps:
                return float(step) / float(max(1, self.config.warmup_steps))
            return 1.0

        return torch.optim.lr_scheduler.LambdaLR(self.optimizer, lr_lambda)

    def train_epoch(self, dataloader: DataLoader) -> Dict[str, float]:
        """Train for one epoch.

        Args:
            dataloader: Training data loader (latent vectors)

        Returns:
            Dict of average metrics
        """
        self.model.train()

        total_loss = 0.0
        num_batches = 0

        for batch in dataloader:
            latents = batch[0].to(self.device)
            batch_size = latents.shape[0]

            # Sample random timesteps
            t = torch.randint(
                0, self.config.num_train_timesteps,
                (batch_size,),
                device=self.device,
                dtype=torch.long,
            )

            # Sample noise
            noise = torch.randn_like(latents)

            # Add noise to latents
            noisy_latents = self.scheduler.add_noise(latents, noise, t)

            # Predict noise
            noise_pred = self.model(noisy_latents, t.float())

            # Compute loss
            loss = F.mse_loss(noise_pred, noise)

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()
            self.lr_scheduler.step()

            # Update EMA
            if self.ema is not None:
                self.ema.update(self.model)

            total_loss += loss.item()
            num_batches += 1
            self.global_step += 1

        self.current_epoch += 1

        return {
            "loss": total_loss / num_batches,
            "lr": self.optimizer.param_groups[0]["lr"],
        }

    def validate(self, dataloader: DataLoader) -> Dict[str, float]:
        """Validate model.

        Args:
            dataloader: Validation data loader

        Returns:
            Dict of average metrics
        """
        self.model.eval()

        # Use EMA parameters for validation
        if self.ema is not None:
            self.ema.apply_shadow(self.model)

        total_loss = 0.0
        num_batches = 0

        with torch.no_grad():
            for batch in dataloader:
                latents = batch[0].to(self.device)
                batch_size = latents.shape[0]

                t = torch.randint(
                    0, self.config.num_train_timesteps,
                    (batch_size,),
                    device=self.device,
                    dtype=torch.long,
                )

                noise = torch.randn_like(latents)
                noisy_latents = self.scheduler.add_noise(latents, noise, t)
                noise_pred = self.model(noisy_latents, t.float())

                loss = F.mse_loss(noise_pred, noise)
                total_loss += loss.item()
                num_batches += 1

        # Restore original parameters
        if self.ema is not None:
            self.ema.restore(self.model)

        return {"loss": total_loss / num_batches}

    def train(
        self,
        train_data: np.ndarray,
        val_data: Optional[np.ndarray] = None,
        checkpoint_dir: Optional[str] = None,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """Full training loop.

        Args:
            train_data: Training latent vectors
            val_data: Optional validation latents
            checkpoint_dir: Directory to save checkpoints
            progress_callback: Optional progress callback

        Returns:
            Dict with training history
        """
        # Create data loaders
        train_tensor = torch.FloatTensor(train_data)
        train_dataset = TensorDataset(train_tensor)
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            drop_last=True,
        )

        val_loader = None
        if val_data is not None:
            val_tensor = torch.FloatTensor(val_data)
            val_dataset = TensorDataset(val_tensor)
            val_loader = DataLoader(
                val_dataset,
                batch_size=self.config.batch_size,
                shuffle=False,
            )

        history = {
            "train_loss": [],
            "val_loss": [],
            "lr": [],
        }

        if checkpoint_dir:
            Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)

        for epoch in range(self.config.epochs):
            # Train
            train_metrics = self.train_epoch(train_loader)
            history["train_loss"].append(train_metrics["loss"])
            history["lr"].append(train_metrics["lr"])

            # Validate
            val_loss = None
            if val_loader:
                val_metrics = self.validate(val_loader)
                val_loss = val_metrics["loss"]
                history["val_loss"].append(val_loss)

            # Progress callback
            if progress_callback:
                progress_callback(
                    epoch=epoch,
                    total_epochs=self.config.epochs,
                    train_loss=train_metrics["loss"],
                    val_loss=val_loss,
                )

            # Logging
            if epoch % 10 == 0:
                logger.info(
                    f"Epoch {epoch}/{self.config.epochs} - "
                    f"Loss: {train_metrics['loss']:.6f}, "
                    f"LR: {train_metrics['lr']:.6f}"
                )

            # Checkpointing
            if checkpoint_dir and (epoch + 1) % self.config.checkpoint_interval == 0:
                self.save_checkpoint(
                    Path(checkpoint_dir) / f"checkpoint_epoch_{epoch + 1}.pt"
                )

            # Early stopping
            current_loss = val_loss if val_loss else train_metrics["loss"]
            if current_loss < self.best_loss:
                self.best_loss = current_loss
                self.patience_counter = 0
                if checkpoint_dir:
                    self.save_checkpoint(Path(checkpoint_dir) / "best.pt")
            else:
                self.patience_counter += 1
                if self.patience_counter >= self.config.early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch}")
                    break

        # Save final checkpoint
        if checkpoint_dir:
            self.save_checkpoint(Path(checkpoint_dir) / "final.pt")

        return {
            "history": history,
            "final_epoch": self.current_epoch,
            "best_loss": self.best_loss,
        }

    def save_checkpoint(self, path: Union[str, Path]) -> None:
        """Save model checkpoint.

        Args:
            path: Path to save checkpoint
        """
        state = {
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "lr_scheduler_state_dict": self.lr_scheduler.state_dict(),
            "config": self.config.to_dict(),
            "epoch": self.current_epoch,
            "global_step": self.global_step,
            "best_loss": self.best_loss,
            "latent_dim": self.model.latent_dim,
        }

        if self.ema is not None:
            state["ema_shadow"] = self.ema.shadow

        torch.save(state, path)
        logger.info(f"Saved diffusion checkpoint to {path}")

    def load_checkpoint(self, path: Union[str, Path]) -> None:
        """Load model checkpoint.

        Args:
            path: Path to checkpoint
        """
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.lr_scheduler.load_state_dict(checkpoint["lr_scheduler_state_dict"])
        self.current_epoch = checkpoint.get("epoch", 0)
        self.global_step = checkpoint.get("global_step", 0)
        self.best_loss = checkpoint.get("best_loss", float("inf"))

        if self.ema is not None and "ema_shadow" in checkpoint:
            self.ema.shadow = checkpoint["ema_shadow"]

        logger.info(f"Loaded diffusion checkpoint from {path}")


def load_diffusion_from_checkpoint(
    path: Union[str, Path],
    device: Optional[str] = None,
    use_ema: bool = True,
) -> DiffusionTransformer:
    """Load diffusion model from checkpoint.

    Args:
        path: Path to checkpoint
        device: Device to load to
        use_ema: Whether to load EMA parameters

    Returns:
        Loaded diffusion model
    """
    if not TORCH_AVAILABLE:
        raise RuntimeError("PyTorch is required to load diffusion checkpoint")

    if device == "auto" or device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(device)

    checkpoint = torch.load(path, map_location=device)

    config = DiffusionConfig.from_dict(checkpoint["config"])
    model = DiffusionTransformer(
        latent_dim=checkpoint["latent_dim"],
        config=config,
    )

    if use_ema and "ema_shadow" in checkpoint:
        # Load EMA parameters
        for name, param in model.named_parameters():
            if name in checkpoint["ema_shadow"]:
                param.data = checkpoint["ema_shadow"][name].to(device)
    else:
        model.load_state_dict(checkpoint["model_state_dict"])

    model.to(device)
    model.eval()

    return model
