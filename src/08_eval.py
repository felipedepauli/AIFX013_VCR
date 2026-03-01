#!/usr/bin/env python3
"""06_eval.py - Evaluate model performance with long-tail metrics.

Usage:
    python 06_eval.py --predictions predictions.jsonl --class-counts data/processed/class_counts.json
    python 06_eval.py --checkpoint runs/train/best.pt --manifest data/manifests/manifest_ready.jsonl --split test
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
from sklearn.metrics import (
    accuracy_score,
    auc,
    balanced_accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_curve,
)
from sklearn.preprocessing import label_binarize
from torch.utils.data import DataLoader

# Import modules
import src.backbones  # noqa: F401
import src.fusion  # noqa: F401

from src.data import ManifestDataset, build_transforms
from src.core.interfaces import PipelineStep

# Import model
sys.path.insert(0, str(Path(__file__).parent))
from importlib.util import spec_from_file_location, module_from_spec
spec = spec_from_file_location("model", Path(__file__).parent / "04_model.py")
model_module = module_from_spec(spec)
spec.loader.exec_module(model_module)
VCRModel = model_module.VCRModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_predictions(
    predictions_path: Path,
) -> tuple[list[int], list[int], list[str], list[list[float]] | None, list[float] | None]:
    """Load predictions from JSONL file.

    Returns:
        Tuple of (y_true, y_pred, sources, y_probs, confidences).
    """
    y_true = []
    y_pred = []
    sources = []
    y_probs: list[list[float]] = []
    confidences: list[float] = []

    with open(predictions_path, "r") as f:
        for line in f:
            record = json.loads(line)
            if "true_idx" in record:
                y_true.append(record["true_idx"])
                y_pred.append(record["pred_idx"])
                sources.append(record.get("source_dataset", "unknown"))

                probs = record.get("probs") or record.get("probabilities")
                if isinstance(probs, list):
                    y_probs.append([float(x) for x in probs])

                if "confidence" in record:
                    try:
                        confidences.append(float(record["confidence"]))
                    except (TypeError, ValueError):
                        pass

    probs_out = y_probs if len(y_probs) == len(y_true) and len(y_true) > 0 else None
    conf_out = confidences if len(confidences) == len(y_true) and len(y_true) > 0 else None

    # If confidences are missing but full probs are available, infer top-1 confidences.
    if conf_out is None and probs_out is not None:
        probs_np = np.asarray(probs_out, dtype=np.float32)
        conf_out = probs_np.max(axis=1).tolist()

    return y_true, y_pred, sources, probs_out, conf_out


def load_class_info(class_path: Path) -> tuple[dict[int, str], dict[str, int]]:
    """Load class names and counts.

    Returns:
        Tuple of (idx_to_class, class_counts).
    """
    with open(class_path, "r") as f:
        data = json.load(f)

    # Could be class_to_idx.json or class_counts.json
    if all(isinstance(v, int) and v < 100 for v in data.values()):
        # class_to_idx format
        idx_to_class = {v: k for k, v in data.items()}
        return idx_to_class, {}
    else:
        # class_counts format {label: count}
        idx_to_class = {i: k for i, k in enumerate(sorted(data.keys()))}
        return idx_to_class, data


def run_inference(
    checkpoint_path: Path,
    manifest_path: Path,
    split: str,
    device: torch.device,
    batch_size: int = 32,
    image_size: int = 224,
) -> tuple[list[int], list[int], list[str], list[list[float]], list[float]]:
    """Run inference on manifest and get predictions.

    Returns:
        Tuple of (y_true, y_pred, sources, y_probs, confidences).
    """
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    config = checkpoint.get("config", {})
    
    # Config structure: full config.yaml with model params under "model" key
    model_cfg = config.get("model", {})
    train_cfg = config.get("train", {})
    
    num_classes = model_cfg.get("num_classes") or train_cfg.get("num_classes") or config.get("num_classes", 10)
    backbone = model_cfg.get("backbone") or train_cfg.get("backbone") or config.get("backbone", "resnet50")
    fusion = model_cfg.get("fusion") or train_cfg.get("fusion") or config.get("fusion", "msff")

    # Infer actual num_classes from checkpoint weights (config may be stale)
    state_dict = checkpoint["model_state_dict"]
    if "head.1.bias" in state_dict:
        actual_nc = state_dict["head.1.bias"].shape[0]
        if actual_nc != num_classes:
            logger.warning(f"Config says {num_classes} classes but weights have {actual_nc}. Using {actual_nc}.")
            num_classes = actual_nc

    model = VCRModel(
        num_classes=num_classes,
        backbone_name=backbone,
        fusion_name=fusion,
    )
    model.load_state_dict(state_dict)
    model = model.to(device)
    model.eval()

    # Load dataset
    dataset = ManifestDataset(
        manifest_path,
        split=split,
        transform=build_transforms({}, is_train=False, image_size=image_size),
    )
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=4)

    y_true = []
    y_pred = []
    y_probs: list[list[float]] = []
    confidences: list[float] = []

    with torch.no_grad():
        for images, targets in loader:
            images = images.to(device)
            logits = model(images)
            probs = torch.softmax(logits, dim=1)
            preds = logits.argmax(dim=1)
            conf = probs.gather(1, preds.unsqueeze(1)).squeeze(1)

            y_true.extend(targets.tolist())
            y_pred.extend(preds.cpu().tolist())
            y_probs.extend(probs.cpu().tolist())
            confidences.extend(conf.cpu().tolist())

    # Extract source info from dataset records
    sources = dataset.sources

    return y_true, y_pred, sources, y_probs, confidences


def compute_metrics(
    y_true: list[int],
    y_pred: list[int],
    idx_to_class: dict[int, str],
    class_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Compute evaluation metrics.

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        idx_to_class: Index to class name mapping.
        class_counts: Training class counts for head/tail analysis.

    Returns:
        Dict with all metrics.
    """
    # Basic metrics
    accuracy = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    macro_precision = precision_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_precision = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    macro_recall = recall_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_recall = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    balanced_acc = balanced_accuracy_score(y_true, y_pred)

    # Per-class metrics - only use classes present in data
    unique_labels = sorted(set(y_true) | set(y_pred))
    class_names = [idx_to_class.get(i, f"class_{i}") for i in unique_labels]
    report = classification_report(y_true, y_pred, labels=unique_labels, target_names=class_names, output_dict=True, zero_division=0)

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)

    # Head/Tail analysis
    head_tail_metrics = {}
    if class_counts:
        counts = [class_counts.get(idx_to_class.get(i, ""), 0) for i in range(len(idx_to_class))]
        median_count = np.median([c for c in counts if c > 0])

        head_classes = [i for i, c in enumerate(counts) if c >= median_count]
        tail_classes = [i for i, c in enumerate(counts) if 0 < c < median_count]

        # Store class names for display
        head_tail_metrics["head_class_names"] = [idx_to_class.get(i, f"class_{i}") for i in head_classes]
        head_tail_metrics["tail_class_names"] = [idx_to_class.get(i, f"class_{i}") for i in tail_classes]

        # Filter y_true/y_pred for head/tail
        head_mask = [i for i, y in enumerate(y_true) if y in head_classes]
        tail_mask = [i for i, y in enumerate(y_true) if y in tail_classes]

        if head_mask:
            head_acc = accuracy_score(
                [y_true[i] for i in head_mask],
                [y_pred[i] for i in head_mask],
            )
            head_tail_metrics["head_accuracy"] = head_acc
            head_tail_metrics["head_f1_macro"] = f1_score(
                [y_true[i] for i in head_mask],
                [y_pred[i] for i in head_mask],
                average="macro",
                zero_division=0,
            )
            head_tail_metrics["head_classes"] = len(head_classes)

        if tail_mask:
            tail_acc = accuracy_score(
                [y_true[i] for i in tail_mask],
                [y_pred[i] for i in tail_mask],
            )
            head_tail_metrics["tail_accuracy"] = tail_acc
            head_tail_metrics["tail_f1_macro"] = f1_score(
                [y_true[i] for i in tail_mask],
                [y_pred[i] for i in tail_mask],
                average="macro",
                zero_division=0,
            )
            head_tail_metrics["tail_classes"] = len(tail_classes)

    return {
        "accuracy": accuracy,
        "balanced_accuracy": balanced_acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "macro_precision": macro_precision,
        "weighted_precision": weighted_precision,
        "macro_recall": macro_recall,
        "weighted_recall": weighted_recall,
        "per_class": report,
        "confusion_matrix": cm.tolist(),
        "head_tail": head_tail_metrics,
    }


