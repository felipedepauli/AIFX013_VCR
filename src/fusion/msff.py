"""Multi-Scale Feature Fusion (MSFF) module.

Fuses features from multiple scales (c2, c3, c4, c5) for color recognition.
Inspired by "Vehicle Color Recognition Based on Smooth Modulation Neural Network
with Multi-Scale Feature Fusion" (Hu et al., 2023).
"""

from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F

from src.core.factories import FusionFactory
from src.core.interfaces import BaseFusion


class MSFFusion(BaseFusion):
    """Multi-Scale Feature Fusion module.

    Upsamples all feature maps to the same resolution, applies channel
    reduction, and fuses them via concatenation + convolution.
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        """Initialize MSFF.

        Args:
            cfg: Configuration with keys:
                - in_channels: Dict of input channels per level {'c2': 256, ...}
                - out_channels: Output channels after fusion (default: 256)
                - target_size: Target spatial size for upsampling (default: 14)
        """
        super().__init__()

        in_channels = cfg.get("in_channels", {"c2": 256, "c3": 512, "c4": 1024, "c5": 2048})
        self.out_channels = cfg.get("out_channels", 256)
        self.target_size = cfg.get("target_size", 14)

        # Channel reduction for each level
        self.reduce_c2 = nn.Conv2d(in_channels["c2"], self.out_channels, 1)
        self.reduce_c3 = nn.Conv2d(in_channels["c3"], self.out_channels, 1)
        self.reduce_c4 = nn.Conv2d(in_channels["c4"], self.out_channels, 1)
        self.reduce_c5 = nn.Conv2d(in_channels["c5"], self.out_channels, 1)

        # Fusion conv after concatenation (4 * out_channels -> out_channels)
        self.fuse_conv = nn.Sequential(
            nn.Conv2d(4 * self.out_channels, self.out_channels, 3, padding=1),
            nn.BatchNorm2d(self.out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(self.out_channels, self.out_channels, 3, padding=1),
            nn.BatchNorm2d(self.out_channels),
            nn.ReLU(inplace=True),
        )

        # Global average pooling for final output
        self.gap = nn.AdaptiveAvgPool2d(1)

    def forward(self, features: dict[str, torch.Tensor]) -> torch.Tensor:
        """Fuse multi-scale features.

        Args:
            features: Dict with keys 'c2', 'c3', 'c4', 'c5'.

        Returns:
            Fused feature tensor (B, out_channels).
        """
        target_size = (self.target_size, self.target_size)

        # Reduce channels and upsample to target size
        f2 = F.interpolate(self.reduce_c2(features["c2"]), size=target_size, mode="bilinear", align_corners=False)
        f3 = F.interpolate(self.reduce_c3(features["c3"]), size=target_size, mode="bilinear", align_corners=False)
        f4 = F.interpolate(self.reduce_c4(features["c4"]), size=target_size, mode="bilinear", align_corners=False)
        f5 = F.interpolate(self.reduce_c5(features["c5"]), size=target_size, mode="bilinear", align_corners=False)

        # Concatenate
        fused = torch.cat([f2, f3, f4, f5], dim=1)

        # Apply fusion conv
        fused = self.fuse_conv(fused)

        # Global average pooling -> (B, out_channels)
        out = self.gap(fused).flatten(1)

        return out

    def get_output_channels(self) -> int:
        """Return output feature dimension."""
        return self.out_channels


class SimpleConcatFusion(BaseFusion):
    """Simple fusion: just use c5 with GAP.

    Baseline approach without multi-scale fusion.
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        """Initialize simple fusion.

        Args:
            cfg: Configuration with keys:
                - in_channels: Dict with at least 'c5' key
        """
        super().__init__()

        in_channels = cfg.get("in_channels", {"c5": 2048})
        self._out_channels = in_channels["c5"]
        self.gap = nn.AdaptiveAvgPool2d(1)

    def forward(self, features: dict[str, torch.Tensor]) -> torch.Tensor:
        """Just use c5 features.

        Args:
            features: Dict with keys 'c2', 'c3', 'c4', 'c5'.

        Returns:
            Feature tensor (B, c5_channels).
        """
        out = self.gap(features["c5"]).flatten(1)
        return out

    def get_output_channels(self) -> int:
        """Return output feature dimension."""
        return self._out_channels


# Register with factory
FusionFactory.register("msff", MSFFusion)
FusionFactory.register("simple_concat", SimpleConcatFusion)
