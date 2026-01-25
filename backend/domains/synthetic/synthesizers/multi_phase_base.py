"""Multi-phase synthesizer base class for synthesizers requiring staged training."""
import logging
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .base import BaseSynthesizer, SynthesizerResult

logger = logging.getLogger(__name__)


class TrainingPhase(str, Enum):
    """Training phases for multi-phase synthesizers."""
    PHASE_1 = "phase_1"  # e.g., VAE training
    PHASE_2 = "phase_2"  # e.g., Diffusion training
    PHASE_3 = "phase_3"  # Optional additional phases


@dataclass
class PhaseResult:
    """Result from a single training phase."""
    phase: TrainingPhase
    success: bool
    checkpoint_path: Optional[str] = None
    metrics: Dict[str, Any] = None
    epochs_completed: int = 0
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}


@dataclass
class PhaseConfig:
    """Configuration for a training phase."""
    phase: TrainingPhase
    epochs: int
    batch_size: int
    learning_rate: float
    checkpoint_interval: int = 10
    additional_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}


class MultiPhaseSynthesizer(BaseSynthesizer):
    """Abstract base class for synthesizers requiring multi-phase training.

    Multi-phase synthesizers train in distinct stages (e.g., VAE then diffusion).
    Each phase can be trained on GPU and produces checkpoints that can be resumed.

    Subclasses must implement:
    - training_phases: Property returning ordered list of phases
    - train_phase(): Train a single phase
    - load_checkpoint(): Load a checkpoint for a phase
    - sample(): Generate synthetic data
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize multi-phase synthesizer.

        Args:
            config: Full configuration dict with per-phase configs
        """
        super().__init__(config)
        self._phase_checkpoints: Dict[TrainingPhase, str] = {}
        self._phase_metrics: Dict[TrainingPhase, Dict[str, Any]] = {}
        self._current_phase: Optional[TrainingPhase] = None

    @property
    @abstractmethod
    def training_phases(self) -> List[TrainingPhase]:
        """Return ordered list of training phases.

        Returns:
            List of TrainingPhase enums in training order
        """
        pass

    @abstractmethod
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
            phase: The training phase to execute
            data: Training data (may be raw or processed depending on phase)
            checkpoint_dir: Directory to save checkpoints
            resume_from: Optional checkpoint path to resume from
            progress_callback: Optional callback for progress updates

        Returns:
            PhaseResult with checkpoint path and metrics
        """
        pass

    @abstractmethod
    def load_checkpoint(self, phase: TrainingPhase, checkpoint_path: str) -> None:
        """Load a checkpoint for a specific phase.

        Args:
            phase: The phase this checkpoint is for
            checkpoint_path: Path to checkpoint file
        """
        pass

    @property
    def current_phase(self) -> Optional[TrainingPhase]:
        """Get current training phase."""
        return self._current_phase

    @property
    def phase_checkpoints(self) -> Dict[TrainingPhase, str]:
        """Get checkpoints for each completed phase."""
        return self._phase_checkpoints.copy()

    @property
    def phase_metrics(self) -> Dict[TrainingPhase, Dict[str, Any]]:
        """Get training metrics for each completed phase."""
        return self._phase_metrics.copy()

    def fit(self, data: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Fit the synthesizer (not supported for multi-phase).

        Multi-phase synthesizers should use train_phase() instead.
        This method is provided for API compatibility but will raise an error.

        Raises:
            NotImplementedError: Always, use train_phase() instead
        """
        raise NotImplementedError(
            "Multi-phase synthesizers do not support synchronous fit(). "
            "Use train_phase() for each training phase instead."
        )

    async def train_all_phases(
        self,
        data: pd.DataFrame,
        checkpoint_dir: str,
        progress_callback: Optional[callable] = None,
    ) -> Dict[TrainingPhase, PhaseResult]:
        """Train all phases sequentially.

        This is a convenience method for local training.
        For production, each phase should be trained separately with
        checkpoints to allow resumption.

        Args:
            data: Training data
            checkpoint_dir: Base directory for checkpoints
            progress_callback: Optional progress callback

        Returns:
            Dict mapping phases to their results
        """
        results = {}

        for phase in self.training_phases:
            self._current_phase = phase
            phase_dir = str(Path(checkpoint_dir) / phase.value)

            logger.info(f"Starting {phase.value} training")

            result = await self.train_phase(
                phase=phase,
                data=data,
                checkpoint_dir=phase_dir,
                progress_callback=progress_callback,
            )

            results[phase] = result

            if not result.success:
                logger.error(f"Phase {phase.value} failed: {result.error_message}")
                break

            # Store checkpoint and metrics
            self._phase_checkpoints[phase] = result.checkpoint_path
            self._phase_metrics[phase] = result.metrics

            logger.info(f"Completed {phase.value}: {result.metrics}")

        # Mark as fitted if all phases completed
        if all(r.success for r in results.values()):
            self._fitted = True
            self._store_metadata(data)

        self._current_phase = None
        return results

    def is_phase_complete(self, phase: TrainingPhase) -> bool:
        """Check if a specific phase has been completed.

        Args:
            phase: The phase to check

        Returns:
            True if phase has a checkpoint
        """
        return phase in self._phase_checkpoints

    def get_required_phases(self) -> List[TrainingPhase]:
        """Get list of phases that still need to be trained.

        Returns:
            List of incomplete phases
        """
        return [p for p in self.training_phases if p not in self._phase_checkpoints]

    def get_state(self) -> Dict[str, Any]:
        """Get serializable state for persistence.

        Returns:
            Dict with checkpoints, metrics, and config
        """
        return {
            "config": self.config,
            "fitted": self._fitted,
            "current_phase": self._current_phase.value if self._current_phase else None,
            "phase_checkpoints": {k.value: v for k, v in self._phase_checkpoints.items()},
            "phase_metrics": {k.value: v for k, v in self._phase_metrics.items()},
            "columns": self._columns,
            "dtypes": self._dtypes,
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        """Load state from persistence.

        Args:
            state: State dict from get_state()
        """
        self.config = state.get("config", {})
        self._fitted = state.get("fitted", False)

        if state.get("current_phase"):
            self._current_phase = TrainingPhase(state["current_phase"])

        self._phase_checkpoints = {
            TrainingPhase(k): v
            for k, v in state.get("phase_checkpoints", {}).items()
        }
        self._phase_metrics = {
            TrainingPhase(k): v
            for k, v in state.get("phase_metrics", {}).items()
        }

        self._columns = state.get("columns")
        self._dtypes = state.get("dtypes")
