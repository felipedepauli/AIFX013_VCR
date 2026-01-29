# VCR Validation Protocols

**Reference**: `agents/Projeto_Classificador.md` (Section 5 & 6)
**Purpose**: Define how to validate the correctness and performance of the VCR model.

## 1. Metrics & Evaluation
ALL experiments MUST be evaluated using `07_eval.py` and report the following metrics.

### 1.1 Quantitative Metrics
- **Accuracy**: Global accuracy.
- **Micro/Macro F1-Score**: To handle class imbalance.
- **Weighted Precision/Recall**: For overall performance summary.
- **Per-Class Metrics**: Precision, Recall, and F1 for EACH of the 24 classes.

### 1.2 Head vs. Tail Analysis
Given the Long-Tail nature of vehicle colors, validation MUST separate performance:
- **Head Classes**: Frequent colors (e.g., White, Black, Silver, Gray).
- **Tail Classes**: Rare colors (e.g., Yellow, Green, Pink, Two-tone).
- **Success Criterion**: The model is successful ONLY IF it improves Tail Class performance without significant degradation of Head Classes (compared to baseline).

## 2. Visual Validation
### 2.1 Confusion Matrix
- **Requirement**: A Confusion Matrix (normalized and raw) must be generated for every evaluation run.
- **Analysis**: Check for common confusions (e.g., White vs. Silver, Black vs. Dark Blue).

### 2.2 Grad-CAM (Qualitative)
- **Requirement**: Use Grad-CAM to visualize model attention.
- **Check**: Ensure the model focuses on the vehicle body (paint), ignoring background, asphalt, or windows.

## 3. Validation Workflow
1.  **Run Inference**: Generate predictions on the **Test Set**.
    ```bash
    python 07_eval.py --checkpoint runs/EXP_NAME/train/best.pt --manifest data/manifests/manifest_test.jsonl
    ```
2.  **Review Metrics**: Check `metrics.json` in the output folder.
3.  **Check Artifacts**: Inspect `confusion_matrix.png`.
4.  **Logging**: Ensure all metrics are logged to MLflow for comparison.

## 4. Acceptance Criteria
- [ ] Code runs without errors.
- [ ] MLflow logging is active.
- [ ] `07_eval.py` produces `metrics.json` and `confusion_matrix.png`.
- [ ] "Tail" classes show non-zero recall (indicating learning occurred).
