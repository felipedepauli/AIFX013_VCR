# VCR - Vehicle Color Recognition

A modular Deep Learning pipeline for vehicle color classification, designed to handle **long-tail distributions** (imbalanced classes) using multi-scale feature fusion.

## 🚀 Quick Start

```bash
# 1. Setup Environment
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# 2. Detect & Crop (Using Manual Annotations for Color)
# Crucial: Use --detector manual to read existing 'vehicle_color' labels from JSONs.
# YOLO only detects objects, not colors.
python 01_detect_crop.py \
  --detector manual \
  --dataset bmc --version v2 \
  --source-dir revised_images/train/

# 3. Prepare Data (Experiment-Specific)
# Creates a training manifest and saves config for reproducibility
python 02_prepare_data.py --dataset bmc_v2:v2 --experiment baseline_v2

# 4. Train Model
# Uses the manifest and config from the experiment folder
# Features: Early Stopping (patience=10), Auto-Resume (last.pt)
python 04_train_mlflow.py --experiment runs/baseline_v2

# 5. Optimize Hyperparameters (Optional)
# searches for best LR, Backbone, etc. using Optuna
python 05_optimize.py --experiment "Otimizacao_V1"

# 6. View Results via MLFlow
mlflow ui
```

## 📐 Pipeline Overview

The system follows a structured pipeline from raw data to evaluation. Each step is modular and reproducible.

```mermaid
graph LR
    Raw[Raw Images] --> Detect[01_detect_crop.py]
    Detect --> Crops[Vehicle Crops]
    Crops --> CVAT[Manual Annotation]
    CVAT --> RawManifest[manifest_raw.jsonl]
    RawManifest --> Prep[02_prepare_data.py]
    Prep --> ExpData[Experiment Data]
    ExpData --> Train[04_train_mlflow.py]
    Train --> Model[best.pt]
    Model --> Eval[06_eval.py]
```

## 🏗️ System Architecture

The model architecture is designed to capture both global shape and fine details (like paint texture) to distinguish colors accurately.

- **Backbone**: ResNet50 (default) or EfficientNet. Extracts feature maps.
- **Fusion**: MSFF (Multi-Scale Feature Fusion). Combines features from different layers (1x1, 3x3, 5x5 convolution) using attention.
- **Loss**: Smooth Modulation Loss. Dynamically re-weights loss to focus on rare classes (long-tail) as training progresses.

## 📚 Module Documentation

| Module | Description | Documentation |
|--------|-------------|---------------|
| **[Backbones](src/backbones/)** | CNN Feature Extractors | [README](src/backbones/README.md) |
| **[Fusion](src/fusion/)** | Multi-Scale Fusion | [README](src/fusion/README.md) |
| **[Losses](src/losses/)** | Long-tail Loss Functions | [README](src/losses/README.md) |
| **[Data](src/data/)** | Dataset & Transforms | [README](src/data/README.md) |
| **[Optimization](src/optimization/)** | Hyperparameter Search | [README](src/optimization/README.md) |
| **[Detectors](src/detectors/)** | Vehicle Detection | [README](src/detectors/README.md) |
| **[Strategies](src/strategies/)** | Training Recipes & Loops | [README](src/strategies/README.md) |
| **[Core](src/core/)** | Factories & Base Classes | [README](src/core/README.md) |
| **[Utils](src/utils/)** | Config & IO Helpers | [README](src/utils/README.md) |

## 📂 Directory Structure

```
AIFX013-VCR/
├── data/
│   └── prf_v1/              # Versioned Dataset
│       ├── raw/             # Original Images
│       ├── crops/           # Vehicle Crops
│       └── manifests/       # Global Manifests
├── runs/
│   └── exp_001/             # Experiment Run
│       ├── data/            # Experiment Manifest & Config
│       ├── train/           # Checkpoints
│       └── eval/            # Evaluation Plots
├── src/                     # Source Code
├── scripts/                 # Helper Scripts
├── 01_detect_crop.py        # Step 1: Detection
├── 02_prepare_data.py       # Step 2: Experiment Prep
├── 03_model.py              # Step 3: Model Def
├── 04_train_mlflow.py       # Step 4: Training
├── 05_optimize.py           # Step 5: Hyperparam Search
├── 05_infer.py              # Step 6: Inference
└── 06_eval.py               # Step 7: Evaluation
```

## 🛠️ Step-by-Step Execution

### Step 1: Detection & Cropping
Detect vehicles in raw images. For color recognition, we require **manual annotations** or a specialized detector, as standard YOLO only detects object presence.

**Option A: Import & Detect (Correct Workflow)**
Imports images and their corresponding JSON labels (which contain color info).
```bash
python 01_detect_crop.py \
  --detector manual \
  --dataset bmc_v2 --version v2 \
  --source-dir revised_images/train/
```

### Step 2: Data Preparation
Split data into Train/Val/Test and freeze the configuration (seed, transforms) for a specific experiment.
```bash
python 02_prepare_data.py --dataset bmc_v2:v2 --experiment baseline_v2
```

### Step 3: Training with MLFlow
Train the model using the prepared experiment data. Includes **Early Stopping** and **Auto-Resume**.
```bash
python 04_train_mlflow.py --experiment runs/baseline_v2
```
*Tip: If the training is interrupted, run the same command again to resume from the last epoch.*

### Step 4: Optimization (Optional)
Search for the best hyperparameters using Optuna.
```bash
python 05_optimize.py --experiment "Otimizacao_V1"
```

### Step 7: Inference
Run the model on new images.
```bash
python 05_infer.py --checkpoint runs/baseline_v1/train/best.pt --image test_car.jpg
```

### Step 8: Evaluation
Analyze performance on Head (frequent) vs Tail (rare) classes.
```bash
python 06_eval.py --checkpoint runs/baseline_v1/train/best.pt \
                  --manifest runs/baseline_v1/data/manifest.jsonl
```
