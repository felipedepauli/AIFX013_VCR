
import torch
import sys
import io
from pathlib import Path

def get_size(obj):
    """Estimate size of object in bytes."""
    buf = io.BytesIO()
    torch.save(obj, buf)
    return buf.getbuffer().nbytes

def inspect(path):
    print(f"Inspecting: {path}")
    data = torch.load(path, map_location="cpu")
    print(f"Keys: {list(data.keys())}")
    
    total = 0
    for k, v in data.items():
        try:
            sz = get_size(v)
            print(f"  {k}: {sz / (1024*1024):.2f} MB")
            total += sz
        except:
            print(f"  {k}: <error sizing>")
            
    print(f"Total sized: {total / (1024*1024):.2f} MB")
    
    # helper to drill down
    if "config" in data:
        print("Config breakdown:")
        for k, v in data["config"].items():
             print(f"    {k}: {get_size(v)/1024:.2f} KB")
        print("Model Config:")
        print(data["config"].get("model", "No model config found"))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect(sys.argv[1])
    else:
        print("Usage: python inspect_checkpoint.py <path>")