def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: list[str],
    output_path: Path,
    normalize: bool = True,
) -> None:
    """Plot confusion matrix."""
    if normalize:
        cm = cm.astype("float") / cm.sum(axis=1, keepdims=True)
        cm = np.nan_to_num(cm)

    plt.figure(figsize=(max(10, len(class_names)), max(8, len(class_names) * 0.8)))
    sns.heatmap(
        cm,
        annot=True,
        fmt=".2f" if normalize else "d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
    )
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title("Confusion Matrix" + (" (Normalized)" if normalize else ""))
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved confusion matrix to {output_path}")


def plot_per_class_metrics(
    per_class: dict[str, dict],
    output_path: Path,
) -> None:
    """Plot per-class precision, recall, F1."""
    class_names = [k for k in per_class.keys() if k not in ["accuracy", "macro avg", "weighted avg"]]

    precisions = [per_class[c]["precision"] for c in class_names]
    recalls = [per_class[c]["recall"] for c in class_names]
    f1s = [per_class[c]["f1-score"] for c in class_names]

    x = np.arange(len(class_names))
    width = 0.25

    fig, ax = plt.subplots(figsize=(max(10, len(class_names) * 0.8), 6))
    ax.bar(x - width, precisions, width, label="Precision")
    ax.bar(x, recalls, width, label="Recall")
    ax.bar(x + width, f1s, width, label="F1-Score")

    ax.set_xlabel("Class")
    ax.set_ylabel("Score")
    ax.set_title("Per-Class Metrics")
    ax.set_xticks(x)
    ax.set_xticklabels(class_names, rotation=45, ha="right")
    ax.legend()
    ax.set_ylim(0, 1.1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved per-class metrics to {output_path}")


def _compute_calibration_bins(
    confidences: np.ndarray,
    correctness: np.ndarray,
    n_bins: int = 15,
) -> tuple[float, list[dict[str, float]]]:
    """Compute ECE and reliability bins."""
    if confidences.size == 0:
        return 0.0, []

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    rows: list[dict[str, float]] = []
    ece = 0.0
    n = len(confidences)

    for i in range(n_bins):
        left, right = bins[i], bins[i + 1]
        if i == 0:
            mask = (confidences >= left) & (confidences <= right)
        else:
            mask = (confidences > left) & (confidences <= right)
        count = int(mask.sum())
        if count == 0:
            rows.append({
                "bin_left": float(left),
                "bin_right": float(right),
                "count": 0,
                "accuracy": 0.0,
                "avg_confidence": 0.0,
            })
            continue

        bin_acc = float(correctness[mask].mean())
        bin_conf = float(confidences[mask].mean())
        ece += (count / n) * abs(bin_acc - bin_conf)
        rows.append({
            "bin_left": float(left),
            "bin_right": float(right),
            "count": count,
            "accuracy": bin_acc,
            "avg_confidence": bin_conf,
        })

    return float(ece), rows


def plot_confidence_histogram(
    confidences: np.ndarray,
    correctness: np.ndarray,
    output_path: Path,
) -> None:
    """Plot confidence histogram separated by correct vs incorrect predictions."""
    correct_conf = confidences[correctness == 1]
    incorrect_conf = confidences[correctness == 0]

    plt.figure(figsize=(10, 6))
    if correct_conf.size > 0:
        plt.hist(correct_conf, bins=20, alpha=0.6, label="Correct", color="tab:green", density=True)
    if incorrect_conf.size > 0:
        plt.hist(incorrect_conf, bins=20, alpha=0.6, label="Incorrect", color="tab:red", density=True)
    plt.xlabel("Top-1 Confidence")
    plt.ylabel("Density")
    plt.title("Top-1 Confidence Histogram (Correct vs Incorrect)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved confidence histogram to {output_path}")


def plot_reliability_diagram(
    confidences: np.ndarray,
    correctness: np.ndarray,
    output_path: Path,
    n_bins: int = 15,
) -> float:
    """Plot reliability diagram and return ECE."""
    ece, rows = _compute_calibration_bins(confidences, correctness, n_bins=n_bins)
    if not rows:
        return 0.0

    centers = np.array([(r["bin_left"] + r["bin_right"]) / 2.0 for r in rows], dtype=np.float32)
    widths = np.array([r["bin_right"] - r["bin_left"] for r in rows], dtype=np.float32)
    accuracies = np.array([r["accuracy"] for r in rows], dtype=np.float32)

    plt.figure(figsize=(8, 8))
    plt.bar(centers, accuracies, width=widths * 0.95, alpha=0.7, edgecolor="black", label="Empirical Accuracy")
    plt.plot([0, 1], [0, 1], "--", color="black", linewidth=1.5, label="Perfect Calibration")
    plt.xlabel("Confidence")
    plt.ylabel("Accuracy")
    plt.title(f"Reliability Diagram (ECE={ece:.4f})")
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved reliability diagram to {output_path}")
    return ece


def plot_roc_curves(
    y_true: list[int],
    y_probs: np.ndarray,
    class_names: list[str],
    labels: list[int],
    output_path: Path,
) -> None:
    """Plot one-vs-rest ROC curves."""
    y_true_bin = label_binarize(y_true, classes=labels)

    plt.figure(figsize=(11, 9))
    colors = plt.cm.tab20(np.linspace(0, 1, len(labels)))
    plotted = False

    for i, cls in enumerate(labels):
        if cls >= y_probs.shape[1]:
            continue
        if np.sum(y_true_bin[:, i]) == 0 or np.sum(y_true_bin[:, i]) == len(y_true):
            continue
        fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_probs[:, cls])
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, color=colors[i], lw=2, label=f"{class_names[i]} (AUC={roc_auc:.3f})")
        plotted = True

    if not plotted:
        logger.warning("Skipping ROC plot: insufficient class diversity in labels/probabilities.")
        plt.close()
        return

    plt.plot([0, 1], [0, 1], "k--", lw=1.5)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curves (One-vs-Rest)")
    plt.grid(alpha=0.3)
    plt.legend(fontsize=8, ncol=2, loc="lower right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved ROC curves to {output_path}")


