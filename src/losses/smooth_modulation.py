"""Smooth Modulation Loss for long-tail distributions.

Inspired by "Vehicle Color Recognition Based on Smooth Modulation Neural Network
with Multi-Scale Feature Fusion" (Hu et al., 2023).

Gradually increases weight for tail (rare) classes during training.
"""

from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F

from src.core.factories import LossFactory
from src.core.interfaces import BaseLoss


class SmoothModulationLoss(BaseLoss):
    """Smooth Modulation Loss for long-tail class distributions.

    Applies class-dependent weights based on class frequency,
    with smooth modulation that changes over training epochs.

    Weight for class c: w_c = (1 / n_c)^tau * m(epoch)

    Where:
    - n_c is the number of samples in class c
    - tau controls the strength of reweighting
    - m(epoch) is a smooth modulation function
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        """Initialize Smooth Modulation Loss.

        Args:
            cfg: Configuration with keys:
                - tau: Reweighting strength (default: 0.5)
                - max_epoch: Total epochs for modulation schedule (default: 50)
                - modulation_type: 'linear', 'cosine', 'step' (default: 'cosine')
                - reduction: 'mean', 'sum', 'none' (default: 'mean')
        """
        super().__init__()

        self.tau = cfg.get("tau", 0.5)
        self.max_epoch = cfg.get("max_epoch", 50)
        self.modulation_type = cfg.get("modulation_type", "cosine")
        self.reduction = cfg.get("reduction", "mean")

    def _compute_modulation(self, epoch: int) -> float:
        """Compute modulation factor based on epoch.

        Args:
            epoch: Current epoch (0-indexed).

        Returns:
            Modulation factor in [0, 1].
        """
        t = min(epoch / max(self.max_epoch, 1), 1.0)

        if self.modulation_type == "linear":
            return t
        elif self.modulation_type == "cosine":
            return 0.5 * (1 - torch.cos(torch.tensor(t * 3.14159)).item())
        elif self.modulation_type == "step":
            # Step at 50% of training
            return 1.0 if t >= 0.5 else 0.0
        else:
            return t

    def _compute_class_weights(
        self,
        class_counts: torch.Tensor | list[int],
        modulation: float,
        device: torch.device,
    ) -> torch.Tensor:
        """Compute class weights based on frequency.

        Args:
            class_counts: Number of samples per class.
            modulation: Modulation factor [0, 1].
            device: Device for tensor.

        Returns:
            Weight tensor of shape (num_classes,).
        """
        if isinstance(class_counts, list):
            class_counts = torch.tensor(class_counts, dtype=torch.float32, device=device)
        else:
            class_counts = class_counts.float().to(device)

        # Avoid division by zero
        class_counts = class_counts.clamp(min=1)

        # Compute inverse frequency weights
        inv_freq = 1.0 / class_counts

        # Apply tau and normalize
        weights = inv_freq ** self.tau

        # Apply modulation (blend between uniform and weighted)
        uniform = torch.ones_like(weights) / len(weights)
        weights = (1 - modulation) * uniform + modulation * (weights / weights.sum())

        # Normalize so mean is 1
        weights = weights / weights.mean()

        return weights

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
        **kwargs: Any,
    ) -> torch.Tensor:
        """Compute Smooth Modulation Loss.

        Args:
            logits: Predictions (B, num_classes).
            targets: Ground truth labels (B,).
            **kwargs:
                - class_counts: Number of samples per class (required for weighting)
                - epoch: Current epoch (default: 0)

        Returns:
            Scalar loss tensor.
        """
        epoch = kwargs.get("epoch", 0)
        class_counts = kwargs.get("class_counts", None)

        # Compute modulation
        modulation = self._compute_modulation(epoch)

        # Compute weights if class_counts provided
        if class_counts is not None:
            weights = self._compute_class_weights(class_counts, modulation, logits.device)
            weight_per_sample = weights[targets]
        else:
            weight_per_sample = torch.ones(targets.shape[0], device=logits.device)

        # Compute cross entropy per sample
        ce_loss = F.cross_entropy(logits, targets, reduction="none")

        # Apply weights
        loss = weight_per_sample * ce_loss

        # Reduction
        if self.reduction == "mean":
            return loss.mean()
        elif self.reduction == "sum":
            return loss.sum()
        else:
            return loss


# Register with factory
LossFactory.register("smooth_modulation", SmoothModulationLoss)
