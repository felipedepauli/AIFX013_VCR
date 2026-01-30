#!/usr/bin/env python3
"""02_prepare_data.py - Prepare dataset for a specific experiment using Optuna's trial info.

This script:
1. Loads the labeled dataset from data/{dataset}/manifests/
2. Applies splits (Train/Val/Test)
3. Generates experiment-specific manifest in runs/{experiment}/data/
4. Saves preprocessing config for reproducibility

Usage:
    python 02_prepare_data.py --dataset prf_v1 --experiment exp_001
"""

import argparse
import json
import logging
import sys
import yaml
from pathlib import Path
from typing import Any
from collections import Counter

from sklearn.model_selection import GroupShuffleSplit

from src.core.interfaces import PipelineStep

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_yaml(path: Path) -> dict:
    """Load YAML file safely."""
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def load_jsonl(path: Path) -> list[dict]:
    """Load JSONL file."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def save_jsonl(records: list[dict], path: Path) -> None:
    """Save records to JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def extract_group_key(record: dict[str, Any], group_by: str | None) -> str:
    """Extract group key for split stratification."""
    if group_by is None:
        return record["id"]

    # Try to extract from meta
    if "meta" in record and group_by in record["meta"]:
        return str(record["meta"][group_by])

    # Try to extract from ID pattern (e.g., "000000_henrique_00001_0000")
    if group_by == "camera_id":
        parts = record["id"].split("_")
        if len(parts) >= 2:
            return parts[1]

    return record["id"]


def build_class_mapping(records: list[dict]) -> dict[str, int]:
    """Build class-to-index mapping from records."""
    labels = sorted(set(r["label"] for r in records if r.get("label")))
    return {label: idx for idx, label in enumerate(labels)}



def split_data(
    records: list[dict],
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    group_by: str | None = "camera_id",
    seed: int = 42,
) -> list[dict]:
    """Split records into train/val/test sets using GroupShuffleSplit."""
    import numpy as np

    n = len(records)
    groups = np.array([extract_group_key(r, group_by) for r in records])
    indices = np.arange(n)

    # First split: train+val vs test
    if test_ratio > 0:
        gss_test = GroupShuffleSplit(n_splits=1, test_size=test_ratio, random_state=seed)
        trainval_idx, test_idx = next(gss_test.split(indices, groups=groups))
    else:
        trainval_idx = indices
        test_idx = np.array([], dtype=int)

    # Second split: train vs val
    val_size_adjusted = val_ratio / (train_ratio + val_ratio) if (train_ratio + val_ratio) > 0 else 0
    
    if val_size_adjusted > 0 and len(trainval_idx) > 0:
        trainval_groups = groups[trainval_idx]
        gss_val = GroupShuffleSplit(n_splits=1, test_size=val_size_adjusted, random_state=seed)
        train_idx_local, val_idx_local = next(gss_val.split(trainval_idx, groups=trainval_groups))
        train_idx = trainval_idx[train_idx_local]
        val_idx = trainval_idx[val_idx_local]
    else:
        train_idx = trainval_idx
        val_idx = np.array([], dtype=int)

    # Assign splits
    split_map = {}
    for idx in train_idx: split_map[idx] = "train"
    for idx in val_idx: split_map[idx] = "val"
    for idx in test_idx: split_map[idx] = "test"

    for i, record in enumerate(records):
        record["split"] = split_map.get(i, "train")

    return records


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare dataset for experiment.")
    parser.add_argument("--dataset", required=True, help="Dataset name inside data/ (e.g. prf_v1 or prf:v1)")
    parser.add_argument("--experiment", required=True, help="Experiment name (e.g. exp_001)")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for splitting")
    return parser.parse_args()


