# Backbones module
from src.backbones.resnet import ResNetBackbone
from src.backbones.efficientnet import EfficientNetBackbone
from src.backbones.convnext import ConvNeXtBackbone

__all__ = ["ResNetBackbone", "EfficientNetBackbone", "ConvNeXtBackbone"]
