#!/usr/bin/env python3
"""Visualize VCR dataset with FiftyOne.

Usage:
    python visualize_dataset.py --manifest data/manifests/manifest_raw.jsonl
    python visualize_dataset.py --manifest data/manifests/manifest_ready.jsonl --filter-color red
    python visualize_dataset.py --dataset-dir data/processed/train
"""

import argparse
import json
import logging
from pathlib import Path

import fiftyone as fo
import fiftyone.zoo as foz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_manifest(manifest_path: Path) -> list[dict]:
    """Load manifest JSONL file."""
    records = []
    with open(manifest_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def create_fiftyone_dataset(
    manifest_path: Path,
    dataset_name: str = "vcr_dataset",
    filter_color: str = None,
) -> fo.Dataset:
    """Create FiftyOne dataset from manifest.
    
    Args:
        manifest_path: Path to manifest JSONL file
        dataset_name: Name for the FiftyOne dataset
        filter_color: Optional color to filter (e.g., "red", "blue")
        
    Returns:
        FiftyOne dataset
    """
    # Load manifest
    logger.info(f"Loading manifest from {manifest_path}...")
    records = load_manifest(manifest_path)
    logger.info(f"Loaded {len(records)} records")
    
    # Filter by color if specified
    if filter_color:
        records = [r for r in records if r.get("label", "").lower() == filter_color.lower()]
        logger.info(f"Filtered to {len(records)} records with color '{filter_color}'")
    
    # Create dataset
    if fo.dataset_exists(dataset_name):
        logger.info(f"Deleting existing dataset '{dataset_name}'")
        fo.delete_dataset(dataset_name)
    
    dataset = fo.Dataset(dataset_name)
    dataset.persistent = True
    
    # Add samples
    samples = []
    for record in records:
        # Get image path (prefer crop_path, fallback to image_path)
        image_path = record.get("crop_path") or record.get("image_path")
        if not image_path:
            continue
            
        # Convert to absolute path if relative
        image_path = Path(image_path)
        
        if not image_path.is_absolute():
            # Try multiple resolution strategies
            candidates = [
                image_path,  # Try as-is first
                manifest_path.parent.parent / image_path,  # Relative to data/
                Path.cwd() / image_path,  # Relative to current directory
                # Handle duplicated paths like "data/train_v0/data/train_v0/crops/..."
                Path(str(image_path).replace("data/train_v0/data/train_v0/", "data/train_v0/")),
            ]
            
            # Find first existing path
            for candidate in candidates:
                if candidate.exists():
                    image_path = candidate
                    break
        
        if not image_path.exists():
            logger.warning(f"Image not found: {image_path}")
            continue
        
        # Create sample
        sample = fo.Sample(filepath=str(image_path))
        
        # Add color label
        if "label" in record:
            sample["color"] = fo.Classification(label=record["label"])
        
        # Add bounding box if available
        if "bbox" in record and "image_path" in record:
            bbox = record["bbox"]
            # Normalize bbox to [0, 1] if needed
            # FiftyOne expects [x, y, width, height] in relative coords
            # If bbox is in pixel coords, we'd need image dimensions
            # For now, assume it's a detection label
            sample["detection"] = fo.Detection(
                label=record.get("label", "vehicle"),
                bounding_box=bbox if isinstance(bbox, list) else None,
            )
        
        # Add metadata
        sample["crop_id"] = record.get("crop_id", "")
        sample["split"] = record.get("split", "")
        
        # Add vehicle metadata if available
        meta = record.get("meta", {})
        if meta:
            sample["vehicle_type"] = meta.get("vehicle_type", "")
            sample["brand"] = meta.get("brand", "")
            sample["model"] = meta.get("model", "")
        
        samples.append(sample)
    
    dataset.add_samples(samples)
    logger.info(f"Created dataset with {len(dataset)} samples")
    
    return dataset


def create_dataset_from_directory(
    dataset_dir: Path,
    dataset_name: str = "vcr_dataset",
) -> fo.Dataset:
    """Create FiftyOne dataset from processed data directory.
    
    Assumes structure:
        dataset_dir/
            images/
            manifest.jsonl
    """
    manifest_path = dataset_dir / "manifest.jsonl"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    return create_fiftyone_dataset(manifest_path, dataset_name)


def main():
    parser = argparse.ArgumentParser(description="Visualize VCR dataset with FiftyOne")
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Path to manifest JSONL file",
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        help="Path to dataset directory (alternative to --manifest)",
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default="vcr_dataset",
        help="Name for the FiftyOne dataset (default: vcr_dataset)",
    )
    parser.add_argument(
        "--filter-color",
        type=str,
        help="Filter by specific color (e.g., 'red', 'blue', 'black')",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5151,
        help="Port for FiftyOne app (default: 5151)",
    )
    
    args = parser.parse_args()
    
    # Create dataset
    if args.dataset_dir:
        dataset = create_dataset_from_directory(args.dataset_dir, args.dataset_name)
    elif args.manifest:
        dataset = create_fiftyone_dataset(
            args.manifest,
            args.dataset_name,
            filter_color=args.filter_color,
        )
    else:
        parser.error("Either --manifest or --dataset-dir must be specified")
    
    # Print dataset info
    print("\n" + "="*80)
    print("DATASET SUMMARY")
    print("="*80)
    print(f"Name: {dataset.name}")
    print(f"Total samples: {len(dataset)}")
    
    # Print color distribution
    if "color" in dataset.get_field_schema():
        color_counts = dataset.count_values("color.label")
        print(f"\nColor distribution:")
        for color, count in sorted(color_counts.items(), key=lambda x: -x[1]):
            print(f"  {color}: {count}")
    
    # Print splits if available
    if "split" in dataset.get_field_schema():
        split_counts = dataset.count_values("split")
        print(f"\nSplit distribution:")
        for split, count in split_counts.items():
            print(f"  {split}: {count}")
    
    print("\n" + "="*80)
    print("LAUNCHING FIFTYONE APP")
    print("="*80)
    print(f"URL: http://localhost:{args.port}")
    print("\nUseful filters:")
    print("  - Select color: Click on 'color' field and choose values")
    print("  - Search: Use search bar (e.g., 'red', 'silver')")
    print("  - Filter by split: Use 'split' field")
    print("\nPress Ctrl+C to exit")
    print("="*80 + "\n")
    
    # Launch app
    session = fo.launch_app(dataset, port=args.port)
    session.wait()


if __name__ == "__main__":
    main()
