"""MobileOne backbone with multi-scale feature extraction.

MobileOne is Apple's re-parameterized CNN for extremely fast inference.
Returns features at c2, c3, c4, c5 levels (FPN-style keys).
Uses timm for MobileOne models.
"""

from typing import Any

import timm
import torch
import torch.nn as nn

from src.core.factories import BackboneFactory
from src.core.interfaces import BaseBackbone


class MobileOneBackbone(BaseBackbone):
    """MobileOne backbone with multi-scale outputs.

    Uses timm's feature extraction to get intermediate features.
    Re-parameterized architecture for ultra-fast inference.
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        """Initialize MobileOne backbone.

        Args:
            cfg: Configuration with keys:
                - variant: 'mobileone_s0', 'mobileone_s1', etc.
                - pretrained: Whether to use pretrained weights (default: True)
        """
        super().__init__()

        variant = cfg.get("variant", "mobileone_s1")
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
BackboneFactory.register("mobileone_s0", MobileOneBackbone)
BackboneFactory.register("mobileone_s1", MobileOneBackbone)
BackboneFactory.register("mobileone_s2", MobileOneBackbone)
