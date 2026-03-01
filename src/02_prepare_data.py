#!/usr/bin/env python3
"""02_prepare_data.py - Prepare dataset for a specific experiment using Optuna's trial info.

This script:
1. Loads the labeled dataset from data/{dataset}/manifests/ or data/manifests/ (multi-source)
2. Applies splits (Train/Val/Test) — or keeps existing splits from directory structure
3. Generates experiment-specific manifest in runs/{experiment}/data/
4. Saves preprocessing config for reproducibility

Usage:
    # Read everything from config.yaml (multi-source mode):
    python 02_prepare_data.py

    # Override dataset/experiment via CLI:
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


# Portuguese → English label normalization
LABEL_NORMALIZE: dict[str, str] = {
    "Bege": "brown",
    "Dourada": "yellow",
    "Roxa": "purple",
    "Outros ou Desconhecido": "unknown",
    "Amarela": "yellow",
    "Azul": "blue",
    "Branca": "white",
    "Cinza": "gray",
    "Laranja": "orange",
    "Marrom": "brown",
    "Prata": "silver",
    "Preta": "black",
    "Verde": "green",
    "Vermelha": "red",
}


def normalize_labels(records: list[dict]) -> tuple[list[dict], dict[str, str]]:
    """Normalize labels using LABEL_NORMALIZE mapping.

    Returns:
        Tuple of (records, dict of original→normalized for labels that were changed).
    """
    applied: dict[str, str] = {}
    for record in records:
        label = record.get("label", "")
        if label in LABEL_NORMALIZE:
            normalized = LABEL_NORMALIZE[label]
            if label not in applied:
                applied[label] = normalized
            record["label"] = normalized
    return records, applied


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
    parser.add_argument("--dataset", default=None, help="Dataset name inside data/ (e.g. prf_v1). If omitted, uses multi-source manifest from config.yaml")
    parser.add_argument("--experiment", default=None, help="Experiment name (e.g. exp_001). If omitted, reads from config.yaml 'experiment' key")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for splitting (default: from config or 42)")
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
        data_root = self.project_root / "data"
        runs_dir = self.project_root / "runs"
        exp_dir = runs_dir / self.experiment_name
        exp_data_dir = exp_dir / "data"

        # Load Config first to get paths
        config_path = self.project_root / self.config.get("config_file", "config.yaml")
        config = load_yaml(config_path)

        # Locate manifest:
        # - Multi-source mode (no dataset_name): use paths.manifests_dir from config
        # - Single-dataset mode: data/{dataset}/manifests/manifest_raw_labeled.jsonl (or variants)
        if not self.dataset_name:
            # Multi-source: use global manifest produced by 01_detect_crop.py
            paths_cfg = config.get("paths", {})
            manifests_dir_name = paths_cfg.get("manifests_dir", "data/manifests")
            # Handle absolute vs relative paths
            if Path(manifests_dir_name).is_absolute():
                manifests_dir = Path(manifests_dir_name)
            else:
                manifests_dir = self.project_root / manifests_dir_name
                
            manifest_path = manifests_dir / "manifest_raw_labeled.jsonl"
            if not manifest_path.exists():
                manifest_path = manifests_dir / "manifest_labeled.jsonl"
            if not manifest_path.exists():
                manifest_path = manifests_dir / "manifest_raw.jsonl"
            if not manifest_path.exists():
                logger.error(f"No manifest found in {manifests_dir}/. Run 01_detect_crop.py first.")
                return 1
        else:
            if not self.validate():
                return 1
            dataset_name = self.dataset_name.replace(":", "_")
            dataset_dir = data_root / dataset_name
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

        # Preprocessing settings
        preprocess_cfg = config.get("preprocess", {})
        split_from_dirs = preprocess_cfg.get("split_from_dirs", False)
        split_ratios = preprocess_cfg.get("split_ratios", {"train": 0.7, "val": 0.15, "test": 0.15})
        group_by = preprocess_cfg.get("group_by", "camera_id")

        # Apply Split — or keep existing splits from directory structure
        has_existing_splits = all("split" in r for r in records)
        if split_from_dirs and has_existing_splits:
            logger.info("Using existing splits from directory structure (split_from_dirs=true).")
            split_counts = Counter(r["split"] for r in records)
        else:
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

        # Normalize labels (Portuguese → English)
        raw_labels = sorted(set(r["label"] for r in records if r.get("label")))
        logger.info(f"Raw labels found ({len(raw_labels)}): {raw_labels}")

        records, applied_mappings = normalize_labels(records)
        if applied_mappings:
            logger.info("Label normalization applied:")
            for orig, norm in sorted(applied_mappings.items()):
                logger.info(f"  '{orig}' → '{norm}'")
        else:
            logger.info("No label normalization needed (all labels already in English).")

        # Build and Encode Labels
        logger.info("Encoding labels...")
        class_to_idx = build_class_mapping(records)
        class_counts = dict(Counter(r["label"] for r in records if r.get("label")))

        logger.info(f"Final classes ({len(class_to_idx)}): {list(class_to_idx.keys())}")
        for cls, count in sorted(class_counts.items(), key=lambda x: -x[1]):
            logger.info(f"  {cls}: {count}")

        for record in records:
            if "label" in record:
                record["label_idx"] = class_to_idx[record["label"]]

        # Prepare Transforms Config
        source_names = [s["name"] for s in config.get("paths", {}).get("sources", [])] if not self.dataset_name else [self.dataset_name]
        transforms_config = {
            "source_datasets": source_names,
            "seed": self.seed,
            "split_from_dirs": split_from_dirs,
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

        logger.info("Step02PrepareData completed successfully.")
        return 0


def main():
    args = parse_args()

    # Load config
    config_path = Path(args.config)
    config = load_yaml(config_path)

    # Resolve experiment name: CLI > config.yaml > error
    experiment = args.experiment or config.get("experiment")
    if not experiment:
        logger.error("Experiment name required. Pass --experiment or set 'experiment' in config.yaml.")
        return 1

    # Resolve seed: CLI > config.yaml > 42
    seed = args.seed if args.seed is not None else config.get("preprocess", {}).get("seed", 42)

    step = Step02PrepareData(config={"config_file": args.config})
    step.dataset_name = args.dataset or ""  # empty string = multi-source mode
    step.experiment_name = experiment
    step.seed = seed

    return step.run()


if __name__ == "__main__":
    sys.exit(main())
