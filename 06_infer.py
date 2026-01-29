#!/usr/bin/env python3
"""05_infer.py - Run inference on images.

Usage:
    # Single image
    python 05_infer.py --checkpoint runs/train/best.pt --image data/crops/test.jpg

    # Manifest (batch)
    python 05_infer.py --checkpoint runs/train/best.pt --manifest data/manifests/manifest_ready.jsonl --split test

    # Directory of images
    python 05_infer.py --checkpoint runs/train/best.pt --image-dir data/crops/ --output predictions.jsonl
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import torch
from PIL import Image
from torch.utils.data import DataLoader

# Import modules to trigger factory registrations
import src.backbones  # noqa: F401
import src.fusion  # noqa: F401

from src.data import ManifestDataset, build_transforms
from src.utils.config import load_config

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


def load_model(checkpoint_path: Path, device: torch.device) -> tuple[VCRModel, dict[str, Any]]:
    """Load model from checkpoint.

    Args:
        checkpoint_path: Path to .pt checkpoint.
        device: Device to load model on.

    Returns:
        Tuple of (model, config).
    """
    checkpoint = torch.load(checkpoint_path, map_location=device)

    config = checkpoint.get("config", {})
    
    # Handle nested config from optimization (config["train"])
    train_config = config.get("train", config)
    
    num_classes = train_config.get("num_classes", 10)
    backbone = train_config.get("backbone", "resnet50")
    fusion = train_config.get("fusion", "msff")

    model = VCRModel(
        num_classes=num_classes,
        backbone_name=backbone,
        fusion_name=fusion,
    )

    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    logger.info(f"Loaded model from {checkpoint_path}")
    logger.info(f"  Backbone: {backbone}, Fusion: {fusion}, Classes: {num_classes}")

    return model, config


def load_class_names(class_to_idx_path: Path) -> dict[int, str]:
    """Load class names from class_to_idx.json.

    Args:
        class_to_idx_path: Path to class_to_idx.json.

    Returns:
        Dict mapping index to class name.
    """
    with open(class_to_idx_path, "r") as f:
        class_to_idx = json.load(f)
    return {v: k for k, v in class_to_idx.items()}


def predict_single(
    model: VCRModel,
    image_path: Path,
    transform,
    device: torch.device,
    idx_to_class: dict[int, str] | None = None,
) -> dict[str, Any]:
    """Predict on a single image.

    Args:
        model: Loaded VCRModel.
        image_path: Path to image.
        transform: Image transform.
        device: Device.
        idx_to_class: Optional mapping from index to class name.

    Returns:
        Dict with prediction results.
    """
    image = Image.open(image_path).convert("RGB")
    tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)
        pred_idx = logits.argmax(dim=1).item()
        confidence = probs[0, pred_idx].item()

    result = {
        "image_path": str(image_path),
        "pred_idx": pred_idx,
        "confidence": round(confidence, 4),
    }

    if idx_to_class:
        result["pred_label"] = idx_to_class.get(pred_idx, f"class_{pred_idx}")

    return result


def predict_batch(
    model: VCRModel,
    loader: DataLoader,
    device: torch.device,
    idx_to_class: dict[int, str] | None = None,
) -> list[dict[str, Any]]:
    """Predict on a dataloader.

    Args:
        model: Loaded VCRModel.
        loader: DataLoader with ManifestDataset.
        device: Device.
        idx_to_class: Optional mapping from index to class name.

    Returns:
        List of prediction dicts.
    """
    results = []
    dataset = loader.dataset

    all_preds = []
    all_probs = []

    with torch.no_grad():
        for images, _ in loader:
            images = images.to(device)
            logits = model(images)
            probs = torch.softmax(logits, dim=1)
            preds = logits.argmax(dim=1)

            all_preds.extend(preds.cpu().tolist())
            all_probs.extend(probs.cpu().tolist())

    for i, (pred_idx, probs) in enumerate(zip(all_preds, all_probs)):
        record = dataset.records[i]
        confidence = probs[pred_idx]

        result = {
            "id": record["id"],
            "image_path": record.get("crop_path", record.get("image_path", "")),
            "pred_idx": pred_idx,
            "confidence": round(confidence, 4),
        }

        if idx_to_class:
            result["pred_label"] = idx_to_class.get(pred_idx, f"class_{pred_idx}")

        # Include ground truth if available
        if "label" in record:
            result["true_label"] = record["label"]
        if "label_idx" in record:
            result["true_idx"] = record["label_idx"]

        results.append(result)

    return results


def predict_directory(
    model: VCRModel,
    image_dir: Path,
    transform,
    device: torch.device,
    idx_to_class: dict[int, str] | None = None,
) -> list[dict[str, Any]]:
    """Predict on all images in a directory.

    Args:
        model: Loaded VCRModel.
        image_dir: Directory with images.
        transform: Image transform.
        device: Device.
        idx_to_class: Optional mapping from index to class name.

    Returns:
        List of prediction dicts.
    """
    extensions = (".jpg", ".jpeg", ".png")
    image_paths = []
    for ext in extensions:
        image_paths.extend(image_dir.glob(f"*{ext}"))
        image_paths.extend(image_dir.glob(f"*{ext.upper()}"))

    image_paths = sorted(set(image_paths))
    logger.info(f"Found {len(image_paths)} images in {image_dir}")

    results = []
    for img_path in image_paths:
        result = predict_single(model, img_path, transform, device, idx_to_class)
        results.append(result)

    return results


def save_predictions(predictions: list[dict], output_path: Path) -> None:
    """Save predictions to JSONL file."""
    with open(output_path, "w", encoding="utf-8") as f:
        for pred in predictions:
            f.write(json.dumps(pred, ensure_ascii=False) + "\n")
    logger.info(f"Saved {len(predictions)} predictions to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run inference with VCR model")

    parser.add_argument("--checkpoint", type=str, required=True,
                        help="Path to model checkpoint (.pt)")
    parser.add_argument("--class-names", type=str, default="data/processed/class_to_idx.json",
                        help="Path to class_to_idx.json")

    # Input modes (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--image", type=str, help="Single image path")
    input_group.add_argument("--image-dir", type=str, help="Directory with images")
    input_group.add_argument("--manifest", type=str, help="Manifest file for batch inference")

    parser.add_argument("--split", type=str, default=None,
                        help="Filter manifest by split (train/val/test)")
    parser.add_argument("--output", type=str, default="predictions.jsonl",
                        help="Output file for predictions")
    parser.add_argument("--batch-size", type=int, default=32,
                        help="Batch size for manifest inference")
    parser.add_argument("--image-size", type=int, default=224,
                        help="Input image size")
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
    logger.info(f"Using device: {device}")

    # Load model
    model, config = load_model(Path(args.checkpoint), device)

    # Load class names
    idx_to_class = None
    if Path(args.class_names).exists():
        idx_to_class = load_class_names(Path(args.class_names))
        logger.info(f"Loaded {len(idx_to_class)} class names")

    # Transform
    transform = build_transforms(config={}, is_train=False, image_size=args.image_size)

    # Run inference based on input mode
    if args.image:
        # Single image
        result = predict_single(model, Path(args.image), transform, device, idx_to_class)
        print(json.dumps(result, indent=2))
        return 0

    elif args.image_dir:
        # Directory of images
        predictions = predict_directory(model, Path(args.image_dir), transform, device, idx_to_class)
        save_predictions(predictions, Path(args.output))

    elif args.manifest:
        # Manifest batch
        dataset = ManifestDataset(
            args.manifest,
            split=args.split,
            transform=transform,
        )
        loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=4)
        logger.info(f"Loaded {len(dataset)} samples from manifest")

        predictions = predict_batch(model, loader, device, idx_to_class)
        save_predictions(predictions, Path(args.output))

    return 0


if __name__ == "__main__":
    sys.exit(main())
