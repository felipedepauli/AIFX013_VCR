# VCR - Vehicle Color Recognition

A modular Deep Learning pipeline for vehicle color classification, designed to handle **long-tail distributions** (imbalanced classes) using multi-scale feature fusion and a custom lightweight backbone (ColorNet-V1).

## Quick Start

```bash
# 1. Setup Environment
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# 2. Detect & Crop (reads all sources from config.yaml automatically)
python 01_detect_crop.py

# 3. Prepare Data (reads experiment name + settings from config.yaml)
#    Normalizes Portuguese labels, keeps directory splits, encodes labels
python 02_prepare_data.py

# 4. Preprocess (validate, filter, generate class mappings)
python 03_preprocess.py --manifest data/manifests/manifest_raw.jsonl --split-from-dirs --skip-image-check

# 5. Train
python 06_train.py --experiment colornet_multisource

# 6. Inference on test split
python 07_infer.py \
  --checkpoint runs/colornet_multisource/train/best.pt \
  --manifest runs/colornet_multisource/data/manifest.jsonl \
  --class-names runs/colornet_multisource/data/class_to_idx.json \
  --split test --image-size 256 \
  --output runs/colornet_multisource/predictions.jsonl

# 7. Evaluate
python 08_eval.py \
  --checkpoint runs/colornet_multisource/train/best.pt \
  --manifest runs/colornet_multisource/data/manifest.jsonl \
  --class-names runs/colornet_multisource/data/class_to_idx.json \
  --class-counts runs/colornet_multisource/data/class_counts.json \
  --split test \
  --output-dir runs/colornet_multisource/eval

# 8. View Results via MLflow
mlflow ui
```

## Pipeline Overview

```mermaid
graph LR
    Sources[Multi-Source Images] --> Detect[01_detect_crop.py]
    Detect --> Manifest[manifest_raw.jsonl + crops]
    Manifest --> Prep[02_prepare_data.py]
    Prep --> ExpData[runs/EXP/data/manifest.jsonl]
    ExpData --> Preprocess[03_preprocess.py]
    Preprocess --> Ready[manifest_ready.jsonl]
    Ready --> Train[06_train.py]
    Train --> Model[best.pt]
    Model --> Infer[07_infer.py]
    Infer --> Preds[predictions.jsonl]
    Preds --> Eval[08_eval.py]
    Eval --> Report[Metrics + Plots]
```

## System Architecture

- **Backbone**: ColorNet-V1 (1.5M params) — custom lightweight MBConv backbone with Squeeze-and-Excitation, optimized for vehicle color recognition. Also supports ResNet50 and EfficientNet.
- **Fusion**: MSFF (Multi-Scale Feature Fusion) — combines c2..c5 feature maps using 1x1, 3x3, 5x5 convolutions with attention.
- **Loss**: Smooth Modulation Loss — dynamically re-weights loss to focus on rare classes (long-tail) as training progresses.
- **Optimizer**: AdamW with cosine annealing LR scheduler.

## Module Documentation

| Module | Description | Documentation |
|--------|-------------|---------------|
| **[Backbones](src/backbones/)** | CNN Feature Extractors (ColorNet-V1, ResNet, EfficientNet) | [README](src/backbones/README.md) |
| **[Fusion](src/fusion/)** | Multi-Scale Feature Fusion | [README](src/fusion/README.md) |
| **[Losses](src/losses/)** | Long-tail Loss Functions | [README](src/losses/README.md) |
| **[Data](src/data/)** | Dataset & Transforms | [README](src/data/README.md) |
| **[Detectors](src/detectors/)** | Vehicle Detection (YOLO, Manual) | [README](src/detectors/README.md) |
| **[Strategies](src/strategies/)** | Training Recipes & Loops | [README](src/strategies/README.md) |
| **[Core](src/core/)** | Factories & Base Classes | [README](src/core/README.md) |
| **[Utils](src/utils/)** | Config & IO Helpers | [README](src/utils/README.md) |

## Directory Structure

```
AIFX013_VCR/
├── config.yaml              # Main pipeline configuration
├── hyperparameters.yaml     # Optuna hyperparameter search space
├── 01_detect_crop.py        # Step 1: Detection & cropping
├── 02_prepare_data.py       # Step 2: Experiment data prep
├── 03_preprocess.py         # Step 3: Preprocessing & splits
├── 04_model.py              # Model definition (VCRModel)
├── 05_optimize.py           # Optuna hyperparameter optimization
├── 06_train.py              # Training with MLflow logging
├── 07_infer.py              # Inference (single image, batch, manifest)
├── 08_eval.py               # Evaluation with metrics & plots
├── src/                     # Source code modules
├── scripts/                 # Helper scripts
├── data/
│   ├── crops/               # Cropped vehicle images
│   └── manifests/           # Global manifests
└── runs/
    └── colornet_multisource/  # Experiment run
        ├── data/            # manifest.jsonl, class_to_idx.json, class_counts.json
        ├── train/           # best.pt, last.pt, artifacts/
        └── eval/            # Confusion matrices, ROC curves, per-class metrics
```

## Step-by-Step Guide

### Step 1: Detection & Cropping

Reads all dataset sources from `config.yaml` → `paths.sources`, detects vehicles, writes crops, and produces a single `data/manifests/manifest_raw.jsonl` with all records.

**Multi-source mode** (recommended — everything from config):
```bash
python 01_detect_crop.py
```

