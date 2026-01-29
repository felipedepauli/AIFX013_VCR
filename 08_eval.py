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
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from torch.utils.data import DataLoader

# Import modules
import src.backbones  # noqa: F401
import src.fusion  # noqa: F401

from src.data import ManifestDataset, build_transforms

# Import model
sys.path.insert(0, str(Path(__file__).parent))
from importlib.util import spec_from_file_location, module_from_spec
spec = spec_from_file_location("model", Path(__file__).parent / "03_model.py")
model_module = module_from_spec(spec)
spec.loader.exec_module(model_module)
VCRModel = model_module.VCRModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_predictions(predictions_path: Path) -> tuple[list[int], list[int]]:
    """Load predictions from JSONL file.

    Returns:
        Tuple of (y_true, y_pred).
    """
    y_true = []
    y_pred = []

    with open(predictions_path, "r") as f:
        for line in f:
            record = json.loads(line)
            if "true_idx" in record:
                y_true.append(record["true_idx"])
                y_pred.append(record["pred_idx"])

    return y_true, y_pred


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
) -> tuple[list[int], list[int]]:
    """Run inference on manifest and get predictions.

    Returns:
        Tuple of (y_true, y_pred).
    """
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)
    config = checkpoint.get("config", {})
    
    # Handle nested config from optimization (config["train"])
    train_config = config.get("train", config)

    model = VCRModel(
        num_classes=train_config.get("num_classes", 10),
        backbone_name=train_config.get("backbone", "resnet50"),
        fusion_name=train_config.get("fusion", "msff"),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
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

    with torch.no_grad():
        for images, targets in loader:
            images = images.to(device)
            logits = model(images)
            preds = logits.argmax(dim=1)

            y_true.extend(targets.tolist())
            y_pred.extend(preds.cpu().tolist())

    return y_true, y_pred


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
    macro_recall = recall_score(y_true, y_pred, average="macro", zero_division=0)

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
            head_tail_metrics["head_classes"] = len(head_classes)

        if tail_mask:
            tail_acc = accuracy_score(
                [y_true[i] for i in tail_mask],
                [y_pred[i] for i in tail_mask],
            )
            head_tail_metrics["tail_accuracy"] = tail_acc
            head_tail_metrics["tail_classes"] = len(tail_classes)

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
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


def print_summary(metrics: dict[str, Any], idx_to_class: dict[int, str]) -> None:
    """Print metrics summary."""
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)

    # Overall metrics
    print(f"\nOverall Metrics:")
    print(f"  Accuracy:        {metrics['accuracy']:.4f}")
    print(f"  Macro F1:        {metrics['macro_f1']:.4f}")
    print(f"  Weighted F1:     {metrics['weighted_f1']:.4f}")
    print(f"  Macro Precision: {metrics['macro_precision']:.4f}")
    print(f"  Macro Recall:    {metrics['macro_recall']:.4f}")

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
        
        if "tail_class_names" in ht:
            tail_classes_str = ", ".join(ht["tail_class_names"])
            print(f"  Tail Classes: {tail_classes_str}")
            if "tail_accuracy" in ht:
                print(f"  Tail Accuracy: {ht['tail_accuracy']:.4f}")

    print("\n" + "-" * 60)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate VCR model")

    # Input options
    parser.add_argument("--predictions", type=str,
                        help="Path to predictions.jsonl (from 05_infer.py)")
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

    # Output
    parser.add_argument("--output-dir", type=str, default="runs/eval",
                        help="Output directory for plots and metrics")

    # Device
    parser.add_argument("--device", type=str, default="auto",
                        choices=["auto", "cuda", "cpu"])

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Device
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)

    # Get predictions
    if args.predictions:
        logger.info(f"Loading predictions from {args.predictions}")
        y_true, y_pred = load_predictions(Path(args.predictions))
    elif args.checkpoint and args.manifest:
        logger.info(f"Running inference with {args.checkpoint}")
        y_true, y_pred = run_inference(
            Path(args.checkpoint),
            Path(args.manifest),
            args.split,
            device,
        )
    else:
        logger.error("Must provide either --predictions or (--checkpoint and --manifest)")
        return 1

    logger.info(f"Evaluating {len(y_true)} samples")

    # Load class info
    idx_to_class = {}
    class_counts = {}

    if Path(args.class_names).exists():
        idx_to_class, _ = load_class_info(Path(args.class_names))
    elif args.manifest:
        # Fallback: check maniifest directory
        manifest_dir = Path(args.manifest).parent
        candidate = manifest_dir / "class_to_idx.json"
        if candidate.exists():
            logger.info(f"Auto-detected class names at {candidate}")
            idx_to_class, _ = load_class_info(candidate)

    if Path(args.class_counts).exists():
        with open(args.class_counts, "r") as f:
            class_counts = json.load(f)
    elif args.manifest:
         # Fallback: check maniifest directory
        manifest_dir = Path(args.manifest).parent
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
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save metrics JSON
    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {metrics_path}")

    # Plot confusion matrix
    if idx_to_class:
        cm = np.array(metrics["confusion_matrix"])
        # Only use classes that appear in the confusion matrix
        unique_labels = sorted(set(y_true) | set(y_pred))
        class_names = [idx_to_class.get(i, f"class_{i}") for i in unique_labels]
        plot_confusion_matrix(cm, class_names, output_dir / "confusion_matrix.png")
        plot_per_class_metrics(metrics["per_class"], output_dir / "per_class_metrics.png")

    logger.info(f"Evaluation complete. Results saved to {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
