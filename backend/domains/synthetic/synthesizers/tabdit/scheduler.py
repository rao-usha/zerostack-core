"""Noise schedulers for diffusion process."""
import logging
import math
from typing import Optional, Tuple, Union

import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

from .config import DiffusionConfig

logger = logging.getLogger(__name__)


class NoiseScheduler:
    """DDPM/DDIM noise scheduler for diffusion process.

    Handles:
    - Adding noise to data (forward process)
    - Removing noise from data (reverse process)
    - Different beta schedules (linear, cosine, etc.)
    """

    def __init__(
        self,
        num_train_timesteps: int = 1000,
        beta_schedule: str = "cosine",
        beta_start: float = 0.0001,
        beta_end: float = 0.02,
        prediction_type: str = "epsilon",
    ):
        """Initialize noise scheduler.

        Args:
            num_train_timesteps: Total diffusion timesteps
            beta_schedule: Schedule type ("linear", "cosine", "squaredcos_cap_v2")
            beta_start: Starting beta value (for linear)
            beta_end: Ending beta value (for linear)
            prediction_type: What model predicts ("epsilon", "v_prediction", "sample")
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for NoiseScheduler")

        self.num_train_timesteps = num_train_timesteps
        self.beta_schedule = beta_schedule
        self.beta_start = beta_start
        self.beta_end = beta_end
        self.prediction_type = prediction_type

        # Compute betas
        self.betas = self._get_betas()

        # Compute alphas and related values
        self.alphas = 1.0 - self.betas
        self.alphas_cumprod = torch.cumprod(self.alphas, dim=0)
        self.alphas_cumprod_prev = F_pad(self.alphas_cumprod[:-1], (1, 0), value=1.0)

        # For adding noise
        self.sqrt_alphas_cumprod = torch.sqrt(self.alphas_cumprod)
        self.sqrt_one_minus_alphas_cumprod = torch.sqrt(1.0 - self.alphas_cumprod)

        # For denoising
        self.sqrt_recip_alphas = torch.sqrt(1.0 / self.alphas)
        self.sqrt_recip_alphas_cumprod = torch.sqrt(1.0 / self.alphas_cumprod)
        self.sqrt_recipm1_alphas_cumprod = torch.sqrt(1.0 / self.alphas_cumprod - 1)

        # Posterior variance
        self.posterior_variance = (
            self.betas * (1.0 - self.alphas_cumprod_prev) / (1.0 - self.alphas_cumprod)
        )
        self.posterior_log_variance_clipped = torch.log(
            torch.clamp(self.posterior_variance, min=1e-20)
        )
        self.posterior_mean_coef1 = (
            self.betas * torch.sqrt(self.alphas_cumprod_prev) / (1.0 - self.alphas_cumprod)
        )
        self.posterior_mean_coef2 = (
            (1.0 - self.alphas_cumprod_prev) * torch.sqrt(self.alphas) / (1.0 - self.alphas_cumprod)
        )

    def _get_betas(self) -> "torch.Tensor":
        """Compute beta schedule."""
        if self.beta_schedule == "linear":
            return torch.linspace(
                self.beta_start,
                self.beta_end,
                self.num_train_timesteps,
                dtype=torch.float32,
            )

        elif self.beta_schedule == "cosine":
            return self._cosine_beta_schedule()

        elif self.beta_schedule == "squaredcos_cap_v2":
            return self._squaredcos_cap_v2_schedule()

        else:
            raise ValueError(f"Unknown beta schedule: {self.beta_schedule}")

    def _cosine_beta_schedule(self, s: float = 0.008) -> "torch.Tensor":
        """Cosine beta schedule from Improved DDPM paper."""
        steps = self.num_train_timesteps + 1
        t = torch.linspace(0, self.num_train_timesteps, steps, dtype=torch.float32)
        alphas_cumprod = torch.cos(((t / self.num_train_timesteps) + s) / (1 + s) * math.pi * 0.5) ** 2
        alphas_cumprod = alphas_cumprod / alphas_cumprod[0]
        betas = 1 - (alphas_cumprod[1:] / alphas_cumprod[:-1])
        return torch.clamp(betas, 0.0001, 0.9999)

    def _squaredcos_cap_v2_schedule(self) -> "torch.Tensor":
        """Squared cosine schedule with cap."""
        steps = self.num_train_timesteps + 1
        t = torch.linspace(0, self.num_train_timesteps, steps, dtype=torch.float32)
        alphas_cumprod = torch.cos((t / self.num_train_timesteps * math.pi / 2)) ** 2
        alphas_cumprod = alphas_cumprod / alphas_cumprod[0]
        betas = 1 - (alphas_cumprod[1:] / alphas_cumprod[:-1])
        return torch.clamp(betas, 0.0, 0.999)

    def add_noise(
        self,
        original: "torch.Tensor",
        noise: "torch.Tensor",
        timesteps: "torch.Tensor",
    ) -> "torch.Tensor":
        """Add noise to samples (forward diffusion process).

        Args:
            original: Original clean samples of shape (batch, dim)
            noise: Noise to add of shape (batch, dim)
            timesteps: Timesteps for each sample of shape (batch,)

        Returns:
            Noisy samples of shape (batch, dim)
        """
        device = original.device

        sqrt_alpha_cumprod = self.sqrt_alphas_cumprod.to(device)[timesteps]
        sqrt_one_minus_alpha_cumprod = self.sqrt_one_minus_alphas_cumprod.to(device)[timesteps]

        # Expand dims for broadcasting
        sqrt_alpha_cumprod = sqrt_alpha_cumprod.unsqueeze(-1)
        sqrt_one_minus_alpha_cumprod = sqrt_one_minus_alpha_cumprod.unsqueeze(-1)

        noisy = sqrt_alpha_cumprod * original + sqrt_one_minus_alpha_cumprod * noise
        return noisy

    def step(
        self,
        model_output: "torch.Tensor",
        timestep: int,
        sample: "torch.Tensor",
        eta: float = 0.0,
        generator: Optional["torch.Generator"] = None,
    ) -> Tuple["torch.Tensor", "torch.Tensor"]:
        """Perform one denoising step.

        Uses DDIM sampling when eta=0, DDPM when eta=1.

        Args:
            model_output: Model's noise prediction
            timestep: Current timestep
            sample: Current noisy sample
            eta: Noise scale (0=DDIM, 1=DDPM)
            generator: Random generator for reproducibility

        Returns:
            Tuple of (prev_sample, pred_original_sample)
        """
        device = sample.device
        t = timestep

        # Get values for current and previous timestep
        alpha_cumprod_t = self.alphas_cumprod.to(device)[t]
        alpha_cumprod_t_prev = (
            self.alphas_cumprod.to(device)[t - 1] if t > 0 else torch.tensor(1.0, device=device)
        )

        # Compute predicted original sample from noise prediction
        if self.prediction_type == "epsilon":
            pred_original_sample = (
                sample - torch.sqrt(1 - alpha_cumprod_t) * model_output
            ) / torch.sqrt(alpha_cumprod_t)
        elif self.prediction_type == "v_prediction":
            pred_original_sample = (
                torch.sqrt(alpha_cumprod_t) * sample - torch.sqrt(1 - alpha_cumprod_t) * model_output
            )
        elif self.prediction_type == "sample":
            pred_original_sample = model_output
        else:
            raise ValueError(f"Unknown prediction type: {self.prediction_type}")

        # Clip predicted original sample
        pred_original_sample = torch.clamp(pred_original_sample, -5.0, 5.0)

        # DDIM variance
        variance = (
            (1 - alpha_cumprod_t_prev) / (1 - alpha_cumprod_t)
            * (1 - alpha_cumprod_t / alpha_cumprod_t_prev)
        )
        std_dev_t = eta * torch.sqrt(variance)

        # Compute predicted direction
        pred_sample_direction = torch.sqrt(1 - alpha_cumprod_t_prev - std_dev_t ** 2) * model_output

        # Compute prev sample
        prev_sample = (
            torch.sqrt(alpha_cumprod_t_prev) * pred_original_sample + pred_sample_direction
        )

        # Add noise if eta > 0
        if eta > 0:
            noise = torch.randn(sample.shape, device=device, generator=generator)
            prev_sample = prev_sample + std_dev_t * noise

        return prev_sample, pred_original_sample

    def get_velocity(
        self,
        sample: "torch.Tensor",
        noise: "torch.Tensor",
        timesteps: "torch.Tensor",
    ) -> "torch.Tensor":
        """Get velocity for v-prediction training.

        Args:
            sample: Clean samples
            noise: Noise
            timesteps: Timesteps

        Returns:
            Velocity tensor
        """
        device = sample.device

        sqrt_alpha_cumprod = self.sqrt_alphas_cumprod.to(device)[timesteps]
        sqrt_one_minus_alpha_cumprod = self.sqrt_one_minus_alphas_cumprod.to(device)[timesteps]

        sqrt_alpha_cumprod = sqrt_alpha_cumprod.unsqueeze(-1)
        sqrt_one_minus_alpha_cumprod = sqrt_one_minus_alpha_cumprod.unsqueeze(-1)

        velocity = sqrt_alpha_cumprod * noise - sqrt_one_minus_alpha_cumprod * sample
        return velocity


def F_pad(tensor: "torch.Tensor", pad: Tuple[int, int], value: float = 0.0) -> "torch.Tensor":
    """Pad tensor (helper function)."""
    return torch.nn.functional.pad(tensor, pad, value=value)


class DDIMScheduler(NoiseScheduler):
    """DDIM scheduler with configurable inference steps.

    Allows faster sampling with fewer steps than training.
    """

    def __init__(
        self,
        num_train_timesteps: int = 1000,
        num_inference_steps: int = 50,
        beta_schedule: str = "cosine",
        beta_start: float = 0.0001,
        beta_end: float = 0.02,
        prediction_type: str = "epsilon",
    ):
        """Initialize DDIM scheduler.

        Args:
            num_train_timesteps: Training timesteps
            num_inference_steps: Inference timesteps (can be fewer)
            beta_schedule: Beta schedule type
            beta_start: Starting beta
            beta_end: Ending beta
            prediction_type: Prediction type
        """
        super().__init__(
            num_train_timesteps=num_train_timesteps,
            beta_schedule=beta_schedule,
            beta_start=beta_start,
            beta_end=beta_end,
            prediction_type=prediction_type,
        )

        self.num_inference_steps = num_inference_steps
        self._timesteps = None

    def set_timesteps(self, num_inference_steps: Optional[int] = None) -> None:
        """Set timesteps for inference.

        Args:
            num_inference_steps: Number of inference steps (default: config value)
        """
        if num_inference_steps is not None:
            self.num_inference_steps = num_inference_steps

        # Create evenly spaced timesteps
        step_ratio = self.num_train_timesteps // self.num_inference_steps
        timesteps = (
            np.arange(0, self.num_inference_steps) * step_ratio
        ).round()[::-1].copy().astype(np.int64)

        self._timesteps = torch.from_numpy(timesteps)

    @property
    def timesteps(self) -> "torch.Tensor":
        """Get timesteps for inference."""
        if self._timesteps is None:
            self.set_timesteps()
        return self._timesteps

    @classmethod
    def from_config(cls, config: DiffusionConfig) -> "DDIMScheduler":
        """Create scheduler from config.

        Args:
            config: Diffusion configuration

        Returns:
            DDIMScheduler instance
        """
        return cls(
            num_train_timesteps=config.num_train_timesteps,
            num_inference_steps=config.num_inference_steps,
            beta_schedule=config.beta_schedule,
            beta_start=config.beta_start,
            beta_end=config.beta_end,
            prediction_type=config.prediction_type,
        )


def create_scheduler(config: DiffusionConfig) -> NoiseScheduler:
    """Create noise scheduler from config.

    Args:
        config: Diffusion configuration

    Returns:
        NoiseScheduler instance
    """
    return DDIMScheduler.from_config(config)