Each source entry in `config.yaml` must have `train/`, `valid/`, `test/` subdirectories with `.jpg` + `.json` pairs:
```yaml
paths:
  sources:
    - name: "3mpx_v1"
      path: "/data/pdi_datasets/data/datasets/3mpx_v1"
    - name: "bmc_v3"
      path: "/data/pdi_datasets/data/datasets/bmc/v3"
    # ...
```

**Single-source mode** (override for a specific directory):
```bash
python 01_detect_crop.py --detector manual --dataset my_data --version v1 --source-dir /path/to/images/
```

### Step 2: Data Preparation

Reads experiment name and preprocessing settings from `config.yaml`. Loads the global manifest, **normalizes Portuguese labels to English** (e.g. `Bege`→`brown`, `Dourada`→`yellow`, `Roxa`→`purple`, `Outros ou Desconhecido`→`unknown`), keeps existing train/val/test splits from directory structure, builds class mappings, and saves everything to `runs/{experiment}/data/`.

**Config-driven mode** (recommended — zero CLI args):
```bash
python 02_prepare_data.py
```

Requires in `config.yaml`:
```yaml
experiment: "colornet_multisource"

preprocess:
  split_from_dirs: true   # Keep splits from directory structure
  seed: 42
```

**CLI override mode** (for single-dataset experiments):
```bash
python 02_prepare_data.py --dataset prf_v1 --experiment my_experiment --seed 123
```

Output (example):
```
Raw labels found (16): ['Bege', 'Dourada', 'Outros ou Desconhecido', 'Roxa', 'black', ...]
Label normalization applied:
  'Bege' → 'brown'
  'Dourada' → 'yellow'
  'Outros ou Desconhecido' → 'unknown'
  'Roxa' → 'purple'
Final classes (12): ['black', 'blue', 'brown', 'gray', 'green', 'orange', 'purple', 'red', 'silver', 'unknown', 'white', 'yellow']
  white: 11458
  silver: 6334
  black: 5574
  ...
```

### Step 3: Preprocessing

Validate records, filter bad data, and generate class mappings:
```bash
python 03_preprocess.py \
  --manifest data/manifests/manifest_raw.jsonl \
  --split-from-dirs \
  --skip-image-check
```

### Step 4: Training

Train with MLflow logging, early stopping, and auto-resume:
```bash
python 06_train.py --experiment colornet_multisource
```

Key features:
- **Early Stopping**: Configurable via `training.early_stopping_patience` in config.yaml
- **Auto-Resume**: If interrupted, re-run the same command to resume from `last.pt`
- **MLflow**: All metrics, artifacts, and checkpoints are logged

### Step 5: Hyperparameter Optimization (Optional)

Search for optimal hyperparameters using Optuna with TPE sampler:
```bash
python 05_optimize.py --hp-config hyperparameters.yaml --n-trials 150
```

View Optuna dashboard:
```bash
optuna-dashboard sqlite:///runs/experiments.db
```

### Step 6: Inference

**On test split** (batch):
```bash
python 07_infer.py \
  --checkpoint runs/colornet_multisource/train/best.pt \
  --manifest runs/colornet_multisource/data/manifest.jsonl \
  --class-names runs/colornet_multisource/data/class_to_idx.json \
  --split test --image-size 256 \
  --output runs/colornet_multisource/predictions.jsonl
```

**Single image**:
```bash
python 07_infer.py \
  --checkpoint runs/colornet_multisource/train/best.pt \
  --class-names runs/colornet_multisource/data/class_to_idx.json \
  --image /path/to/vehicle.jpg --image-size 256
```

**Directory of images**:
```bash
python 07_infer.py \
  --checkpoint runs/colornet_multisource/train/best.pt \
  --class-names runs/colornet_multisource/data/class_to_idx.json \
  --image-dir /path/to/images/ --image-size 256 \
  --output predictions.jsonl
```

### Step 7: Evaluation

**From predictions file**:
```bash
python 08_eval.py \
  --predictions runs/colornet_multisource/predictions.jsonl \
  --class-names runs/colornet_multisource/data/class_to_idx.json \
  --class-counts runs/colornet_multisource/data/class_counts.json \
  --output-dir runs/colornet_multisource/eval
```

**Directly from checkpoint** (runs inference + evaluation):
```bash
python 08_eval.py \
  --checkpoint runs/colornet_multisource/train/best.pt \
  --manifest runs/colornet_multisource/data/manifest.jsonl \
  --class-names runs/colornet_multisource/data/class_to_idx.json \
  --class-counts runs/colornet_multisource/data/class_counts.json \
  --split test \
  --output-dir runs/colornet_multisource/eval
```

Generates: confusion matrix, normalized confusion matrix, ROC curves, precision-recall curves, per-class metrics, and classification report.

### Step 8: View Results

**MLflow UI**:
```bash
mlflow ui
# Open http://localhost:5000
```

**Optuna Dashboard** (if optimization was run):
```bash
optuna-dashboard sqlite:///runs/experiments.db
```

## Configuration

All pipeline settings are in `config.yaml`. Key sections:

| Section | Key Parameters |
|---------|---------------|
| `paths.sources` | List of multi-source image directories |
| `detector.bbox_format` | Bounding box format: `"xywh"` or `"xyxy"` |
| `model.backbone` | `"colornet_v1"`, `"resnet50"`, `"efficientnet_b0"` |
| `model.num_classes` | Number of color classes |
| `training.epochs` | Max training epochs |
| `training.early_stopping_patience` | Epochs without improvement before stopping |
| `training.lr` | Learning rate |
| `training.input_size` | Image resize dimension |
| `loss.name` | `"smooth_modulation"` or `"focal"` |
