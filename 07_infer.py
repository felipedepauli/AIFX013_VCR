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


class Step07Infer(PipelineStep):
    """Pipeline step for model inference.

    This step:
    1. Loads a trained model from checkpoint
    2. Runs inference on images (single, directory, or manifest)
    3. Saves predictions to JSONL
    """

    @property
    def name(self) -> str:
        return "07_infer"

    @property
    def description(self) -> str:
        return "Run inference with trained VCR model."

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.checkpoint_path: Path | None = None
        self.class_names_path: Path | None = None
        self.image_path: Path | None = None
        self.image_dir: Path | None = None
        self.manifest_path: Path | None = None
        self.split: str | None = None
        self.output_path: Path = Path("predictions.jsonl")
        self.batch_size: int = 32
        self.image_size: int = 224
        self.device: str = "auto"

    def validate(self) -> bool:
        """Validate that checkpoint exists."""
        if self.checkpoint_path is None or not self.checkpoint_path.exists():
            logger.error(f"Checkpoint not found: {self.checkpoint_path}")
            return False
        if self.image_path is None and self.image_dir is None and self.manifest_path is None:
            logger.error("Must specify --image, --image-dir, or --manifest")
            return False
        return True

    def run(self) -> int:
        """Execute inference.

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
        logger.info(f"Using device: {device}")

        # Load model
        model, model_config = load_model(self.checkpoint_path, device)

        # Load class names
        idx_to_class = None
        if self.class_names_path and self.class_names_path.exists():
            idx_to_class = load_class_names(self.class_names_path)
            logger.info(f"Loaded {len(idx_to_class)} class names")

        # Transform
        transform = build_transforms(config={}, is_train=False, image_size=self.image_size)

        # Run inference
        if self.image_path:
            result = predict_single(model, self.image_path, transform, device, idx_to_class)
            print(json.dumps(result, indent=2))
        elif self.image_dir:
            predictions = predict_directory(model, self.image_dir, transform, device, idx_to_class)
            save_predictions(predictions, self.output_path)
        elif self.manifest_path:
            dataset = ManifestDataset(str(self.manifest_path), split=self.split, transform=transform)
            loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False, num_workers=4)
            logger.info(f"Loaded {len(dataset)} samples from manifest")
            predictions = predict_batch(model, loader, device, idx_to_class)
            save_predictions(predictions, self.output_path)

        logger.info("Step07Infer completed successfully.")
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run inference with VCR model")
    parser.add_argument("--checkpoint", type=str, required=True,
                        help="Path to model checkpoint (.pt)")
    parser.add_argument("--class-names", type=str, default="data/processed/class_to_idx.json",
                        help="Path to class_to_idx.json")
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--image", type=str, help="Single image path")
    input_group.add_argument("--image-dir", type=str, help="Directory with images")
    input_group.add_argument("--manifest", type=str, help="Manifest file for batch inference")
    parser.add_argument("--split", type=str, default=None,
                        help="Filter manifest by split (train/val/test)")
    parser.add_argument("--output", type=str, default="predictions.jsonl",
                        help="Output file for predictions")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cuda", "cpu"])
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    step = Step07Infer(config={})
    step.checkpoint_path = Path(args.checkpoint)
    step.class_names_path = Path(args.class_names)
    step.image_path = Path(args.image) if args.image else None
    step.image_dir = Path(args.image_dir) if args.image_dir else None
    step.manifest_path = Path(args.manifest) if args.manifest else None
    step.split = args.split
    step.output_path = Path(args.output)
    step.batch_size = args.batch_size
    step.image_size = args.image_size
    step.device = args.device

    return step.run()


if __name__ == "__main__":
    sys.exit(main())
