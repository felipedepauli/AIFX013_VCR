"""YOLO-based vehicle detector.

Uses Ultralytics YOLOv8 for vehicle detection.
"""

from pathlib import Path
from typing import Any

from ultralytics import YOLO

from src.core.factories import DetectorFactory
from src.core.interfaces import BaseDetector, BBox, DetectionResult


class YOLODetector(BaseDetector):
    """Vehicle detector using YOLOv8.

    Detects vehicles (car, bus, truck) in images using a pre-trained YOLO model.
    """

    # COCO class IDs for vehicles
    VEHICLE_CLASSES = {
        2: "car",
        5: "bus",
        7: "truck",
    }

    def __init__(self, cfg: dict[str, Any]) -> None:
        """Initialize YOLO detector.

        Args:
            cfg: Configuration dictionary with keys:
                - model: Model name or path (default: "yolov8n.pt")
                - conf_threshold: Confidence threshold (default: 0.5)
                - classes: List of class IDs to detect (default: [2, 5, 7])
        """
        model_name = cfg.get("model", "yolo11n.pt")
        self.conf_threshold = cfg.get("conf_threshold", 0.5)
        self.classes = cfg.get("classes", [2, 5, 7])

        self.model = YOLO(model_name)

    def detect(self, image_path: str) -> DetectionResult:
        """Detect vehicles in a single image.

        Args:
            image_path: Path to the input image.

        Returns:
            DetectionResult with detected bounding boxes.
        """
        results = self.model(
            image_path,
            conf=self.conf_threshold,
            classes=self.classes,
            verbose=False,
        )

        bboxes = []
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                xyxy = boxes.xyxy[i].cpu().numpy()
                conf = float(boxes.conf[i].cpu().numpy())
                cls_id = int(boxes.cls[i].cpu().numpy())

                bboxes.append(
                    BBox(
                        x1=float(xyxy[0]),
                        y1=float(xyxy[1]),
                        x2=float(xyxy[2]),
                        y2=float(xyxy[3]),
                        confidence=conf,
                        class_id=cls_id,
                    )
                )

        return DetectionResult(image_path=image_path, bboxes=bboxes)

    def detect_batch(self, image_paths: list[str]) -> list[DetectionResult]:
        """Detect vehicles in multiple images.

        Args:
            image_paths: List of paths to input images.

        Returns:
            List of DetectionResult objects.
        """
        results_list = self.model(
            image_paths,
            conf=self.conf_threshold,
            classes=self.classes,
            verbose=False,
        )

        detection_results = []
        for image_path, results in zip(image_paths, results_list):
            bboxes = []
            if results.boxes is not None:
                boxes = results.boxes
                for i in range(len(boxes)):
                    xyxy = boxes.xyxy[i].cpu().numpy()
                    conf = float(boxes.conf[i].cpu().numpy())
                    cls_id = int(boxes.cls[i].cpu().numpy())

                    bboxes.append(
                        BBox(
                            x1=float(xyxy[0]),
                            y1=float(xyxy[1]),
                            x2=float(xyxy[2]),
                            y2=float(xyxy[3]),
                            confidence=conf,
                            class_id=cls_id,
                        )
                    )

            detection_results.append(
                DetectionResult(image_path=image_path, bboxes=bboxes)
            )

        return detection_results


# Register with factory
DetectorFactory.register("yolo", YOLODetector)
