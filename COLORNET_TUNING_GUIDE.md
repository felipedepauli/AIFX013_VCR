# 🎯 ColorNet-V1 Fine-Tuning Guide

Since you've identified **ColorNet-V1** as your best architecture, this guide explains the expanded hyperparameter search space for deep fine-tuning.

## 📊 New Hyperparameters Added

### 🔥 Loss Function Parameters

#### Smooth Modulation Loss
- **`tau`** (float: 0.3 - 0.8)
  - Controls reweighting strength for rare classes
  - Higher = more weight to tail classes
  - Formula: `w_c = (1 / n_c)^tau * m(epoch)`
  - **Recommendation**: Start around 0.5, increase if tail classes underperform

- **`modulation_type`** (categorical: linear, cosine, step)
  - How class reweighting changes during training
  - `linear`: Gradual linear increase
  - `cosine`: Smooth S-curve (recommended)
  - `step`: Sudden change at 50% training
  - **Recommendation**: `cosine` usually works best

#### Focal Loss
- **`focal_gamma`** (float: 1.0 - 3.0)
  - Focusing parameter for hard examples
  - Higher = more focus on misclassified samples
  - Formula: `FL = -α(1-p_t)^γ * log(p_t)`
  - **Recommendation**: 2.0 is standard, try 2.5-3.0 for very imbalanced data

- **`focal_alpha`** (float: 0.1 - 0.5)
  - Balancing factor between classes
  - Lower = less aggressive reweighting
  - **Recommendation**: 0.25 is default, tune if one class dominates

### 🎨 Model Regularization
- **`dropout`** (float: 0.1 - 0.5)
  - Dropout rate in classification head
  - Higher = more regularization (prevents overfitting)
  - Lower = more capacity (better for small models)
  - **Recommendation**: 0.2-0.3 for ColorNet's size

