"""ResNet backbone with multi-scale feature extraction.

Returns features at c2, c3, c4, c5 levels (FPN-style keys).
"""

from typing import Any

import torch
import torch.nn as nn
from torchvision import models
from torchvision.models import ResNet50_Weights, ResNet34_Weights, ResNet18_Weights

from src.core.factories import BackboneFactory
from src.core.interfaces import BaseBackbone


class ResNetBackbone(BaseBackbone):
    """ResNet backbone with multi-scale outputs.

    Extracts features from layer1 (c2), layer2 (c3), layer3 (c4), layer4 (c5).
    """

    # Channel counts for different ResNet variants
    CHANNELS = {
        "resnet18": {"c2": 64, "c3": 128, "c4": 256, "c5": 512},
        "resnet34": {"c2": 64, "c3": 128, "c4": 256, "c5": 512},
        "resnet50": {"c2": 256, "c3": 512, "c4": 1024, "c5": 2048},
        "resnet101": {"c2": 256, "c3": 512, "c4": 1024, "c5": 2048},
    }

    def __init__(self, cfg: dict[str, Any]) -> None:
        """Initialize ResNet backbone.

        Args:
            cfg: Configuration with keys:
                - variant: 'resnet18', 'resnet34', 'resnet50' (default: 'resnet50')
                - pretrained: Whether to use pretrained weights (default: True)
        """
        super().__init__()

        variant = cfg.get("variant", "resnet50")
        pretrained = cfg.get("pretrained", True)

        # Load pretrained model
        if variant == "resnet18":
            weights = ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
            resnet = models.resnet18(weights=weights)
        elif variant == "resnet34":
            weights = ResNet34_Weights.IMAGENET1K_V1 if pretrained else None
            resnet = models.resnet34(weights=weights)
        elif variant == "resnet50":
            weights = ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
            resnet = models.resnet50(weights=weights)
        else:
            raise ValueError(f"Unknown ResNet variant: {variant}")

        self.variant = variant
        self._channels = self.CHANNELS[variant]

        # Extract layers
        self.stem = nn.Sequential(
            resnet.conv1,
            resnet.bn1,
            resnet.relu,
            resnet.maxpool,
        )
        self.layer1 = resnet.layer1  # c2
        self.layer2 = resnet.layer2  # c3
        self.layer3 = resnet.layer3  # c4
        self.layer4 = resnet.layer4  # c5

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        """Extract multi-scale features.

        Args:
            x: Input tensor (B, 3, H, W).

        Returns:
            Dict with keys 'c2', 'c3', 'c4', 'c5'.
        """
        x = self.stem(x)

        c2 = self.layer1(x)
        c3 = self.layer2(c2)
        c4 = self.layer3(c3)
        c5 = self.layer4(c4)

        return {"c2": c2, "c3": c3, "c4": c4, "c5": c5}

    def get_feature_channels(self) -> dict[str, int]:
        """Return channel counts for each feature level."""
        return self._channels.copy()


# Register variants
BackboneFactory.register("resnet18", ResNetBackbone)
BackboneFactory.register("resnet34", ResNetBackbone)
BackboneFactory.register("resnet50", ResNetBackbone)
