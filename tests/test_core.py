"""Tests for core interfaces and factories."""

import pytest
import torch

from src.core.interfaces import BaseBackbone, BaseDetector, BaseFusion, BaseLoss, BBox, DetectionResult
from src.core.factories import BackboneFactory, DetectorFactory, FusionFactory, LossFactory


class TestBBox:
    """Tests for BBox dataclass."""

    def test_bbox_creation(self):
        bbox = BBox(x1=10, y1=20, x2=100, y2=200)
        assert bbox.x1 == 10
        assert bbox.y1 == 20
        assert bbox.x2 == 100
        assert bbox.y2 == 200
        assert bbox.confidence == 1.0  # default
        assert bbox.class_id == -1  # default

    def test_bbox_to_xyxy(self):
        bbox = BBox(x1=10, y1=20, x2=100, y2=200, confidence=0.9, class_id=2)
        assert bbox.to_xyxy() == [10, 20, 100, 200]


class TestDetectionResult:
    """Tests for DetectionResult dataclass."""

    def test_detection_result_creation(self):
        bboxes = [BBox(0, 0, 50, 50), BBox(60, 60, 100, 100)]
        result = DetectionResult(image_path="/path/to/img.jpg", bboxes=bboxes)
        assert result.image_path == "/path/to/img.jpg"
        assert len(result.bboxes) == 2
        assert result.metadata is None


class TestFactoryRegistry:
    """Tests for factory registration pattern."""

    def test_detector_factory_register_and_create(self):
        # Create a mock detector
        class MockDetector(BaseDetector):
            def __init__(self, cfg):
                self.cfg = cfg

            def detect(self, image_path):
                return DetectionResult(image_path=image_path, bboxes=[])

            def detect_batch(self, image_paths):
                return [self.detect(p) for p in image_paths]

        # Register and create
        DetectorFactory.register("mock", MockDetector)
        detector = DetectorFactory.create("mock", {"key": "value"})

        assert isinstance(detector, MockDetector)
        assert detector.cfg == {"key": "value"}
        assert "mock" in DetectorFactory.available()

    def test_detector_factory_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown detector"):
            DetectorFactory.create("nonexistent", {})

    def test_backbone_factory_register_and_create(self):
        class MockBackbone(BaseBackbone):
            def __init__(self, cfg):
                super().__init__()
                self.cfg = cfg

            def forward(self, x):
                return {"c2": x, "c3": x, "c4": x, "c5": x}

            def get_feature_channels(self):
                return {"c2": 64, "c3": 128, "c4": 256, "c5": 512}

        BackboneFactory.register("mock_backbone", MockBackbone)
        backbone = BackboneFactory.create("mock_backbone", {"pretrained": True})

        assert isinstance(backbone, MockBackbone)
        assert "mock_backbone" in BackboneFactory.available()

    def test_loss_factory_register_and_create(self):
        class MockLoss(BaseLoss):
            def __init__(self, cfg):
                super().__init__()
                self.cfg = cfg

            def forward(self, logits, targets, **kwargs):
                return torch.tensor(0.0)

        LossFactory.register("mock_loss", MockLoss)
        loss = LossFactory.create("mock_loss", {"gamma": 2.0})

        assert isinstance(loss, MockLoss)
        assert "mock_loss" in LossFactory.available()

    def test_fusion_factory_register_and_create(self):
        class MockFusion(BaseFusion):
            def __init__(self, cfg):
                super().__init__()
                self.cfg = cfg

            def forward(self, features):
                return features["c5"]

            def get_output_channels(self):
                return 512

        FusionFactory.register("mock_fusion", MockFusion)
        fusion = FusionFactory.create("mock_fusion", {})

        assert isinstance(fusion, MockFusion)
        assert "mock_fusion" in FusionFactory.available()


class TestInterfaceContracts:
    """Tests to verify interface contracts."""

    def test_backbone_returns_correct_keys(self):
        class TestBackbone(BaseBackbone):
            def __init__(self):
                super().__init__()

            def forward(self, x):
                b, c, h, w = x.shape
                return {
                    "c2": torch.randn(b, 64, h // 4, w // 4),
                    "c3": torch.randn(b, 128, h // 8, w // 8),
                    "c4": torch.randn(b, 256, h // 16, w // 16),
                    "c5": torch.randn(b, 512, h // 32, w // 32),
                }

            def get_feature_channels(self):
                return {"c2": 64, "c3": 128, "c4": 256, "c5": 512}

        backbone = TestBackbone()
        x = torch.randn(2, 3, 224, 224)
        features = backbone(x)

        assert set(features.keys()) == {"c2", "c3", "c4", "c5"}
        assert features["c2"].shape == (2, 64, 56, 56)
        assert features["c5"].shape == (2, 512, 7, 7)

    def test_loss_accepts_kwargs(self):
        class TestLoss(BaseLoss):
            def __init__(self):
                super().__init__()

            def forward(self, logits, targets, **kwargs):
                # Should accept any kwargs
                epoch = kwargs.get("epoch", 0)
                class_counts = kwargs.get("class_counts", None)
                return torch.nn.functional.cross_entropy(logits, targets)

        loss_fn = TestLoss()
        logits = torch.randn(4, 10)
        targets = torch.randint(0, 10, (4,))

        # Should work with no kwargs
        loss1 = loss_fn(logits, targets)
        assert loss1.shape == ()

        # Should work with kwargs
        loss2 = loss_fn(logits, targets, epoch=5, class_counts=[100, 50, 25])
        assert loss2.shape == ()