### 📐 Data & Training
- **`image_size`** (categorical: 224, 256, 288)
  - Added 288 back for ColorNet (it's small enough to handle it)
  - Larger = more detail, slower training
  - **Recommendation**: 224 for speed, 256 for balance, 288 for max accuracy

- **`batch_size`** (categorical: 16, 32, 48, 64)
  - Added 16 and 48 for more exploration
  - Smaller = more gradient updates, less stable
  - Larger = more stable, needs more memory
  - **Recommendation**: 32-48 works well for most cases

### ⚙️ Optimizer (Expanded Range)
- **`lr`** (float: 5e-5 to 5e-3, log scale)
  - Expanded upper range for ColorNet
  - Small models can sometimes handle higher LR
  - **Recommendation**: Let Optuna explore, watch for 1e-3 to 3e-3

- **`weight_decay`** (float: 1e-6 to 5e-3, log scale)
  - Expanded for stronger regularization options
  - **Recommendation**: 1e-4 to 1e-3 range usually optimal

## 🚀 Running the Optimization

```bash
# Run 150 trials with new search space
python 05_optimize.py \
    --hp-config hyperparameters.yaml \
    --n-trials 150 \
    --experiment colornet_finetune
```

## 📈 What to Expect

With **150 trials** and **10+ hyperparameters**, you're exploring a much larger space:

### Previous Search Space
- Backbones: 1 (colornet_v1)
- Other params: 5
- **Total combinations**: ~thousands

### New Search Space
- Backbones: 1 (colornet_v1)
- Fusion: 3 choices
- Loss: 2 choices × loss-specific params
- Regularization: continuous (dropout)
- Training: expanded ranges
- **Total combinations**: ~millions

### Timeline Estimate
- Per trial: 15-30 minutes (depending on early stopping)
- 150 trials: 40-75 hours (~2-3 days)
- **Tip**: Use pruning to kill bad trials early!

## 🎯 Expected Improvements

### Head Classes (Frequent)
- **Current**: Already performing well
- **Target**: Maintain 90-95% accuracy
- **Key params**: dropout, lr

### Tail Classes (Rare)
- **Current**: Likely 40-70% accuracy
- **Target**: Boost to 60-80%
- **Key params**: tau, focal_gamma, modulation_type

### Overall Accuracy
- **Expected gain**: +2-5% validation accuracy
- **Realistic best case**: 85-90% on validation set

## 📊 Monitoring Strategy

### During Optimization

1. **Check MLflow UI regularly**:
   ```bash
   mlflow ui
   ```
   - Look for trials with val_acc > current best
   - Check if certain param combinations emerge

2. **Watch for patterns**:
   - Does focal or smooth_modulation perform better?
   - Is higher dropout helping?
   - Does 256 or 288 image size help?

3. **Identify winners early**:
   ```bash
   # After 50 trials, check top performers
   python analyze_study.py
   ```

### After Optimization

1. **Analyze results**:
   ```bash
   python analyze_study.py --save-configs
   ```

2. **Check parameter importance**:
   ```bash
   # Launch Optuna dashboard
   optuna-dashboard sqlite:///runs/experiments.db
   ```
   - Go to "Parameter Importances" tab
   - See which hyperparameters matter most

3. **Compare top 5 trials**:
   - Load in MLflow UI
   - Look for common patterns
   - Check learning curves

## 🔬 Advanced: Two-Stage Tuning (Optional)

If you want even better results:

### Stage 1: Broad Search (Done)
- 150 trials with wide ranges
- Identifies promising regions

### Stage 2: Narrow Search
- Take top 3 param combinations
- Narrow ranges around them
- Run 50 more trials per region

Example for Stage 2:
```yaml
hyperparameters:
  # Lock best choices from Stage 1
  fusion:
    type: "categorical"
    choices: ["msff"]  # If it won in Stage 1
  
  loss_fn:
    type: "categorical"
    choices: ["smooth_modulation"]  # If it won
  
  # Narrow range around best value
  tau:
    type: "float"
    low: 0.45  # Best was 0.5
    high: 0.55
  
  lr:
    type: "float"
    low: 8e-4  # Best was 1e-3
    high: 1.5e-3
    log: true
```

## 🎓 Parameter Interaction Tips

### Good Combinations
1. **High tau + Smooth Modulation + Weighted Sampler**
   - Triple-combo for tail classes
   - Best for severely imbalanced data

2. **Higher dropout + Lower weight_decay**
   - Prevents overfitting without killing capacity

3. **Larger image_size + Lower batch_size**
   - More detail without OOM errors

4. **Focal Loss + Lower learning rate**
   - Focal loss has sharper gradients

### Avoid These
1. **High tau + Focal Loss + High gamma**
   - Too much tail class boosting = head classes suffer

2. **High dropout + High weight_decay + Low lr**
   - Over-regularization = underfitting

3. **Batch size 16 + Image size 288**
   - Unstable batch norm + slow training

## 📝 Quick Reference: Default Values

| Parameter | Default | Tuning Range | Best Practice |
|-----------|---------|--------------|---------------|
| tau | 0.5 | 0.3 - 0.8 | Start mid, adjust for tail |
| modulation_type | cosine | linear/cosine/step | Cosine usually wins |
| focal_gamma | 2.0 | 1.0 - 3.0 | 2.0-2.5 for most cases |
| focal_alpha | 0.25 | 0.1 - 0.5 | Lower for better balance |
| dropout | 0.2 | 0.1 - 0.5 | 0.2-0.3 for ColorNet |
| lr | 1e-3 | 5e-5 - 5e-3 | Let Optuna explore |
| weight_decay | 1e-4 | 1e-6 - 5e-3 | 1e-4 to 1e-3 sweet spot |
| batch_size | 32 | 16/32/48/64 | 32-48 recommended |
| image_size | 224 | 224/256/288 | 256 for balance |

## 🚨 Troubleshooting

**Issue**: All trials getting similar scores
- **Fix**: Check if pruning is too aggressive
- **Fix**: Ensure loss parameters are actually being used (check logs)

**Issue**: Tail classes still performing poorly
- **Fix**: Increase tau range (try up to 1.0)
- **Fix**: Lock to smooth_modulation with cosine
- **Fix**: Ensure weighted sampler is enabled

**Issue**: Overfitting (train >> val accuracy)
- **Fix**: Increase dropout to 0.3-0.4
- **Fix**: Increase weight_decay
- **Fix**: Use more aggressive data augmentation

**Issue**: Training too slow
- **Fix**: Lock image_size to 224
- **Fix**: Increase n_startup_trials for pruner
- **Fix**: Use batch_size 48-64

## 🎉 Success Criteria

You'll know optimization succeeded when:
- ✅ Validation accuracy improved by 2-5%
- ✅ Tail class F1 scores increased
- ✅ Best config is consistent (similar params in top trials)
- ✅ Parameter importance plot shows clear winners
- ✅ Learning curves are smooth (no severe overfitting)

---

**Good luck with the optimization!** 🚀

See [VISUALIZATION_GUIDE.md](VISUALIZATION_GUIDE.md) for how to analyze results.
