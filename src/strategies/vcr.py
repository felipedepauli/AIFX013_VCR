"""Default VCR Training Strategy."""

import sys
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

from src.core.factories import LossFactory
from src.core.interfaces import BaseTrainingStrategy

# Load VCRModel dynamically to avoid circular imports or just standard import if path is fixed
# Assuming 04_model.py is where VCRModel lives. 
# Ideal refactor would move VCRModel to src/core/models.py, but for now we import from 04_model.py
sys.path.insert(0, str(Path(__file__).parents[2]))  # Add project root to path
from importlib.util import spec_from_file_location, module_from_spec

def import_model_class():
    """Dynamically import VCRModel from 04_model.py."""
    try:
        # Try relative import first if in python path
        # But 03_model is at root, so...
        project_root = Path(__file__).parents[2]
        spec = spec_from_file_location("model_module", project_root / "04_model.py")
        if spec and spec.loader:
            model_module = module_from_spec(spec)
            spec.loader.exec_module(model_module)
            return model_module.VCRModel
    except Exception as e:
        print(f"Failed to import VCRModel: {e}")
        return None

VCRModel = import_model_class()


class VCRStrategy(BaseTrainingStrategy):
    """Standard VCR training strategy (Backbone + MSFF + Smooth Loss)."""

    def build_model(self) -> nn.Module:
        """Build VCRModel."""
        if VCRModel is None:
            raise ImportError("Could not import VCRModel from 04_model.py")
            
        # Architecture params are in "model" section
        model_cfg = self.config.get("model", {})
        train_cfg = self.config.get("training", {}) # Fallback to looking here? No, stick to structure
        
        # Determine architecture params
        # Priorities: Config > Defaults
        return VCRModel(
            num_classes=self.num_classes,
            backbone_name=model_cfg.get("backbone", "resnet50"),
            fusion_name=model_cfg.get("fusion", "msff"),
            dropout=float(model_cfg.get("dropout", 0.2)),
        )

    def configure_loss(self) -> nn.Module:
        """Configure loss function."""
        # Loss params are in "loss" section
        loss_section = self.config.get("loss", {})
        train_section = self.config.get("training", {})
        
        loss_fn = loss_section.get("name", "smooth_modulation")
        
        # Build loss config with all necessary parameters
        loss_cfg = {
            "max_epoch": int(train_section.get("epochs", 50)),
        }
        
        # Add loss-specific parameters
        if loss_fn == "smooth_modulation":
            loss_cfg["tau"] = loss_section.get("tau", 0.5)
            loss_cfg["modulation_type"] = loss_section.get("modulation_type", "cosine")
            loss_cfg["reduction"] = loss_section.get("reduction", "mean")
        elif loss_fn == "focal":
            loss_cfg["gamma"] = loss_section.get("gamma", 2.0)
            loss_cfg["alpha"] = loss_section.get("alpha", 0.25)
            loss_cfg["reduction"] = loss_section.get("reduction", "mean")
            
        return LossFactory.create(loss_fn, loss_cfg)

    def configure_optimizers(self, model: nn.Module) -> tuple[torch.optim.Optimizer, Any]:
        """Configure AdamW and CosineAnnealingLR."""
        train_cfg = self.config.get("training", {})
        lr = float(train_cfg.get("lr", 1e-4))
        weight_decay = float(train_cfg.get("weight_decay", 1e-4))
        epochs = int(train_cfg.get("epochs", 50))

        optimizer = AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
        scheduler = CosineAnnealingLR(optimizer, T_max=epochs)
        
        return optimizer, scheduler

    def training_step(
        self,
        model: nn.Module,
        batch: Any,
        criterion: nn.Module,
        batch_idx: int,
        **kwargs: Any
    ) -> dict[str, float]:
        """Run one training step."""
        images, targets = batch
        images = images.to(self.device)
        targets = targets.to(self.device)

        # Forward
        logits = model(images)

        # Compute loss
        # SmoothModulationLoss needs class_counts and epoch
        loss_kwargs = {}
        if "class_counts" in kwargs:
            loss_kwargs["class_counts"] = kwargs["class_counts"]
        if "epoch" in kwargs:
            loss_kwargs["epoch"] = kwargs["epoch"]
            
        loss = criterion(logits, targets, **loss_kwargs)

        # Metrics
        _, predicted = logits.max(1)
        acc = predicted.eq(targets).float().mean()

        return {"loss": loss, "accuracy": acc.item()}

    def validation_step(
        self,
        model: nn.Module,
        batch: Any,
        criterion: nn.Module,
        **kwargs: Any
    ) -> dict[str, float]:
        """Run one validation step."""
        images, targets = batch
        images = images.to(self.device)
        targets = targets.to(self.device)

        logits = model(images)
        loss = criterion(logits, targets)

        _, predicted = logits.max(1)
        acc = predicted.eq(targets).float().mean()

        return {"loss": loss.item(), "accuracy": acc.item()}