def plot_precision_recall_curves(
    y_true: list[int],
    y_probs: np.ndarray,
    class_names: list[str],
    labels: list[int],
    output_path: Path,
) -> None:
    """Plot one-vs-rest Precision-Recall curves."""
    y_true_bin = label_binarize(y_true, classes=labels)

    plt.figure(figsize=(11, 9))
    colors = plt.cm.tab20(np.linspace(0, 1, len(labels)))
    plotted = False

    for i, cls in enumerate(labels):
        if cls >= y_probs.shape[1]:
            continue
        if np.sum(y_true_bin[:, i]) == 0:
            continue
        precision, recall, _ = precision_recall_curve(y_true_bin[:, i], y_probs[:, cls])
        ap = average_precision_score(y_true_bin[:, i], y_probs[:, cls])
        plt.plot(recall, precision, color=colors[i], lw=2, label=f"{class_names[i]} (AP={ap:.3f})")
        plotted = True

    if not plotted:
        logger.warning("Skipping PR plot: probabilities unavailable for evaluable classes.")
        plt.close()
        return

    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curves (One-vs-Rest)")
    plt.grid(alpha=0.3)
    plt.legend(fontsize=8, ncol=2, loc="lower left")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved precision-recall curves to {output_path}")


def plot_class_distribution(
    y_true: list[int],
    idx_to_class: dict[int, str],
    class_counts: dict[str, int] | None,
    output_path: Path,
) -> None:
    """Plot train-vs-eval class distribution."""
    if idx_to_class:
        indices = sorted(idx_to_class.keys())
    else:
        indices = sorted(set(y_true))

    class_names = [idx_to_class.get(i, f"class_{i}") for i in indices]
    eval_counts = [int(sum(1 for y in y_true if y == i)) for i in indices]
    train_counts = None
    if class_counts:
        train_counts = [int(class_counts.get(name, 0)) for name in class_names]

    x = np.arange(len(indices))
    plt.figure(figsize=(max(10, len(indices) * 0.7), 6))
    if train_counts is not None:
        width = 0.4
        plt.bar(x - width / 2, train_counts, width, label="Train count")
        plt.bar(x + width / 2, eval_counts, width, label="Eval support")
    else:
        plt.bar(x, eval_counts, 0.6, label="Eval support")

    plt.xticks(x, class_names, rotation=45, ha="right")
    plt.ylabel("Samples")
    plt.title("Class Distribution")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved class distribution plot to {output_path}")


