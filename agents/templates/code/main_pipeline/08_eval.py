#!/usr/bin/env python3
"""08_eval.py - Evaluate model performance with long-tail metrics.

Usage:
    python 08_eval.py --predictions predictions.jsonl --class-counts data/processed/class_counts.json
    python 08_eval.py --checkpoint runs/train/best.pt --manifest data/manifests/manifest_ready.jsonl --split test
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


class Step08Eval(PipelineStep):
    """Pipeline step for model evaluation."""

    @property
    def name(self) -> str:
        return "08_eval"

    @property
    def description(self) -> str:
        return "Evaluate model performance and generate metrics."

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.predictions_path: Path | None = None
        self.checkpoint_path: Path | None = None
        self.manifest_path: Path | None = None
        self.split: str = "test"
        self.class_names_path: Path = Path("data/processed/class_to_idx.json")
        self.class_counts_path: Path = Path("data/processed/class_counts.json")
        self.output_dir: Path = Path("runs/eval")
        self.device: str = "auto"

    def validate(self) -> bool:
        """Validate that required inputs exist."""
        if self.predictions_path:
            if not self.predictions_path.exists():
                logger.error(f"Predictions file not found: {self.predictions_path}")
                return False
        elif self.checkpoint_path and self.manifest_path:
            if not self.checkpoint_path.exists():
                logger.error(f"Checkpoint not found: {self.checkpoint_path}")
                return False
            if not self.manifest_path.exists():
                logger.error(f"Manifest not found: {self.manifest_path}")
                return False
        else:
            logger.error("Must provide either --predictions or (--checkpoint and --manifest)")
            return False
        return True

    def run(self) -> int:
        """Execute evaluation.

        Returns:
            0 on success, 1 on failure.
        """
        if not self.validate():
            return 1

        # TODO: Implement evaluation logic
        # 1. Load predictions or run inference
        # 2. Compute metrics
        # 3. Generate plots (confusion matrix, per-class metrics)
        # 4. Save results

        logger.info("Step08Eval completed.")
        return 0


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Evaluate model performance.")
    parser.add_argument("--predictions", type=str, help="Path to predictions.jsonl")
    parser.add_argument("--checkpoint", type=str, help="Path to model checkpoint")
    parser.add_argument("--manifest", type=str, help="Path to manifest")
    parser.add_argument("--split", type=str, default="test")
    parser.add_argument("--class-names", type=str, default="data/processed/class_to_idx.json")
    parser.add_argument("--class-counts", type=str, default="data/processed/class_counts.json")
    parser.add_argument("--output-dir", type=str, default="runs/eval")
    parser.add_argument("--device", type=str, default="auto")
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    step = Step08Eval(config={})
    step.predictions_path = Path(args.predictions) if args.predictions else None
    step.checkpoint_path = Path(args.checkpoint) if args.checkpoint else None
    step.manifest_path = Path(args.manifest) if args.manifest else None
    step.split = args.split
    step.class_names_path = Path(args.class_names)
    step.class_counts_path = Path(args.class_counts)
    step.output_dir = Path(args.output_dir)
    step.device = args.device

    return step.run()


if __name__ == "__main__":
    sys.exit(main())
