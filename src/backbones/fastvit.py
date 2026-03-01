"""FastViT backbone with multi-scale feature extraction.

FastViT is Apple's efficient Vision Transformer optimized for mobile devices.
Returns features at c2, c3, c4, c5 levels (FPN-style keys).
Uses timm for FastViT models.
"""

from typing import Any

import timm
import torch
import torch.nn as nn

from src.core.factories import BackboneFactory
from src.core.interfaces import BaseBackbone


class FastViTBackbone(BaseBackbone):
    """FastViT backbone with multi-scale outputs.

    Uses timm's feature extraction to get intermediate features.
    Vision Transformer architecture optimized for speed.
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        """Initialize FastViT backbone.

        Args:
            cfg: Configuration with keys:
                - variant: 'fastvit_t8', 'fastvit_t12', etc.
                - pretrained: Whether to use pretrained weights (default: True)
        """
        super().__init__()

        variant = cfg.get("variant", "fastvit_t8")
        pretrained = cfg.get("pretrained", True)

        # Create model with feature extraction
        # Note: FastViT has 4 stages (indices 0-3), unlike other models
        self.model = timm.create_model(
            variant,
            pretrained=pretrained,
            features_only=True,
            out_indices=(0, 1, 2, 3),  # Get all 4 available feature levels
        )

        self.variant = variant

        # Get channel info from model
        feature_info = self.model.feature_info.channels()
        self._channels = {
            "c2": feature_info[0],
            "c3": feature_info[1],
            "c4": feature_info[2],
            "c5": feature_info[3],
        }

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        """Extract multi-scale features.

        Args:
            x: Input tensor (B, 3, H, W).

        Returns:
            Dict with keys 'c2', 'c3', 'c4', 'c5'.
        """
        features = self.model(x)

        return {
            "c2": features[0],
            "c3": features[1],
            "c4": features[2],
            "c5": features[3],
        }

    def get_feature_channels(self) -> dict[str, int]:
        """Return channel counts for each feature level."""
        return self._channels.copy()


# Register variants
BackboneFactory.register("fastvit_t8", FastViTBackbone)
BackboneFactory.register("fastvit_t12", FastViTBackbone)