def load_training_history(training_history_path: Path | None) -> dict[str, Any] | None:
    """Load training history JSON if available."""
    if training_history_path is None or not training_history_path.exists():
        return None
    with open(training_history_path, "r") as f:
        return json.load(f)


def plot_history_curves(history: dict[str, Any], output_dir: Path) -> None:
    """Generate training-history based plots."""
    train_loss = history.get("train_loss", [])
    val_loss = history.get("val_loss", [])
    train_acc = history.get("train_acc", [])
    val_acc = history.get("val_acc", [])
    lr = history.get("lr", [])
    epochs = np.arange(1, len(train_loss) + 1)
    if len(epochs) == 0:
        logger.warning("No history available to plot training curves.")
        return

    # 1) Loss curves
    plt.figure(figsize=(10, 6))
    plt.plot(epochs, train_loss, label="Train Loss", linewidth=2)
    plt.plot(epochs, val_loss, label="Val Loss", linewidth=2)
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Class Loss (Train vs Validation)")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "class_loss_curve.png", dpi=150)
    plt.close()

    # 2) Accuracy curves
    plt.figure(figsize=(10, 6))
    plt.plot(epochs, train_acc, label="Train Accuracy", linewidth=2)
    plt.plot(epochs, val_acc, label="Val Accuracy", linewidth=2)
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.title("Accuracy (Train vs Validation)")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "accuracy_curve.png", dpi=150)
    plt.close()

    # 3) Learning rate
    if len(lr) == len(epochs):
        plt.figure(figsize=(10, 6))
        plt.plot(epochs, lr, linewidth=2)
        plt.xlabel("Epoch")
        plt.ylabel("Learning Rate")
        plt.title("Learning Rate Schedule")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_dir / "learning_rate_curve.png", dpi=150)
        plt.close()

    # 4) Macro/Weighted F1 + Balanced Accuracy over epochs
    val_macro_f1 = history.get("val_macro_f1", [])
    val_weighted_f1 = history.get("val_weighted_f1", [])
    val_balanced_acc = history.get("val_balanced_acc", [])
    if len(val_macro_f1) == len(epochs):
        plt.figure(figsize=(10, 6))
        plt.plot(epochs, val_macro_f1, label="Val Macro F1", linewidth=2)
        if len(val_weighted_f1) == len(epochs):
            plt.plot(epochs, val_weighted_f1, label="Val Weighted F1", linewidth=2)
        if len(val_balanced_acc) == len(epochs):
            plt.plot(epochs, val_balanced_acc, label="Val Balanced Accuracy", linewidth=2)
        plt.xlabel("Epoch")
        plt.ylabel("Score")
        plt.title("Validation Summary Metrics")
        plt.grid(alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / "validation_summary_metrics_curve.png", dpi=150)
        plt.close()

    # 5) Head vs Tail metrics over epochs
    val_head_f1 = history.get("val_head_f1", [])
    val_tail_f1 = history.get("val_tail_f1", [])
    val_head_acc = history.get("val_head_acc", [])
    val_tail_acc = history.get("val_tail_acc", [])
    if len(val_head_f1) == len(epochs) or len(val_head_acc) == len(epochs):
        plt.figure(figsize=(10, 6))
        if len(val_head_f1) == len(epochs):
            plt.plot(epochs, [np.nan if v is None else v for v in val_head_f1], label="Head Macro F1", linewidth=2)
        if len(val_tail_f1) == len(epochs):
            plt.plot(epochs, [np.nan if v is None else v for v in val_tail_f1], label="Tail Macro F1", linewidth=2)
        if len(val_head_acc) == len(epochs):
            plt.plot(epochs, [np.nan if v is None else v for v in val_head_acc], "--", label="Head Accuracy", linewidth=2)
        if len(val_tail_acc) == len(epochs):
            plt.plot(epochs, [np.nan if v is None else v for v in val_tail_acc], "--", label="Tail Accuracy", linewidth=2)
        plt.xlabel("Epoch")
        plt.ylabel("Score")
        plt.title("Head vs Tail Performance Over Epochs")
        plt.grid(alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / "head_tail_over_epochs.png", dpi=150)
        plt.close()


