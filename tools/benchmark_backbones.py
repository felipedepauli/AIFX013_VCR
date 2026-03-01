
import argparse
import sys
import time
# import humanize
import torch
import yaml
from pathlib import Path
import pandas as pd
from contextlib import redirect_stdout
import os
import io

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

from src.utils.config import load_config

# Import modules with numeric prefixes
import importlib.util
def import_from_path(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

train_module = import_from_path("06_train.py", "step06_train")
Step06TrainMlflow = train_module.Step06TrainMlflow

model_module = import_from_path("04_model.py", "step04_model")
VCRModel = model_module.VCRModel

# Benchmark Configuration
EPOCHS = 3
RUNS_DIR = Path("runs/benchmark")
BACKBONES = [
    # Lightweight / Efficient
    "colornet_v1", 
    "mobilenetv4_small",
    "fastvit_t8",
    "efficientnet_b0",
    "convnext_tiny",
    # Heavyweight / Standard
    "resnet18",
    "resnet50",
    # "efficientnet_b4" # Might be too slow/heavy, optional
]

# Fusion mapping: Use global_concat for ColorNet, MSFF for everything else (Standard Baseline)
FUSION_MAP = {
    "colornet_v1": "global_concat",
}
DEFAULT_FUSION = "msff"

def get_model_size(model_path):
    """Get model size in bytes."""
    return os.path.getsize(model_path)

def count_parameters(model):
    """Count trainable parameters."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def benchmark_inference(model, device, iterations=100, warmup=10, image_size=224):
    """Measure inference time (avg of iter 10-20 as requested, or full avg)."""
    model.eval()
    input_tensor = torch.randn(1, 3, image_size, image_size).to(device)
    
    # Warmup
    with torch.no_grad():
        for _ in range(warmup):
            _ = model(input_tensor)
            
    # Measure
    times = []
    with torch.no_grad():
        for i in range(iterations):
            start = time.perf_counter()
            _ = model(input_tensor)
            torch.cuda.synchronize() # Wait for CUDA
            end = time.perf_counter()
            times.append((end - start) * 1000) # ms
            
    # Requested: Avg of 10th to 20th inference (indices 10 to 19 if 0-indexed)
    # But user said "decima a vigésima" (10th to 20th). 
    # Let's ensure we have enough samples.
    if len(times) >= 20:
        segment = times[9:20] # 10th (index 9) to 20th (index 19) inclusive-ish
        avg_time = sum(segment) / len(segment)
    else:
        avg_time = sum(times) / len(times)
        
    return avg_time

def main():
    results = []
    
    # Load base config
    base_config = load_config("config.yaml")

    for backbone in BACKBONES:
        print(f"\n========================================")
        print(f"Benchmarking: {backbone}")
        print(f"========================================")
        
        run_name = f"bench_{backbone}"
        exp_dir = RUNS_DIR / run_name
        exp_dir.mkdir(parents=True, exist_ok=True) # Create dir for validate()
        
        # Determine fusion
        fusion = FUSION_MAP.get(backbone, DEFAULT_FUSION)
        
        # Prepare Config Override
        config = base_config.copy()
        config["model"]["backbone"] = backbone
        config["model"]["fusion"] = fusion
        config["model"]["pretrained"] = False # Scratch training for fair comparison usually? 
        # User config used scratch for ColorNet. For fairness, maybe scratch for all?
        # Or Pretrained for standard ones? 
        # User asked "rodar um treinamento...". Usually one compares scratch vs scratch or pretrained vs pretrained.
        # Given ColorNet is scratch, let's try to be consistent if possible, BUT standard backbones usually avail pretrained.
        # I will stick to what's in config.yaml, but override pretrained=False for fairness if user wants "training".
        # If we use pretrained=True for ResNet, it converges instantly. ColorNet is scratch.
        # Let's verify config.yaml state. User set pretrained=False in step 240.
        # So it will be scratch for all. Good.
        
        config["training"]["epochs"] = EPOCHS
        # Force num_classes used in creation to avoids mismatch even if config says 24
        # logic is handled in Strategy
        
        # 1. TRAIN
        # Create Step
        step = Step06TrainMlflow(config=config)
        step.experiment_dir = exp_dir
        step.device = "auto"
        # Mock manifest path to existing ready one
        step.manifest_path = Path("runs/vamo_que_vamo/data/manifest.jsonl") # Reuse manifest
        
        # Capture output to avoid cluttering benchmark logs too much, or keep it?
        # User might want to see progress. I'll keep it.
        try:
            step.run()
        except Exception as e:
            print(f"Training failed for {backbone}: {e}")
            continue
            
        # 2. EVALUATE (Metrics + Size + Time)
        best_model_path = exp_dir / "train" / "best.pt"
        if not best_model_path.exists():
            print(f"Checkpoint not found for {backbone}")
            continue
            
        # Load Model
        checkpoint = torch.load(best_model_path, map_location="cuda")
        
        # Instantiate model directly to measure
        # Need to know correct arguments strategy uses. 
        # VCRStrategy does: VCRModel(backbone_name=..., fusion_name=...)
        # We can just load the state dict into a fresh model
        model = VCRModel(
            num_classes=24, # Assume 24 based on config
            backbone_name=backbone,
            fusion_name=fusion
        )
        model.to("cuda")
        
        # Params
        params = count_parameters(model)
        
        # File Size
        size_bytes = get_model_size(best_model_path)
        
        # Inference Time
        print("Running inference benchmark...")
        avg_time = benchmark_inference(model, "cuda", iterations=50) # Run 50 to cover 10-20
        
        # Get Best Val Acc from training result (stored in checkpoint)
        val_acc = checkpoint.get("best_val_acc", 0.0)
        
        results.append({
            "Backbone": backbone,
            "Fusion": fusion,
            "Params (M)": params / 1e6,
            "Size (MB)": size_bytes / (1024 * 1024),
            "Time (ms)": avg_time,
            "Val Acc (%)": val_acc * 100
        })
        
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Format
    pd.options.display.float_format = '{:.2f}'.format
    
    print("\n\n")
    print("========================================")
    print("BENCHMARK RESULTS")
    print("========================================")
    print(df.to_string(index=False))
    
    # Save to file
    df.to_csv("benchmark_results.csv", index=False)
    print("\nSaved result to benchmark_results.csv")

if __name__ == "__main__":
    main()
