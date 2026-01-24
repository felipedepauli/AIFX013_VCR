# Utils

## 📖 Overview
The **Utils** module provides shared helper functions for configuration management, manifest I/O, and path handling. It isolates repetitive logic used across scripts like `01_detect_crop.py` and `04_train_mlflow.py`.

## 🔑 Key Components

### `ManifestIO` (in `manifest_io.py`)
Handles reading and writing the JSONL manifest files, ensuring consistent encoding (UTF-8) and format.
- `read_manifest(path)`: Returns list of dicts.
- `write_manifest(records, path)`: Saves list of dicts to JSONL.

### `Config` (in `config.py`)
Utilities for loading and merging YAML configurations.
- `load_config(path)`: Loads standard YAML.

## 💻 Usage Examples

### Reading a Manifest
```python
from src.utils.manifest_io import read_manifest

records = read_manifest("data/prf_v1/manifests/manifest_raw.jsonl")
print(f"Loaded {len(records)} records")
```

### Loading Config
```python
from src.utils.config import load_config

cfg = load_config("config.yaml")
learning_rate = cfg["training"]["lr"]
```

## ⚙️ Configuration
This module handles configuration loading but does not have its own configuration entries.
