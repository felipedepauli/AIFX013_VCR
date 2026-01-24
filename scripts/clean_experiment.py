#!/usr/bin/env python3
"""
clean_experiment.py - Utility to remove experiment artifacts.

Usage:
    python scripts/clean_experiment.py --experiment exp_001
    python scripts/clean_experiment.py --experiment runs/exp_001 --force
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


def clean_experiment(experiment_name: str, force: bool = False) -> int:
    # Handle "runs/exp_001" vs "exp_001"
    exp_path = Path(experiment_name)
    if "runs" not in exp_path.parts:
        # User passed name only
        exp_dir = Path("runs") / experiment_name
        mlflow_exp_name = experiment_name
    else:
        # User passed path
        exp_dir = exp_path
        mlflow_exp_name = exp_path.name
        
    if not exp_dir.exists():
        logger.error(f"Experiment directory not found: {exp_dir}")
        return 1

    # Confirm
    if not force:
        print(f"\n⚠️  WARNING: This will PERMANENTLY DELETE:")
        print(f"  - Directory: {exp_dir.absolute()}")
        if mlflow:
            print(f"  - MLFlow Experiment: {mlflow_exp_name}")
        
        response = input("\nAre you sure? [y/N]: ").lower().strip()
        if response != "y":
            logger.info("Operation cancelled.")
            return 0

    # Delete Directory
    try:
        shutil.rmtree(exp_dir)
        logger.info(f"✅ Deleted directory: {exp_dir}")
    except Exception as e:
        logger.error(f"Failed to delete directory: {e}")
        return 1

    # Delete MLFlow Experiment
    if mlflow:
        try:
            # Check if experiment exists
            exp = mlflow.get_experiment_by_name(mlflow_exp_name)
            if exp:
                mlflow.delete_experiment(exp.experiment_id)
                logger.info(f"✅ Deleted MLFlow experiment: {mlflow_exp_name} (ID: {exp.experiment_id})")
            else:
                logger.info(f"MLFlow experiment '{mlflow_exp_name}' not found (maybe already deleted).")
        except Exception as e:
            logger.warning(f"Failed to delete MLFlow experiment (or not supported): {e}")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Clean experiment data and artifacts.")
    parser.add_argument("--experiment", required=True, help="Experiment name or path (e.g. 'exp_01' or 'runs/exp_01')")
    parser.add_argument("--force", action="store_true", help="Skip confirmation")
    
    args = parser.parse_args()
    
    sys.exit(clean_experiment(args.experiment, args.force))


if __name__ == "__main__":
    main()