def print_summary(metrics: dict[str, Any], idx_to_class: dict[int, str]) -> None:
    """Print metrics summary."""
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)

    # Overall metrics
    print(f"\nOverall Metrics:")
    print(f"  Accuracy:          {metrics['accuracy']:.4f}")
    print(f"  Balanced Accuracy: {metrics['balanced_accuracy']:.4f}")
    print(f"  Weighted F1:       {metrics['weighted_f1']:.4f}")
    print(f"  Weighted Precision:{metrics['weighted_precision']:.4f}")
    print(f"  Weighted Recall:   {metrics['weighted_recall']:.4f}")
    print(f"  Macro F1:          {metrics['macro_f1']:.4f} (Avg of per-class F1)")

    # Per-class metrics
    per_class = metrics.get("per_class", {})
    class_names = [k for k in per_class.keys() if k not in ["accuracy", "macro avg", "weighted avg"]]
    
    if class_names:
        print(f"\nPer-Class Metrics:")
        print(f"  {'Class':<15} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<10}")
        print(f"  {'-'*15} {'-'*12} {'-'*12} {'-'*12} {'-'*10}")
        for cls in class_names:
            metrics_cls = per_class[cls]
            print(f"  {cls:<15} {metrics_cls['precision']:<12.4f} {metrics_cls['recall']:<12.4f} "
                  f"{metrics_cls['f1-score']:<12.4f} {int(metrics_cls['support']):<10}")

    # Head/Tail analysis
    if metrics.get("head_tail"):
        ht = metrics["head_tail"]
        print(f"\nHead/Tail Analysis:")
        
        if "head_class_names" in ht:
            head_classes_str = ", ".join(ht["head_class_names"])
            print(f"  Head Classes: {head_classes_str}")
            if "head_accuracy" in ht:
                print(f"  Head Accuracy: {ht['head_accuracy']:.4f}")
            if "head_f1_macro" in ht:
                print(f"  Head Macro F1: {ht['head_f1_macro']:.4f}")
        
        if "tail_class_names" in ht:
            tail_classes_str = ", ".join(ht["tail_class_names"])
            print(f"  Tail Classes: {tail_classes_str}")
            if "tail_accuracy" in ht:
                print(f"  Tail Accuracy: {ht['tail_accuracy']:.4f}")
            if "tail_f1_macro" in ht:
                print(f"  Tail Macro F1: {ht['tail_f1_macro']:.4f}")

    print("\n" + "-" * 60)


