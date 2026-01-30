#!/usr/bin/env python3
"""01_detect_crop.py - Vehicle detection and cropping.

This script detects vehicles in raw images and generates:
- data/manifests/manifest_raw.jsonl (detection manifest)
- data/crops/ (optional cropped images)

Usage:
    python 01_detect_crop.py --config config.yaml
    python 01_detect_crop.py --detector yolo --save-crops
    python 01_detect_crop.py --detector manual --annotations data/labels.jsonl
"""

import argparse
import logging
import shutil
import sys
from pathlib import Path
from typing import Any

from PIL import Image

# Import detectors to trigger factory registration
import src.detectors  # noqa: F401
from src.core.factories import DetectorFactory
from src.core.interfaces import BBox, DetectionResult, PipelineStep
from src.utils.config import load_config
from src.utils.manifest_io import write_manifest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def import_data(source_dir: Path, target_dir: Path, extensions: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".json")) -> None:
    """Copy images from source directory to target directory."""
    if not source_dir.exists():
        logger.error(f"Source directory not found: {source_dir}")
        return

    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Find images
    image_files = []
    for ext in extensions:
        image_files.extend(source_dir.rglob(f"*{ext}"))
        image_files.extend(source_dir.rglob(f"*{ext.upper()}"))
    
    image_files = sorted(set(image_files))
    
    if not image_files:
        logger.warning(f"No images found in {source_dir}")
        return

    logger.info(f"Importing {len(image_files)} images from {source_dir} to {target_dir}...")
    
    count = 0
    for file in image_files:
        try:
            # Flatten structure or keep? Let's flatten for "raw" to match manifest expectations easier
            # But preserve unique names if conflicts? For now, simple copy.
            shutil.copy2(file, target_dir / file.name)
            count += 1
        except Exception as e:
            logger.error(f"Failed to copy {file}: {e}")
            
    logger.info(f"Imported {count} images.")



def get_image_files(raw_dir: Path, extensions: tuple[str, ...] = (".jpg", ".jpeg", ".png")) -> list[Path]:
    """Recursively find all image files in a directory."""
    image_files = []
    for ext in extensions:
        image_files.extend(raw_dir.rglob(f"*{ext}"))
        image_files.extend(raw_dir.rglob(f"*{ext.upper()}"))
    return sorted(set(image_files))


def crop_and_save(
    image_path: Path,
    bbox: BBox,
    crop_id: str,
    crops_dir: Path,
) -> Path | None:
    """Crop a region from an image and save it.

    Args:
        image_path: Path to the source image.
        bbox: Bounding box to crop.
        crop_id: Unique identifier for the crop.
        crops_dir: Directory to save crops.

    Returns:
        Path to the saved crop, or None if bbox is invalid.
    """
    # Validate bbox coordinates
    x1, y1, x2, y2 = int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)

    # Auto-fix swapped coordinates
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1

    # Skip if bbox has zero or negative area
    if x2 <= x1 or y2 <= y1:
        logger.warning(f"Invalid bbox for {crop_id}: [{x1}, {y1}, {x2}, {y2}]")
        return None

    crops_dir.mkdir(parents=True, exist_ok=True)

    img = Image.open(image_path)

    # Clamp to image bounds
    width, height = img.size
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(width, x2)
    y2 = min(height, y2)

    crop = img.crop((x1, y1, x2, y2))

    crop_filename = f"{crop_id}.jpg"
    crop_path = crops_dir / crop_filename
    crop.save(crop_path, "JPEG", quality=95)

    return crop_path


def generate_crop_id(image_path: Path, bbox_idx: int) -> str:
    """Generate a unique ID for a crop."""
    stem = image_path.stem
    return f"{stem}_{bbox_idx:04d}"


