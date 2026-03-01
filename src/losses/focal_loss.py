"""Focal Loss for class imbalance.

From "Focal Loss for Dense Object Detection" (Lin et al., 2017).
Reduces weight for well-classified examples, focusing on hard ones.
"""

from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F

from src.core.factories import LossFactory
from src.core.interfaces import BaseLoss


class FocalLoss(BaseLoss):
    """Focal Loss for handling class imbalance.

    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)

    Where p_t is the probability of the correct class.
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        """Initialize Focal Loss.

        Args:
            cfg: Configuration with keys:
                - gamma: Focusing parameter (default: 2.0)
                - alpha: Class weights (default: None = balanced)
                - reduction: 'mean', 'sum', 'none' (default: 'mean')
        """
        super().__init__()

        self.gamma = cfg.get("gamma", 2.0)
        self.alpha = cfg.get("alpha", None)
        self.reduction = cfg.get("reduction", "mean")

    def forward(
        self,
        logits: torch.Tensor,
        targets: torch.Tensor,
        **kwargs: Any,
    ) -> torch.Tensor:
        """Compute Focal Loss.

        Args:
            logits: Predictions (B, num_classes).
            targets: Ground truth labels (B,).
            **kwargs: Optional - alpha (class weights) can be passed here.

        Returns:
            Scalar loss tensor.
        """
        # Get alpha from kwargs if provided, else use config
        alpha = kwargs.get("alpha", self.alpha)

        # Compute cross entropy
        ce_loss = F.cross_entropy(logits, targets, reduction="none")

        # Compute pt (probability of correct class)
        pt = torch.exp(-ce_loss)

        # Compute focal weight
        focal_weight = (1 - pt) ** self.gamma

        # Apply alpha if provided
        if alpha is not None:
            if isinstance(alpha, (float, int)):
                # Scalar alpha
                focal_weight = alpha * focal_weight
            else:
                # Class weights
                if isinstance(alpha, (list, tuple)):
                    alpha = torch.tensor(alpha, device=logits.device, dtype=logits.dtype)
                
                # Ensure alpha is on correct device if it came from config
                if isinstance(alpha, torch.Tensor) and alpha.device != logits.device:
                    alpha = alpha.to(logits.device)
                    
                alpha_t = alpha[targets]
                focal_weight = alpha_t * focal_weight

        # Compute focal loss
        loss = focal_weight * ce_loss

        # Reduction
        if self.reduction == "mean":
            return loss.mean()
        elif self.reduction == "sum":
            return loss.sum()
        else:
            return loss


# Register with factory
LossFactory.register("focal", FocalLoss)
