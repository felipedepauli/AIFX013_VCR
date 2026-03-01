"""Directory-based 'detector' for ImageNet style datasets.

Treats the parent directory of an image as its class label.
Assumes the entire image is the bounding box.
"""

from pathlib import Path
from typing import Any
from PIL import Image

from src.core.factories import DetectorFactory
from src.core.interfaces import BaseDetector, BBox, DetectionResult


class DirectoryReader(BaseDetector):
    """Reads labels from directory names (ImageNet format).

    For an image at `dataset/train/blue/car_001.jpg`:
    - Label: "blue"
    - BBox: [0, 0, width, height]
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        """Initialize directory reader.

        Args:
            cfg: Configuration dictionary (can be empty).
        """
        self.cfg = cfg

    def detect(self, image_path: str) -> DetectionResult:
        """Create a detection result from the directory name.

        Args:
            image_path: Path to the input image.

        Returns:
            DetectionResult with a full-image bounding box and directory label.
        """
        path = Path(image_path)
        
        # The label is the name of the parent directory
        label = path.parent.name
        
        # Get image dimensions to create a full-image bounding box
        try:
            with Image.open(path) as img:
                width, height = img.size
        except Exception:
            # Fallback if image cannot be read (will be caught by validation later)
            width, height = 100, 100

        bbox = BBox(
            x1=0.0,
            y1=0.0,
            x2=float(width),
            y2=float(height),
            confidence=1.0,
            class_id=-1,
            label=label,
        )

        return DetectionResult(
            image_path=image_path,
            bboxes=[bbox],
            metadata={"source": "directory"},
        )

    def detect_batch(self, image_paths: list[str]) -> list[DetectionResult]:
        """Process multiple images.

        Args:
            image_paths: List of paths to input images.

        Returns:
            List of DetectionResult objects.
        """
        return [self.detect(p) for p in image_paths]


# Register with factory
DetectorFactory.register("directory", DirectoryReader)
