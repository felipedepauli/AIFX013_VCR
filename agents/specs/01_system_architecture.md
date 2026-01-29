# VCR System Architecture Specification

**Reference**: `agents/Projeto_Classificador.md`
**Role**: Single Source of Truth for System Architecture.

## 1. Core Architecture
The system MUST implement a Convolutional Neural Network (CNN) based classifier focused on Vehicle Color Recognition (VCR).

### 1.1 Backbone
- **Requirement**: The system must support interchangeable backbones.
- **Supported Models**:
  - `ResNet50` (Default, robustness priority)
  - `EfficientNet-B4` (Efficiency priority)
- **Implementation**: `src.backbones` factory pattern.

### 1.2 Feature Fusion
- **Requirement**: Must implement Multi-Scale Feature Fusion (MSFF) to capture both local texture (e.g., metallic paint reflections) and global shape/color context.
- **Mechanism**: Extraction of feature maps from multiple depths of the backbone, followed by fusion (concatenation/attention) before the classification head.
- **Implementation**: `src.fusion` factory pattern.

### 1.3 Classification Head
- **Requirement**: A final dense layer projecting fused features to $N$ class logits.
- **Classes**: Target $N=24$ distinct colors (extending from basic 8).

## 2. Training Strategy (Long-Tail Handling)
The architecture must inherently account for class imbalance (Long-Tail distribution).

### 2.1 Loss Functions
- **Primary**: Smooth Modulation Loss (or Cross-Entropy with modulation).
- **Alternative**: Focal Loss ($\gamma=2$).
- **Goal**: Dynamic re-weighting of loss to penalize errors in rare classes more heavily than frequent ones.

### 2.2 Data Sampling
- **Requirement**: Support for `WeightedRandomSampler` to balance batches during training.
- **Implementation**: `src.strategies` and `src.data`.

### 2.3 MLflow Integration
- **Requirement**: All training runs must be logged to MLflow.
- **Metrics**: Loss (Train/Val), Accuracy (Train/Val), LR.
- **Artifacts**: `best.pt`, `last.pt`.

## 3. Directory Structure Standards
Agents modifying the system MUST adhere to this structure:
- `data/`: Dataset storage (versioned).
- `src/`: Source code (modular).
- `runs/`: Experiment outputs.
- `scripts/` or Root `0x_*.py`: Executable pipeline steps.
