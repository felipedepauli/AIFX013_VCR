#!/usr/bin/env python3
"""Fix rect coordinates in JSON files for already-cropped images.

When images are already cropped, the rect should be [0, 0, width, height].
This script updates all JSON files to match the actual image dimensions.

Usage:
    python fix_cropped_rects.py --dir images/xywh/revised_images
    python fix_cropped_rects.py --dir images/xywh/revised_images --recursive
"""

import argparse
import json
import logging
from pathlib import Path

from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def fix_json_rect(json_path: Path, image_path: Path, rect_format: str = "xyxy") -> bool:
    """Fix rect in JSON to match actual image dimensions.
    
    Args:
        json_path: Path to JSON file
        image_path: Path to corresponding image
        rect_format: "xyxy" or "xywh" (default: "xyxy")
        
    Returns:
        True if updated, False otherwise
    """
    try:
        # Read JSON
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list) or len(data) == 0:
            logger.warning(f"Skipping {json_path}: not a list or empty")
            return False
        
        # Get image dimensions
        with Image.open(image_path) as img:
            width, height = img.size
        
        # Update all items
        updated = False
        for item in data:
            if "rect" in item:
                old_rect = item["rect"]
                
                # Set new rect based on format
                if rect_format == "xywh":
                    # [x, y, width, height]
                    new_rect = [0, 0, width, height]
                else:  # xyxy
                    # [x1, y1, x2, y2]
                    new_rect = [0, 0, width, height]
                
                if old_rect != new_rect:
                    item["rect"] = new_rect
                    updated = True
                    logger.debug(f"Updated {json_path.name}: {old_rect} -> {new_rect}")
        
        # Save if updated
        if updated:
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error processing {json_path}: {e}")
        return False


def process_directory(directory: Path, recursive: bool = True, rect_format: str = "xyxy") -> tuple[int, int]:
    """Process all JSON files in directory.
    
    Args:
        directory: Directory to process
        recursive: Whether to process subdirectories
        rect_format: "xyxy" or "xywh"
        
    Returns:
        Tuple of (total_processed, total_updated)
    """
    # Find all JSON files
    if recursive:
        json_files = list(directory.rglob("*.json"))
    else:
        json_files = list(directory.glob("*.json"))
    
    if not json_files:
        logger.warning(f"No JSON files found in {directory}")
        return 0, 0
    
    logger.info(f"Found {len(json_files)} JSON files")
    
    processed = 0
    updated = 0
    
    for json_path in json_files:
        # Find corresponding image
        image_path = json_path.with_suffix('.jpg')
        if not image_path.exists():
            # Try other extensions
            for ext in ['.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
                alt_path = json_path.with_suffix(ext)
                if alt_path.exists():
                    image_path = alt_path
                    break
            else:
                logger.warning(f"No image found for {json_path.name}")
                continue
        
        # Fix rect
        if fix_json_rect(json_path, image_path, rect_format):
            updated += 1
        processed += 1
        
        if processed % 100 == 0:
            logger.info(f"Processed {processed}/{len(json_files)} files, updated {updated}")
    
    return processed, updated


def main():
    parser = argparse.ArgumentParser(
        description="Fix rect coordinates in JSON files for cropped images"
    )
    parser.add_argument(
        "--dir",
        type=Path,
        required=True,
        help="Directory containing JSON and image files",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process subdirectories recursively",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["xyxy", "xywh"],
        default="xyxy",
        help="Rect format: xyxy [x1,y1,x2,y2] or xywh [x,y,w,h] (default: xyxy)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )
    
    args = parser.parse_args()
    
    if not args.dir.exists():
        logger.error(f"Directory not found: {args.dir}")
        return 1
    
    if args.dry_run:
        logger.info("DRY RUN MODE - no files will be modified")
    
    logger.info(f"Processing directory: {args.dir}")
    logger.info(f"Rect format: {args.format}")
    logger.info(f"Recursive: {args.recursive}")
    
    processed, updated = process_directory(args.dir, args.recursive, args.format)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total JSON files processed: {processed}")
    print(f"Files updated: {updated}")
    print(f"Files unchanged: {processed - updated}")
    
    if args.dry_run:
        print("\n(DRY RUN - no changes were made)")
    else:
        print(f"\n✓ All rects updated to match image dimensions!")
    
    return 0


if __name__ == "__main__":
    exit(main())
