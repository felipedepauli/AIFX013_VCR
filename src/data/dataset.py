"""Dataset for loading samples from manifest."""

from pathlib import Path
from typing import Any, Callable

from PIL import Image
from torch.utils.data import Dataset

from src.utils.manifest_io import read_manifest


class ManifestDataset(Dataset):
    """Dataset that loads samples from a manifest file.

    Supports:
    - Loading from crop_path (pre-cropped images)
    - On-the-fly cropping from image_path + bbox_xyxy
    """

    def __init__(
        self,
        manifest_path: str | Path,
        split: str | None = None,
        transform: Callable | None = None,
        use_crop_path: bool = True,
    ) -> None:
        """Initialize dataset.

        Args:
            manifest_path: Path to manifest JSONL file.
            split: Filter by split ('train', 'val', 'test') or None for all.
            transform: Image transform function.
            use_crop_path: If True, load from crop_path. If False, crop on-the-fly.
        """
        self.manifest_path = Path(manifest_path)
        self.transform = transform
        self.use_crop_path = use_crop_path

        # Load manifest
        all_records = read_manifest(self.manifest_path)

        # Filter by split if specified
        if split is not None:
            self.records = [r for r in all_records if r.get("split") == split]
        else:
            self.records = all_records

        # Build index for quick label lookup
        self._labels = [r.get("label_idx", r.get("label", 0)) for r in self.records]

    def __len__(self) -> int:
        """Return number of samples."""
        return len(self.records)

    def __getitem__(self, idx: int) -> tuple[Any, int]:
        """Get a sample.

        Args:
            idx: Sample index.

        Returns:
            Tuple of (image_tensor, label_idx).
        """
        record = self.records[idx]

        # Load image
        if self.use_crop_path and "crop_path" in record:
            # Load pre-cropped image
            image_path = record["crop_path"]
            image = Image.open(image_path).convert("RGB")
        else:
            # Load full image and crop
            image_path = record["image_path"]
            image = Image.open(image_path).convert("RGB")

            if "bbox_xyxy" in record:
                bbox = record["bbox_xyxy"]
                image = image.crop((int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])))

        # Apply transforms
        if self.transform is not None:
            image = self.transform(image)

        # Get label
        label = record.get("label_idx", 0)
        if isinstance(label, str):
            label = 0  # Fallback if label_idx not set

        return image, label

    def get_class_counts(self) -> list[int]:
        """Get sample counts per class.

        Returns:
            List where index i = count of class i.
        """
        from collections import Counter
        counts = Counter(self._labels)
        num_classes = max(counts.keys()) + 1
        return [counts.get(i, 0) for i in range(num_classes)]

    def get_sample_weights(self) -> list[float]:
        """Get sample weights for WeightedRandomSampler.

        Returns:
            List of weights, one per sample.
        """
        class_counts = self.get_class_counts()
        weights = []
        for label in self._labels:
            count = class_counts[label] if label < len(class_counts) else 1
            weights.append(1.0 / max(count, 1))
        return weights
