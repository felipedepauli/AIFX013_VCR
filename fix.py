#!/usr/bin/env python3
"""Validate bounding box coordinates in CVAT JSON annotations.

Checks for invalid rectangles where:
- x2 <= x1 (right coordinate less than or equal to left)
- y2 <= y1 (bottom coordinate less than or equal to top)
- Negative coordinates
- Coordinates out of image bounds

Usage:
    python validate_annotations.py <directory>
    python validate_annotations.py data/raw --fix
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def validate_bbox(bbox: dict[str, Any], image_width: int = None, image_height: int = None) -> list[str]:
    """Validate a single bounding box.
    
    Args:
        bbox: Bounding box dict with 'points' or 'rect' key
        image_width: Optional image width for bounds checking
        image_height: Optional image height for bounds checking
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Handle different coordinate formats
    # Format 1: "points": [[x1, y1], [x2, y2]]
    # Format 2: "rect": [x1, y1, x2, y2]
    if "points" in bbox:
        points = bbox["points"]
        if len(points) != 2:
            errors.append(f"Invalid points length: {len(points)} (expected 2)")
            return errors
        x1, y1 = points[0]
        x2, y2 = points[1]
    elif "rect" in bbox:
        rect = bbox["rect"]
        if len(rect) != 4:
            errors.append(f"Invalid rect length: {len(rect)} (expected 4)")
            return errors
        x1, y1, x2, y2 = rect
    else:
        errors.append("Missing 'points' or 'rect' field")
        return errors
    
    # Check coordinate order
    if x2 <= x1:
        errors.append(f"Invalid width: x2={x2} <= x1={x1}")
    
    if y2 <= y1:
        errors.append(f"Invalid height: y2={y2} <= y1={y1}")
    
    # Check for negative coordinates
    if x1 < 0 or y1 < 0:
        errors.append(f"Negative top-left: ({x1}, {y1})")
    
    if x2 < 0 or y2 < 0:
        errors.append(f"Negative bottom-right: ({x2}, {y2})")
    
    # Check bounds if image dimensions provided
    if image_width is not None and (x1 >= image_width or x2 > image_width):
        errors.append(f"X coordinates out of bounds: x1={x1}, x2={x2}, width={image_width}")
    
    if image_height is not None and (y1 >= image_height or y2 > image_height):
        errors.append(f"Y coordinates out of bounds: y1={y1}, y2={y2}, height={image_height}")
    
    return errors


def fix_bbox(bbox: dict[str, Any]) -> bool:
    """Fix a bounding box by swapping coordinates if needed.
    
    Args:
        bbox: Bounding box dict with 'points' or 'rect' key
        
    Returns:
        True if fixed, False if no fix needed
    """
    fixed = False
    
    # Handle 'points' format: [[x1, y1], [x2, y2]]
    if "points" in bbox:
        if len(bbox["points"]) != 2:
            return False
        
        points = bbox["points"]
        x1, y1 = points[0]
        x2, y2 = points[1]
        
        # Fix swapped coordinates
        if x2 < x1:
            points[0][0], points[1][0] = x2, x1
            fixed = True
        
        if y2 < y1:
            points[0][1], points[1][1] = y2, y1
            fixed = True
        
        # Clamp negative coordinates to 0
        if points[0][0] < 0:
            points[0][0] = 0
            fixed = True
        
        if points[0][1] < 0:
            points[0][1] = 0
            fixed = True
        
        if points[1][0] < 0:
            points[1][0] = 0
            fixed = True
        
        if points[1][1] < 0:
            points[1][1] = 0
            fixed = True
    
    # Handle 'rect' format: [x1, y1, x2, y2]
    elif "rect" in bbox:
        if len(bbox["rect"]) != 4:
            return False
        
        rect = bbox["rect"]
        x1, y1, x2, y2 = rect
        
        # Fix swapped coordinates
        if x2 < x1:
            rect[0], rect[2] = x2, x1
            fixed = True
        
        if y2 < y1:
            rect[1], rect[3] = y2, y1
            fixed = True
        
        # Clamp negative coordinates to 0
        for i in range(4):
            if rect[i] < 0:
                rect[i] = 0
                fixed = True
    
    return fixed


