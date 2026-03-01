"""EfficientNet backbone with multi-scale feature extraction.

Returns features at c2, c3, c4, c5 levels (FPN-style keys).
Uses timm for EfficientNet models.
"""

from typing import Any

import timm
import torch
import torch.nn as nn

from src.core.factories import BackboneFactory
from src.core.interfaces import BaseBackbone


class EfficientNetBackbone(BaseBackbone):
    """EfficientNet backbone with multi-scale outputs.

    Uses timm's feature extraction to get intermediate features.
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        """Initialize EfficientNet backbone.

        Args:
            cfg: Configuration with keys:
                - variant: 'efficientnet_b0', 'efficientnet_b4', etc. (default: 'efficientnet_b4')
                - pretrained: Whether to use pretrained weights (default: True)
        """
        super().__init__()

        variant = cfg.get("variant", "efficientnet_b4")
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
BackboneFactory.register("efficientnet_b0", EfficientNetBackbone)
BackboneFactory.register("efficientnet_b2", EfficientNetBackbone)
BackboneFactory.register("efficientnet_b4", EfficientNetBackbone)