def evaluate_per_source(
    y_true: list[int],
    y_pred: list[int],
    sources: list[str],
    idx_to_class: dict[int, str],
    class_counts: dict[str, int] | None,
    output_dir: Path,
) -> dict[str, dict[str, Any]]:
    """Evaluate metrics separately for each source dataset.

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        sources: Source dataset per sample.
        idx_to_class: Index to class name mapping.
        class_counts: Training class counts.
        output_dir: Base output directory.

    Returns:
        Dict mapping source_name -> metrics dict.
    """
    unique_sources = sorted(set(sources))
    if len(unique_sources) <= 1 and unique_sources[0] == "unknown":
        return {}

    per_source_results = {}

    print("\n" + "=" * 60)
    print("PER-SOURCE EVALUATION")
    print("=" * 60)

    for source_name in unique_sources:
        if source_name == "unknown":
            continue

        # Filter indices for this source
        indices = [i for i, s in enumerate(sources) if s == source_name]
        if not indices:
            continue

        src_y_true = [y_true[i] for i in indices]
        src_y_pred = [y_pred[i] for i in indices]

        # Compute metrics
        src_metrics = compute_metrics(src_y_true, src_y_pred, idx_to_class, class_counts)
        per_source_results[source_name] = src_metrics

        # Print summary
        print(f"\n--- {source_name} ({len(indices)} samples) ---")
        print(f"  Accuracy:     {src_metrics['accuracy']:.4f}")
        print(f"  Weighted F1:  {src_metrics['weighted_f1']:.4f}")
        print(f"  Macro F1:     {src_metrics['macro_f1']:.4f}")

        # Save per-source outputs
        source_dir = output_dir / f"per_source/{source_name}"
        source_dir.mkdir(parents=True, exist_ok=True)

        with open(source_dir / "metrics.json", "w") as f:
            json.dump(src_metrics, f, indent=2)

        # Plot per-source confusion matrix
        cm = np.array(src_metrics["confusion_matrix"])
        unique_labels = sorted(set(src_y_true) | set(src_y_pred))
        class_names = [idx_to_class.get(i, f"class_{i}") for i in unique_labels]
        plot_confusion_matrix(cm, class_names, source_dir / "confusion_matrix.png")
        plot_per_class_metrics(src_metrics["per_class"], source_dir / "per_class_metrics.png")

    # Print comparison table
    if per_source_results:
        print(f"\n{'='*60}")
        print("SOURCE COMPARISON SUMMARY")
        print(f"{'='*60}")
        print(f"  {'Source':<20} {'Samples':<10} {'Accuracy':<12} {'W-F1':<12} {'M-F1':<12}")
        print(f"  {'-'*20} {'-'*10} {'-'*12} {'-'*12} {'-'*12}")
        for src in sorted(per_source_results.keys()):
            m = per_source_results[src]
            n = len([s for s in sources if s == src])
            print(f"  {src:<20} {n:<10} {m['accuracy']:<12.4f} {m['weighted_f1']:<12.4f} {m['macro_f1']:<12.4f}")
        print(f"  {'-'*20} {'-'*10} {'-'*12} {'-'*12} {'-'*12}")

    return per_source_results


def write_evaluation_report(
    output_path: Path,
    metrics: dict[str, Any],
    generated_artifacts: list[str],
    skipped_items: list[str],
) -> None:
    """Write a markdown report summarizing evaluation and generated artifacts."""
    lines = [
        "# Evaluation Report",
        "",
        "## Overall Metrics",
        f"- Accuracy: `{metrics.get('accuracy', 0.0):.4f}`",
        f"- Balanced Accuracy: `{metrics.get('balanced_accuracy', 0.0):.4f}`",
        f"- Macro F1: `{metrics.get('macro_f1', 0.0):.4f}`",
        f"- Weighted F1: `{metrics.get('weighted_f1', 0.0):.4f}`",
        "",
        "## Generated Artifacts",
    ]
    for item in generated_artifacts:
        lines.append(f"- `{item}`")

    if skipped_items:
        lines.extend(["", "## Skipped (Missing Inputs)"])
        for item in skipped_items:
            lines.append(f"- {item}")

    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    logger.info(f"Saved evaluation report to {output_path}")