def validate_json_file(json_path: Path, fix: bool = False) -> tuple[int, int, int]:
    """Validate all bounding boxes in a JSON file.
    
    Args:
        json_path: Path to JSON annotation file
        fix: Whether to fix invalid boxes
        
    Returns:
        Tuple of (total_boxes, invalid_boxes, fixed_boxes)
    """
    with open(json_path) as f:
        data = json.load(f)
    
    total_boxes = 0
    invalid_boxes = 0
    fixed_boxes = 0
    modified = False
    
    # Handle different JSON structures
    # Format 1: List of shapes directly
    # Format 2: Dict with "shapes" key
    if isinstance(data, list):
        shapes = data
        image_width = None
        image_height = None
    elif isinstance(data, dict):
        shapes = data.get("shapes", [])
        image_width = data.get("width")
        image_height = data.get("height")
    else:
        print(f"  ⚠️  Unknown JSON format in {json_path.name}")
        return 0, 0, 0
    
    # Check shapes
    for idx, shape in enumerate(shapes):
        total_boxes += 1
        
        errors = validate_bbox(shape, image_width, image_height)
        
        if errors:
            invalid_boxes += 1
            print(f"  ❌ {json_path.name} - Shape {idx + 1}:")
            print(f"     Label: {shape.get('label', 'N/A')}")
            # Display coordinates in the format they're stored
            if "points" in shape:
                print(f"     Points: {shape.get('points', 'N/A')}")
            elif "rect" in shape:
                print(f"     Rect: {shape.get('rect', 'N/A')}")
            else:
                print(f"     Coords: N/A")
            for error in errors:
                print(f"     - {error}")
            
            if fix:
                if fix_bbox(shape):
                    fixed_boxes += 1
                    modified = True
                    if "points" in shape:
                        print(f"     ✓ Fixed points: {shape['points']}")
                    elif "rect" in shape:
                        print(f"     ✓ Fixed rect: {shape['rect']}")
    
    # Save if modified
    if modified:
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  💾 Saved fixes to {json_path.name}")
    
    return total_boxes, invalid_boxes, fixed_boxes


def main():
    parser = argparse.ArgumentParser(description="Validate CVAT JSON annotations")
    parser.add_argument(
        "directory",
        type=str,
        help="Directory containing JSON annotation files"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically fix invalid bounding boxes"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.json",
        help="File pattern to match (default: *.json)"
    )
    
    args = parser.parse_args()
    
    directory = Path(args.directory)
    if not directory.exists():
        print(f"Error: Directory not found: {directory}")
        return 1
    
    # Find all JSON files
    json_files = list(directory.rglob(args.pattern))
    
    if not json_files:
        print(f"No JSON files found in {directory}")
        return 1
    
    print(f"Found {len(json_files)} JSON files")
    print(f"Validating annotations...\n")
    
    total_files = 0
    files_with_errors = 0
    total_boxes = 0
    total_invalid = 0
    total_fixed = 0
    
    for json_file in sorted(json_files):
        try:
            boxes, invalid, fixed = validate_json_file(json_file, fix=args.fix)
            total_files += 1
            total_boxes += boxes
            total_invalid += invalid
            total_fixed += fixed
            
            if invalid > 0:
                files_with_errors += 1
                print()
        
        except Exception as e:
            print(f"  ❌ Error processing {json_file.name}: {e}\n")
            files_with_errors += 1
    
    # Summary
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Files processed: {total_files}")
    print(f"Files with errors: {files_with_errors}")
    print(f"Total bounding boxes: {total_boxes}")
    print(f"Invalid boxes: {total_invalid}")
    
    if args.fix:
        print(f"Fixed boxes: {total_fixed}")
    
    if total_invalid > 0:
        if not args.fix:
            print(f"\n💡 Run with --fix to automatically fix invalid boxes")
        return 1
    else:
        print("\n✅ All bounding boxes valid!")
        return 0


if __name__ == "__main__":
    sys.exit(main())

