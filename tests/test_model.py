"""Tests for model components."""

import torch
import pytest

# Import to trigger factory registrations
import src.backbones
import src.fusion
import src.losses

from src.core.factories import BackboneFactory, FusionFactory, LossFactory


class TestBackbones:
    """Tests for backbone implementations."""

    def test_resnet50_forward(self):
        """Test ResNet50 forward pass."""
        backbone = BackboneFactory.create("resnet50", {"pretrained": False})
        x = torch.randn(2, 3, 224, 224)

        features = backbone(x)

        assert set(features.keys()) == {"c2", "c3", "c4", "c5"}
        assert features["c2"].shape[1] == 256
        assert features["c5"].shape[1] == 2048

    def test_resnet18_forward(self):
        """Test ResNet18 forward pass."""
        backbone = BackboneFactory.create("resnet18", {"variant": "resnet18", "pretrained": False})
        x = torch.randn(2, 3, 224, 224)

        features = backbone(x)

        assert features["c2"].shape[1] == 64
        assert features["c5"].shape[1] == 512

    def test_efficientnet_forward(self):
        """Test EfficientNet forward pass."""
        backbone = BackboneFactory.create("efficientnet_b0", {"variant": "efficientnet_b0", "pretrained": False})
        x = torch.randn(2, 3, 224, 224)

        features = backbone(x)

        assert set(features.keys()) == {"c2", "c3", "c4", "c5"}
        # Check channels match what model reports
        channels = backbone.get_feature_channels()
        assert features["c5"].shape[1] == channels["c5"]

    def test_backbone_channels_method(self):
        """Test get_feature_channels returns correct info."""
        backbone = BackboneFactory.create("resnet50", {"pretrained": False})
        channels = backbone.get_feature_channels()

        assert channels == {"c2": 256, "c3": 512, "c4": 1024, "c5": 2048}


class TestFusion:
    """Tests for fusion modules."""

    def test_msff_forward(self):
        """Test MSFF forward pass."""
        cfg = {
            "in_channels": {"c2": 256, "c3": 512, "c4": 1024, "c5": 2048},
            "out_channels": 256,
        }
        fusion = FusionFactory.create("msff", cfg)

        # Create dummy features
        features = {
            "c2": torch.randn(2, 256, 56, 56),
            "c3": torch.randn(2, 512, 28, 28),
            "c4": torch.randn(2, 1024, 14, 14),
            "c5": torch.randn(2, 2048, 7, 7),
        }

        output = fusion(features)

        assert output.shape == (2, 256)
        assert fusion.get_output_channels() == 256

    def test_simple_concat_forward(self):
        """Test simple concat fusion."""
        cfg = {"in_channels": {"c5": 2048}}
        fusion = FusionFactory.create("simple_concat", cfg)

        features = {
            "c2": torch.randn(2, 256, 56, 56),
            "c5": torch.randn(2, 2048, 7, 7),
        }

        output = fusion(features)

        assert output.shape == (2, 2048)


class TestLosses:
    """Tests for loss functions."""

    def test_focal_loss(self):
        """Test Focal Loss computation."""
        loss_fn = LossFactory.create("focal", {"gamma": 2.0})

        logits = torch.randn(4, 10)
        targets = torch.randint(0, 10, (4,))

        loss = loss_fn(logits, targets)

        assert loss.shape == ()
        assert loss >= 0

    def test_focal_loss_with_alpha(self):
        """Test Focal Loss with class weights."""
        loss_fn = LossFactory.create("focal", {"gamma": 2.0})

        logits = torch.randn(4, 3)
        targets = torch.randint(0, 3, (4,))
        alpha = [0.5, 1.0, 2.0]

        loss = loss_fn(logits, targets, alpha=alpha)

        assert loss.shape == ()

    def test_smooth_modulation_loss(self):
        """Test Smooth Modulation Loss."""
        loss_fn = LossFactory.create("smooth_modulation", {"tau": 0.5})

        logits = torch.randn(4, 5)
        targets = torch.randint(0, 5, (4,))
        class_counts = [100, 50, 25, 10, 5]

        loss = loss_fn(logits, targets, class_counts=class_counts, epoch=10)

        assert loss.shape == ()
        assert loss >= 0

    def test_smooth_modulation_without_counts(self):
        """Test Smooth Modulation Loss without class counts (uniform weights)."""
        loss_fn = LossFactory.create("smooth_modulation", {})

        logits = torch.randn(4, 5)
        targets = torch.randint(0, 5, (4,))

        loss = loss_fn(logits, targets)

        assert loss.shape == ()


class TestVCRModel:
    """Tests for complete VCR model."""

    def test_model_forward(self):
        """Test VCRModel forward pass."""
        from importlib.util import spec_from_file_location, module_from_spec
        from pathlib import Path

        spec = spec_from_file_location("model", Path(__file__).parent.parent / "04_model.py")
        model_module = module_from_spec(spec)
        spec.loader.exec_module(model_module)

        model = model_module.VCRModel(
            num_classes=10,
            backbone_name="resnet50",
            backbone_cfg={"pretrained": False},
            fusion_name="msff",
        )

        x = torch.randn(2, 3, 224, 224)
        model.eval()

        with torch.no_grad():
            logits = model(x)

        assert logits.shape == (2, 10)

    def test_model_param_count(self):
        """Test parameter counting."""
        from importlib.util import spec_from_file_location, module_from_spec
        from pathlib import Path

        spec = spec_from_file_location("model", Path(__file__).parent.parent / "04_model.py")
        model_module = module_from_spec(spec)
        spec.loader.exec_module(model_module)

        model = model_module.VCRModel(
            num_classes=10,
            backbone_name="resnet50",
            backbone_cfg={"pretrained": False},
            fusion_name="simple_concat",
        )

        params = model.get_num_params()
        assert params > 20_000_000  # ResNet50 has ~23M params
