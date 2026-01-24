#!/usr/bin/env python3
"""04_train_mlflow.py - Training script with MLflow logging.

Usage:
    python 04_train_mlflow.py --experiment runs/exp_001
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

# Import modules to trigger registrations
import src.backbones  # noqa: F401
import src.fusion  # noqa: F401
import src.losses  # noqa: F401
import src.strategies.vcr  # noqa: F401 -> Registers VCRStrategy

from src.core.factories import StrategyFactory
from src.data import ManifestDataset
from src.data.transforms import build_transforms
from src.utils.config import load_config

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
    image_size = config.get("train", {}).get("image_size", 224)
    batch_size = config.get("train", {}).get("batch_size", 32)
    use_weighted_sampler = not config.get("train", {}).get("no_weighted_sampler", False)

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
    strategy_name = config.get("train", {}).get("strategy", "vcr") # Default to VCR
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
    
    epochs = int(config.get("train", {}).get("epochs", 50))

    # --- MLFlow ---
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=run_name):
        mlflow.log_params(config.get("train", {}))
        mlflow.log_param("strategy", strategy_name)
        mlflow.log_dict({"class_counts": class_counts}, "class_counts.json")

        best_val_acc = 0.0
        best_epoch = 0

        for epoch in range(epochs):
            # --- Training Loop ---
            model.train()
            total_loss = 0.0
            total_acc = 0.0
            num_batches = 0
            
            for i, batch in enumerate(train_loader):
                optimizer.zero_grad()
                
                # Delegate step to strategy
                metrics = strategy.training_step(
                    model, batch, criterion, i, 
                    class_counts=class_counts, epoch=epoch
                )
                
                metrics["loss"].backward()
                optimizer.step()
                
                total_loss += metrics["loss"].item()
                total_acc += metrics.get("accuracy", 0.0)
                num_batches += 1

            train_loss = total_loss / num_batches
            train_acc = total_acc / num_batches

            # --- Validation Loop ---
            model.eval()
            val_loss = 0.0
            val_acc = 0.0
            num_val_batches = 0
            
            with torch.no_grad():
                for batch in val_loader:
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
                    "val_acc": best_val_acc,
                    "config": config
                }, output_dir / "best.pt")

    return {"best_val_acc": best_val_acc, "best_epoch": best_epoch}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=str, required=True, help="Experiment directory (e.g. runs/exp_01)")
    parser.add_argument("--manifest", type=str, help="Override manifest path")
    parser.add_argument("--config", type=str, default="config.yaml", help="Global config path")
    parser.add_argument("--device", type=str, default="auto")
    args = parser.parse_args()

    # Load Experiment Config
    exp_dir = Path(args.experiment)
    # Try loading experiment-specific config first
    exp_config_path = exp_dir / "data" / "config.yaml" # If we saved it there? Usually we use the global + overrides
    # Actually, usually we rely on "config.yaml" at root.
    
    cfg = load_config(args.config)
    
    # Manifest resolution (priority: args > exp_dir > default)
    if args.manifest:
        manifest_path = Path(args.manifest)
    else:
        # Check exp_dir
        manifest_path = exp_dir / "data" / "manifest.jsonl"
        if not manifest_path.exists():
            # Fallback
            manifest_path = Path("data/manifests/manifest_ready.jsonl")

    # Preprocessing Config
    prep_config = {}
    prep_path = exp_dir / "data" / "preprocessing.yaml"
    if prep_path.exists():
        with open(prep_path) as f:
            prep_config = yaml.safe_load(f)

    train(
        manifest_path=manifest_path,
        output_dir=exp_dir / "train",
        config=cfg,
        device=args.device,
        experiment_name=exp_dir.name,
        preprocessing_config=prep_config
    )

if __name__ == "__main__":
    main()
