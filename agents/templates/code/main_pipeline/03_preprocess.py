#!/usr/bin/env python3
"""03_preprocess.py - Validate and prepare dataset for training.

This script:
1. Validates manifest entries (checks images exist, labels present)
2. Encodes string labels to indices (class_to_idx.json)
3. Splits data using GroupShuffleSplit (train/val/test)
4. Outputs manifest_ready.jsonl with split assignments

Usage:
    python 03_preprocess.py --manifest data/manifests/manifest_raw_labeled.jsonl
    python 03_preprocess.py --config config.yaml
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


class Step03Preprocess(PipelineStep):
    """Pipeline step for preprocessing and validation."""

    @property
    def name(self) -> str:
        return "03_preprocess"

    @property
    def description(self) -> str:
        return "Validate manifest, encode labels, and split data."

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.manifest_path: Path | None = None
        self.output_manifest: Path = Path("data/manifests/manifest_ready.jsonl")
        self.output_dir: Path = Path("data/processed")
        self.group_by: str = "camera_id"
        self.seed: int = 42

    def validate(self) -> bool:
        """Validate that manifest exists."""
        if self.manifest_path is None or not self.manifest_path.exists():
            logger.error(f"Manifest not found: {self.manifest_path}")
            return False
        return True

    def run(self) -> int:
        """Execute preprocessing.

        Returns:
            0 on success, 1 on failure.
        """
        if not self.validate():
            return 1

        # TODO: Implement preprocessing logic
        # 1. Load and validate records
        # 2. Build class mapping
        # 3. Split data
        # 4. Save outputs

        logger.info("Step03Preprocess completed.")
        return 0


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Preprocess manifest.")
    parser.add_argument("--manifest", type=str, help="Path to input manifest")
    parser.add_argument("--config", type=str, default="config.yaml")
    parser.add_argument("--output-manifest", type=str, default="data/manifests/manifest_ready.jsonl")
    parser.add_argument("--output-dir", type=str, default="data/processed")
    parser.add_argument("--group-by", type=str, default="camera_id")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    step = Step03Preprocess(config={})
    step.manifest_path = Path(args.manifest) if args.manifest else None
    step.output_manifest = Path(args.output_manifest)
    step.output_dir = Path(args.output_dir)
    step.group_by = args.group_by
    step.seed = args.seed

    return step.run()


if __name__ == "__main__":
    sys.exit(main())
