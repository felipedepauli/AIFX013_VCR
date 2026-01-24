"""Transforms factory for data augmentation."""

import logging
from typing import Any, Callable

import torch
import torchvision.transforms as T

logger = logging.getLogger(__name__)


def build_transforms(
    config: dict[str, Any],
    is_train: bool = True,
    image_size: int = 224,
) -> Callable:
    """Build transform pipeline from config.

    Args:
        config: Dict containing transform configuration.
        is_train: Whether to include augmentation transforms.
        image_size: Target image size.

    Returns:
        Composed transform function.
    """
    transforms_list = []

    # 1. Base Augmentations (Train only)
    if is_train:
        # Custom augmentations from config
        if "brightness" in config:
            factor = config["brightness"].get("factor", 0.0)
            if factor > 0:
                logger.debug(f"Adding ColorJitter(brightness={factor})")
                transforms_list.append(T.ColorJitter(brightness=factor))

        if "contrast" in config:
            factor = config["contrast"].get("factor", 0.0)
            if factor > 0:
                logger.debug(f"Adding ColorJitter(contrast={factor})")
                transforms_list.append(T.ColorJitter(contrast=factor))

        if config.get("histogram_equalization", False):
            logger.debug("Adding RandomEqualize(p=1.0)")
            transforms_list.append(T.RandomEqualize(p=1.0))

        if "gaussian_blur" in config:
            kernel_size = config["gaussian_blur"].get("kernel_size", 3)
            logger.debug(f"Adding GaussianBlur(kernel_size={kernel_size})")
            transforms_list.append(T.GaussianBlur(kernel_size=kernel_size))

        # Standard augmentations
        transforms_list.append(T.RandomHorizontalFlip(p=0.5))
        transforms_list.append(T.RandomRotation(degrees=10))

    # 2. Resize
    transforms_list.append(T.Resize((image_size, image_size)))

    # 3. ToTensor
    transforms_list.append(T.ToTensor())

    # 4. Normalize (ImageNet stats)
    transforms_list.append(
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    )

    return T.Compose(transforms_list)
