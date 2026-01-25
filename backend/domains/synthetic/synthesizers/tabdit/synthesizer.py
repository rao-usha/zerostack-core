"""TabDiT Synthesizer - Tabular Diffusion Transformer for synthetic data."""
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

from ..base import SynthesizerResult
from ..multi_phase_base import (
    MultiPhaseSynthesizer,
    TrainingPhase,
    PhaseResult,
)
from .config import TabDiTConfig, VAEConfig, DiffusionConfig
from .tokenizer import TabularTokenizer
from .vae import TabularVAE, VAETrainer, load_vae_from_checkpoint
from .diffusion import DiffusionTransformer, DiffusionTrainer, load_diffusion_from_checkpoint
from .scheduler import DDIMScheduler, create_scheduler

logger = logging.getLogger(__name__)


class TabDiTSynthesizer(MultiPhaseSynthesizer):
    """Tabular Diffusion Transformer synthesizer.

    TabDiT combines a Variational Autoencoder (VAE) with a Diffusion Transformer
    for high-quality synthetic tabular data generation.

    Training phases:
    1. VAE Training: Learn to compress tabular rows into latent vectors
    2. Diffusion Training: Learn to generate latent vectors via denoising

    Generation:
    1. Sample random noise
    2. Denoise using the diffusion model (50 steps)
    3. Decode latent vectors to tabular rows using VAE decoder
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize TabDiT synthesizer.

        Args:
            config: Configuration dict or TabDiTConfig fields
        """
        super().__init__(config)

        # Parse configuration
        if isinstance(config, dict):
            self._tabdit_config = TabDiTConfig.from_dict(config)
        else:
            self._tabdit_config = TabDiTConfig()

        # Models (initialized during training)
        self._tokenizer: Optional[TabularTokenizer] = None
        self._vae: Optional[TabularVAE] = None
        self._diffusion: Optional[DiffusionTransformer] = None
        self._scheduler: Optional[DDIMScheduler] = None

        # Device
        self._device = None

    @property
    def name(self) -> str:
        """Human-readable synthesizer name."""
        return "TabDiT (Tabular Diffusion Transformer)"

    @property
    def synthesizer_type(self) -> str:
        """Synthesizer type identifier."""
        return "tabdit"

    @property
    def training_phases(self) -> List[TrainingPhase]:
        """Return ordered list of training phases."""
        return [TrainingPhase.PHASE_1, TrainingPhase.PHASE_2]

    @property
    def tabdit_config(self) -> TabDiTConfig:
        """Get TabDiT configuration."""
        return self._tabdit_config

    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        """Get information about this synthesizer."""
        return {
            "id": "tabdit",
            "name": "TabDiT (Tabular Diffusion Transformer)",
            "description": (
                "State-of-the-art diffusion-based synthesizer. "
                "Combines VAE compression with diffusion transformer generation. "
                "Best quality but requires GPU training."
            ),
            "speed": "slow",
            "quality": "excellent",
            "gpu_required": True,
            "best_for": [
                "High-quality synthetic data",
                "Complex distributions",
                "Large datasets",
                "When training time is not a constraint",
            ],
            "config_schema": {
                "vae_epochs": {"type": "integer", "default": 100, "min": 10, "max": 500},
                "vae_latent_dim": {"type": "integer", "default": 128, "min": 32, "max": 512},
                "diffusion_epochs": {"type": "integer", "default": 200, "min": 50, "max": 1000},
                "diffusion_layers": {"type": "integer", "default": 6, "min": 2, "max": 12},
                "inference_steps": {"type": "integer", "default": 50, "min": 10, "max": 200},
            },
        }

    def _setup_device(self) -> "torch.device":
        """Setup compute device."""
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for TabDiT")

        if self._device is not None:
            return self._device

        device_str = self._tabdit_config.device
        if device_str == "auto":
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self._device = torch.device(device_str)

        logger.info(f"Using device: {self._device}")
        return self._device

    async def train_phase(
        self,
        phase: TrainingPhase,
        data: pd.DataFrame,
        checkpoint_dir: str,
        resume_from: Optional[str] = None,
        progress_callback: Optional[callable] = None,
    ) -> PhaseResult:
        """Train a single phase.

        Args:
            phase: PHASE_1 (VAE) or PHASE_2 (Diffusion)
            data: Training data
            checkpoint_dir: Directory to save checkpoints
            resume_from: Optional checkpoint to resume from
            progress_callback: Optional progress callback

        Returns:
            PhaseResult with checkpoint path and metrics
        """
        if phase == TrainingPhase.PHASE_1:
            return await self._train_vae(data, checkpoint_dir, resume_from, progress_callback)
        elif phase == TrainingPhase.PHASE_2:
            return await self._train_diffusion(data, checkpoint_dir, resume_from, progress_callback)
        else:
            raise ValueError(f"Unknown phase: {phase}")

    async def _train_vae(
        self,
        data: pd.DataFrame,
        checkpoint_dir: str,
        resume_from: Optional[str] = None,
        progress_callback: Optional[callable] = None,
    ) -> PhaseResult:
        """Train VAE phase.

        Args:
            data: Training data
            checkpoint_dir: Checkpoint directory
            resume_from: Checkpoint to resume from
            progress_callback: Progress callback

        Returns:
            PhaseResult
        """
        try:
            self._setup_device()
            checkpoint_dir = Path(checkpoint_dir)
            checkpoint_dir.mkdir(parents=True, exist_ok=True)

            # Initialize tokenizer
            logger.info("Fitting tokenizer...")
            self._tokenizer = TabularTokenizer(self._tabdit_config.tokenizer)
            self._tokenizer.fit(data)
            self._tokenizer.save(checkpoint_dir / "tokenizer.json")

            # Transform data
            logger.info("Tokenizing data...")
            train_data = self._tokenizer.transform(data)

            # Split for validation
            val_split = 0.1
            n_val = int(len(train_data) * val_split)
            indices = np.random.permutation(len(train_data))
            val_data = train_data[indices[:n_val]]
            train_data = train_data[indices[n_val:]]

            # Initialize VAE
            logger.info(f"Initializing VAE with input_dim={self._tokenizer.input_dim}")
            self._vae = TabularVAE(
                input_dim=self._tokenizer.input_dim,
                config=self._tabdit_config.vae,
            )

            # Initialize trainer
            trainer = VAETrainer(
                model=self._vae,
                config=self._tabdit_config.vae,
                device=self._tabdit_config.device,
            )

            # Resume if checkpoint provided
            if resume_from:
                trainer.load_checkpoint(resume_from)
                logger.info(f"Resumed from {resume_from}")

            # Train
            logger.info(f"Starting VAE training for {self._tabdit_config.vae.epochs} epochs")
            result = trainer.train(
                train_data=train_data,
                val_data=val_data,
                checkpoint_dir=str(checkpoint_dir),
                progress_callback=progress_callback,
            )

            # Save final checkpoint path
            checkpoint_path = str(checkpoint_dir / "best.pt")

            return PhaseResult(
                phase=TrainingPhase.PHASE_1,
                success=True,
                checkpoint_path=checkpoint_path,
                metrics={
                    "final_loss": result["history"]["train_loss"][-1],
                    "best_loss": result["best_loss"],
                    "epochs_completed": result["final_epoch"],
                    "recon_loss": result["history"]["recon_loss"][-1],
                    "kl_loss": result["history"]["kl_loss"][-1],
                },
                epochs_completed=result["final_epoch"],
            )

        except Exception as e:
            logger.error(f"VAE training failed: {e}")
            return PhaseResult(
                phase=TrainingPhase.PHASE_1,
                success=False,
                error_message=str(e),
            )

    async def _train_diffusion(
        self,
        data: pd.DataFrame,
        checkpoint_dir: str,
        resume_from: Optional[str] = None,
        progress_callback: Optional[callable] = None,
    ) -> PhaseResult:
        """Train diffusion phase.

        Args:
            data: Training data
            checkpoint_dir: Checkpoint directory
            resume_from: Checkpoint to resume from
            progress_callback: Progress callback

        Returns:
            PhaseResult
        """
        try:
            self._setup_device()
            checkpoint_dir = Path(checkpoint_dir)
            checkpoint_dir.mkdir(parents=True, exist_ok=True)

            # Load VAE if not already loaded
            if self._vae is None:
                vae_checkpoint = self._phase_checkpoints.get(TrainingPhase.PHASE_1)
                if not vae_checkpoint:
                    raise RuntimeError("VAE must be trained before diffusion")

                self._vae = load_vae_from_checkpoint(vae_checkpoint, self._tabdit_config.device)
                logger.info(f"Loaded VAE from {vae_checkpoint}")

            # Load tokenizer if not loaded
            if self._tokenizer is None:
                vae_dir = Path(self._phase_checkpoints[TrainingPhase.PHASE_1]).parent
                tokenizer_path = vae_dir / "tokenizer.json"
                self._tokenizer = TabularTokenizer.load(tokenizer_path)
                logger.info(f"Loaded tokenizer from {tokenizer_path}")

            # Transform data and encode to latent space
            logger.info("Encoding data to latent space...")
            train_data = self._tokenizer.transform(data)
            train_tensor = torch.FloatTensor(train_data).to(self._device)

            self._vae.eval()
            with torch.no_grad():
                latents = self._vae.encode_to_latent(train_tensor, use_mean=False)
                latents = latents.cpu().numpy()

            # Split for validation
            val_split = 0.1
            n_val = int(len(latents) * val_split)
            indices = np.random.permutation(len(latents))
            val_latents = latents[indices[:n_val]]
            train_latents = latents[indices[n_val:]]

            # Initialize diffusion model
            logger.info(f"Initializing DiffusionTransformer with latent_dim={self._vae.latent_dim}")
            self._diffusion = DiffusionTransformer(
                latent_dim=self._vae.latent_dim,
                config=self._tabdit_config.diffusion,
            )

            # Initialize scheduler
            self._scheduler = create_scheduler(self._tabdit_config.diffusion)

            # Initialize trainer
            trainer = DiffusionTrainer(
                model=self._diffusion,
                scheduler=self._scheduler,
                config=self._tabdit_config.diffusion,
                device=self._tabdit_config.device,
            )

            # Resume if checkpoint provided
            if resume_from:
                trainer.load_checkpoint(resume_from)
                logger.info(f"Resumed from {resume_from}")

            # Train
            logger.info(f"Starting diffusion training for {self._tabdit_config.diffusion.epochs} epochs")
            result = trainer.train(
                train_data=train_latents,
                val_data=val_latents,
                checkpoint_dir=str(checkpoint_dir),
                progress_callback=progress_callback,
            )

            # Save final checkpoint path
            checkpoint_path = str(checkpoint_dir / "best.pt")

            return PhaseResult(
                phase=TrainingPhase.PHASE_2,
                success=True,
                checkpoint_path=checkpoint_path,
                metrics={
                    "final_loss": result["history"]["train_loss"][-1],
                    "best_loss": result["best_loss"],
                    "epochs_completed": result["final_epoch"],
                },
                epochs_completed=result["final_epoch"],
            )

        except Exception as e:
            logger.error(f"Diffusion training failed: {e}")
            return PhaseResult(
                phase=TrainingPhase.PHASE_2,
                success=False,
                error_message=str(e),
            )

    def load_checkpoint(self, phase: TrainingPhase, checkpoint_path: str) -> None:
        """Load a checkpoint for a specific phase.

        Args:
            phase: The phase this checkpoint is for
            checkpoint_path: Path to checkpoint file
        """
        self._setup_device()

        if phase == TrainingPhase.PHASE_1:
            self._vae = load_vae_from_checkpoint(checkpoint_path, self._tabdit_config.device)

            # Also load tokenizer
            tokenizer_path = Path(checkpoint_path).parent / "tokenizer.json"
            if tokenizer_path.exists():
                self._tokenizer = TabularTokenizer.load(tokenizer_path)

            self._phase_checkpoints[phase] = checkpoint_path
            logger.info(f"Loaded VAE checkpoint from {checkpoint_path}")

        elif phase == TrainingPhase.PHASE_2:
            self._diffusion = load_diffusion_from_checkpoint(
                checkpoint_path,
                device=self._tabdit_config.device,
                use_ema=self._tabdit_config.diffusion.use_ema,
            )
            self._scheduler = create_scheduler(self._tabdit_config.diffusion)
            self._phase_checkpoints[phase] = checkpoint_path
            self._fitted = True
            logger.info(f"Loaded diffusion checkpoint from {checkpoint_path}")

    def sample(self, num_rows: int) -> SynthesizerResult:
        """Generate synthetic data.

        Args:
            num_rows: Number of rows to generate

        Returns:
            SynthesizerResult with synthetic data
        """
        self._validate_fitted()

        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for sampling")

        start_time = time.time()
        self._setup_device()

        # Ensure models are loaded
        if self._vae is None or self._diffusion is None or self._tokenizer is None:
            raise RuntimeError(
                "Models not loaded. Call load_checkpoint() for both phases first."
            )

        self._vae.eval()
        self._diffusion.eval()

        # Set inference steps
        self._scheduler.set_timesteps(self._tabdit_config.diffusion.num_inference_steps)

        # Generate in batches
        batch_size = self._tabdit_config.diffusion.batch_size
        all_samples = []

        with torch.no_grad():
            for start_idx in range(0, num_rows, batch_size):
                batch_num = min(batch_size, num_rows - start_idx)

                # Sample random noise
                latents = torch.randn(
                    batch_num,
                    self._vae.latent_dim,
                    device=self._device,
                )

                # Iterative denoising
                for t in self._scheduler.timesteps:
                    t_batch = torch.full(
                        (batch_num,),
                        t.item(),
                        device=self._device,
                        dtype=torch.float,
                    )

                    # Predict noise
                    noise_pred = self._diffusion(latents, t_batch)

                    # Denoise step
                    latents, _ = self._scheduler.step(
                        noise_pred,
                        t.item(),
                        latents,
                        eta=0.0,  # DDIM deterministic
                    )

                # Decode latents to tabular features
                decoded = self._vae.decode(latents)
                all_samples.append(decoded.cpu().numpy())

        # Concatenate all batches
        all_samples = np.concatenate(all_samples, axis=0)

        # Inverse transform to DataFrame
        synthetic_df = self._tokenizer.inverse_transform(all_samples)

        # Post-process
        synthetic_df = self._post_process(synthetic_df)

        sample_time = time.time() - start_time

        return SynthesizerResult(
            synthetic_data=synthetic_df,
            metadata={
                "synthesizer": self.synthesizer_type,
                "num_inference_steps": self._tabdit_config.diffusion.num_inference_steps,
                "latent_dim": self._vae.latent_dim,
            },
            sample_time_seconds=sample_time,
        )

    def save(self, path: Union[str, Path]) -> None:
        """Save synthesizer to directory.

        Args:
            path: Directory to save to
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save state
        state = self.get_state()
        state["tabdit_config"] = self._tabdit_config.to_dict()

        with open(path / "state.json", "w") as f:
            json.dump(state, f, indent=2)

        # Copy checkpoints if they exist
        if self._tokenizer is not None:
            self._tokenizer.save(path / "tokenizer.json")

        logger.info(f"Saved TabDiT synthesizer to {path}")

    @classmethod
    def load(cls, path: Union[str, Path]) -> "TabDiTSynthesizer":
        """Load synthesizer from directory.

        Args:
            path: Directory to load from

        Returns:
            Loaded synthesizer
        """
        path = Path(path)

        with open(path / "state.json", "r") as f:
            state = json.load(f)

        config = state.get("tabdit_config", {})
        synthesizer = cls(config)
        synthesizer.load_state(state)

        # Load tokenizer
        tokenizer_path = path / "tokenizer.json"
        if tokenizer_path.exists():
            synthesizer._tokenizer = TabularTokenizer.load(tokenizer_path)

        # Load model checkpoints
        for phase_str, checkpoint_path in state.get("phase_checkpoints", {}).items():
            phase = TrainingPhase(phase_str)
            if Path(checkpoint_path).exists():
                synthesizer.load_checkpoint(phase, checkpoint_path)

        logger.info(f"Loaded TabDiT synthesizer from {path}")
        return synthesizer
