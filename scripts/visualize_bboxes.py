#!/usr/bin/env python3
"""
visualize_bboxes.py - Debug script to visualize bounding boxes and labels.

Reads a manifest file (JSONL), loads original images,
draws bounding boxes and labels using OpenCV, and saves matches for inspection.

Usage:
    python scripts/visualize_bboxes.py --manifest data/prf_v1/manifests/manifest_raw.jsonl
    python scripts/visualize_bboxes.py --image-dir revised_images/train
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_manifest(path: Path) -> List[Dict[str, Any]]:
    """Load JSONL manifest."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def load_from_directory(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load annotations from a directory of images and sidecar JSONs."""
    grouped = {}
    
    # Extensions to look for
    valid_exts = {".jpg", ".jpeg", ".png", ".bmp"}
    
    files = list(path.rglob("*"))
    image_files = [f for f in files if f.suffix.lower() in valid_exts]
    
    for img_path in sorted(image_files):
        json_path = img_path.with_suffix(".json")
        records = []
        
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                # Handle list of dicts (PRF format)
                if isinstance(data, list):
                    for item in data:
                        record = {"image_path": str(img_path)}
                        
                        # Extract BBox
                        if "rect" in item:
                            # PRF "rect" is [x, y, w, h]
                            r = item["rect"]
                            x, y, w, h = r[0], r[1], r[2], r[3]
                            x1, y1, x2, y2 = x, y, x + w, y + h
                            record["bbox_xyxy"] = [x1, y1, x2, y2]
                        elif "bbox_xyxy" in item:
                            record["bbox_xyxy"] = item["bbox_xyxy"]
                            
                        # Extract Label
                        record["label"] = item.get("color") or item.get("label", "unknown")
                        record["confidence"] = item.get("confidence", 1.0)
                        
                        if "bbox_xyxy" in record:
                            records.append(record)
                            
            except Exception as e:
                logger.error(f"Error loading JSON {json_path}: {e}")
        
        grouped[str(img_path)] = records
        
    return grouped


def group_records_by_image(records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group manifest records by image_path."""
    grouped = {}
    for r in records:
        img_path = r["image_path"]
        if img_path not in grouped:
            grouped[img_path] = []
        grouped[img_path].append(r)
    return grouped


def draw_bboxes(image: np.ndarray, records: List[Dict[str, Any]]) -> np.ndarray:
    """Draw bounding boxes and labels on the image."""
    img_viz = image.copy()
    
    for r in records:
        bbox = r.get("bbox_xyxy")
        if not bbox:
            continue
            
        x1, y1, x2, y2 = map(int, bbox)
        label = r.get("label", "unknown")
        confidence = r.get("confidence", 1.0)
        
        # Color: Green for box
        color_box = (0, 255, 0)
        thickness = 2
        
        # Draw Rectangle (BGR)
        cv2.rectangle(img_viz, (x1, y1), (x2, y2), color_box, thickness)
        
        # Draw Label in Center
        text = f"{label} ({confidence:.2f})"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        color_text = (0, 0, 255) # Red text
        thickness_text = 2
        
        # Calculate text size to center it
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness_text)
        center_x = x1 + (x2 - x1) // 2
        center_y = y1 + (y2 - y1) // 2
        
        text_x = max(0, center_x - text_width // 2)
        text_y = max(0, center_y + text_height // 2)

        # Draw text background
        cv2.rectangle(img_viz, 
                      (text_x - 5, text_y + baseline + 5), 
                      (text_x + text_width + 5, text_y - text_height - 5), 
                      (255, 255, 255), 
                      -1) # Filled white
        
        cv2.putText(img_viz, text, (text_x, text_y), font, font_scale, color_text, thickness_text)
        
    return img_viz


def main():
    parser = argparse.ArgumentParser(description="Visualize bounding boxes from manifest or directory.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--manifest", help="Path to manifest JSONL file")
    group.add_argument("--image-dir", help="Directory containing images and sidecar JSONs")
    
    parser.add_argument("--output-dir", default="debug_viz", help="Directory to save visualized images")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of images to process")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    grouped_records = {}
    
    if args.manifest:
        manifest_path = Path(args.manifest)
        if not manifest_path.exists():
            logger.error(f"Manifest not found: {manifest_path}")
            return
        logger.info("Loading manifest...")
        records = load_manifest(manifest_path)
        grouped_records = group_records_by_image(records)
        
    elif args.image_dir:
        image_dir = Path(args.image_dir)
        if not image_dir.exists():
            logger.error(f"Image directory not found: {image_dir}")
            return
        logger.info(f"Scanning directory: {image_dir}...")
        grouped_records = load_from_directory(image_dir)
    
    logger.info(f"Found {len(grouped_records)} images to process.")
    
    processed_count = 0
    for i, (img_path_str, img_records) in enumerate(grouped_records.items()):
        if args.limit and processed_count >= args.limit:
            break
            
        img_path = Path(img_path_str)
        if not img_path.exists():
            logger.warning(f"Image not found: {img_path}")
            continue
            
        # Read Image using OpenCV
        img = cv2.imread(str(img_path))
        if img is None:
            logger.warning(f"Failed to read image: {img_path}")
            continue
            
        # Draw
        if img_records:
            viz_img = draw_bboxes(img, img_records)
        else:
            # Just copy the image if no detections, or maybe skip? 
            # Let's save it anyway to show it has no bboxes
            viz_img = img.copy()
            cv2.putText(viz_img, "No Annotations", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Save
        out_name = f"{img_path.stem}_viz.jpg"
        out_path = output_dir / out_name
        cv2.imwrite(str(out_path), viz_img)
        
        processed_count += 1
        if processed_count % 10 == 0:
            logger.info(f"Processed {processed_count} images...")

    logger.info(f"Done! Saved {processed_count} visualized images to {output_dir}")


if __name__ == "__main__":
    main()
