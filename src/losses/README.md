# Losses

## 📖 Overview
The **Losses** module implements specialized loss functions to handle the **long-tail distribution** problem in vehicle color recognition, where some colors (White, Silver) are much more frequent than others (Yellow, Blue).

## 🏗️ Architecture / Theory

### Smooth Modulation
A curriculum learning approach that dynamically adjusts the loss weight for each class based on training progress.

- **Phase 1 (Early)**: Balanced weights. The model learns general features from head classes.
- **Phase 2 (Late)**: Tail-heavy weights. The model focuses on learning rare classes without forgetting the frequent ones.

Equation:
```
weight_c = (1 / n_c)^tau * modulation(epoch)
```

### Focal Loss
Penalizes hard-to-classify examples more than easy ones, implicitly helping with class imbalance and ambiguous samples.

## 🔑 Key Components

### `SmoothModulationLoss`
Recommended for VCR.
- **Parameters**:
    - `max_epoch`: Total training epochs (for scheduling).
    - `tau`: Modulation strength (default: 1.0).

### `FocalLoss`
Standard implementation for hard example mining.
- **Parameters**:
    - `gamma`: Focusing parameter (default: 2.0).
    - `alpha`: Class balance factor.

## 💻 Usage Examples

### Using Factory
```python
from src.core import LossFactory

# Create Smooth Modulation Loss
loss_fn = LossFactory.create("smooth_modulation", {"max_epoch": 50, "tau": 1.0})

# Forward pass (needs extra kwargs)
loss = loss_fn(logits, targets, class_counts=counts, epoch=current_epoch)
```

### Direct Instantiation
```python
from src.losses import FocalLoss

loss_fn = FocalLoss(gamma=2.0)
loss = loss_fn(logits, targets)
```

## ⚙️ Configuration
In `config.yaml`:

```yaml
train:
  loss: "smooth_modulation"
```

In `hyperparameters.yaml`:
```yaml
loss:
  type: "categorical"
  choices: ["smooth_modulation", "focal"]
```
