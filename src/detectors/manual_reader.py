"""Manual bounding box reader.

Reads pre-existing bounding boxes from JSON or CSV files.
Useful when detections have already been performed externally.
"""

import csv
import json
from pathlib import Path
from typing import Any

from src.core.factories import DetectorFactory
from src.core.interfaces import BaseDetector, BBox, DetectionResult


class ManualBBoxReader(BaseDetector):
    """Reads bounding boxes from annotation files.

    Supports two modes:
    1. Per-image JSON files (image.jpg -> image.json)
    2. Single CSV/JSONL file with all annotations

    JSON format per image:
    {
        "bboxes": [
            {"x1": 10, "y1": 20, "x2": 100, "y2": 200, "label": "white"},
            ...
        ]
    }

    CSV format:
    image_path,x1,y1,x2,y2,label
    img001.jpg,10,20,100,200,white

    JSONL format:
    {"image_path": "img001.jpg", "bbox_xyxy": [10,20,100,200], "label": "white"}
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        """Initialize manual reader.

        Args:
            cfg: Configuration dictionary with keys:
                - annotations_file: Path to CSV/JSONL with all annotations (optional)
                - annotations_dir: Directory with per-image JSON files (optional)
                - bbox_format: "xyxy" or "xywh" (default: "xyxy")
                    - "xyxy": [x1, y1, x2, y2]
                    - "xywh": [x, y, width, height]
        """
        self.annotations_file = cfg.get("annotations_file")
        self.annotations_dir = cfg.get("annotations_dir")
        self.bbox_format = cfg.get("bbox_format", "xyxy")

        # Pre-load annotations if a file is specified
        self._annotations_cache: dict[str, list[dict]] = {}
        if self.annotations_file:
            self._load_annotations_file(self.annotations_file)

    def _load_annotations_file(self, path: str) -> None:
        """Load annotations from CSV or JSONL file."""
        path = Path(path)

        if path.suffix == ".csv":
            self._load_csv(path)
        elif path.suffix in (".jsonl", ".json"):
            self._load_jsonl(path)
        else:
            raise ValueError(f"Unsupported annotation format: {path.suffix}")

    def _load_csv(self, path: Path) -> None:
        """Load annotations from CSV."""
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                image_path = row["image_path"]
                bbox_data = {
                    "x1": float(row["x1"]),
                    "y1": float(row["y1"]),
                    "x2": float(row["x2"]),
                    "y2": float(row["y2"]),
                    "label": row.get("label", ""),
                }
                if image_path not in self._annotations_cache:
                    self._annotations_cache[image_path] = []
                self._annotations_cache[image_path].append(bbox_data)

    def _load_jsonl(self, path: Path) -> None:
        """Load annotations from JSONL."""
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                image_path = record.get("image_path", "")

                # Support both formats
                if "bbox_xyxy" in record:
                    bbox = record["bbox_xyxy"]
                    bbox_data = {
                        "x1": bbox[0],
                        "y1": bbox[1],
                        "x2": bbox[2],
                        "y2": bbox[3],
                        "label": record.get("label", ""),
                    }
                else:
                    bbox_data = {
                        "x1": record.get("x1", 0),
                        "y1": record.get("y1", 0),
                        "x2": record.get("x2", 0),
                        "y2": record.get("y2", 0),
                        "label": record.get("label", ""),
                    }

                if image_path not in self._annotations_cache:
                    self._annotations_cache[image_path] = []
                self._annotations_cache[image_path].append(bbox_data)

    def _load_per_image_json(self, image_path: str) -> list[dict]:
        """Load annotations from per-image JSON file.

        Supports multiple formats:
        1. {"bboxes": [{"x1":..., "y1":..., "x2":..., "y2":..., "label":...}]}
        2. [{"rect": [x1,y1,x2,y2], "color": "...", "label": "..."}]  (PRF format)
        """
        image_path = Path(image_path)

        # Try multiple JSON locations
        json_candidates = []
        if self.annotations_dir:
            json_candidates.append(
                Path(self.annotations_dir) / f"{image_path.stem}.json"
            )
        json_candidates.append(image_path.with_suffix(".json"))

        for json_path in json_candidates:
            if json_path.exists():
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Handle different formats
                if isinstance(data, list):
                    # PRF format: list of objects with rect and color
                    bboxes = []
                    for item in data:
                        bbox_data = {}

                        # Get bounding box
                        if "rect" in item:
                            rect = item["rect"]
                            
                            # Parse based on configured format
                            if self.bbox_format == "xywh":
                                # Format: [x, y, width, height]
                                x, y, w, h = rect[0], rect[1], rect[2], rect[3]
                                bbox_data["x1"] = x
                                bbox_data["y1"] = y
                                bbox_data["x2"] = x + w
                                bbox_data["y2"] = y + h
                            else:  # "xyxy" (default)
                                # Format: [x1, y1, x2, y2]
                                bbox_data["x1"] = rect[0]
                                bbox_data["y1"] = rect[1]
                                bbox_data["x2"] = rect[2]
                                bbox_data["y2"] = rect[3]
                        elif "bbox_xyxy" in item:
                            bbox = item["bbox_xyxy"]
                            bbox_data["x1"] = bbox[0]
                            bbox_data["y1"] = bbox[1]
                            bbox_data["x2"] = bbox[2]
                            bbox_data["y2"] = bbox[3]

                        # Get label (prefer "color" for VCR, fallback to "label")
                        bbox_data["label"] = item.get("color") or item.get("label", "")

                        # Store additional metadata
                        bbox_data["vehicle_type"] = item.get("label", "")  # car, truck, etc.
                        bbox_data["brand"] = item.get("brand", "")
                        bbox_data["model"] = item.get("model", "")

                        if bbox_data.get("x1") is not None:
                            bboxes.append(bbox_data)

                    return bboxes

                elif isinstance(data, dict):
                    # Standard format with "bboxes" key
                    return data.get("bboxes", [])

        return []

    def _convert_bbox(self, bbox_data: dict) -> BBox:
        """Convert bbox dict to BBox object.
        
        Note: xywh->xyxy conversion is already done in _load_per_image_json,
        so we always read x1, y1, x2, y2 here.
        """
        x1 = bbox_data.get("x1", 0)
        y1 = bbox_data.get("y1", 0)
        x2 = bbox_data.get("x2", 0)
        y2 = bbox_data.get("y2", 0)

        return BBox(
            x1=float(x1),
            y1=float(y1),
            x2=float(x2),
            y2=float(y2),
            confidence=float(bbox_data.get("confidence", 1.0)),
            class_id=int(bbox_data.get("class_id", -1)),
            label=str(bbox_data.get("label", "")),
        )

    def detect(self, image_path: str) -> DetectionResult:
        """Read bounding boxes for a single image.

        Args:
            image_path: Path to the input image.

        Returns:
            DetectionResult with pre-existing bounding boxes.
        """
        # Normalize path for lookup
        image_key = Path(image_path).name

        # Check cache first (from annotations file)
        if image_key in self._annotations_cache:
            bbox_list = self._annotations_cache[image_key]
        elif image_path in self._annotations_cache:
            bbox_list = self._annotations_cache[image_path]
        else:
            # Try per-image JSON
            bbox_list = self._load_per_image_json(image_path)

        bboxes = [self._convert_bbox(b) for b in bbox_list]

        return DetectionResult(
            image_path=image_path,
            bboxes=bboxes,
            metadata={"source": "manual"},
        )

    def detect_batch(self, image_paths: list[str]) -> list[DetectionResult]:
        """Read bounding boxes for multiple images.

        Args:
            image_paths: List of paths to input images.

        Returns:
            List of DetectionResult objects.
        """
        return [self.detect(p) for p in image_paths]


# Register with factory
DetectorFactory.register("manual", ManualBBoxReader)
