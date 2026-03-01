#!/usr/bin/env python3
"""
janitor.py - Utility to clean up experiments and datasets.

Usage:
    python scripts/janitor.py --experiment exp_001
    python scripts/janitor.py --dataset prf:v1
    python scripts/janitor.py --experiment exp_001 --force

Options:
    --experiment NAME   Remove experiment directory (runs/NAME) and MLFlow run.
    --dataset NAME:VER  Remove dataset directory (data/NAME_VER).
    --force             Skip confirmation prompt.
"""

import argparse
import shutil
import sys
from pathlib import Path
import logging

try:
    import mlflow
except ImportError:
    mlflow = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def clean_experiment(experiment_name: str, force: bool = False) -> bool:
    """Remove experiment artifacts."""
    # Handle "runs/exp_001" vs "exp_001"
    exp_path = Path(experiment_name)
    if "runs" not in exp_path.parts:
        exp_dir = Path("runs") / experiment_name
        mlflow_exp_name = experiment_name
    else:
        exp_dir = exp_path
        mlflow_exp_name = exp_path.name
        
    if not exp_dir.exists():
        logger.error(f"Experiment directory not found: {exp_dir}")
        return False

    # Confirm
    if not force:
        print(f"\n⚠️  WARNING: This will PERMANENTLY DELETE:")
        print(f"  - Experiment Directory: {exp_dir.absolute()}")
        if mlflow:
            print(f"  - MLFlow Experiment: {mlflow_exp_name}")
        
        response = input("\nAre you sure? [y/N]: ").lower().strip()
        if response != "y":
            logger.info("Operation cancelled.")
            return False

    # Delete Directory
    try:
        shutil.rmtree(exp_dir)
        logger.info(f"✅ Deleted directory: {exp_dir}")
    except Exception as e:
        logger.error(f"Failed to delete directory: {e}")
        return False

    # Delete MLFlow Experiment
    if mlflow:
        try:
            exp = mlflow.get_experiment_by_name(mlflow_exp_name)
            if exp:
                mlflow.delete_experiment(exp.experiment_id)
                logger.info(f"✅ Deleted MLFlow experiment: {mlflow_exp_name} (ID: {exp.experiment_id})")
            else:
                logger.info(f"MLFlow experiment '{mlflow_exp_name}' not found (maybe already deleted).")
        except Exception as e:
            logger.warning(f"Failed to delete MLFlow experiment: {e}")

    return True


def clean_dataset(dataset_arg: str, force: bool = False) -> bool:
    """Remove dataset directory. Expects format 'name:version' e.g., 'prf:v1'."""
    
    # Parse name:version
    if ":" in dataset_arg:
        name, version = dataset_arg.split(":", 1)
        dir_name = f"{name}_{version}"
    else:
        # Fallback if user passes "prf_v1" directly
        dir_name = dataset_arg

    dataset_dir = Path("data") / dir_name
    
    if not dataset_dir.exists():
        logger.error(f"Dataset directory not found: {dataset_dir}")
        return False

    # Confirm
    if not force:
        print(f"\n⚠️  WARNING: This will PERMANENTLY DELETE:")
        print(f"  - Dataset Directory: {dataset_dir.absolute()}")
        
        response = input("\nAre you sure? [y/N]: ").lower().strip()
        if response != "y":
            logger.info("Operation cancelled.")
            return False

    # Delete
    try:
        shutil.rmtree(dataset_dir)
        logger.info(f"✅ Deleted dataset: {dataset_dir}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete dataset: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Clean experiment data and artifacts.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--experiment", help="Experiment name (e.g. 'exp_01')")
    group.add_argument("--dataset", help="Dataset name:version (e.g. 'prf:v1')")
    
    parser.add_argument("--force", action="store_true", help="Skip confirmation")
    
    args = parser.parse_args()
    
    success = False
    if args.experiment:
        success = clean_experiment(args.experiment, args.force)
    elif args.dataset:
        success = clean_dataset(args.dataset, args.force)
        
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
