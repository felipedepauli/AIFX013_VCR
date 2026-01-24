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


def main():
    args = parse_args()
    
    # Paths
    project_root = Path(__file__).parent
    data_root = project_root / "data"
    
    # Handle dataset:version -> dataset_version
    dataset_name = args.dataset.replace(":", "_")
    
    dataset_dir = data_root / dataset_name
    runs_dir = project_root / "runs"
    exp_dir = runs_dir / args.experiment
    exp_data_dir = exp_dir / "data"

    if not dataset_dir.exists():
        logger.error(f"Dataset not found: {dataset_dir}")
        return 1

    # Load Manifest
    # Prefer generated manifest if exists, else look for raw
    manifest_path = dataset_dir / "manifests" / "manifest_raw_labeled.jsonl"
    if not manifest_path.exists():
        manifest_path = dataset_dir / "manifests" / "manifest_labeled.jsonl"
    
    # Fallback to manifest_raw.jsonl (if using import without explicit labeling step yet)
    if not manifest_path.exists():
        manifest_path = dataset_dir / "manifests" / "manifest_raw.jsonl"
    
    if not manifest_path.exists():
        logger.error(f"Manifest not found in {dataset_dir}/manifests/")
        return 1

    logger.info(f"Loading manifest from {manifest_path}...")
    records = load_jsonl(manifest_path)
    logger.info(f"Loaded {len(records)} records.")

    # Load Config (Global + Experiment specific if any)
    config_path = project_root / args.config
    config = load_yaml(config_path)
    
    # Preprocessing settings
    preprocess_cfg = config.get("preprocess", {})
    split_ratios = preprocess_cfg.get("split_ratios", {"train": 0.7, "val": 0.15, "test": 0.15})
    group_by = preprocess_cfg.get("group_by", "camera_id")
    seed = args.seed

    # Apply Split
    logger.info(f"Splitting data (Seed: {seed}, GroupBy: {group_by})...")
    records = split_data(
        records,
        train_ratio=split_ratios["train"],
        val_ratio=split_ratios["val"],
        test_ratio=split_ratios["test"],
        group_by=group_by,
        seed=seed
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

    # Prepare Transforms Config (To be saved)
    transforms_config = {
        "source_dataset": args.dataset,
        "seed": seed,
        "split_ratios": split_ratios,
        "group_by": group_by,
        "transforms": preprocess_cfg.get("transforms", {})  # brightness, etc.
    }

    # Output
    logger.info(f"Saving experiment data to {exp_data_dir}...")
    exp_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Save manifest
    output_manifest = exp_data_dir / "manifest.jsonl"
    save_jsonl(records, output_manifest)
    
    # Save preprocessing config
    with open(exp_data_dir / "preprocessing.yaml", "w") as f:
        yaml.dump(transforms_config, f)

    # Save class metadata
    with open(exp_data_dir / "class_to_idx.json", "w") as f:
        json.dump(class_to_idx, f, indent=2)
    with open(exp_data_dir / "class_counts.json", "w") as f:
        json.dump(class_counts, f, indent=2)
        
    # Symlink or Copy logic could go here if we were copying images
    # For now, we just rely on paths in manifest being absolute or relative to project root
    # Note: Manifest paths in 'image_path' are usually relative.
    # We should ensure they remain valid. 
    # Current manifest paths: likely "data/crops/..." or "data/raw/..."
    # With the move, they are now "data/prf_v1/crops/..."
    # We might need to fix paths in the manifest if they were hardcoded relative to root.
    
    # Let's check a record path and fix it if necessary
    sample_path = str(records[0].get("crop_path", ""))
    if sample_path.startswith("data/crops/"):
        # Fix paths to new location
        logger.info("Updating paths in manifest to new structure...")
        for r in records:
            if "crop_path" in r:
                r["crop_path"] = r["crop_path"].replace("data/crops/", f"data/{args.dataset}/crops/")
            if "image_path" in r:
                r["image_path"] = r["image_path"].replace("data/raw/", f"data/{args.dataset}/raw/")
        
        # Save again with updated paths
        save_jsonl(records, output_manifest)

    logger.info("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
