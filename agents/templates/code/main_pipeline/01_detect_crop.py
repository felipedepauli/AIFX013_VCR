#!/usr/bin/env python3
"""01_detect_crop.py - Vehicle detection and cropping.

This script detects vehicles in raw images and generates:
- data/manifests/manifest_raw.jsonl (detection manifest)
- data/crops/ (optional cropped images)

Usage:
    python 01_detect_crop.py --config config.yaml
    python 01_detect_crop.py --detector yolo --save-crops
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from .00_interface import PipelineStep

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Step01DetectCrop(PipelineStep):
    """Pipeline step for vehicle detection and cropping."""

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
        self.save_crops: bool = True

    def validate(self) -> bool:
        """Validate that required directories exist."""
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

        # TODO: Implement detection logic
        # 1. Find all images in raw_dir
        # 2. Run detector on images
        # 3. Optionally crop and save
        # 4. Write manifest

        logger.info("Step01DetectCrop completed.")
        return 0


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Detect vehicles and generate manifest.",
    )
    parser.add_argument("--config", type=str, default="config.yaml")
    parser.add_argument("--detector", type=str, choices=["yolo", "manual"], default="yolo")
    parser.add_argument("--save-crops", type=int, choices=[0, 1], default=1)
    parser.add_argument("--raw-dir", type=str, help="Directory with raw images")
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    step = Step01DetectCrop(config={"detector": args.detector})
    step.raw_dir = Path(args.raw_dir) if args.raw_dir else Path("data/raw")
    step.save_crops = bool(args.save_crops)

    return step.run()


if __name__ == "__main__":
    sys.exit(main())
