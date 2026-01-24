"""Abstract base classes for VCR pipeline components.

These interfaces define the contracts for interchangeable strategies:
- BaseDetector: Vehicle detection
- BaseBackbone: Feature extraction (multi-scale)
- BaseLoss: Training loss computation
- BaseFusion: Multi-scale feature fusion
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import torch
from torch import Tensor, nn


@dataclass
class BBox:
    """Bounding box representation."""

    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float = 1.0
    class_id: int = -1
    label: str = ""  # Color label for VCR

    def to_xyxy(self) -> list[float]:
        """Return [x1, y1, x2, y2] format."""
        return [self.x1, self.y1, self.x2, self.y2]


@dataclass
class DetectionResult:
    """Result from a detector."""

    image_path: str
    bboxes: list[BBox]
    metadata: dict[str, Any] | None = None


class BaseDetector(ABC):
    """Abstract base class for vehicle detectors.

    Implementations: YOLODetector, ManualBBoxReader
    """

    @abstractmethod
    def detect(self, image_path: str) -> DetectionResult:
        """Detect vehicles in an image.

        Args:
            image_path: Path to the input image.

        Returns:
            DetectionResult containing bounding boxes and metadata.
        """
        pass

    @abstractmethod
    def detect_batch(self, image_paths: list[str]) -> list[DetectionResult]:
        """Detect vehicles in multiple images.

        Args:
            image_paths: List of paths to input images.

        Returns:
            List of DetectionResult objects.
        """
        pass


class BaseBackbone(nn.Module, ABC):
    """Abstract base class for feature extraction backbones.

    Returns multi-scale features with standardized keys: c2, c3, c4, c5.
    Implementations: ResNetBackbone, EfficientNetBackbone
    """

    @abstractmethod
    def forward(self, x: Tensor) -> dict[str, Tensor]:
        """Extract multi-scale features.

        Args:
            x: Input tensor of shape (B, C, H, W).

        Returns:
            Dictionary with keys 'c2', 'c3', 'c4', 'c5' mapping to feature tensors.
            Each tensor has shape (B, C_i, H_i, W_i) with decreasing spatial dims.
        """
        pass

    @abstractmethod
    def get_feature_channels(self) -> dict[str, int]:
        """Return the number of channels for each feature level.

        Returns:
            Dictionary mapping 'c2', 'c3', 'c4', 'c5' to channel counts.
        """
        pass


class BaseLoss(nn.Module, ABC):
    """Abstract base class for loss functions.

    Supports flexible kwargs for different loss strategies.
    Implementations: SmoothModulationLoss, FocalLoss
    """

    @abstractmethod
    def forward(self, logits: Tensor, targets: Tensor, **kwargs: Any) -> Tensor:
        """Compute the loss.

        Args:
            logits: Model predictions of shape (B, num_classes).
            targets: Ground truth labels of shape (B,).
            **kwargs: Additional arguments (class_counts, epoch, alpha, etc.)

        Returns:
            Scalar loss tensor.
        """
        pass


class BaseFusion(nn.Module, ABC):
    """Abstract base class for multi-scale feature fusion.

    Implementations: MSFFusion, SimpleConcatFusion
    """

    @abstractmethod
    def forward(self, features: dict[str, Tensor]) -> Tensor:
        """Fuse multi-scale features.

        Args:
            features: Dictionary with keys 'c2', 'c3', 'c4', 'c5'.

        Returns:
            Fused feature tensor of shape (B, out_channels, H, W) or (B, out_channels).
        """
        pass

    @abstractmethod
    def get_output_channels(self) -> int:
        """Return the number of output channels after fusion."""
        pass


class BaseTrainingStrategy(ABC):
    """Abstract base class for training strategies.

    Encapsulates the model architecture, optimization logic, and training steps.
    Similar to PyTorch Lightning's LightningModule but simpler.
    """

    def __init__(self, config: dict[str, Any], num_classes: int):
        """Initialize strategy.

        Args:
            config: Full configuration dictionary.
            num_classes: Number of classes in the dataset.
        """
        self.config = config
        self.num_classes = num_classes
        self.device = torch.device("cpu")  # Will be set by runner

    @abstractmethod
    def build_model(self) -> nn.Module:
        """Build and return the model architecture."""
        pass

    @abstractmethod
    def configure_optimizers(self, model: nn.Module) -> tuple[torch.optim.Optimizer, Any]:
        """Configure optimizer and scheduler.

        Returns:
            Tuple of (optimizer, scheduler). Scheduler can be None.
        """
        pass

    @abstractmethod
    def configure_loss(self) -> nn.Module:
        """Configure the loss function."""
        pass

    @abstractmethod
    def training_step(
        self,
        model: nn.Module,
        batch: Any,
        criterion: nn.Module,
        batch_idx: int,
        **kwargs: Any
    ) -> dict[str, float]:
        """Perform a single training step.

        Args:
            model: The model instance.
            batch: Batch data (images, targets).
            criterion: Loss function.
            batch_idx: Index of the batch.

        Returns:
            Dictionary with metrics (must include 'loss').
        """
        pass

    @abstractmethod
    def validation_step(
        self,
        model: nn.Module,
        batch: Any,
        criterion: nn.Module,
        **kwargs: Any
    ) -> dict[str, float]:
        """Perform a single validation step.

        Returns:
            Dictionary with metrics.
        """
        pass

