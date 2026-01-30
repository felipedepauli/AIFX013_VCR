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
from src.core.interfaces import PipelineStep

# Import training function
sys.path.insert(0, str(Path(__file__).parent))
from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location("train_module", Path(__file__).parent / "06_train_mlflow.py")
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
        "training": {
            # Strategy params
            "strategy": kwargs.get("strategy", "vcr"),
            "backbone": kwargs.get("backbone", "resnet50"),
            "fusion": kwargs.get("fusion", "msff"),
            "loss": kwargs.get("loss_fn", "smooth_modulation"),
            
            # Training params
            "epochs": kwargs.get("epochs", 20),
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


class Step05Optimize(PipelineStep):
    """Pipeline step for hyperparameter optimization with Optuna.

    This step:
    1. Loads hyperparameter search space from config
    2. Runs Optuna optimization with train_wrapper
    3. Logs trials to MLflow
    4. Saves best hyperparameters and study
    """

    @property
    def name(self) -> str:
        return "05_optimize"

    @property
    def description(self) -> str:
        return "Hyperparameter optimization with Optuna + MLflow."

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.hp_config_path: Path = Path("hyperparameters.yaml")
        self.manifest_path: Path = Path("data/manifests/manifest_ready.jsonl")
        self.output_dir: Path = Path("runs/optimization")
        self.n_trials: int | None = None
        self.experiment_name: str = "VCR-Optimization"

    def validate(self) -> bool:
        """Validate that hp_config and manifest exist."""
        if not self.hp_config_path.exists():
            logger.error(f"Hyperparameter config not found: {self.hp_config_path}")
            return False
        if not self.manifest_path.exists():
            logger.error(f"Manifest not found: {self.manifest_path}")
            return False
        return True

    def run(self) -> int:
        """Execute optimization.

        Returns:
            0 on success, 1 on failure.
        """
        if not self.validate():
            return 1

        logger.info(f"Loading hyperparameter config from {self.hp_config_path}")
        hp_cfg = load_config(str(self.hp_config_path))

        study_config = hp_cfg.get("study", {})
        if self.n_trials:
            study_config["n_trials"] = self.n_trials

        hp_config = hp_cfg.get("hyperparameters", {})
        fixed_params = hp_cfg.get("fixed", {})

        fixed_params["manifest_path"] = self.manifest_path
        fixed_params["output_dir"] = self.output_dir

        logger.info(f"Starting optimization with {study_config.get('n_trials', 50)} trials")
        logger.info(f"Hyperparameters to optimize: {list(hp_config.keys())}")

        study = run_optimization(
            train_fn=train_wrapper,
            hp_config=hp_config,
            fixed_params=fixed_params,
            study_config=study_config,
            experiment_name=self.experiment_name,
        )

        # Save study
        import joblib
        study_path = self.output_dir / "study.pkl"
        study_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(study, str(study_path))

        print(f"\n{'='*60}")
        print("OPTIMIZATION COMPLETE")
        print(f"{'='*60}")
        print(f"Best trial: {study.best_trial.number}")
        print(f"Best value: {study.best_trial.value:.4f}")
        print(f"\nBest hyperparameters:")
        for k, v in study.best_trial.params.items():
            print(f"  {k}: {v}")
        print(f"\nStudy saved to: {study_path}")

        logger.info("Step05Optimize completed successfully.")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Optuna hyperparameter optimization")
    parser.add_argument("--experiment", type=str, help="Experiment name (auto-resolves manifest)")
    parser.add_argument("--hp-config", type=str, default="hyperparameters.yaml",
                        help="Hyperparameter configuration file")
    parser.add_argument("--manifest", type=str, help="Override manifest path")
    parser.add_argument("--output-dir", type=str, help="Override output directory")
    parser.add_argument("--n-trials", type=int, default=None,
                        help="Override number of trials")
    parser.add_argument("--config", type=str, default="config.yaml", help="Global config path")

    args = parser.parse_args()

    cfg = load_config(args.config)
    runs_dir = Path(cfg.get("paths", {}).get("runs_dir", "runs"))

    step = Step05Optimize(config=cfg)
    step.hp_config_path = Path(args.hp_config)
    step.n_trials = args.n_trials

    # Resolve paths from experiment or use defaults
    if args.experiment:
        exp_name = args.experiment
        if "/" not in exp_name:
            exp_dir = runs_dir / exp_name
        else:
            exp_dir = Path(exp_name)
        
        step.experiment_name = exp_name
        step.output_dir = args.output_dir and Path(args.output_dir) or exp_dir / "optimization"
        
        # Manifest resolution
        if args.manifest:
            step.manifest_path = Path(args.manifest)
        else:
            step.manifest_path = exp_dir / "data" / "manifest.jsonl"
            if not step.manifest_path.exists():
                step.manifest_path = Path("data/manifests/manifest_ready.jsonl")
    else:
        step.experiment_name = "VCR-Optimization"
        step.output_dir = Path(args.output_dir or "runs/optimization")
        step.manifest_path = Path(args.manifest or "data/manifests/manifest_ready.jsonl")

    return step.run()


if __name__ == "__main__":
    sys.exit(main())

