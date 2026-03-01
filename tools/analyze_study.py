#!/usr/bin/env python3
"""Analyze Optuna study results and extract best hyperparameters per backbone.

Usage:
    python analyze_study.py  # Auto-finds database
    python analyze_study.py --db runs/experiments.db
    python analyze_study.py --db runs/experiments.db --save-configs
"""

import argparse
import optuna
from pathlib import Path
from collections import defaultdict
import yaml
from typing import Optional


def analyze_study(db_path: str, study_name: Optional[str] = None, save_configs: bool = False):
    """Load and analyze the Optuna study from database."""
    
    # Load the study from database
    storage_url = f"sqlite:///{db_path}"
    print(f"Loading study from database: {db_path}")
    
    # If no study name provided, get the first/only study
    if study_name is None:
        available_studies = optuna.study.get_all_study_summaries(storage_url)
        if not available_studies:
            print(f"Error: No studies found in database: {db_path}")
            return None, None
        
        study_name = available_studies[0].study_name
        print(f"Found study: {study_name}")
        
        if len(available_studies) > 1:
            print(f"\nNote: Found {len(available_studies)} studies. Using '{study_name}'.")
            print("Available studies:")
            for s in available_studies:
                print(f"  - {s.study_name}")
    
    study = optuna.load_study(study_name=study_name, storage=storage_url)
    
    print(f"\n{'='*80}")
    print("STUDY OVERVIEW")
    print(f"{'='*80}")
    print(f"Study name: {study.study_name}")
    print(f"Number of trials: {len(study.trials)}")
    print(f"Number of complete trials: {len([t for t in study.trials if t.state.name == 'COMPLETE'])}")
    print(f"Number of pruned trials: {len([t for t in study.trials if t.state.name == 'PRUNED'])}")
    print(f"Number of failed trials: {len([t for t in study.trials if t.state.name == 'FAIL'])}")
    
    # Overall best trial
    print(f"\n{'='*80}")
    print("OVERALL BEST TRIAL")
    print(f"{'='*80}")
    try:
        best_trial = study.best_trial
        print(f"Trial number: {best_trial.number}")
        print(f"Best value: {best_trial.value:.4f}")
        print(f"\nBest hyperparameters:")
        for key, value in best_trial.params.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"Could not retrieve best trial: {e}")
    
    # Group by backbone
    print(f"\n{'='*80}")
    print("BEST HYPERPARAMETERS PER BACKBONE")
    print(f"{'='*80}")
    
    backbone_trials = defaultdict(list)
    for trial in study.trials:
        if trial.state.name == 'COMPLETE' and 'backbone' in trial.params:
            backbone = trial.params['backbone']
            backbone_trials[backbone].append(trial)
    
    best_per_backbone = {}
    for backbone, trials in sorted(backbone_trials.items()):
        # Find best trial for this backbone
        best_trial = max(trials, key=lambda t: t.value)
        best_per_backbone[backbone] = best_trial
        
        print(f"\n{backbone.upper()}:")
        print(f"  Trials tested: {len(trials)}")
        print(f"  Best trial: #{best_trial.number}")
        print(f"  Best score: {best_trial.value:.4f}")
        print(f"  Best hyperparameters:")
        for key, value in best_trial.params.items():
            if key != 'backbone':  # Don't repeat the backbone
                print(f"    {key}: {value}")
    
    # All trials summary
    print(f"\n{'='*80}")
    print("ALL TRIALS SUMMARY")
    print(f"{'='*80}")
    print(f"{'Trial':<8} {'Backbone':<15} {'Score':<10} {'Status':<12}")
    print("-" * 80)
    
    for trial in study.trials:
        backbone = trial.params.get('backbone', 'N/A')
        score = f"{trial.value:.4f}" if trial.value is not None else "N/A"
        status = trial.state.name
        print(f"{trial.number:<8} {backbone:<15} {score:<10} {status:<12}")
    
    # Save configs if requested
    if save_configs:
        save_best_configs(best_per_backbone, Path(db_path).parent)
    
    return study, best_per_backbone


def save_best_configs(best_per_backbone: dict, output_dir: Path):
    """Save configuration files for each backbone with best hyperparameters."""
    
    configs_dir = output_dir / "best_configs"
    configs_dir.mkdir(exist_ok=True)
    
    print(f"\n{'='*80}")
    print("SAVING CONFIGURATION FILES")
    print(f"{'='*80}")
    
    for backbone, trial in best_per_backbone.items():
        # Create training config for this backbone
        config = {
            "training": {
                "backbone": backbone,
                "strategy": trial.params.get("strategy", "vcr"),
                "fusion": trial.params.get("fusion", "msff"),
                "loss": trial.params.get("loss_fn", "smooth_modulation"),
                "epochs": trial.params.get("epochs", 20),
                "batch_size": trial.params.get("batch_size", 32),
                "image_size": trial.params.get("image_size", 224),
                "lr": trial.params.get("lr", 1e-4),
                "weight_decay": trial.params.get("weight_decay", 1e-4),
                "device": trial.params.get("device", "auto"),
                "use_weighted_sampler": trial.params.get("use_weighted_sampler", True),
            },
            "metadata": {
                "trial_number": trial.number,
                "best_score": trial.value,
                "optimization_date": str(trial.datetime_complete),
            }
        }
        
        config_path = configs_dir / f"{backbone}_best.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✓ Saved: {config_path}")
    
    print(f"\n✓ All configs saved to: {configs_dir}")


def main():
    parser = argparse.ArgumentParser(description="Analyze Optuna study results")
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help="Path to the SQLite database file (e.g., runs/experiments.db)"
    )
    parser.add_argument(
        "--study-name",
        type=str,
        default=None,
        help="Name of the study to load (auto-detected if not specified)"
    )
    parser.add_argument(
        "--save-configs",
        action="store_true",
        help="Save best configuration files for each backbone"
    )
    
    args = parser.parse_args()
    
    # Auto-discover database if not specified
    if args.db is None:
        # Try common locations
        possible_paths = [
            Path("runs/experiments.db"),
            Path("runs/optimization/experiments.db"),
        ]
        
        # Also search for any experiments.db file
        from glob import glob
        found_dbs = glob("**/experiments.db", recursive=True)
        possible_paths.extend([Path(p) for p in found_dbs])
        
        db_path = None
        for path in possible_paths:
            if path.exists():
                db_path = path
                break
        
        if db_path is None:
            print("Error: No experiments.db file found.")
            print("\nSearched locations:")
            for p in possible_paths[:2]:
                print(f"  - {p}")
            if found_dbs:
                print("\nFound database files:")
                for f in found_dbs:
                    print(f"  - {f}")
            print(f"\nPlease specify with: python {__file__} --db <path>")
            return 1
    else:
        db_path = Path(args.db)
        if not db_path.exists():
            print(f"Error: Database file not found: {db_path}")
            return 1
    
    study, best_per_backbone = analyze_study(
        str(db_path),
        study_name=args.study_name,
        save_configs=args.save_configs
    )
    
    if study is None:
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
