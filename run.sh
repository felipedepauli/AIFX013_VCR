#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <config.{yaml,yml,json}>"
  exit 1
fi

CONFIG_PATH="$1"
if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "Config file not found: $CONFIG_PATH"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
  PYTHON_BIN="${PYTHON_BIN:-python}"
fi

read_config_value() {
  local key="$1"
  "$PYTHON_BIN" - "$CONFIG_PATH" "$key" <<'PY'
import json
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
key = sys.argv[2]

suffix = config_path.suffix.lower()
if suffix == ".json":
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    import yaml
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

value = data
for part in key.split("."):
    if isinstance(value, dict) and part in value:
        value = value[part]
    else:
        value = ""
        break

if isinstance(value, bool):
    print("true" if value else "false")
elif value is None:
    print("")
else:
    print(value)
PY
}

EXPERIMENT="$(read_config_value "experiment")"
if [[ -z "$EXPERIMENT" ]]; then
  base_name="$(basename "$CONFIG_PATH")"
  EXPERIMENT="${base_name%.*}"
fi

RUNS_DIR="$(read_config_value "paths.runs_dir")"
RUNS_DIR="${RUNS_DIR:-runs}"

BACKBONE="$(read_config_value "model.backbone")"
BACKBONE="${BACKBONE:-resnet50}"

FUSION="$(read_config_value "model.fusion")"
FUSION="${FUSION:-msff}"

NUM_CLASSES="$(read_config_value "model.num_classes")"
NUM_CLASSES="${NUM_CLASSES:-10}"

SPLIT_FROM_DIRS="$(read_config_value "preprocess.split_from_dirs")"
GROUP_BY="$(read_config_value "preprocess.group_by")"
GROUP_BY="${GROUP_BY:-camera_id}"

RUN_DIR="$RUNS_DIR/$EXPERIMENT"
DATA_DIR="$RUN_DIR/data"
TRAIN_DIR="$RUN_DIR/train"
INFER_DIR="$RUN_DIR/infer"
EVAL_DIR="$RUN_DIR/eval"
MODEL_DIR="$RUN_DIR/model"
OPT_DIR="$RUN_DIR/optimization"

mkdir -p "$RUN_DIR" "$INFER_DIR" "$EVAL_DIR" "$MODEL_DIR"

RUN_OPTIMIZE="${RUN_OPTIMIZE:-1}"
HP_CONFIG="${HP_CONFIG:-hyperparameters.yaml}"
N_TRIALS="${N_TRIALS:-}"

run_step() {
  local title="$1"
  shift
  echo
  echo "============================================================"
  echo "$title"
  echo "============================================================"
  echo "Command: $*"
  "$@"
}

run_step "01 - Detect and Crop" \
  "$PYTHON_BIN" 01_detect_crop.py \
  --config "$CONFIG_PATH"

run_step "02 - Prepare Data" \
  "$PYTHON_BIN" 02_prepare_data.py \
  --config "$CONFIG_PATH" \
  --experiment "$EXPERIMENT"

PREPROCESS_ARGS=(
  "$PYTHON_BIN" 03_preprocess.py
  --config "$CONFIG_PATH"
  --manifest "$DATA_DIR/manifest.jsonl"
  --output-manifest "$DATA_DIR/manifest.jsonl"
  --output-dir "$DATA_DIR"
  --group-by "$GROUP_BY"
)

if [[ "$SPLIT_FROM_DIRS" == "true" ]]; then
  PREPROCESS_ARGS+=(--split-from-dirs)
fi

run_step "03 - Preprocess" "${PREPROCESS_ARGS[@]}"

MODEL_SUMMARY_CMD="\"$PYTHON_BIN\" 04_model.py --summary --backbone \"$BACKBONE\" --fusion \"$FUSION\" --num-classes \"$NUM_CLASSES\" | tee \"$MODEL_DIR/model_summary.txt\""
run_step "04 - Model Summary" \
  bash -lc \
  "$MODEL_SUMMARY_CMD"

if [[ "$RUN_OPTIMIZE" == "1" ]]; then
  OPT_CMD=(
    "$PYTHON_BIN" 05_optimize.py
    --config "$CONFIG_PATH"
    --experiment "$EXPERIMENT"
    --hp-config "$HP_CONFIG"
    --output-dir "$OPT_DIR"
  )
  if [[ -n "$N_TRIALS" ]]; then
    OPT_CMD+=(--n-trials "$N_TRIALS")
  fi
  run_step "05 - Optimize" "${OPT_CMD[@]}"
else
  echo
  echo "============================================================"
  echo "05 - Optimize (skipped)"
  echo "============================================================"
  echo "Set RUN_OPTIMIZE=1 to enable."
fi

run_step "06 - Train" \
  "$PYTHON_BIN" 06_train.py \
  --config "$CONFIG_PATH" \
  --experiment "$EXPERIMENT"

run_step "07 - Infer" \
  "$PYTHON_BIN" 07_infer.py \
  --checkpoint "$TRAIN_DIR/best.pt" \
  --manifest "$DATA_DIR/manifest.jsonl" \
  --split test \
  --class-names "$DATA_DIR/class_to_idx.json" \
  --output "$INFER_DIR/predictions.jsonl"

run_step "08 - Evaluate" \
  "$PYTHON_BIN" 08_eval.py \
  --checkpoint "$TRAIN_DIR/best.pt" \
  --manifest "$DATA_DIR/manifest.jsonl" \
  --split test \
  --class-names "$DATA_DIR/class_to_idx.json" \
  --class-counts "$DATA_DIR/class_counts.json" \
  --training-history "$TRAIN_DIR/artifacts/training_history.json" \
  --output-dir "$EVAL_DIR"

echo
echo "Pipeline complete."
echo "Experiment: $EXPERIMENT"
echo "Run dir:    $RUN_DIR"
