#!/usr/bin/env python3
"""06_train_mlflow.py - Training script with MLflow logging.

Usage:
    python 06_train_mlflow.py --experiment runs/exp_001
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any
import yaml

import mlflow
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, WeightedRandomSampler
from tqdm import tqdm

# Import modules to trigger registrations
import src.backbones  # noqa: F401
import src.fusion  # noqa: F401
import src.losses  # noqa: F401
import src.strategies.vcr  # noqa: F401 -> Registers VCRStrategy

from src.core.factories import StrategyFactory
from src.core.interfaces import PipelineStep
from src.data import ManifestDataset
from src.data.transforms import build_transforms
from src.utils.config import load_config
from src.utils.callbacks import EarlyStopping

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def train(
    manifest_path: Path,
    output_dir: Path,
    config: dict[str, Any],
    device: str = "auto",
    experiment_name: str = "VCR",
    run_name: str | None = None,
    preprocessing_config: dict | None = None,
    trial: "optuna.Trial | None" = None,
) -> dict[str, Any]:
    """Generic training function using Strategy pattern."""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device)
    logger.info(f"Using device: {device}")

    # --- Data Loading ---
    image_size = config.get("training", {}).get("image_size", 224)
    batch_size = config.get("training", {}).get("batch_size", 32)
    use_weighted_sampler = not config.get("training", {}).get("no_weighted_sampler", False)

    # Build transforms from config
    transforms_cfg = preprocessing_config.get("transforms", {}) if preprocessing_config else {}
    train_transform = build_transforms(transforms_cfg, is_train=True, image_size=image_size)
    val_transform = build_transforms(transforms_cfg, is_train=False, image_size=image_size)

    train_dataset = ManifestDataset(manifest_path, split="train", transform=train_transform)
    val_dataset = ManifestDataset(manifest_path, split="val", transform=val_transform)

    logger.info(f"Train: {len(train_dataset)}, Val: {len(val_dataset)}")
    
    # Class Info
    class_counts = train_dataset.get_class_counts()
    num_classes = len(class_counts)
    
    # Sampler
    if use_weighted_sampler:
        sample_weights = train_dataset.get_sample_weights()
        sampler = WeightedRandomSampler(sample_weights, len(sample_weights))
        shuffle = False
    else:
        sampler = None
        shuffle = True

    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=shuffle, 
        sampler=sampler, num_workers=4, pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False, 
        num_workers=4, pin_memory=True
    )

    # --- Strategy Setup ---
    strategy_name = config.get("training", {}).get("strategy", "vcr") # Default to VCR
    logger.info(f"Using strategy: {strategy_name}")
    
    # Register VCR manually just in case import didn't work (sanity check)
    from src.strategies.vcr import VCRStrategy
    StrategyFactory.register("vcr", VCRStrategy)
    
    strategy = StrategyFactory.create(strategy_name, config, num_classes)
    strategy.device = device # Inject device

    # Build components via strategy
    model = strategy.build_model().to(device)
    optimizer, scheduler = strategy.configure_optimizers(model)
    criterion = strategy.configure_loss()
    
    epochs = int(config.get("training", {}).get("epochs", 50))
    patience = int(config.get("training", {}).get("patience", 10)) # Default patience 10 epochs
    
    
    early_stopping = EarlyStopping(patience=patience, verbose=True, mode="max")

    # --- Resume Logic ---
    start_epoch = 0
    checkpoint_path = output_dir / "last.pt"
    if checkpoint_path.exists():
        logger.info(f"Resuming from checkpoint: {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        if "optimizer_state_dict" in checkpoint:
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        if "scheduler_state_dict" in checkpoint and scheduler:
            scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        start_epoch = checkpoint["epoch"] + 1
        best_val_acc = checkpoint.get("best_val_acc", 0.0)
        logger.info(f"Resuming from epoch {start_epoch}")

    # --- MLFlow ---
    mlflow.set_experiment(experiment_name)
    # Allow nested runs so this can be called from optuna_runner
    with mlflow.start_run(run_name=run_name, nested=True):
        mlflow.log_params(config.get("training", {}))
        mlflow.log_param("strategy", strategy_name)
        mlflow.log_dict({"class_counts": class_counts}, "class_counts.json")

        best_val_acc = 0.0
        best_epoch = 0

        for epoch in range(start_epoch, epochs):
            # --- Training Loop ---
            model.train()
            total_loss = 0.0
            total_acc = 0.0
            num_batches = 0
            
            pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs} [Train]")
            for i, batch in enumerate(pbar):
                optimizer.zero_grad()
                
                # Delegate step to strategy
                metrics = strategy.training_step(
                    model, batch, criterion, i, 
                    class_counts=class_counts, epoch=epoch
                )
                
                metrics["loss"].backward()
                optimizer.step()
                
                loss_val = metrics["loss"].item()
                acc_val = metrics.get("accuracy", 0.0)
                
                total_loss += loss_val
                total_acc += acc_val
                num_batches += 1
                
                pbar.set_postfix({"loss": f"{loss_val:.4f}", "acc": f"{acc_val:.4f}"})

            train_loss = total_loss / num_batches
            train_acc = total_acc / num_batches

            # --- Validation Loop ---
            model.eval()
            val_loss = 0.0
            val_acc = 0.0
            num_val_batches = 0
            
            with torch.no_grad():
                val_pbar = tqdm(val_loader, desc=f"Epoch {epoch+1}/{epochs} [Val]", leave=False)
                for batch in val_pbar:
                    metrics = strategy.validation_step(model, batch, criterion)
                    val_loss += metrics["loss"]
                    val_acc += metrics.get("accuracy", 0.0)
                    num_val_batches += 1
            
            val_loss /= num_val_batches
            val_acc /= num_val_batches

            # Scheduler Step
            if scheduler:
                scheduler.step()

            # Reporting & Logging
            current_lr = scheduler.get_last_lr()[0] if scheduler else 0.0
            
            # Optuna Pruning
            if trial is not None:
                trial.report(val_acc, epoch)
                if trial.should_prune():
                    import optuna
                    raise optuna.TrialPruned()

            mlflow.log_metrics({
                "train_loss": train_loss, "train_acc": train_acc,
                "val_loss": val_loss, "val_acc": val_acc,
                "lr": current_lr
            }, step=epoch)

            logger.info(
                f"Epoch {epoch+1}/{epochs} | "
                f"Train Loss: {train_loss:.4f}, Acc: {train_acc:.4f} | "
                f"Val Loss: {val_loss:.4f}, Acc: {val_acc:.4f}"
            )

            # Checkpoint
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_epoch = epoch
                torch.save({
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "scheduler_state_dict": scheduler.state_dict() if scheduler else None,
                    "val_acc": best_val_acc,
                    "best_val_acc": best_val_acc,
                    "config": config
                }, output_dir / "best.pt")
            
            # Save Last Checkpoint
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "scheduler_state_dict": scheduler.state_dict() if scheduler else None,
                "val_acc": val_acc,
                "best_val_acc": best_val_acc,
                "config": config
            }, output_dir / "last.pt")
            
            # Early Stopping Check
            early_stopping(val_acc, model)
            if early_stopping.early_stop:
                logger.info(f"Early stopping triggered at epoch {epoch+1}")
                break

    return {"best_val_acc": best_val_acc, "best_epoch": best_epoch}


class Step06TrainMlflow(PipelineStep):
    """Pipeline step for model training with MLflow logging.

    This step:
    1. Loads experiment data (manifest, preprocessing config)
    2. Trains the model using VCRStrategy
    3. Logs metrics to MLflow
    4. Saves checkpoints (best.pt, last.pt)
    """

    @property
    def name(self) -> str:
        return "06_train_mlflow"

    @property
    def description(self) -> str:
        return "Train VCR model with MLflow experiment tracking."

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.experiment_dir: Path | None = None
        self.manifest_path: Path | None = None
        self.device: str = "auto"
        self.preprocessing_config: dict = {}

    def validate(self) -> bool:
        """Validate that experiment directory and manifest exist."""
        if self.experiment_dir is None or not self.experiment_dir.exists():
            logger.error(f"Experiment directory not found: {self.experiment_dir}")
            return False
        if self.manifest_path is None or not self.manifest_path.exists():
            logger.error(f"Manifest not found: {self.manifest_path}")
            return False
        return True

    def run(self) -> int:
        """Execute training.

        Returns:
            0 on success, 1 on failure.
        """
        if not self.validate():
            return 1

        result = train(
            manifest_path=self.manifest_path,
            output_dir=self.experiment_dir / "train",
            config=self.config,
            device=self.device,
            experiment_name=self.experiment_dir.name,
            preprocessing_config=self.preprocessing_config,
        )

        logger.info(f"Training completed. Best val acc: {result['best_val_acc']:.4f} at epoch {result['best_epoch']}")
        logger.info("Step06TrainMlflow completed successfully.")
        return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=str, required=True, help="Experiment name (e.g. first_experiment)")
    parser.add_argument("--manifest", type=str, help="Override manifest path")
    parser.add_argument("--config", type=str, default="config.yaml", help="Global config path")
    parser.add_argument("--device", type=str, default="auto")
    args = parser.parse_args()

    cfg = load_config(args.config)
    
    # Get runs_dir from config (default: "runs")
    runs_dir = Path(cfg.get("paths", {}).get("runs_dir", "runs"))
    
    # Auto-prefix with runs_dir if not already a path
    exp_name = args.experiment
    if "/" not in exp_name:
        exp_dir = runs_dir / exp_name
    else:
        exp_dir = Path(exp_name)

    step = Step06TrainMlflow(config=cfg)
    step.experiment_dir = exp_dir
    step.device = args.device

    # Manifest resolution (priority: args > exp_dir > default)
    if args.manifest:
        step.manifest_path = Path(args.manifest)
    else:
        step.manifest_path = exp_dir / "data" / "manifest.jsonl"
        if not step.manifest_path.exists():
            step.manifest_path = Path("data/manifests/manifest_ready.jsonl")

    # Preprocessing Config
    prep_path = exp_dir / "data" / "preprocessing.yaml"
    if prep_path.exists():
        with open(prep_path) as f:
            step.preprocessing_config = yaml.safe_load(f)

    return step.run()


if __name__ == "__main__":
    sys.exit(main())