class Step02PrepareData(PipelineStep):
    """Pipeline step for preparing dataset for an experiment.

    This step:
    1. Loads manifest from dataset directory
    2. Applies train/val/test splits
    3. Encodes labels
    4. Saves experiment data to runs/{experiment}/data/
    """

    @property
    def name(self) -> str:
        return "02_prepare_data"

    @property
    def description(self) -> str:
        return "Prepare dataset: load, split, and encode labels for an experiment."

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.dataset_name: str = ""
        self.experiment_name: str = ""
        self.seed: int = 42
        self.project_root: Path = Path(__file__).parent

    def validate(self) -> bool:
        """Validate that dataset exists."""
        if not self.dataset_name:
            logger.error("Dataset name is required.")
            return False
        dataset_dir = self.project_root / "data" / self.dataset_name.replace(":", "_")
        if not dataset_dir.exists():
            logger.error(f"Dataset not found: {dataset_dir}")
            return False
        return True

    def run(self) -> int:
        """Execute data preparation.

        Returns:
            0 on success, 1 on failure.
        """
        if not self.validate():
            return 1

        data_root = self.project_root / "data"
        dataset_name = self.dataset_name.replace(":", "_")
        dataset_dir = data_root / dataset_name
        runs_dir = self.project_root / "runs"
        exp_dir = runs_dir / self.experiment_name
        exp_data_dir = exp_dir / "data"

        # Load Manifest
        manifest_path = dataset_dir / "manifests" / "manifest_raw_labeled.jsonl"
        if not manifest_path.exists():
            manifest_path = dataset_dir / "manifests" / "manifest_labeled.jsonl"
        if not manifest_path.exists():
            manifest_path = dataset_dir / "manifests" / "manifest_raw.jsonl"
        if not manifest_path.exists():
            logger.error(f"Manifest not found in {dataset_dir}/manifests/")
            return 1

        logger.info(f"Loading manifest from {manifest_path}...")
        records = load_jsonl(manifest_path)
        logger.info(f"Loaded {len(records)} records.")

        # Load Config
        config_path = self.project_root / self.config.get("config_file", "config.yaml")
        config = load_yaml(config_path)

        # Preprocessing settings
        preprocess_cfg = config.get("preprocess", {})
        split_ratios = preprocess_cfg.get("split_ratios", {"train": 0.7, "val": 0.15, "test": 0.15})
        group_by = preprocess_cfg.get("group_by", "camera_id")

        # Apply Split
        logger.info(f"Splitting data (Seed: {self.seed}, GroupBy: {group_by})...")
        records = split_data(
            records,
            train_ratio=split_ratios["train"],
            val_ratio=split_ratios["val"],
            test_ratio=split_ratios["test"],
            group_by=group_by,
            seed=self.seed
        )

        split_counts = Counter(r["split"] for r in records)
        logger.info(f"Split distribution: {dict(split_counts)}")

        # Build and Encode Labels
        logger.info("Encoding labels...")
        class_to_idx = build_class_mapping(records)
        class_counts = dict(Counter(r["label"] for r in records if r.get("label")))

        logger.info(f"Classes ({len(class_to_idx)}): {list(class_to_idx.keys())}")

        for record in records:
            if "label" in record:
                record["label_idx"] = class_to_idx[record["label"]]

        # Prepare Transforms Config
        transforms_config = {
            "source_dataset": self.dataset_name,
            "seed": self.seed,
            "split_ratios": split_ratios,
            "group_by": group_by,
            "transforms": preprocess_cfg.get("transforms", {})
        }

        # Output
        logger.info(f"Saving experiment data to {exp_data_dir}...")
        exp_data_dir.mkdir(parents=True, exist_ok=True)

        output_manifest = exp_data_dir / "manifest.jsonl"
        save_jsonl(records, output_manifest)

        with open(exp_data_dir / "preprocessing.yaml", "w") as f:
            yaml.dump(transforms_config, f)

        with open(exp_data_dir / "class_to_idx.json", "w") as f:
            json.dump(class_to_idx, f, indent=2)
        with open(exp_data_dir / "class_counts.json", "w") as f:
            json.dump(class_counts, f, indent=2)

        # Fix paths if needed
        sample_path = str(records[0].get("crop_path", ""))
        if sample_path.startswith("data/crops/"):
            logger.info("Updating paths in manifest to new structure...")
            for r in records:
                if "crop_path" in r:
                    r["crop_path"] = r["crop_path"].replace("data/crops/", f"data/{self.dataset_name}/crops/")
                if "image_path" in r:
                    r["image_path"] = r["image_path"].replace("data/raw/", f"data/{self.dataset_name}/raw/")
            save_jsonl(records, output_manifest)

        logger.info("Step02PrepareData completed successfully.")
        return 0


def main():
    args = parse_args()

    step = Step02PrepareData(config={"config_file": args.config})
    step.dataset_name = args.dataset
    step.experiment_name = args.experiment
    step.seed = args.seed

    return step.run()


if __name__ == "__main__":
    sys.exit(main())
