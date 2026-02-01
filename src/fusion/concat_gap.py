"""Global Concatenation Fusion (GAP + Concat) for ColorNet-V1."""

from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F

from src.core.factories import FusionFactory
from src.core.interfaces import BaseFusion


class GlobalConcatFusion(BaseFusion):
    """Global Concatenation Fusion module.

    Performs Global Average Pooling (GAP) on features from multiple levels,
    flattens them, and concatenates the resulting vectors.
    
    This is a lightweight fusion strategy suitable for ColorNet-V1.
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        """Initialize GlobalConcatFusion.

        Args:
            cfg: Configuration with keys:
                - in_channels: Dict of input channels per level {'c3': 64, 'c4': 96, 'c5': 160}
        """
        super().__init__()

        in_channels = cfg.get("in_channels", {"c3": 64, "c4": 96, "c5": 160})
        
        # Calculate total output dimension
        # We use c3, c4, c5 as per ColorNet-V1 design
        self.out_channels = 0
        self.levels = ["c3", "c4", "c5"]
        
        for level in self.levels:
            if level in in_channels:
                self.out_channels += in_channels[level]
            else:
                # Warn or just ignore? For now assume valid config provided
                pass

        self.gap = nn.AdaptiveAvgPool2d(1)

    def forward(self, features: dict[str, torch.Tensor]) -> torch.Tensor:
        """Fuse features via GAP and concatenation.

        Args:
            features: Dict with keys 'c3', 'c4', 'c5', etc.

        Returns:
            Fused feature tensor (B, out_channels).
        """
        vectors = []
        for level in self.levels:
            if level in features:
                # GAP -> (B, C, 1, 1) -> Flatten -> (B, C)
                vec = self.gap(features[level]).flatten(1)
                vectors.append(vec)
        
        # Concatenate (B, Sum(C))
        if not vectors:
            raise ValueError("No features found to fuse.")
            
        fused = torch.cat(vectors, dim=1)
        return fused

    def get_output_channels(self) -> int:
        """Return output feature dimension."""
        return self.out_channels


# Register with factory
FusionFactory.register("global_concat", GlobalConcatFusion)
