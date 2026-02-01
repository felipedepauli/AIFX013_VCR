#!/usr/bin/env python3
"""Train the best model from optimization results.

Usage:
    python train_best_model.py
    python train_best_model.py --backbone convnext_tiny
    python train_best_model.py --backbone resnet50
"""

import argparse
import logging
import sys
from pathlib import Path
import yaml

from src.utils.config import load_config

# Import the train function from 06_train_mlflow.py
from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location("train_module", Path(__file__).parent / "06_train.py")
train_module = module_from_spec(spec)
spec.loader.exec_module(train_module)
train_fn = train_module.train

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Train using best hyperparameters from optimization")
    parser.add_argument(
        "--backbone",
        type=str,
        default="efficientnet_b0",
        choices=["efficientnet_b0", "convnext_tiny", "resnet50"],
        help="Backbone to train"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/manifests/manifest_ready.jsonl",
        help="Path to manifest file"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        help="Device to use (auto/cuda/cpu)"
    )
    parser.add_argument(
        "--global-config",
        type=str,
        default="config.yaml",
        help="Global config file"
    )
    
    args = parser.parse_args()
    
    # Load best config for the backbone
    best_config_path = Path(f"runs/best_configs/{args.backbone}_best.yaml")
    if not best_config_path.exists():
        logger.error(f"Best config not found: {best_config_path}")
        logger.error("Run: python analyze_study.py --save-configs")
        return 1
    
    logger.info(f"Loading best config from: {best_config_path}")
    with open(best_config_path) as f:
        best_config = yaml.safe_load(f)
    
    # Load global config for paths
    global_config = load_config(args.global_config)
    
    # Create output directory
    exp_name = f"best_{args.backbone}"
    output_dir = Path("runs") / exp_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the config to experiment dir for reference
    with open(output_dir / "training_config.yaml", 'w') as f:
        yaml.dump(best_config, f, default_flow_style=False, sort_keys=False)
    
    # Check manifest
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return 1
    
    # Load preprocessing config if available
    preprocessing_config = None
    prep_path = Path("data/manifests/preprocessing.yaml")
    if prep_path.exists():
        with open(prep_path) as f:
            preprocessing_config = yaml.safe_load(f)
    
    # Extract metadata for logging
    metadata = best_config.get("metadata", {})
    logger.info(f"\nTraining {args.backbone.upper()}")
    logger.info(f"  Optimization trial: #{metadata.get('trial_number', 'N/A')}")
    logger.info(f"  Expected score: {metadata.get('best_score', 'N/A'):.4f}")
    logger.info(f"  Optimized on: {metadata.get('optimization_date', 'N/A')}")
    logger.info(f"  Output: {output_dir}\n")
    
    # Train
    result = train_fn(
        manifest_path=manifest_path,
        output_dir=output_dir,
        config=best_config,
        device=args.device,
        experiment_name=exp_name,
        run_name=f"{args.backbone}_validation",
        preprocessing_config=preprocessing_config,
    )
    
    # Show results comparison
    print(f"\n{'='*60}")
    print("TRAINING COMPLETE - VALIDATION RESULTS")
    print(f"{'='*60}")
    print(f"Expected (from optimization): {metadata.get('best_score', 'N/A'):.4f}")
    print(f"Actual (this run):            {result['best_val_acc']:.4f}")
    
    diff = result['best_val_acc'] - metadata.get('best_score', 0)
    if abs(diff) < 0.01:
        print(f"Difference:                   {diff:+.4f} ✓ REPRODUCED")
    else:
        print(f"Difference:                   {diff:+.4f} ⚠ VARIANCE")
    print(f"\nBest epoch: {result['best_epoch']}")
    print(f"Checkpoint: {output_dir / 'best.pt'}")
    print(f"{'='*60}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
