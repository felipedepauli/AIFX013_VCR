#!/usr/bin/env python3
"""05_optimize.py - Hyperparameter optimization with Optuna + MLFlow.

Usage:
    python 05_optimize.py --hp-config hyperparameters.yaml
    python 05_optimize.py --hp-config custom_search.yaml --n-trials 100
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from src.optimization.optuna_runner import run_optimization
from src.utils.config import load_config

# Import training function
sys.path.insert(0, str(Path(__file__).parent))
from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location("train_module", Path(__file__).parent / "04_train_mlflow.py")
train_module = module_from_spec(spec)
spec.loader.exec_module(train_module)
train_fn = train_module.train

def train_wrapper(**kwargs: Any) -> dict[str, Any]:
    """Adapter to convert flat Optuna params into config dict for train()."""
    manifest_path = kwargs.pop("manifest_path")
    base_output_dir = kwargs.pop("output_dir")
    trial = kwargs.pop("trial", None)
    
    # Ensure each trial has a unique output directory to prevent
    # checkpoint collisions (e.g. trying to resume a resnet run with efficientnet)
    if trial is not None:
        output_dir = base_output_dir / f"trial_{trial.number}"
    else:
        output_dir = base_output_dir
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Whatever remains is treated as hyperparameters for the config
    # We construct a synthetic config dict
    config = {
        "train": {
            # Strategy params
            "strategy": kwargs.get("strategy", "vcr"),
            "backbone": kwargs.get("backbone", "resnet50"),
            "fusion": kwargs.get("fusion", "msff"),
            "loss": kwargs.get("loss_fn", "smooth_modulation"),
            
            # Training params
            "epochs": kwargs.get("epochs", 30),
            "batch_size": kwargs.get("batch_size", 32),
            "image_size": kwargs.get("image_size", 224),
            "lr": kwargs.get("lr", 1e-4),
            "weight_decay": kwargs.get("weight_decay", 1e-4),
            "device": kwargs.get("device", "auto"),
            "use_weighted_sampler": kwargs.get("use_weighted_sampler", True),
        }
    }
    
    return train_fn(
        manifest_path=manifest_path,
        output_dir=output_dir,
        config=config,
        device=kwargs.get("device", "auto"),
        experiment_name=kwargs.get("experiment_name", "VCR-Optimization"),
        trial=trial,
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Optuna hyperparameter optimization")
    parser.add_argument("--hp-config", type=str, default="hyperparameters.yaml",
                        help="Hyperparameter configuration file")
    parser.add_argument("--manifest", type=str, default="data/manifests/manifest_ready.jsonl")
    parser.add_argument("--output-dir", type=str, default="runs/optimization")
    parser.add_argument("--n-trials", type=int, default=None,
                        help="Override number of trials")
    parser.add_argument("--experiment", type=str, default="VCR-Optimization")
    
    args = parser.parse_args()
    
    # Load hyperparameter configuration
    logger.info(f"Loading hyperparameter config from {args.hp_config}")
    hp_cfg = load_config(args.hp_config)
    
    study_config = hp_cfg.get("study", {})
    if args.n_trials:
        study_config["n_trials"] = args.n_trials
    
    hp_config = hp_cfg.get("hyperparameters", {})
    fixed_params = hp_cfg.get("fixed", {})
    
    # Add manifest and output_dir to fixed params
    fixed_params["manifest_path"] = Path(args.manifest)
    fixed_params["output_dir"] = Path(args.output_dir)
    
    logger.info(f"Starting optimization with {study_config.get('n_trials', 50)} trials")
    logger.info(f"Hyperparameters to optimize: {list(hp_config.keys())}")
    logger.info(f"Fixed parameters: {list(fixed_params.keys())}")
    
    # Run optimization
    study = run_optimization(
        train_fn=train_wrapper,
        hp_config=hp_config,
        fixed_params=fixed_params,
        study_config=study_config,
        experiment_name=args.experiment,
    )
    
    # Save study results
    import optuna
    study_path = Path(args.output_dir) / "study.pkl"
    study_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use joblib to pickle the study
    import joblib
    joblib.dump(study, str(study_path))
    
    # Print results
    print(f"\n{'='*60}")
    print("OPTIMIZATION COMPLETE")
    print(f"{'='*60}")
    print(f"Best trial: {study.best_trial.number}")
    print(f"Best value: {study.best_trial.value:.4f}")
    print(f"\nBest hyperparameters:")
    for k, v in study.best_trial.params.items():
        print(f"  {k}: {v}")
    print(f"\nStudy saved to: {study_path}")
    print(f"View results in MLFlow UI: mlflow ui")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
