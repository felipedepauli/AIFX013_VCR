# VCR Project Requirements & Rules

**Reference**: `agents/Projeto_Classificador.md`

## 1. Business Requirements
- **Goal**: Identify vehicle color from urban surveillance images.
- **Granularity**: 24 distinct classes (expanding from basic 8).
- **Robustness**: Must optimize for varying lighting conditions (day, night, shadow, reflections).

## 2. Technical Constraints
- **Framework**: PyTorch.
- **Tracking**: MLflow.
- **Config**: `config.yaml` based.
- **Reproducibility**: Experiments must be reproducible via specific manifests and frozen seeds (handled by `02_prepare_data.py`).

## 3. Agent Rules
Agents working on this repository MUST follow these rules:

1.  **Do Not Break the Pipeline**: The steps `01` -> `07` are sequential. Do not modify the I/O interface of these scripts without updating the entire chain.
2.  **Config Driven**: Do not hardcode hyperparameters in Python files. Use `config.yaml` or `hyperparameters.yaml`.
3.  **Modular Design**: Put new model logic in `src/`, not in the root scripts.
    - New Backbones -> `src/backbones`
    - New Losses -> `src/losses`
    - New Fusion -> `src/fusion`
4.  **Documentation**: If you change the architecture, update `PIPELINE_VCR.md`.
5.  **Validation**: Before marking a task complete, run `07_eval.py` to ensure metrics are generated.

## 4. Definitions
- **Long-Tail**: Distribution where a few classes are very frequent, and many are rare.
- **Head Classes**: The frequent classes.
- **Tail Classes**: The rare classes.
- **MSFF**: Multi-Scale Feature Fusion.
