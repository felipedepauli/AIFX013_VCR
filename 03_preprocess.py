#!/usr/bin/env python3
"""03_preprocess.py - Validate and prepare dataset for training.

This script:
1. Validates manifest entries (checks images exist, labels present)
2. Encodes string labels to indices (class_to_idx.json)
3. Splits data using GroupShuffleSplit (train/val/test)
4. Outputs manifest_ready.jsonl with split assignments

Usage:
    python 02_preprocess.py --manifest data/manifests/manifest_raw_labeled.jsonl
    python 02_preprocess.py --config config.yaml
"""

import argparse
import json
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from sklearn.model_selection import GroupShuffleSplit

from src.core.interfaces import PipelineStep
from src.utils.config import load_config
from src.utils.manifest_io import read_manifest, write_manifest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def validate_records(
    records: list[dict[str, Any]],
    require_label: bool = True,
    check_images: bool = True,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate manifest records.

    Args:
        records: List of manifest records.
        require_label: Whether to require labels.
        check_images: Whether to check if crop/image files exist.

    Returns:
        Tuple of (valid_records, error_messages).
    """
    valid = []
    errors = []

    for record in records:
        record_id = record.get("id", "unknown")

        # Check required fields
        if "id" not in record:
            errors.append(f"Missing 'id' field")
            continue

        if require_label and "label" not in record:
            errors.append(f"{record_id}: Missing 'label' field")
            continue

        if require_label and not record.get("label"):
            errors.append(f"{record_id}: Empty label")
            continue

        # Check image exists
        if check_images:
            image_path = record.get("crop_path") or record.get("image_path")
            if image_path and not Path(image_path).exists():
                errors.append(f"{record_id}: Image not found: {image_path}")
                continue

        valid.append(record)

    return valid, errors


def build_class_mapping(records: list[dict[str, Any]]) -> dict[str, int]:
    """Build class-to-index mapping from records.

    Args:
        records: List of records with 'label' field.

    Returns:
        Dict mapping label string to integer index.
    """
    labels = sorted(set(r["label"] for r in records if r.get("label")))
    return {label: idx for idx, label in enumerate(labels)}


def get_class_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    """Count samples per class.

    Args:
        records: List of records with 'label' field.

    Returns:
        Dict mapping label to count.
    """
    return dict(Counter(r["label"] for r in records if r.get("label")))


def extract_group_key(record: dict[str, Any], group_by: str | None) -> str:
    """Extract group key for split stratification.

    Args:
        record: Manifest record.
        group_by: Field to group by ('camera_id', 'track_id', etc.)

    Returns:
        Group key string.
    """
    if group_by is None:
        return record["id"]  # Each sample is its own group

    # Try to extract from meta
    if "meta" in record and group_by in record["meta"]:
        return str(record["meta"][group_by])

    # Try to extract from ID pattern (e.g., "000000_henrique_00001_0000")
    # Pattern: {seq}_{camera}_{frame}_{bbox}
    if group_by == "camera_id":
        parts = record["id"].split("_")
        if len(parts) >= 2:
            return parts[1]  # Camera name

    # Fallback: use the record ID
    return record["id"]


def split_data(
    records: list[dict[str, Any]],
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    group_by: str | None = "camera_id",
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Split records into train/val/test sets.

    Uses GroupShuffleSplit to avoid data leakage when group_by is specified.

    Args:
        records: List of manifest records.
        train_ratio: Fraction for training.
        val_ratio: Fraction for validation.
        test_ratio: Fraction for test.
        group_by: Field to group by for split (prevents leakage).
        seed: Random seed.

    Returns:
        Records with 'split' field added.
    """
    import numpy as np

    n = len(records)
    groups = np.array([extract_group_key(r, group_by) for r in records])

    # Create indices
    indices = np.arange(n)

    # First split: train+val vs test
    test_size = test_ratio
    if test_size > 0:
        gss_test = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
        trainval_idx, test_idx = next(gss_test.split(indices, groups=groups))
    else:
        trainval_idx = indices
        test_idx = np.array([], dtype=int)

    # Second split: train vs val (within trainval)
    val_size_adjusted = val_ratio / (train_ratio + val_ratio)
    if val_size_adjusted > 0:
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
    for idx in train_idx:
        split_map[idx] = "train"
    for idx in val_idx:
        split_map[idx] = "val"
    for idx in test_idx:
        split_map[idx] = "test"

    # Add split to records
    for i, record in enumerate(records):
        record["split"] = split_map.get(i, "train")

    return records


def save_json(data: Any, path: Path) -> None:
    """Save data as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess manifest: validate, encode labels, split data.",
    )

    parser.add_argument(
        "--manifest",
        type=str,
        help="Path to input manifest (e.g., manifest_raw_labeled.jsonl)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to config file (default: config.yaml)",
    )
    parser.add_argument(
        "--output-manifest",
        type=str,
        default="data/manifests/manifest_ready.jsonl",
        help="Output manifest path",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Output directory for class_to_idx.json, class_counts.json",
    )
    parser.add_argument(
        "--group-by",
        type=str,
        default="camera_id",
        help="Field to group by for split (null for random split)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for split",
    )
    parser.add_argument(
        "--skip-image-check",
        action="store_true",
        help="Skip checking if image files exist",
    )

    return parser.parse_args()


class Step03Preprocess(PipelineStep):
    """Pipeline step for preprocessing: validate, encode labels, split data.

    This step:
    1. Validates manifest entries (images exist, labels present)
    2. Encodes string labels to indices
    3. Splits data using GroupShuffleSplit
    4. Outputs manifest_ready.jsonl with split assignments
    """

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
        self.group_by: str | None = "camera_id"
        self.seed: int = 42
        self.skip_image_check: bool = False

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

        logger.info(f"Loading manifest: {self.manifest_path}")
        records = read_manifest(self.manifest_path)
        logger.info(f"Loaded {len(records)} records")

        # Validate
        logger.info("Validating records...")
        valid_records, errors = validate_records(
            records,
            require_label=True,
            check_images=not self.skip_image_check,
        )

        if errors:
            logger.warning(f"Validation errors ({len(errors)}):")
            for err in errors[:10]:
                logger.warning(f"  {err}")
            if len(errors) > 10:
                logger.warning(f"  ... and {len(errors) - 10} more")

        logger.info(f"Valid records: {len(valid_records)}/{len(records)}")

        if not valid_records:
            logger.error("No valid records. Exiting.")
            return 1

        # Build class mapping
        class_to_idx = build_class_mapping(valid_records)
        class_counts = get_class_counts(valid_records)

        logger.info(f"Classes ({len(class_to_idx)}): {list(class_to_idx.keys())}")
        logger.info(f"Class counts: {class_counts}")

        # Split data
        preprocess_cfg = self.config.get("preprocess", {})
        split_ratios = preprocess_cfg.get("split_ratios", {})
        train_ratio = split_ratios.get("train", 0.7)
        val_ratio = split_ratios.get("val", 0.15)
        test_ratio = split_ratios.get("test", 0.15)

        group_by = self.group_by
        if group_by == "null" or group_by == "none":
            group_by = None

        logger.info(f"Splitting data (train={train_ratio}, val={val_ratio}, test={test_ratio})")
        logger.info(f"Group by: {group_by}, Seed: {self.seed}")

        valid_records = split_data(
            valid_records,
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            group_by=group_by,
            seed=self.seed,
        )

        # Count splits
        split_counts = Counter(r["split"] for r in valid_records)
        logger.info(f"Split distribution: {dict(split_counts)}")

        # Add label_idx to records
        for record in valid_records:
            record["label_idx"] = class_to_idx[record["label"]]

        # Save outputs
        save_json(class_to_idx, self.output_dir / "class_to_idx.json")
        save_json(class_counts, self.output_dir / "class_counts.json")
        write_manifest(valid_records, self.output_manifest)

        logger.info(f"Saved class_to_idx.json to {self.output_dir / 'class_to_idx.json'}")
        logger.info(f"Saved class_counts.json to {self.output_dir / 'class_counts.json'}")
        logger.info(f"Saved manifest_ready.jsonl to {self.output_manifest}")
        logger.info("Step03Preprocess completed successfully.")

        return 0


def main() -> int:
    args = parse_args()

    # Load config
    try:
        cfg = load_config(args.config)
    except FileNotFoundError:
        logger.warning(f"Config not found: {args.config}. Using defaults.")
        cfg = {}

    step = Step03Preprocess(config=cfg)

    # Determine input manifest
    if args.manifest:
        step.manifest_path = Path(args.manifest)
    else:
        manifests_dir = cfg.get("paths", {}).get("manifests_dir", "data/manifests")
        step.manifest_path = Path(manifests_dir) / "manifest_raw_labeled.jsonl"
        if not step.manifest_path.exists():
            step.manifest_path = Path(manifests_dir) / "manifest_raw.jsonl"

    step.output_manifest = Path(args.output_manifest)
    step.output_dir = Path(args.output_dir)
    step.group_by = args.group_by
    step.seed = args.seed
    step.skip_image_check = args.skip_image_check

    return step.run()


if __name__ == "__main__":
    sys.exit(main())
