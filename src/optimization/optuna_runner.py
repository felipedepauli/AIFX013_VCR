"""Optuna hyperparameter optimization with MLFlow tracking."""

import logging
from pathlib import Path
from typing import Any, Callable

import mlflow
import optuna
from optuna.trial import Trial

logger = logging.getLogger(__name__)


class OptunaMLFlowCallback:
    """Callback to log Optuna trials to MLFlow as nested runs."""
    
    def __init__(self, parent_run_id: str, metric_name: str = "val_acc"):
        self.parent_run_id = parent_run_id
        self.metric_name = metric_name
    
    def __call__(self, study: optuna.Study, trial: optuna.Trial) -> None:
        """Log trial results to MLFlow."""
        with mlflow.start_run(run_name=f"trial_{trial.number}", nested=True):
            # Log trial hyperparameters
            mlflow.log_params(trial.params)
            
            # Log trial result
            if trial.value is not None:
                mlflow.log_metric(self.metric_name, trial.value)
                mlflow.log_metric("trial_number", trial.number)
            
            # Log trial state
            mlflow.set_tag("trial_state", trial.state.name)
            
            if trial.state == optuna.trial.TrialState.COMPLETE:
                mlflow.set_tag("status", "completed")
            elif trial.state == optuna.trial.TrialState.PRUNED:
                mlflow.set_tag("status", "pruned")
            elif trial.state == optuna.trial.TrialState.FAIL:
                mlflow.set_tag("status", "failed")


def create_objective(
    train_fn: Callable,
    hp_config: dict[str, Any],
    fixed_params: dict[str, Any],
) -> Callable[[Trial], float]:
    """Create Optuna objective function.
    
    Args:
        train_fn: Training function that returns dict with metrics.
        hp_config: Hyperparameter search space configuration.
        fixed_params: Fixed parameters not being optimized.
    
    Returns:
        Objective function for Optuna.
    """
    def objective(trial: Trial) -> float:
        # Sample hyperparameters based on configuration
        params = {}
        for name, config in hp_config.items():
            hp_type = config["type"]
            
            if hp_type == "categorical":
                params[name] = trial.suggest_categorical(name, config["choices"])
            elif hp_type == "int":
                params[name] = trial.suggest_int(
                    name, config["low"], config["high"],
                    log=config.get("log", False)
                )
            elif hp_type == "float":
                params[name] = trial.suggest_float(
                    name, config["low"], config["high"],
                    log=config.get("log", False)
                )
            else:
                raise ValueError(f"Unknown hyperparameter type: {hp_type}")
        
        # Merge with fixed parameters
        all_params = {**fixed_params, **params}
        
        # Add trial for pruning support
        all_params["trial"] = trial
        
        # Run training with these hyperparameters
        try:
            result = train_fn(**all_params)
            val_acc = result.get("best_val_acc", 0.0)
            
            # Report intermediate values for pruning
            # (Optuna can prune bad trials early)
            trial.report(val_acc, step=result.get("best_epoch", 0))
            
            if trial.should_prune():
                raise optuna.TrialPruned()
            
            return val_acc
            
        except Exception as e:
            logger.error(f"Trial {trial.number} failed: {e}")
            raise
    
    return objective


def run_optimization(
    train_fn: Callable,
    hp_config: dict[str, Any],
    fixed_params: dict[str, Any],
    study_config: dict[str, Any],
    experiment_name: str = "VCR-Optimization",
    storage: str | None = None,
) -> optuna.Study:
    """Run Optuna hyperparameter optimization.
    
    Args:
        train_fn: Training function.
        hp_config: Hyperparameter search space.
        fixed_params: Fixed parameters.
        study_config: Optuna study configuration.
        experiment_name: MLFlow experiment name.
    
    Returns:
        Completed Optuna study.
    """
    # Set MLFlow experiment
    mlflow.set_experiment(experiment_name)
    
    # Create or load study
    study_name = study_config.get("name", "VCR-Optimization")
    
    # Configure sampler
    sampler_type = study_config.get("sampler", {}).get("type", "TPE")
    if sampler_type == "TPE":
        sampler = optuna.samplers.TPESampler()
    elif sampler_type == "Random":
        sampler = optuna.samplers.RandomSampler()
    elif sampler_type == "CmaEs":
        sampler = optuna.samplers.CmaEsSampler()
    else:
        sampler = None
    
    # Configure pruner
    pruner_config = study_config.get("pruner", {})
    pruner_type = pruner_config.get("type")
    
    if pruner_type == "MedianPruner":
        pruner = optuna.pruners.MedianPruner(
            n_startup_trials=pruner_config.get("n_startup_trials", 5),
            n_warmup_steps=pruner_config.get("n_warmup_steps", 10),
        )
    elif pruner_type == "HyperbandPruner":
        pruner = optuna.pruners.HyperbandPruner()
    elif pruner_type == "PercentilePruner":
        pruner = optuna.pruners.PercentilePruner(
            percentile=pruner_config.get("percentile", 25.0)
        )
    else:
        pruner = None
    
    direction = study_config.get("direction", "maximize")
    
    study = optuna.create_study(
        study_name=study_name,
        storage=storage,
        direction=direction,
        sampler=sampler,
        pruner=pruner,
        load_if_exists=True,  # Resume if study exists
    )
    
    # Create objective
    objective = create_objective(train_fn, hp_config, fixed_params)
    
    # Start parent MLFlow run
    with mlflow.start_run(run_name=f"optimization_{study_name}"):
        # Log study configuration
        mlflow.log_params({
            "study_name": study_name,
            "n_trials": study_config.get("n_trials", 50),
            "direction": direction,
            "sampler": sampler_type,
            "pruner": pruner_type,
        })
        
        parent_run_id = mlflow.active_run().info.run_id
        
        # Create callback for logging trials
        callback = OptunaMLFlowCallback(parent_run_id)
        
        # Run optimization
        n_trials = study_config.get("n_trials", 50)
        timeout = study_config.get("timeout", None)
        
        study.optimize(
            objective,
            n_trials=n_trials,
            timeout=timeout,
            callbacks=[callback],
        )
        
        # Log best trial results
        best_trial = study.best_trial
        mlflow.log_params({
            f"best_{k}": v for k, v in best_trial.params.items()
        })
        mlflow.log_metric("best_value", best_trial.value)
        mlflow.log_metric("n_trials_completed", len(study.trials))
        
        logger.info(f"Best trial: {best_trial.number}")
        logger.info(f"Best value: {best_trial.value:.4f}")
        logger.info(f"Best params: {best_trial.params}")
    
    return study
