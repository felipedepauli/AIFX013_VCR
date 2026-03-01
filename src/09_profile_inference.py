#!/usr/bin/env python3
"""Profile trained checkpoints for inference and model size metrics."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
import time
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any

import torch


def load_vcr_model_class(project_root: Path):
    model_file = project_root / "04_model.py"
    spec = spec_from_file_location("step04_model", model_file)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import {model_file}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.VCRModel


def find_checkpoints(paths: list[str], include_last: bool) -> list[Path]:
    patterns = ["**/train/best.pt"]
    if include_last:
        patterns.append("**/train/last.pt")

    found: list[Path] = []
    if paths:
        for raw in paths:
            p = Path(raw)
            if p.is_file():
                found.append(p.resolve())
            elif p.is_dir():
                for pattern in patterns:
                    found.extend(sorted(x.resolve() for x in p.glob(pattern)))
    else:
        for pattern in patterns:
            found.extend(sorted(x.resolve() for x in Path(".").glob(pattern)))

    return list(dict.fromkeys(found))


def extract_info(checkpoint: dict[str, Any], checkpoint_path: Path) -> dict[str, Any]:
    config = checkpoint.get("config", {}) or {}
    model_cfg = config.get("model", {}) or {}
    train_cfg = config.get("training", {}) or {}
    state_dict = checkpoint["model_state_dict"]

    if "head.1.bias" in state_dict:
        num_classes = int(state_dict["head.1.bias"].shape[0])
    elif "head.1.weight" in state_dict:
        num_classes = int(state_dict["head.1.weight"].shape[0])
    else:
        num_classes = int(model_cfg.get("num_classes", train_cfg.get("num_classes", 10)))

    return {
        "experiment": config.get("experiment") or checkpoint_path.parent.parent.name,
        "backbone": model_cfg.get("backbone") or train_cfg.get("backbone") or config.get("backbone") or "resnet50",
        "fusion": model_cfg.get("fusion") or train_cfg.get("fusion") or config.get("fusion") or "msff",
        "dropout": float(model_cfg.get("dropout", 0.2)),
        "fusion_cfg": model_cfg.get("fusion_cfg") or {},
        "input_size": int(train_cfg.get("input_size") or train_cfg.get("image_size") or 224),
        "num_classes": num_classes,
    }


def count_params(model: torch.nn.Module) -> tuple[int, int]:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable


def benchmark_inference(
    model: torch.nn.Module,
    device: torch.device,
    input_size: int,
    batch_size: int,
    warmup: int,
    iters: int,
) -> dict[str, float]:
    model.eval()
    model.to(device)
    x = torch.randn(batch_size, 3, input_size, input_size, device=device)

    with torch.no_grad():
        for _ in range(warmup):
            _ = model(x)
        if device.type == "cuda":
            torch.cuda.synchronize()

        times_ms: list[float] = []
        for _ in range(iters):
            t0 = time.perf_counter()
            _ = model(x)
            if device.type == "cuda":
                torch.cuda.synchronize()
            t1 = time.perf_counter()
            times_ms.append((t1 - t0) * 1000.0)

    mean_ms = statistics.mean(times_ms)
    p50_ms = statistics.median(times_ms)
    p95_ms = sorted(times_ms)[max(0, math.ceil(0.95 * len(times_ms)) - 1)]
    std_ms = statistics.pstdev(times_ms) if len(times_ms) > 1 else 0.0
    throughput = (batch_size * 1000.0) / mean_ms if mean_ms > 0 else 0.0

    return {
        "inference_mean_ms": mean_ms,
        "inference_p50_ms": p50_ms,
        "inference_p95_ms": p95_ms,
        "inference_std_ms": std_ms,
        "throughput_img_s": throughput,
    }


def write_outputs(rows: list[dict[str, Any]], output_csv: Path, output_json: Path, output_md: Path) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)

    with open(output_json, "w") as f:
        json.dump(rows, f, indent=2)

    if rows:
        with open(output_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    else:
        with open(output_csv, "w") as f:
            f.write("")

    lines = [
        "# Inference Profiling Results",
        "",
        "| Checkpoint | Experiment | Backbone | Fusion | Classes | Params (M) | Checkpoint (MB) | Mean Inference (ms) | P95 (ms) | Throughput (img/s) |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row["checkpoint"]),
                    str(row["experiment"]),
                    str(row["backbone"]),
                    str(row["fusion"]),
                    str(row["num_classes"]),
                    f"{float(row['params_million']):.3f}",
                    f"{float(row['checkpoint_size_mb']):.2f}",
                    f"{float(row['inference_mean_ms']):.2f}",
                    f"{float(row['inference_p95_ms']):.2f}",
                    f"{float(row['throughput_img_s']):.2f}",
                ]
            )
            + " |"
        )

    with open(output_md, "w") as f:
        f.write("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile inference and model size from trained checkpoints.")
    parser.add_argument("--paths", nargs="*", default=[], help="Files/directories with checkpoints.")
    parser.add_argument("--include-last", action="store_true", help="Include last.pt (default: only best.pt).")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--iters", type=int, default=40)
    parser.add_argument("--output-csv", type=Path, default=Path("final_results/inference_profile.csv"))
    parser.add_argument("--output-json", type=Path, default=Path("final_results/inference_profile.json"))
    parser.add_argument("--output-md", type=Path, default=Path("final_results/inference_profile.md"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    device = torch.device("cuda" if (args.device == "auto" and torch.cuda.is_available()) else args.device if args.device != "auto" else "cpu")
    checkpoints = find_checkpoints(args.paths, include_last=args.include_last)
    if not checkpoints:
        print("No checkpoints found.")
        return 1

    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    VCRModel = load_vcr_model_class(project_root)

    rows: list[dict[str, Any]] = []
    print(f"Profiling {len(checkpoints)} checkpoint(s) on {device}...")
    for ckpt_path in checkpoints:
        print(f"- {ckpt_path}")
        checkpoint = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        info = extract_info(checkpoint, ckpt_path)

        model = VCRModel(
            num_classes=info["num_classes"],
            backbone_name=info["backbone"],
            backbone_cfg={"pretrained": False},
            fusion_name=info["fusion"],
            fusion_cfg=info["fusion_cfg"],
            dropout=info["dropout"],
        )
        model.load_state_dict(checkpoint["model_state_dict"], strict=True)

        total_params, trainable_params = count_params(model)
        inf = benchmark_inference(
            model=model,
            device=device,
            input_size=info["input_size"],
            batch_size=args.batch_size,
            warmup=args.warmup,
            iters=args.iters,
        )

        ckpt_size_bytes = ckpt_path.stat().st_size
        rows.append(
            {
                "checkpoint": str(ckpt_path),
                "experiment": info["experiment"],
                "backbone": info["backbone"],
                "fusion": info["fusion"],
                "num_classes": info["num_classes"],
                "input_size": info["input_size"],
                "device": str(device),
                "params_total": total_params,
                "params_trainable": trainable_params,
                "params_million": total_params / 1e6,
                "checkpoint_size_bytes": ckpt_size_bytes,
                "checkpoint_size_mb": ckpt_size_bytes / (1024 ** 2),
                "batch_size": args.batch_size,
                "warmup_iters": args.warmup,
                "benchmark_iters": args.iters,
                **inf,
            }
        )

    write_outputs(rows, args.output_csv, args.output_json, args.output_md)
    print("\nSaved:")
    print(f"- {args.output_csv}")
    print(f"- {args.output_json}")
    print(f"- {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
