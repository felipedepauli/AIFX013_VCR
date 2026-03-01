#!/usr/bin/env python3
"""04_model.py - VCR Model definition.

This module defines the VCRModel which combines:
- Backbone (ResNet or EfficientNet)
- Multi-Scale Feature Fusion (MSFF)
- Classification head

Usage:
    python 04_model.py --test  # Run a forward pass test
"""

import argparse
import sys
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn

# Import to trigger factory registrations
import src.backbones  # noqa: F401
import src.fusion  # noqa: F401
import src.losses  # noqa: F401

from src.core.factories import BackboneFactory, FusionFactory, LossFactory
from src.core.interfaces import PipelineStep
from src.utils.config import load_config


class VCRModel(nn.Module):
    """Vehicle Color Recognition Model.

    Combines:
    - Backbone: Feature extraction (ResNet/EfficientNet)
    - Fusion: Multi-scale feature fusion (MSFF)
    - Head: Classification head
    """

    def __init__(
        self,
        num_classes: int,
        backbone_name: str = "resnet50",
        backbone_cfg: dict[str, Any] | None = None,
        fusion_name: str = "msff",
        fusion_cfg: dict[str, Any] | None = None,
        dropout: float = 0.2,
    ) -> None:
        """Initialize VCR Model.

        Args:
            num_classes: Number of color classes.
            backbone_name: Backbone to use ('resnet50', 'efficientnet_b4', etc.)
            backbone_cfg: Backbone configuration.
            fusion_name: Fusion module ('msff' or 'simple_concat').
            fusion_cfg: Fusion configuration.
            dropout: Dropout rate before classifier.
        """
        super().__init__()

        self.num_classes = num_classes

        # Build backbone
        backbone_cfg = backbone_cfg or {"pretrained": True}
        # Map backbone name to variant if needed
        if "resnet" in backbone_name:
            backbone_cfg["variant"] = backbone_name
        elif "efficientnet" in backbone_name:
            backbone_cfg["variant"] = backbone_name

        self.backbone = BackboneFactory.create(backbone_name, backbone_cfg)

        # Get channel info from backbone
        channels = self.backbone.get_feature_channels()

        # Build fusion
        fusion_cfg = fusion_cfg or {}
        fusion_cfg["in_channels"] = channels
        self.fusion = FusionFactory.create(fusion_name, fusion_cfg)

        # Classification head
        fusion_out = self.fusion.get_output_channels()
        self.head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(fusion_out, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input images (B, 3, H, W).

        Returns:
            Logits (B, num_classes).
        """
        # Extract multi-scale features
        features = self.backbone(x)

        # Fuse features
        fused = self.fusion(features)

        # Classify
        logits = self.head(fused)

        return logits

    def get_num_params(self, trainable_only: bool = True) -> int:
        """Count model parameters.

        Args:
            trainable_only: Count only trainable parameters.

        Returns:
            Number of parameters.
        """
        if trainable_only:
            return sum(p.numel() for p in self.parameters() if p.requires_grad)
        return sum(p.numel() for p in self.parameters())


def create_model_from_config(cfg: dict[str, Any], num_classes: int) -> VCRModel:
    """Create VCRModel from configuration.

    Args:
        cfg: Configuration dict (from config.yaml).
        num_classes: Number of classes.

    Returns:
        VCRModel instance.
    """
    model_cfg = cfg.get("model", {})

    return VCRModel(
        num_classes=num_classes,
        backbone_name=model_cfg.get("backbone", "resnet50"),
        backbone_cfg={"pretrained": model_cfg.get("pretrained", True)},
        fusion_name=model_cfg.get("fusion", "msff"),
        fusion_cfg=model_cfg.get("fusion_cfg", {}),
        dropout=model_cfg.get("dropout", 0.2),
    )


def print_model_summary(
    model: VCRModel,
    input_size: tuple[int, int, int, int] = (1, 3, 224, 224),
    verbose: int = 1,
) -> None:
    """Print detailed model summary using torchinfo.

    Args:
        model: VCRModel instance.
        input_size: Input tensor size (B, C, H, W).
        verbose: 0=minimal, 1=default, 2=detailed.
    """
    from torchinfo import summary

    print("\n" + "=" * 80)
    print("VCR MODEL SUMMARY")
    print("=" * 80)

    summary(
        model,
        input_size=input_size,
        col_names=["input_size", "output_size", "num_params", "trainable"],
        col_width=20,
        row_settings=["var_names"],
        verbose=verbose,
    )

    print("\n" + "-" * 80)
    print(f"Backbone: {model.backbone.variant if hasattr(model.backbone, 'variant') else 'unknown'}")
    print(f"Fusion: {model.fusion.__class__.__name__}")
    print(f"Num classes: {model.num_classes}")
    print(f"Total params: {model.get_num_params() / 1e6:.2f}M")
    print("-" * 80 + "\n")


def test_model():
    """Test model forward pass."""
    print("Testing VCRModel...")

    # Create model
    model = VCRModel(
        num_classes=10,
        backbone_name="resnet50",
        fusion_name="msff",
    )

    print(f"Model created with {model.get_num_params() / 1e6:.2f}M trainable parameters")

    # Test forward pass
    x = torch.randn(2, 3, 224, 224)
    model.eval()

    with torch.no_grad():
        logits = model(x)

    print(f"Input shape: {x.shape}")
    print(f"Output shape: {logits.shape}")
    assert logits.shape == (2, 10), f"Expected (2, 10), got {logits.shape}"

    print("✓ Forward pass successful!")

    # Test with EfficientNet
    print("\nTesting with EfficientNet backbone...")
    model_eff = VCRModel(
        num_classes=10,
        backbone_name="efficientnet_b0",
        fusion_name="simple_concat",
    )
    print(f"EfficientNet model: {model_eff.get_num_params() / 1e6:.2f}M params")

    with torch.no_grad():
        logits_eff = model_eff(x)

    print(f"Output shape: {logits_eff.shape}")
    print("✓ EfficientNet forward pass successful!")


class Step04Model(PipelineStep):
    """Pipeline step for model definition and testing.

    This step:
    1. Creates or loads a VCRModel
    2. Optionally runs forward pass tests
    3. Prints model summary
    """

    @property
    def name(self) -> str:
        return "04_model"

    @property
    def description(self) -> str:
        return "Define and test VCR model architecture."

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.backbone_name: str = "resnet50"
        self.fusion_name: str = "msff"
        self.num_classes: int = 10
        self.run_test: bool = False
        self.run_test: bool = False
        self.show_summary: bool = False
        self.fusion_channels: int | None = None

    def validate(self) -> bool:
        """Validate configuration."""
        return True

    def run(self) -> int:
        """Execute model step.

        Returns:
            0 on success, 1 on failure.
        """
        if self.run_test:
            test_model()
            return 0

        fusion_cfg = {}
        if self.fusion_channels:
            fusion_cfg["out_channels"] = self.fusion_channels

        # Create model
        model = VCRModel(
            num_classes=self.num_classes,
            backbone_name=self.backbone_name,
            fusion_name=self.fusion_name,
            fusion_cfg=fusion_cfg,
        )

        if self.show_summary:
            print_model_summary(model)
        else:
            print(f"VCRModel: {model.get_num_params() / 1e6:.2f}M parameters")
            print(f"  Backbone: {self.backbone_name}")
            print(f"  Fusion: {self.fusion_name}")
            print(f"  Classes: {self.num_classes}")
            print("\nUse --summary for detailed layer-by-layer breakdown")

        print("Step04Model completed successfully.")
        return 0


def main():
    parser = argparse.ArgumentParser(description="VCR Model")
    parser.add_argument("--test", action="store_true", help="Run forward pass test")
    parser.add_argument("--summary", action="store_true", help="Show model summary")
    parser.add_argument("--backbone", type=str, default="resnet50",
                        choices=["resnet18", "resnet34", "resnet50", "efficientnet_b0", "efficientnet_b4", "convnext_tiny", "convnext_small", "convnext_base", "mobilenetv4_small", "colornet_v1"],
                        help="Backbone architecture")
    parser.add_argument("--fusion", type=str, default="msff",
                        choices=["msff", "simple_concat", "global_concat"],
                        help="Fusion module")
    parser.add_argument("--num-classes", type=int, default=10, help="Number of classes")
    parser.add_argument("--fusion-channels", type=int, default=None, help="Fusion output channels")
    parser.add_argument("--config", type=str, default="config.yaml", help="Config file")

    args = parser.parse_args()

    step = Step04Model(config={})
    step.backbone_name = args.backbone
    step.fusion_name = args.fusion
    step.num_classes = args.num_classes
    step.run_test = args.test
    step.show_summary = args.summary
    step.fusion_channels = args.fusion_channels

    return step.run()


if __name__ == "__main__":
    sys.exit(main())