class Step08Eval(PipelineStep):
    """Pipeline step for model evaluation.

    This step:
    1. Loads predictions (from file or by running inference)
    2. Computes metrics (Accuracy, F1, Precision, Recall)
    3. Performs head/tail analysis for long-tailed datasets
    4. Plots confusion matrix and per-class metrics
    """

    @property
    def name(self) -> str:
        return "08_eval"

    @property
    def description(self) -> str:
        return "Evaluate model performance with long-tail metrics."

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.predictions_path: Path | None = None
        self.checkpoint_path: Path | None = None
        self.manifest_path: Path | None = None
        self.split: str = "test"
        self.class_names_path: Path | None = None
        self.class_counts_path: Path | None = None
        self.training_history_path: Path | None = None
        self.output_dir: Path = Path("runs/eval")
        self.device: str = "auto"

    def validate(self) -> bool:
        """Validate inputs."""
        if not self.predictions_path and not (self.checkpoint_path and self.manifest_path):
            logger.error("Must provide either predictions_path or (checkpoint_path and manifest_path)")
            return False
        return True

    def run(self) -> int:
        """Execute evaluation.

        Returns:
            0 on success, 1 on failure.
        """
        if not self.validate():
            return 1

        # Device
        if self.device == "auto":
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            device = torch.device(self.device)

        # Get predictions
        if self.predictions_path:
            logger.info(f"Loading predictions from {self.predictions_path}")
            y_true, y_pred, sources, y_probs, confidences = load_predictions(self.predictions_path)
        else:
            logger.info(f"Running inference with {self.checkpoint_path}")
            y_true, y_pred, sources, y_probs, confidences = run_inference(
                self.checkpoint_path,
                self.manifest_path,
                self.split,
                device,
            )

        logger.info(f"Evaluating {len(y_true)} samples")

        # Load class info
        idx_to_class = {}
        class_counts = {}

        # 1. Try explicit paths
        if self.class_names_path and self.class_names_path.exists():
            idx_to_class, _ = load_class_info(self.class_names_path)
        # 2. Try auto-detect from manifest dir
        elif self.manifest_path:
            manifest_dir = self.manifest_path.parent
            candidate = manifest_dir / "class_to_idx.json"
            if candidate.exists():
                logger.info(f"Auto-detected class names at {candidate}")
                idx_to_class, _ = load_class_info(candidate)

        if self.class_counts_path and self.class_counts_path.exists():
             with open(self.class_counts_path, "r") as f:
                class_counts = json.load(f)
        elif self.manifest_path:
            manifest_dir = self.manifest_path.parent
            candidate = manifest_dir / "class_counts.json"
            if candidate.exists():
                logger.info(f"Auto-detected class counts at {candidate}")
                with open(candidate, "r") as f:
                    class_counts = json.load(f)

        # Compute metrics
        metrics = compute_metrics(y_true, y_pred, idx_to_class, class_counts)

        # Print summary
        print_summary(metrics, idx_to_class)

        # Save outputs
        self.output_dir.mkdir(parents=True, exist_ok=True)

        metrics_path = self.output_dir / "metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Saved metrics to {metrics_path}")

        generated_artifacts: list[str] = ["metrics.json"]
        skipped_items: list[str] = []

        unique_labels = sorted(set(y_true) | set(y_pred))
        class_names = [idx_to_class.get(i, f"class_{i}") for i in unique_labels]

        # Plot confusion matrix (raw + normalized) and per-class metrics
        cm = np.array(metrics["confusion_matrix"])
        plot_confusion_matrix(cm, class_names, self.output_dir / "confusion_matrix_raw.png", normalize=False)
        plot_confusion_matrix(cm, class_names, self.output_dir / "confusion_matrix.png", normalize=True)
        plot_per_class_metrics(metrics["per_class"], self.output_dir / "per_class_metrics.png")
        generated_artifacts.extend([
            "confusion_matrix_raw.png",
            "confusion_matrix.png",
            "per_class_metrics.png",
        ])

        # Class distribution plot (train counts vs eval support)
        plot_class_distribution(y_true, idx_to_class, class_counts, self.output_dir / "class_distribution.png")
        generated_artifacts.append("class_distribution.png")

        probs_np = np.asarray(y_probs, dtype=np.float32) if y_probs is not None and len(y_probs) > 0 else None
        conf_np: np.ndarray | None = None
        if confidences is not None and len(confidences) == len(y_true):
            conf_np = np.asarray(confidences, dtype=np.float32)
        elif probs_np is not None:
            conf_np = probs_np.max(axis=1)

        # Confidence histogram + reliability (ECE)
        if conf_np is not None:
            correctness = (np.asarray(y_true) == np.asarray(y_pred)).astype(np.int32)
            plot_confidence_histogram(conf_np, correctness, self.output_dir / "confidence_histogram.png")
            ece = plot_reliability_diagram(conf_np, correctness, self.output_dir / "reliability_diagram.png")
            metrics["calibration"] = {"ece": float(ece)}
            generated_artifacts.extend(["confidence_histogram.png", "reliability_diagram.png"])
        else:
            skipped_items.append("confidence_histogram + reliability_diagram (confidence/probabilities unavailable)")

        # ROC + PR curves (requires full per-class probabilities)
        if probs_np is not None and probs_np.ndim == 2:
            plot_roc_curves(y_true, probs_np, class_names, unique_labels, self.output_dir / "roc_curves.png")
            plot_precision_recall_curves(
                y_true, probs_np, class_names, unique_labels, self.output_dir / "precision_recall_curves.png"
            )
            generated_artifacts.extend(["roc_curves.png", "precision_recall_curves.png"])
        else:
            skipped_items.append("roc_curves + precision_recall_curves (full probabilities unavailable)")

        # --- Per-source evaluation ---
        per_source_metrics = evaluate_per_source(
            y_true, y_pred, sources, idx_to_class, class_counts, self.output_dir
        )
        if per_source_metrics:
            metrics["per_source"] = {
                src: {k: v for k, v in m.items() if k != "confusion_matrix"}
                for src, m in per_source_metrics.items()
            }
            # Re-save metrics with per-source data
            with open(metrics_path, "w") as f:
                json.dump(metrics, f, indent=2)

        # Training-history based plots
        history_path = self.training_history_path
        if history_path is None and self.checkpoint_path is not None:
            auto_history = self.checkpoint_path.parent / "artifacts" / "training_history.json"
            if auto_history.exists():
                history_path = auto_history
                logger.info(f"Auto-detected training history at {history_path}")

        history = load_training_history(history_path)
        if history:
            plot_history_curves(history, self.output_dir)
            for artifact_name in [
                "class_loss_curve.png",
                "accuracy_curve.png",
                "learning_rate_curve.png",
                "validation_summary_metrics_curve.png",
                "head_tail_over_epochs.png",
            ]:
                if (self.output_dir / artifact_name).exists():
                    generated_artifacts.append(artifact_name)
                else:
                    skipped_items.append(f"{artifact_name} (metric not available in history)")
        else:
            skipped_items.append("history-based curves (training_history.json unavailable)")

        # Save enriched metrics and markdown report
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)
        write_evaluation_report(
            self.output_dir / "evaluation_report.md",
            metrics,
            generated_artifacts,
            skipped_items,
        )

        logger.info(f"Evaluation complete. Results saved to {self.output_dir}")
        logger.info("Step08Eval completed successfully.")
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate VCR model")
    
    # Input options
    parser.add_argument("--predictions", type=str,
                        help="Path to predictions.jsonl (from 07_infer.py)")
    parser.add_argument("--checkpoint", type=str,
                        help="Path to model checkpoint (runs inference)")
    parser.add_argument("--manifest", type=str,
                        help="Path to manifest (required if using --checkpoint)")
    parser.add_argument("--split", type=str, default="test",
                        help="Split to evaluate (default: test)")

    # Class info
    parser.add_argument("--class-names", type=str, default="data/processed/class_to_idx.json",
                        help="Path to class_to_idx.json")
    parser.add_argument("--class-counts", type=str, default="data/processed/class_counts.json",
                        help="Path to class_counts.json (for head/tail analysis)")
    parser.add_argument("--training-history", type=str, default=None,
                        help="Path to training_history.json for epoch-based curves")

    # Output
    parser.add_argument("--output-dir", type=str, default="runs/eval",
                        help="Output directory for plots and metrics")

    # Device
    parser.add_argument("--device", type=str, default="auto",
                        choices=["auto", "cuda", "cpu"])

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    step = Step08Eval(config={})
    step.predictions_path = Path(args.predictions) if args.predictions else None
    step.checkpoint_path = Path(args.checkpoint) if args.checkpoint else None
    step.manifest_path = Path(args.manifest) if args.manifest else None
    step.split = args.split
    step.class_names_path = Path(args.class_names)
    step.class_counts_path = Path(args.class_counts)
    step.training_history_path = Path(args.training_history) if args.training_history else None
    step.output_dir = Path(args.output_dir)
    step.device = args.device

    return step.run()


if __name__ == "__main__":
    sys.exit(main())

