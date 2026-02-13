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
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix, 
    classification_report, 
    roc_curve, 
    auc,
    precision_recall_curve,
    average_precision_score
)
from sklearn.preprocessing import label_binarize
import json

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
    
    # Create artifacts directory
    artifacts_dir = output_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

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
        
        # History tracking for plots
        history = {
            "train_loss": [],
            "train_acc": [],
            "val_loss": [],
            "val_acc": [],
            "lr": []
        }
        
        # Initialize for final visualization (will be updated each epoch)
        all_preds = []
        all_labels = []
        all_probs = []

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
            
            # Reset predictions for this epoch (keep last epoch for visualization)
            all_preds.clear()
            all_labels.clear()
            all_probs.clear()
            
            with torch.no_grad():
                val_pbar = tqdm(val_loader, desc=f"Epoch {epoch+1}/{epochs} [Val]", leave=False)
                for batch in val_pbar:
                    metrics = strategy.validation_step(model, batch, criterion)
                    val_loss += metrics["loss"]
                    val_acc += metrics.get("accuracy", 0.0)
                    num_val_batches += 1
                    
                    # Store predictions for visualization
                    images, labels = batch
                    images = images.to(device)
                    labels = labels.to(device)
                    outputs = model(images)
                    probs = torch.softmax(outputs, dim=1)
                    _, preds = torch.max(outputs, 1)
                    
                    all_preds.extend(preds.cpu().numpy())
                    all_labels.extend(labels.cpu().numpy())
                    all_probs.extend(probs.cpu().numpy())
            
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

            # Update history
            history["train_loss"].append(train_loss)
            history["train_acc"].append(train_acc)
            history["val_loss"].append(val_loss)
            history["val_acc"].append(val_acc)
            history["lr"].append(current_lr)
            
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
        
        # ============ Generate Visualizations ============
        logger.info("Generating visualization artifacts...")
        
        # If no epochs were run (e.g., resumed from completed training), run validation to collect predictions
        if len(all_preds) == 0:
            logger.info("No validation data collected during training. Running final validation pass...")
            # Load best model checkpoint for evaluation
            best_checkpoint = output_dir / "best.pt"
            if best_checkpoint.exists():
                logger.info(f"Loading best model from {best_checkpoint}")
                checkpoint = torch.load(best_checkpoint, map_location=device)
                model.load_state_dict(checkpoint["model_state_dict"])
            
            # Create a simple dataloader without multiprocessing to avoid issues
            final_val_loader = DataLoader(
                val_dataset, batch_size=batch_size, shuffle=False, 
                num_workers=0, pin_memory=False
            )
            
            model.eval()
            with torch.no_grad():
                val_pbar = tqdm(final_val_loader, desc="Final Validation", leave=False)
                for batch in val_pbar:
                    images, labels = batch
                    images = images.to(device)
                    labels = labels.to(device)
                    outputs = model(images)
                    probs = torch.softmax(outputs, dim=1)
                    _, preds = torch.max(outputs, 1)
                    
                    all_preds.extend(preds.cpu().numpy())
                    all_labels.extend(labels.cpu().numpy())
                    all_probs.extend(probs.cpu().numpy())
            logger.info(f"Collected {len(all_preds)} validation predictions")
        
        # Convert to numpy arrays
        all_preds = np.array(all_preds)
        all_labels = np.array(all_labels)
        all_probs = np.array(all_probs)
        
        # Get class names - try to load from class_to_idx.json
        class_to_idx_path = Path("data/processed/class_to_idx.json")
        idx_to_class = {}
        if class_to_idx_path.exists():
            with open(class_to_idx_path, 'r') as f:
                class_to_idx = json.load(f)
                idx_to_class = {v: k for k, v in class_to_idx.items()}
        
        # Use only classes that appear in the data
        unique_labels = np.unique(np.concatenate([all_labels, all_preds]))
        class_names = [idx_to_class.get(i, f"Class_{i}") for i in unique_labels]
        actual_num_classes = len(unique_labels)
        
        # 1. Confusion Matrix
        cm = confusion_matrix(all_labels, all_preds, labels=unique_labels)
        plt.figure(figsize=(14, 12))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=class_names, yticklabels=class_names)
        plt.title(f'Confusion Matrix - Best Epoch {best_epoch+1}', fontsize=14, pad=20)
        plt.ylabel('True Label', fontsize=12)
        plt.xlabel('Predicted Label', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        cm_path = artifacts_dir / "confusion_matrix.png"
        plt.savefig(cm_path, dpi=300, bbox_inches='tight')
        mlflow.log_artifact(str(cm_path))
        plt.close()
        
        # 2. Normalized Confusion Matrix
        row_sums = cm.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        cm_norm = cm.astype('float') / row_sums
        plt.figure(figsize=(14, 12))
        sns.heatmap(cm_norm, annot=True, fmt='.2f', cmap='Blues',
                   xticklabels=class_names, yticklabels=class_names)
        plt.title(f'Normalized Confusion Matrix - Best Epoch {best_epoch+1}', fontsize=14, pad=20)
        plt.ylabel('True Label', fontsize=12)
        plt.xlabel('Predicted Label', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        cm_norm_path = artifacts_dir / "confusion_matrix_normalized.png"
        plt.savefig(cm_norm_path, dpi=300, bbox_inches='tight')
        mlflow.log_artifact(str(cm_norm_path))
        plt.close()
        
        # 3. Training History - Loss and Accuracy (only if we have history)
        if len(history["train_loss"]) > 0:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
            
            epochs_range = range(1, len(history["train_loss"]) + 1)
            
            # Loss plot
            ax1.plot(epochs_range, history["train_loss"], 'b-', label='Train Loss', linewidth=2)
            ax1.plot(epochs_range, history["val_loss"], 'r-', label='Val Loss', linewidth=2)
            ax1.axvline(x=best_epoch+1, color='g', linestyle='--', label=f'Best Epoch ({best_epoch+1})')
            ax1.set_xlabel('Epoch', fontsize=12)
            ax1.set_ylabel('Loss', fontsize=12)
            ax1.set_title('Training and Validation Loss', fontsize=14)
            ax1.legend(fontsize=10)
            ax1.grid(True, alpha=0.3)
            
            # Accuracy plot
            ax2.plot(epochs_range, history["train_acc"], 'b-', label='Train Accuracy', linewidth=2)
            ax2.plot(epochs_range, history["val_acc"], 'r-', label='Val Accuracy', linewidth=2)
            ax2.axvline(x=best_epoch+1, color='g', linestyle='--', label=f'Best Epoch ({best_epoch+1})')
            ax2.set_xlabel('Epoch', fontsize=12)
            ax2.set_ylabel('Accuracy', fontsize=12)
            ax2.set_title('Training and Validation Accuracy', fontsize=14)
            ax2.legend(fontsize=10)
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            history_path = artifacts_dir / "training_history.png"
            plt.savefig(history_path, dpi=300, bbox_inches='tight')
            mlflow.log_artifact(str(history_path))
            plt.close()
        else:
            logger.info("No training history available, skipping history plots")
        
        # 4. Learning Rate Schedule (only if we have history)
        if len(history["lr"]) > 0:
            epochs_range_lr = range(1, len(history["lr"]) + 1)
            plt.figure(figsize=(10, 6))
            plt.plot(epochs_range_lr, history["lr"], 'b-', linewidth=2)
            plt.xlabel('Epoch', fontsize=12)
            plt.ylabel('Learning Rate', fontsize=12)
            plt.title('Learning Rate Schedule', fontsize=14)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            lr_path = artifacts_dir / "learning_rate.png"
            plt.savefig(lr_path, dpi=300, bbox_inches='tight')
            mlflow.log_artifact(str(lr_path))
            plt.close()
        
        # 5. ROC Curves (One-vs-Rest)
        y_bin = label_binarize(all_labels, classes=unique_labels)
        
        # Expand probs to match all possible classes
        all_probs_expanded = np.zeros((len(all_labels), len(unique_labels)))
        for i, label in enumerate(unique_labels):
            if label < all_probs.shape[1]:
                all_probs_expanded[:, i] = all_probs[:, label]
        
        plt.figure(figsize=(12, 10))
        colors = plt.cm.rainbow(np.linspace(0, 1, actual_num_classes))
        
        for i, (label_idx, color) in enumerate(zip(unique_labels, colors)):
            if np.sum(y_bin[:, i]) > 0:  # Only plot if class has samples
                fpr, tpr, _ = roc_curve(y_bin[:, i], all_probs_expanded[:, i])
                roc_auc = auc(fpr, tpr)
                plt.plot(fpr, tpr, color=color, lw=2,
                        label=f'{class_names[i]} (AUC = {roc_auc:.3f})')
        
        plt.plot([0, 1], [0, 1], 'k--', lw=2, label='Random Classifier')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate', fontsize=12)
        plt.ylabel('True Positive Rate', fontsize=12)
        plt.title('ROC Curves - One-vs-Rest', fontsize=14)
        plt.legend(loc='lower right', fontsize=8, ncol=2)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        roc_path = artifacts_dir / "roc_curves.png"
        plt.savefig(roc_path, dpi=300, bbox_inches='tight')
        mlflow.log_artifact(str(roc_path))
        plt.close()
        
        # 6. Precision-Recall Curves
        plt.figure(figsize=(12, 10))
        colors_pr = plt.cm.rainbow(np.linspace(0, 1, actual_num_classes))
        
        for i, (label_idx, color) in enumerate(zip(unique_labels, colors_pr)):
            if np.sum(y_bin[:, i]) > 0:  # Only plot if class has samples
                precision, recall, _ = precision_recall_curve(y_bin[:, i], all_probs_expanded[:, i])
                avg_precision = average_precision_score(y_bin[:, i], all_probs_expanded[:, i])
                plt.plot(recall, precision, color=color, lw=2,
                        label=f'{class_names[i]} (AP = {avg_precision:.3f})')
        
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('Recall', fontsize=12)
        plt.ylabel('Precision', fontsize=12)
        plt.title('Precision-Recall Curves', fontsize=14)
        plt.legend(loc='lower left', fontsize=8, ncol=2)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        pr_path = artifacts_dir / "precision_recall_curves.png"
        plt.savefig(pr_path, dpi=300, bbox_inches='tight')
        mlflow.log_artifact(str(pr_path))
        plt.close()
        
        # 7. Per-Class Metrics
        report = classification_report(all_labels, all_preds, 
                                      labels=unique_labels,
                                      target_names=class_names, 
                                      output_dict=True,
                                      zero_division=0)
        
        # Extract per-class metrics
        classes = [c for c in class_names if c in report]
        precisions = [report[c]['precision'] for c in classes]
        recalls = [report[c]['recall'] for c in classes]
        f1_scores = [report[c]['f1-score'] for c in classes]
        supports = [report[c]['support'] for c in classes]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        
        x_pos = np.arange(len(classes))
        
        # Precision
        bars1 = ax1.bar(x_pos, precisions, color='skyblue', edgecolor='black')
        ax1.set_ylabel('Precision', fontsize=12)
        ax1.set_title('Per-Class Precision', fontsize=14)
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(classes, rotation=45, ha='right')
        ax1.set_ylim([0, 1.05])
        ax1.grid(True, alpha=0.3, axis='y')
        for bar, val in zip(bars1, precisions):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.2f}', ha='center', va='bottom', fontsize=8)
        
        # Recall
        bars2 = ax2.bar(x_pos, recalls, color='lightcoral', edgecolor='black')
        ax2.set_ylabel('Recall', fontsize=12)
        ax2.set_title('Per-Class Recall', fontsize=14)
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(classes, rotation=45, ha='right')
        ax2.set_ylim([0, 1.05])
        ax2.grid(True, alpha=0.3, axis='y')
        for bar, val in zip(bars2, recalls):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.2f}', ha='center', va='bottom', fontsize=8)
        
        # F1-Score
        bars3 = ax3.bar(x_pos, f1_scores, color='lightgreen', edgecolor='black')
        ax3.set_ylabel('F1-Score', fontsize=12)
        ax3.set_title('Per-Class F1-Score', fontsize=14)
        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(classes, rotation=45, ha='right')
        ax3.set_ylim([0, 1.05])
        ax3.grid(True, alpha=0.3, axis='y')
        for bar, val in zip(bars3, f1_scores):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.2f}', ha='center', va='bottom', fontsize=8)
        
        # Support
        bars4 = ax4.bar(x_pos, supports, color='plum', edgecolor='black')
        ax4.set_ylabel('Support (# samples)', fontsize=12)
        ax4.set_title('Per-Class Support', fontsize=14)
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels(classes, rotation=45, ha='right')
        ax4.grid(True, alpha=0.3, axis='y')
        for bar, val in zip(bars4, supports):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(val)}', ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        metrics_path = artifacts_dir / "per_class_metrics.png"
        plt.savefig(metrics_path, dpi=300, bbox_inches='tight')
        mlflow.log_artifact(str(metrics_path))
        plt.close()
        
        # 8. Save Classification Report as JSON
        report_path = artifacts_dir / "classification_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        mlflow.log_artifact(str(report_path))
        
        # 9. Training Summary
        summary = {
            "best_val_acc": float(best_val_acc),
            "best_epoch": int(best_epoch),
            "final_train_acc": float(history["train_acc"][-1]) if len(history["train_acc"]) > 0 else None,
            "final_val_acc": float(history["val_acc"][-1]) if len(history["val_acc"]) > 0 else None,
            "final_train_loss": float(history["train_loss"][-1]) if len(history["train_loss"]) > 0 else None,
            "final_val_loss": float(history["val_loss"][-1]) if len(history["val_loss"]) > 0 else None,
            "total_epochs": len(history["train_loss"]),
            "num_classes": num_classes,
            "actual_classes_in_val": int(actual_num_classes),
            "train_samples": len(train_dataset),
            "val_samples": len(val_dataset)
        }
        summary_path = artifacts_dir / "training_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        mlflow.log_artifact(str(summary_path))
        
        # 10. Save training history as JSON
        history_json_path = artifacts_dir / "training_history.json"
        with open(history_json_path, 'w') as f:
            json.dump(history, f, indent=2)
        mlflow.log_artifact(str(history_json_path))
        
        logger.info(f"All artifacts saved to {artifacts_dir}")
        logger.info("Visualization generation complete!")

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
