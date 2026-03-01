"""MobileNetV4 backbone with multi-scale feature extraction.

MobileNetV4 is Google's latest mobile-optimized architecture (2024).
Returns features at c2, c3, c4, c5 levels (FPN-style keys).
Uses timm for MobileNetV4 models.
"""

from typing import Any

import timm
import torch
import torch.nn as nn

from src.core.factories import BackboneFactory
from src.core.interfaces import BaseBackbone


class MobileNetV4Backbone(BaseBackbone):
    """MobileNetV4 backbone with multi-scale outputs.

    Uses timm's feature extraction to get intermediate features.
    Optimized for mobile and edge deployment.
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        """Initialize MobileNetV4 backbone.

        Args:
            cfg: Configuration with keys:
                - variant: 'mobilenetv4_conv_small', 'mobilenetv4_conv_medium', etc.
                - pretrained: Whether to use pretrained weights (default: True)
        """
        super().__init__()

        variant = cfg.get("variant", "mobilenetv4_conv_small")
        pretrained = cfg.get("pretrained", True)

        # Create model with feature extraction
        self.model = timm.create_model(
            variant,
            pretrained=pretrained,
            features_only=True,
            out_indices=(1, 2, 3, 4),  # Get features at multiple scales
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
BackboneFactory.register("mobilenetv4_small", MobileNetV4Backbone)
BackboneFactory.register("mobilenetv4_conv_small", MobileNetV4Backbone)
