#!/usr/bin/env python3
"""07_infer.py - Run inference on images.

Usage:
    # Single image
    python 07_infer.py --checkpoint runs/train/best.pt --image data/crops/test.jpg

    # Manifest (batch)
    python 07_infer.py --checkpoint runs/train/best.pt --manifest data/manifests/manifest_ready.jsonl --split test

    # Directory of images
    python 07_infer.py --checkpoint runs/train/best.pt --image-dir data/crops/ --output predictions.jsonl
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


class Step07Infer(PipelineStep):
    """Pipeline step for running inference."""

    @property
    def name(self) -> str:
        return "07_infer"

    @property
    def description(self) -> str:
        return "Run inference on images using a trained model."

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.checkpoint_path: Path | None = None
        self.image_path: Path | None = None
        self.image_dir: Path | None = None
        self.manifest_path: Path | None = None
        self.output_path: Path = Path("predictions.jsonl")
        self.device: str = "auto"
        self.batch_size: int = 32

    def validate(self) -> bool:
        """Validate that checkpoint exists."""
        if self.checkpoint_path is None or not self.checkpoint_path.exists():
            logger.error(f"Checkpoint not found: {self.checkpoint_path}")
            return False
        return True

    def run(self) -> int:
        """Execute inference.

        Returns:
            0 on success, 1 on failure.
        """
        if not self.validate():
            return 1

        # TODO: Implement inference logic
        # 1. Load model from checkpoint
        # 2. Run inference on input (single image, directory, or manifest)
        # 3. Save predictions

        logger.info("Step07Infer completed.")
        return 0


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run inference with trained model.")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--class-names", type=str, default="data/processed/class_to_idx.json")

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--image", type=str, help="Single image path")
    input_group.add_argument("--image-dir", type=str, help="Directory with images")
    input_group.add_argument("--manifest", type=str, help="Manifest file for batch inference")

    parser.add_argument("--split", type=str, default=None)
    parser.add_argument("--output", type=str, default="predictions.jsonl")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", type=str, default="auto")
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    step = Step07Infer(config={})
    step.checkpoint_path = Path(args.checkpoint)
    step.output_path = Path(args.output)
    step.device = args.device
    step.batch_size = args.batch_size

    if args.image:
        step.image_path = Path(args.image)
    elif args.image_dir:
        step.image_dir = Path(args.image_dir)
    elif args.manifest:
        step.manifest_path = Path(args.manifest)

    return step.run()


if __name__ == "__main__":
    sys.exit(main())
