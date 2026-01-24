"""Tests for data module."""

import tempfile
from pathlib import Path

import pytest
import torch

from src.data.transforms import get_train_transforms, get_val_transforms


class TestTransforms:
    """Tests for image transforms."""

    def test_train_transforms_output_shape(self):
        """Test train transforms produce correct output."""
        from PIL import Image
        import numpy as np

        transform = get_train_transforms(image_size=224)
        img = Image.fromarray(np.random.randint(0, 255, (300, 400, 3), dtype=np.uint8))

        result = transform(img)

        assert result.shape == (3, 224, 224)
        assert result.dtype == torch.float32

    def test_val_transforms_output_shape(self):
        """Test val transforms produce correct output."""
        from PIL import Image
        import numpy as np

        transform = get_val_transforms(image_size=224)
        img = Image.fromarray(np.random.randint(0, 255, (300, 400, 3), dtype=np.uint8))

        result = transform(img)

        assert result.shape == (3, 224, 224)

    def test_transforms_normalization(self):
        """Test that normalization is applied."""
        from PIL import Image
        import numpy as np

        transform = get_val_transforms(image_size=64)
        # White image
        img = Image.fromarray(np.ones((100, 100, 3), dtype=np.uint8) * 255)

        result = transform(img)

        # After normalization, values should not be in [0, 1]
        assert result.max() > 1.0 or result.min() < 0.0


class TestManifestDataset:
    """Tests for ManifestDataset."""

    def test_dataset_loading(self, tmp_path):
        """Test dataset loads from manifest."""
        from PIL import Image
        import numpy as np

        # Create test image
        img_dir = tmp_path / "crops"
        img_dir.mkdir()
        img_path = img_dir / "test_0000.jpg"
        img = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        img.save(img_path)

        # Create manifest
        manifest_path = tmp_path / "manifest.jsonl"
        with open(manifest_path, "w") as f:
            f.write('{"id": "test_0000", "crop_path": "' + str(img_path) + '", "label_idx": 0, "split": "train"}\n')
            f.write('{"id": "test_0001", "crop_path": "' + str(img_path) + '", "label_idx": 1, "split": "train"}\n')
            f.write('{"id": "test_0002", "crop_path": "' + str(img_path) + '", "label_idx": 0, "split": "val"}\n')

        from src.data.dataset import ManifestDataset

        # Test loading all
        dataset = ManifestDataset(manifest_path, split=None)
        assert len(dataset) == 3

        # Test loading by split
        train_dataset = ManifestDataset(manifest_path, split="train")
        assert len(train_dataset) == 2

        val_dataset = ManifestDataset(manifest_path, split="val")
        assert len(val_dataset) == 1

    def test_dataset_getitem(self, tmp_path):
        """Test __getitem__ returns correct types."""
        from PIL import Image
        import numpy as np

        # Create test image
        img_dir = tmp_path / "crops"
        img_dir.mkdir()
        img_path = img_dir / "test.jpg"
        img = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        img.save(img_path)

        # Create manifest
        manifest_path = tmp_path / "manifest.jsonl"
        with open(manifest_path, "w") as f:
            f.write('{"id": "test", "crop_path": "' + str(img_path) + '", "label_idx": 2, "split": "train"}\n')

        from src.data.dataset import ManifestDataset

        dataset = ManifestDataset(
            manifest_path,
            transform=get_val_transforms(image_size=64),
        )

        image, label = dataset[0]

        assert image.shape == (3, 64, 64)
        assert label == 2

    def test_class_counts(self, tmp_path):
        """Test get_class_counts method."""
        from PIL import Image
        import numpy as np

        # Create test image
        img_path = tmp_path / "test.jpg"
        img = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        img.save(img_path)

        # Create manifest with class imbalance
        manifest_path = tmp_path / "manifest.jsonl"
        with open(manifest_path, "w") as f:
            for i in range(10):
                f.write('{"id": "' + f'a{i}' + '", "crop_path": "' + str(img_path) + '", "label_idx": 0, "split": "train"}\n')
            for i in range(3):
                f.write('{"id": "' + f'b{i}' + '", "crop_path": "' + str(img_path) + '", "label_idx": 1, "split": "train"}\n')

        from src.data.dataset import ManifestDataset

        dataset = ManifestDataset(manifest_path)
        counts = dataset.get_class_counts()

        assert counts == [10, 3]
