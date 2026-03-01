#!/usr/bin/env python3
"""reorganize_data_struct.py - Reorganize data into versioned datasets.

This script moves existing data folders into data/prf_v1/ to support the new
data architecture with multiple datasets and versions.
"""

import shutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def main():
    root_dir = Path("data")
    if not root_dir.exists():
        logger.error("data/ directory not found!")
        return 1
        
    # Target structure
    dataset_name = "prf_v1"
    target_dir = root_dir / dataset_name
    
    if target_dir.exists():
        logger.warning(f"Target directory {target_dir} already exists. Skipping reorganization.")
        return 0
        
    logger.info(f"Creating {target_dir}...")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Folders to move
    folders_to_move = ["raw", "crops", "manifests"]
    folder_renames = {"processed": "labeled"}
    
    # Move standard folders
    for folder in folders_to_move:
        src = root_dir / folder
        dst = target_dir / folder
        
        if src.exists():
            logger.info(f"Moving {src} -> {dst}")
            shutil.move(str(src), str(dst))
        else:
            logger.warning(f"Source {src} not found, skipping.")
            
    # Move and rename folders
    for old_name, new_name in folder_renames.items():
        src = root_dir / old_name
        dst = target_dir / new_name
        
        if src.exists():
            logger.info(f"Moving/Renaming {src} -> {dst}")
            shutil.move(str(src), str(dst))
        else:
            logger.warning(f"Source {src} not found, skipping.")
            
    logger.info("Reorganization complete!")
    logger.info(f"New structure in: {target_dir}")
    return 0

if __name__ == "__main__":
    main()
