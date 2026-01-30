"""Variational Autoencoder for tabular data."""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, TYPE_CHECKING

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
    F = None
    DataLoader = None
    TensorDataset = None

from .config import VAEConfig

logger = logging.getLogger(__name__)


if TORCH_AVAILABLE:
    def get_activation(name: str) -> "nn.Module":
        """Get activation function by name."""
        activations = {
            "relu": nn.ReLU(),
            "gelu": nn.GELU(),
            "silu": nn.SiLU(),
            "tanh": nn.Tanh(),
            "leaky_relu": nn.LeakyReLU(0.1),
        }
        return activations.get(name, nn.GELU())

    class Encoder(nn.Module):
        """VAE Encoder network."""

        def __init__(
            self,
            input_dim: int,
            latent_dim: int,
            hidden_layers: List[int],
            activation: str = "gelu",
            dropout: float = 0.1,
        ):
            """Initialize encoder.

            Args:
                input_dim: Input feature dimension
                latent_dim: Latent space dimension
                hidden_layers: List of hidden layer sizes
                activation: Activation function name
                dropout: Dropout rate
            """
            super().__init__()

            layers = []
            prev_dim = input_dim

            for hidden_dim in hidden_layers:
                layers.extend([
                    nn.Linear(prev_dim, hidden_dim),
                    nn.LayerNorm(hidden_dim),
                    get_activation(activation),
                    nn.Dropout(dropout),
                ])
                prev_dim = hidden_dim

            self.encoder = nn.Sequential(*layers)

            # Separate heads for mean and log variance
            self.fc_mu = nn.Linear(prev_dim, latent_dim)
            self.fc_logvar = nn.Linear(prev_dim, latent_dim)

        def forward(self, x: "torch.Tensor") -> Tuple["torch.Tensor", "torch.Tensor"]:
            """Forward pass.

            Args:
                x: Input tensor of shape (batch, input_dim)

            Returns:
                Tuple of (mu, logvar) each of shape (batch, latent_dim)
            """
            h = self.encoder(x)
            mu = self.fc_mu(h)
            logvar = self.fc_logvar(h)
            return mu, logvar

    class Decoder(nn.Module):
        """VAE Decoder network."""

        def __init__(
            self,
            latent_dim: int,
            output_dim: int,
            hidden_layers: List[int],
            activation: str = "gelu",
            dropout: float = 0.1,
        ):
            """Initialize decoder.

            Args:
                latent_dim: Latent space dimension
                output_dim: Output feature dimension
                hidden_layers: List of hidden layer sizes
                activation: Activation function name
                dropout: Dropout rate
            """
            super().__init__()

            layers = []
            prev_dim = latent_dim

            for hidden_dim in hidden_layers:
                layers.extend([
                    nn.Linear(prev_dim, hidden_dim),
                    nn.LayerNorm(hidden_dim),
                    get_activation(activation),
                    nn.Dropout(dropout),
                ])
                prev_dim = hidden_dim

            # Final output layer (no activation for reconstruction)
            layers.append(nn.Linear(prev_dim, output_dim))

            self.decoder = nn.Sequential(*layers)

        def forward(self, z: "torch.Tensor") -> "torch.Tensor":
            """Forward pass.

            Args:
                z: Latent tensor of shape (batch, latent_dim)

            Returns:
                Reconstructed tensor of shape (batch, output_dim)
            """
            return self.decoder(z)

    class TabularVAE(nn.Module):
        """Variational Autoencoder for tabular data.

        The VAE learns a continuous latent representation of tabular rows,
        enabling the diffusion model to operate in a fixed-dimensional space.
        """

        def __init__(
            self,
            input_dim: int,
            config: Optional[VAEConfig] = None,
        ):
            """Initialize VAE.

            Args:
                input_dim: Dimension of tokenized input
                config: VAE configuration
            """
            super().__init__()

            self.config = config or VAEConfig()
            self.input_dim = input_dim
            self.latent_dim = self.config.latent_dim

            self.encoder = Encoder(
                input_dim=input_dim,
                latent_dim=self.config.latent_dim,
                hidden_layers=self.config.encoder_layers,
                activation=self.config.activation,
                dropout=self.config.dropout,
            )

            self.decoder = Decoder(
                latent_dim=self.config.latent_dim,
                output_dim=input_dim,
                hidden_layers=self.config.decoder_layers,
                activation=self.config.activation,
                dropout=self.config.dropout,
            )

        def encode(self, x: "torch.Tensor") -> Tuple["torch.Tensor", "torch.Tensor"]:
            """Encode input to latent distribution.

            Args:
                x: Input tensor of shape (batch, input_dim)

            Returns:
                Tuple of (mu, logvar) each of shape (batch, latent_dim)
            """
            return self.encoder(x)

        def reparameterize(
            self,
            mu: "torch.Tensor",
            logvar: "torch.Tensor",
        ) -> "torch.Tensor":
            """Reparameterization trick for sampling.

            Args:
                mu: Mean of latent distribution
                logvar: Log variance of latent distribution

            Returns:
                Sampled latent vector
            """
            std = torch.exp(0.5 * logvar)
            eps = torch.randn_like(std)
            return mu + eps * std

        def decode(self, z: "torch.Tensor") -> "torch.Tensor":
            """Decode latent to reconstruction.

            Args:
                z: Latent tensor of shape (batch, latent_dim)

            Returns:
                Reconstructed tensor of shape (batch, input_dim)
            """
            return self.decoder(z)

        def forward(
            self,
            x: "torch.Tensor",
        ) -> Tuple["torch.Tensor", "torch.Tensor", "torch.Tensor"]:
            """Forward pass through VAE.

            Args:
                x: Input tensor of shape (batch, input_dim)

            Returns:
                Tuple of (reconstruction, mu, logvar)
            """
            mu, logvar = self.encode(x)
            z = self.reparameterize(mu, logvar)
            recon = self.decode(z)
            return recon, mu, logvar

        def sample(
            self,
            num_samples: int,
            device: Optional["torch.device"] = None,
        ) -> "torch.Tensor":
            """Sample from prior and decode.

            Args:
                num_samples: Number of samples to generate
                device: Device to generate on

            Returns:
                Decoded samples of shape (num_samples, input_dim)
            """
            device = device or next(self.parameters()).device
            z = torch.randn(num_samples, self.latent_dim, device=device)
            return self.decode(z)

        def encode_to_latent(
            self,
            x: "torch.Tensor",
            use_mean: bool = True,
        ) -> "torch.Tensor":
            """Encode input to latent vectors.

            Args:
                x: Input tensor
                use_mean: If True, return mu; otherwise sample

            Returns:
                Latent vectors of shape (batch, latent_dim)
            """
            mu, logvar = self.encode(x)
            if use_mean:
                return mu
            else:
                return self.reparameterize(mu, logvar)

    class VAELoss:
        """VAE loss function with KL annealing."""

        def __init__(
            self,
            reconstruction_weight: float = 1.0,
            kl_weight: float = 0.1,
            kl_annealing: bool = True,
            kl_anneal_epochs: int = 20,
        ):
            """Initialize loss function.

            Args:
                reconstruction_weight: Weight for reconstruction loss
                kl_weight: Weight for KL divergence
                kl_annealing: Whether to anneal KL weight
                kl_anneal_epochs: Number of epochs for KL annealing
            """
            self.reconstruction_weight = reconstruction_weight
            self.kl_weight = kl_weight
            self.kl_annealing = kl_annealing
            self.kl_anneal_epochs = kl_anneal_epochs
            self._current_epoch = 0

        def set_epoch(self, epoch: int) -> None:
            """Set current epoch for KL annealing."""
            self._current_epoch = epoch

        def get_kl_weight(self) -> float:
            """Get current KL weight with annealing."""
            if not self.kl_annealing:
                return self.kl_weight

            # Linear annealing from 0 to kl_weight
            progress = min(1.0, self._current_epoch / self.kl_anneal_epochs)
            return self.kl_weight * progress

        def __call__(
            self,
            recon: "torch.Tensor",
            target: "torch.Tensor",
            mu: "torch.Tensor",
            logvar: "torch.Tensor",
        ) -> Tuple["torch.Tensor", Dict[str, float]]:
            """Compute VAE loss.

            Args:
                recon: Reconstructed tensor
                target: Target tensor
                mu: Latent mean
                logvar: Latent log variance

            Returns:
                Tuple of (total_loss, metrics_dict)
            """
            # Reconstruction loss (MSE)
            recon_loss = F.mse_loss(recon, target, reduction="mean")

            # KL divergence: -0.5 * sum(1 + log(sigma^2) - mu^2 - sigma^2)
            kl_loss = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())

            # Current KL weight
            kl_w = self.get_kl_weight()

            # Total loss
            total_loss = (
                self.reconstruction_weight * recon_loss
                + kl_w * kl_loss
            )

            metrics = {
                "total_loss": total_loss.item(),
                "recon_loss": recon_loss.item(),
                "kl_loss": kl_loss.item(),
                "kl_weight": kl_w,
            }

            return total_loss, metrics

    class VAETrainer:
        """Trainer for TabularVAE."""

        def __init__(
            self,
            model: TabularVAE,
            config: Optional[VAEConfig] = None,
            device: Optional[str] = None,
        ):
            """Initialize trainer.

            Args:
                model: VAE model to train
                config: Training configuration
                device: Device to train on ("cuda", "cpu", or "auto")
            """
            self.model = model
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

            # Initialize loss function
            self.loss_fn = VAELoss(
                reconstruction_weight=self.config.reconstruction_weight,
                kl_weight=self.config.kl_weight,
                kl_annealing=self.config.kl_annealing,
            )

            # Training state
            self.current_epoch = 0
            self.best_loss = float("inf")
            self.patience_counter = 0

        def train_epoch(self, dataloader: DataLoader) -> Dict[str, float]:
            """Train for one epoch.

            Args:
                dataloader: Training data loader

            Returns:
                Dict of average metrics for epoch
            """
            self.model.train()
            self.loss_fn.set_epoch(self.current_epoch)

            total_metrics = {
                "total_loss": 0.0,
                "recon_loss": 0.0,
                "kl_loss": 0.0,
            }
            num_batches = 0

            for batch in dataloader:
                x = batch[0].to(self.device)

                # Forward pass
                recon, mu, logvar = self.model(x)

                # Compute loss
                loss, metrics = self.loss_fn(recon, x, mu, logvar)

                # Backward pass
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                self.optimizer.step()

                # Accumulate metrics
                for key in total_metrics:
                    total_metrics[key] += metrics.get(key, 0.0)
                num_batches += 1

            # Average metrics
            for key in total_metrics:
                total_metrics[key] /= num_batches

            self.current_epoch += 1
            return total_metrics

        def validate(self, dataloader: DataLoader) -> Dict[str, float]:
            """Validate model.

            Args:
                dataloader: Validation data loader

            Returns:
                Dict of average metrics
            """
            self.model.eval()

            total_metrics = {
                "total_loss": 0.0,
                "recon_loss": 0.0,
                "kl_loss": 0.0,
            }
            num_batches = 0

            with torch.no_grad():
                for batch in dataloader:
                    x = batch[0].to(self.device)

                    recon, mu, logvar = self.model(x)
                    _, metrics = self.loss_fn(recon, x, mu, logvar)

                    for key in total_metrics:
                        total_metrics[key] += metrics.get(key, 0.0)
                    num_batches += 1

            for key in total_metrics:
                total_metrics[key] /= num_batches

            return total_metrics

        def train(
            self,
            train_data: np.ndarray,
            val_data: Optional[np.ndarray] = None,
            checkpoint_dir: Optional[str] = None,
            progress_callback: Optional[callable] = None,
        ) -> Dict[str, Any]:
            """Full training loop.

            Args:
                train_data: Training data array
                val_data: Optional validation data
                checkpoint_dir: Directory to save checkpoints
                progress_callback: Optional callback for progress updates

            Returns:
                Dict with training history and final metrics
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
                "recon_loss": [],
                "kl_loss": [],
            }

            if checkpoint_dir:
                Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)

            for epoch in range(self.config.epochs):
                # Train
                train_metrics = self.train_epoch(train_loader)
                history["train_loss"].append(train_metrics["total_loss"])
                history["recon_loss"].append(train_metrics["recon_loss"])
                history["kl_loss"].append(train_metrics["kl_loss"])

                # Validate
                val_loss = None
                if val_loader:
                    val_metrics = self.validate(val_loader)
                    val_loss = val_metrics["total_loss"]
                    history["val_loss"].append(val_loss)

                # Progress callback
                if progress_callback:
                    progress_callback(
                        epoch=epoch,
                        total_epochs=self.config.epochs,
                        train_loss=train_metrics["total_loss"],
                        val_loss=val_loss,
                    )

                # Logging
                if epoch % 10 == 0:
                    logger.info(
                        f"Epoch {epoch}/{self.config.epochs} - "
                        f"Loss: {train_metrics['total_loss']:.4f} "
                        f"(recon: {train_metrics['recon_loss']:.4f}, "
                        f"kl: {train_metrics['kl_loss']:.4f})"
                    )

                # Checkpointing
                if checkpoint_dir and (epoch + 1) % self.config.checkpoint_interval == 0:
                    self.save_checkpoint(
                        Path(checkpoint_dir) / f"checkpoint_epoch_{epoch + 1}.pt"
                    )

                # Early stopping
                current_loss = val_loss if val_loss else train_metrics["total_loss"]
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
            torch.save({
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "config": self.config.to_dict(),
                "epoch": self.current_epoch,
                "best_loss": self.best_loss,
                "input_dim": self.model.input_dim,
                "latent_dim": self.model.latent_dim,
            }, path)
            logger.info(f"Saved VAE checkpoint to {path}")

        def load_checkpoint(self, path: Union[str, Path]) -> None:
            """Load model checkpoint.

            Args:
                path: Path to checkpoint
            """
            checkpoint = torch.load(path, map_location=self.device)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            self.current_epoch = checkpoint.get("epoch", 0)
            self.best_loss = checkpoint.get("best_loss", float("inf"))
            logger.info(f"Loaded VAE checkpoint from {path}")

    def load_vae_from_checkpoint(
        path: Union[str, Path],
        device: Optional[str] = None,
    ) -> TabularVAE:
        """Load VAE model from checkpoint.

        Args:
            path: Path to checkpoint
            device: Device to load to

        Returns:
            Loaded VAE model
        """
        if device == "auto" or device is None:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            device = torch.device(device)

        checkpoint = torch.load(path, map_location=device)

        config = VAEConfig.from_dict(checkpoint["config"])
        model = TabularVAE(
            input_dim=checkpoint["input_dim"],
            config=config,
        )
        model.load_state_dict(checkpoint["model_state_dict"])
        model.to(device)
        model.eval()

        return model

else:
    # PyTorch not available - provide placeholder classes that raise helpful errors
    def get_activation(name: str):
        raise RuntimeError("PyTorch is required for VAE operations. Install with: pip install torch")

    class Encoder:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("PyTorch is required for VAE operations. Install with: pip install torch")

    class Decoder:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("PyTorch is required for VAE operations. Install with: pip install torch")

    class TabularVAE:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("PyTorch is required for VAE operations. Install with: pip install torch")

    class VAELoss:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("PyTorch is required for VAE operations. Install with: pip install torch")

    class VAETrainer:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("PyTorch is required for VAE operations. Install with: pip install torch")

    def load_vae_from_checkpoint(*args, **kwargs):
        raise RuntimeError("PyTorch is required for VAE operations. Install with: pip install torch")
