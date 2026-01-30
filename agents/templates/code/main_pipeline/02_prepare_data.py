#!/usr/bin/env python3
"""02_prepare_data.py - Prepare dataset for a specific experiment.

This script:
1. Loads the labeled dataset from data/{dataset}/manifests/
2. Applies splits (Train/Val/Test)
3. Generates experiment-specific manifest in runs/{experiment}/data/
4. Saves preprocessing config for reproducibility

Usage:
    python 02_prepare_data.py --dataset prf_v1 --experiment exp_001
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


class Step02PrepareData(PipelineStep):
    """Pipeline step for preparing data splits and encoding labels."""

    @property
    def name(self) -> str:
        return "02_prepare_data"

    @property
    def description(self) -> str:
        return "Prepare dataset: load, split, and encode labels."

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.dataset_name: str = ""
        self.experiment_name: str = ""
        self.seed: int = 42

    def validate(self) -> bool:
        """Validate that dataset exists."""
        if not self.dataset_name:
            logger.error("Dataset name is required.")
            return False
        return True

    def run(self) -> int:
        """Execute data preparation.

        Returns:
            0 on success, 1 on failure.
        """
        if not self.validate():
            return 1

        # TODO: Implement data preparation logic
        # 1. Load manifest from dataset
        # 2. Apply train/val/test split
        # 3. Build class mapping
        # 4. Save experiment manifest and metadata

        logger.info("Step02PrepareData completed.")
        return 0


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Prepare dataset for experiment.")
    parser.add_argument("--dataset", required=True, help="Dataset name (e.g. prf_v1)")
    parser.add_argument("--experiment", required=True, help="Experiment name (e.g. exp_001)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for splitting")
    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    step = Step02PrepareData(config={})
    step.dataset_name = args.dataset
    step.experiment_name = args.experiment
    step.seed = args.seed

    return step.run()


if __name__ == "__main__":
    sys.exit(main())
