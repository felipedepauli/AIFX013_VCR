#!/usr/bin/env python3
"""Import CVAT annotations and merge with manifest.

Parses CVAT XML export and updates manifest with color labels.
Only keeps images that have been annotated.

Usage:
    python scripts/import_cvat_labels.py --xml iew/annotations.xml --manifest data/manifests/manifest_raw.jsonl
"""

import argparse
import logging
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.manifest_io import read_manifest, write_manifest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_cvat_xml(xml_path: Path) -> dict[str, str]:
    """Parse CVAT XML and extract image names with their labels.

    Args:
        xml_path: Path to CVAT annotations.xml.

    Returns:
        Dict mapping image filename to label (only annotated images).
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    annotations = {}

    for image_elem in root.findall("image"):
        image_name = image_elem.get("name")

        # Find tag element (color label)
        tag_elem = image_elem.find("tag")
        if tag_elem is not None:
            label = tag_elem.get("label")
            if label:
                annotations[image_name] = label

    return annotations


def merge_annotations(
    manifest_path: Path,
    annotations: dict[str, str],
    output_path: Path,
) -> tuple[int, int]:
    """Merge CVAT annotations into manifest.

    Args:
        manifest_path: Path to original manifest.
        annotations: Dict from image filename to label.
        output_path: Path to write updated manifest.

    Returns:
        Tuple of (matched_count, total_manifest_count).
    """
    records = read_manifest(manifest_path)
    updated_records = []
    matched = 0

    for record in records:
        # Get the crop filename from crop_path or id
        if "crop_path" in record:
            crop_name = Path(record["crop_path"]).name
        else:
            crop_name = record["id"] + ".jpg"

        # Check if this image was annotated
        if crop_name in annotations:
            record["label"] = annotations[crop_name]
            updated_records.append(record)
            matched += 1

    write_manifest(updated_records, output_path)
    return matched, len(records)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import CVAT annotations and merge with manifest.",
    )

    parser.add_argument(
        "--xml",
        type=str,
        required=True,
        help="Path to CVAT annotations.xml",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/manifests/manifest_raw.jsonl",
        help="Path to input manifest (default: data/manifests/manifest_raw.jsonl)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output manifest path (default: overwrites input with _labeled suffix)",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    xml_path = Path(args.xml)
    manifest_path = Path(args.manifest)

    if not xml_path.exists():
        logger.error(f"XML file not found: {xml_path}")
        return 1

    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return 1

    # Default output path
    output_path = Path(args.output) if args.output else manifest_path.with_name(
        manifest_path.stem + "_labeled.jsonl"
    )

    # Parse CVAT XML
    logger.info(f"Parsing CVAT XML: {xml_path}")
    annotations = parse_cvat_xml(xml_path)
    logger.info(f"Found {len(annotations)} annotated images in CVAT")

    # Show label distribution
    from collections import Counter
    label_counts = Counter(annotations.values())
    logger.info(f"Label distribution: {dict(label_counts)}")

    # Merge with manifest
    logger.info(f"Merging with manifest: {manifest_path}")
    matched, total = merge_annotations(manifest_path, annotations, output_path)

    logger.info(f"Matched {matched}/{total} manifest records")
    logger.info(f"Output written to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
