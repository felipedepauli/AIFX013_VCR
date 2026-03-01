"""ColorNet-V1 backbone definition.

Optimized for vehicle color recognition with efficient MBConv blocks and
multi-scale feature extraction.
"""

from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F

from src.core.factories import BackboneFactory
from src.core.interfaces import BaseBackbone


class SqueezeExcitation(nn.Module):
    """Squeeze-and-Excitation block."""

    def __init__(self, in_channels: int, squeeze_factor: int = 4):
        super().__init__()
        squeeze_channels = max(1, in_channels // squeeze_factor)
        self.fc1 = nn.Conv2d(in_channels, squeeze_channels, 1)
        self.fc2 = nn.Conv2d(squeeze_channels, in_channels, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        scale = F.adaptive_avg_pool2d(x, 1)
        scale = self.fc1(scale)
        scale = F.silu(scale, inplace=True)
        scale = self.fc2(scale)
        scale = torch.sigmoid(scale)
        return x * scale


class MBConvBlock(nn.Module):
    """Mobile Inverted Bottleneck Convolution block."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        stride: int = 1,
        expand_ratio: int = 4,
        use_se: bool = True,
    ):
        super().__init__()
        self.stride = stride
        hidden_dim = in_channels * expand_ratio
        self.use_res_connect = self.stride == 1 and in_channels == out_channels

        layers = []
        # Expansion
        if expand_ratio != 1:
            layers.extend([
                nn.Conv2d(in_channels, hidden_dim, 1, bias=False),
                nn.BatchNorm2d(hidden_dim),
                nn.SiLU(inplace=True),
            ])

        # Depthwise
        layers.extend([
            nn.Conv2d(
                hidden_dim, hidden_dim, 3, stride=stride, padding=1,
                groups=hidden_dim, bias=False
            ),
            nn.BatchNorm2d(hidden_dim),
            nn.SiLU(inplace=True),
        ])

        # Squeeze-and-Excitation
        if use_se:
            layers.append(SqueezeExcitation(hidden_dim))

        # Projection
        layers.extend([
            nn.Conv2d(hidden_dim, out_channels, 1, bias=False),
            nn.BatchNorm2d(out_channels),
        ])

        self.conv = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.use_res_connect:
            return x + self.conv(x)
        return self.conv(x)


class ColorNetV1Backbone(BaseBackbone):
    """ColorNet-V1 custom backbone.
    
    Architecture:
    - Stem: Conv3x3, s2
    - Body: 4 Stages of MBConv blocks to reach stride 32
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        super().__init__()
        
        # Hyperparameters for ColorNet-V1
        # Channels per stage: stem -> s1 -> s2 -> s3 -> s4
        # Stride:              2      4      8     16    32
        # Richer capacity configuration (~1.53M params)
        self.channels = [32, 48, 64, 96, 160]
        
        # Stem
        self.stem = nn.Sequential(
            nn.Conv2d(3, self.channels[0], 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(self.channels[0]),
            nn.SiLU(inplace=True),
        )
        
        # Body stages
        # Stage 1 (Stride 4): 1 block
        self.stage1 = MBConvBlock(
            self.channels[0], self.channels[1], stride=2, expand_ratio=4
        )
        
        # Stage 2 (Stride 8, c3): 2 blocks
        self.stage2 = nn.Sequential(
            MBConvBlock(self.channels[1], self.channels[2], stride=2, expand_ratio=4),
            MBConvBlock(self.channels[2], self.channels[2], stride=1, expand_ratio=4)
        )
        
        # Stage 3 (Stride 16, c4): 3 blocks
        self.stage3 = nn.Sequential(
            MBConvBlock(self.channels[2], self.channels[3], stride=2, expand_ratio=4),
            MBConvBlock(self.channels[3], self.channels[3], stride=1, expand_ratio=4),
            MBConvBlock(self.channels[3], self.channels[3], stride=1, expand_ratio=4)
        )
        
        # Stage 4 (Stride 32, c5): 3 blocks
        self.stage4 = nn.Sequential(
            MBConvBlock(self.channels[3], self.channels[4], stride=2, expand_ratio=4),
            MBConvBlock(self.channels[4], self.channels[4], stride=1, expand_ratio=4),
            MBConvBlock(self.channels[4], self.channels[4], stride=1, expand_ratio=4)
        )
        
        # Save output channels info
        self._channels = {
            "c2": self.channels[1],
            "c3": self.channels[2],
            "c4": self.channels[3],
            "c5": self.channels[4],
        }

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        x = self.stem(x)        # Stride 2
        c2 = self.stage1(x)     # Stride 4
        
        c3 = self.stage2(c2)    # Stride 8
        c4 = self.stage3(c3)    # Stride 16
        c5 = self.stage4(c4)    # Stride 32
        
        return {
            "c2": c2,
            "c3": c3,
            "c4": c4,
            "c5": c5,
        }

    def get_feature_channels(self) -> dict[str, int]:
        return self._channels.copy()


# Register backbone
BackboneFactory.register("colornet_v1", ColorNetV1Backbone)