def build_manifest_record(
    image_path: Path,
    bbox: BBox,
    crop_id: str,
    crop_path: Path | None = None,
    label: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a manifest record for a single detection."""
    record = {
        "id": crop_id,
        "image_path": str(image_path),
        "bbox_xyxy": bbox.to_xyxy(),
        "confidence": bbox.confidence,
    }

    if crop_path:
        record["crop_path"] = str(crop_path)

    # Use bbox.label if available, otherwise use provided label
    final_label = bbox.label or label
    if final_label:
        record["label"] = final_label

    if metadata:
        record["meta"] = metadata

    return record


def run_detection(
    raw_dir: Path,
    manifests_dir: Path,
    crops_dir: Path,
    detector_name: str,
    detector_cfg: dict[str, Any],
    save_crops: bool = True,
    batch_size: int = 16,
) -> None:
    """Run detection pipeline.

    Args:
        raw_dir: Directory containing raw images.
        manifests_dir: Directory to save manifest.
        crops_dir: Directory to save crops.
        detector_name: Name of detector to use ("yolo" or "manual").
        detector_cfg: Detector configuration.
        save_crops: Whether to save cropped images.
        batch_size: Batch size for detection.
    """
    # Find all images
    image_files = get_image_files(raw_dir)
    logger.info(f"Found {len(image_files)} images in {raw_dir}")

    if not image_files:
        logger.warning("No images found. Exiting.")
        return

    # Create detector
    detector = DetectorFactory.create(detector_name, detector_cfg)
    logger.info(f"Using detector: {detector_name}")

    # Process images in batches
    all_records = []
    total_detections = 0
    skipped_invalid = 0

    for batch_start in range(0, len(image_files), batch_size):
        batch_end = min(batch_start + batch_size, len(image_files))
        batch_paths = [str(p) for p in image_files[batch_start:batch_end]]

        logger.info(f"Processing batch {batch_start // batch_size + 1}: images {batch_start + 1}-{batch_end}")

        # Detect
        results = detector.detect_batch(batch_paths)

        # Process results
        for result in results:
            image_path = Path(result.image_path)

            for bbox_idx, bbox in enumerate(result.bboxes):
                crop_id = generate_crop_id(image_path, bbox_idx)

                # Optionally save crop
                crop_path = None
                if save_crops:
                    crop_path = crop_and_save(
                        image_path,
                        bbox,
                        crop_id,
                        crops_dir,
                    )
                    # Skip if crop failed (invalid bbox)
                    if crop_path is None:
                        skipped_invalid += 1
                        continue

                # Build record
                record = build_manifest_record(
                    image_path=image_path,
                    bbox=bbox,
                    crop_id=crop_id,
                    crop_path=crop_path,
                )

                # Add metadata from detection
                if result.metadata:
                    record["meta"] = result.metadata

                all_records.append(record)
                total_detections += 1

    # Write manifest
    manifest_path = manifests_dir / "manifest_raw.jsonl"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    write_manifest(all_records, manifest_path)

    logger.info(f"Wrote {len(all_records)} records to {manifest_path}")
    logger.info(f"Total detections: {total_detections}")
    if skipped_invalid > 0:
        logger.warning(f"Skipped {skipped_invalid} invalid bboxes")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Detect vehicles and generate manifest.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--detector",
        type=str,
        choices=["yolo", "manual"],
        help="Detector to use (overrides config)",
    )
    parser.add_argument(
        "--save-crops",
        type=int,
        choices=[0, 1],
        help="Whether to save crops: 0=no, 1=yes (overrides config)",
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        help="Directory with raw images (overrides config)",
    )
    parser.add_argument(
        "--annotations",
        type=str,
        help="Path to annotations file for manual detector",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size for detection (default: 16)",
    )

    # Data Import Args
    parser.add_argument("--dataset", help="Dataset name (e.g. prf)")
    parser.add_argument("--version", help="Dataset version (e.g. v1)")
    parser.add_argument("--source-dir", help="Source directory to import images from")

    return parser.parse_args()


class Step01DetectCrop(PipelineStep):
    """Pipeline step for vehicle detection and cropping.

    This step:
    1. Finds images in raw_dir
    2. Runs detection (YOLO or manual annotations)
    3. Optionally crops and saves vehicle images
    4. Writes manifest_raw.jsonl
    """

    @property
    def name(self) -> str:
        return "01_detect_crop"

    @property
    def description(self) -> str:
        return "Detect vehicles in images and optionally crop them."

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.raw_dir: Path | None = None
        self.crops_dir: Path | None = None
        self.manifests_dir: Path | None = None
        self.detector_name: str = "yolo"
        self.detector_cfg: dict[str, Any] = {}
        self.save_crops: bool = True
        self.batch_size: int = 16

    def validate(self) -> bool:
        """Validate that raw_dir exists."""
        if self.raw_dir is None or not self.raw_dir.exists():
            logger.error(f"Raw directory does not exist: {self.raw_dir}")
            return False
        return True

    def run(self) -> int:
        """Execute detection and cropping.

        Returns:
            0 on success, 1 on failure.
        """
        if not self.validate():
            return 1

        run_detection(
            raw_dir=self.raw_dir,
            manifests_dir=self.manifests_dir,
            crops_dir=self.crops_dir,
            detector_name=self.detector_name,
            detector_cfg=self.detector_cfg,
            save_crops=self.save_crops,
            batch_size=self.batch_size,
        )

        logger.info("Step01DetectCrop completed successfully.")
        return 0


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Load config
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        logger.warning(f"Config file not found: {args.config}. Using defaults.")
        cfg = {}

    # Create step instance
    step = Step01DetectCrop(config=cfg)

    # Get paths from config or defaults
    paths_cfg = cfg.get("paths", {})
    
    # DETERMINE RAW DIR
    if args.dataset and args.version:
        dataset_name = f"{args.dataset}_{args.version}"
        base_data_dir = Path("data") / dataset_name
        step.raw_dir = base_data_dir / "raw"
        step.crops_dir = base_data_dir / "crops"
        step.manifests_dir = base_data_dir / "manifests"
        
        # IMPORT DATA IF SOURCE PROVIDED
        if args.source_dir:
            import_data(Path(args.source_dir), step.raw_dir)
            
    else:
        # Fallback to config or args
        step.raw_dir = Path(args.raw_dir or paths_cfg.get("raw_dir", "data/raw"))
        step.crops_dir = Path(paths_cfg.get("crops_dir", "data/crops"))
        step.manifests_dir = Path(paths_cfg.get("manifests_dir", "data/manifests"))

    # Get detector config
    detector_cfg = cfg.get("detector", {})
    step.detector_name = args.detector or detector_cfg.get("name", "yolo")

    # Handle save_crops override
    if args.save_crops is not None:
        step.save_crops = bool(args.save_crops)
    else:
        step.save_crops = detector_cfg.get("save_crops", True)

    # Build detector-specific config
    if step.detector_name == "yolo":
        step.detector_cfg = detector_cfg.get("yolo", {})
    elif step.detector_name == "manual":
        step.detector_cfg = {
            "annotations_file": args.annotations or detector_cfg.get("annotations_file"),
            "annotations_dir": detector_cfg.get("annotations_dir"),
        }
    else:
        step.detector_cfg = {}

    step.batch_size = args.batch_size

    # Run the step
    return step.run()


if __name__ == "__main__":
    sys.exit(main())
