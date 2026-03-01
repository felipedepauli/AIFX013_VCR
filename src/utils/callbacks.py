import logging
import numpy as np
import torch

logger = logging.getLogger(__name__)

class EarlyStopping:
    """Early stops the training if validation metric doesn't improve after a given patience."""
    
    def __init__(
        self, 
        patience: int = 7, 
        verbose: bool = False, 
        delta: float = 0.0, 
        mode: str = "min",
        path: str = "checkpoint.pt",
        trace_func=logger.info
    ):
        """
        Args:
            patience (int): How long to wait after last time validation metric improved.
            verbose (bool): If True, prints a message for each validation metric improvement. 
            delta (float): Minimum change in the monitored quantity to qualify as an improvement.
            mode (str): One of {"min", "max"}. In "min" mode, training will stop when the 
                        quantity monitored has stopped decreasing; in "max" mode it will 
                        stop when the quantity monitored has stopped increasing.
            path (str): Path for the checkpoint to be saved to.
            trace_func (function): trace print function.
        """
        self.patience = patience
        self.verbose = verbose
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        self.val_loss_min = np.inf
        self.val_acc_max = -np.inf
        self.delta = delta
        self.mode = mode
        self.path = path
        self.trace_func = trace_func
        
        if mode not in ["min", "max"]:
            raise ValueError(f"EarlyStopping mode must be 'min' or 'max', got {mode}")

    def __call__(self, metric_val, model):
        score = -metric_val if self.mode == "min" else metric_val

        if self.best_score is None:
            self.best_score = score
            self.save_checkpoint(metric_val, model)
        elif score < self.best_score + self.delta:
            self.counter += 1
            if self.verbose:
                self.trace_func(f"EarlyStopping counter: {self.counter} out of {self.patience}")
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = score
            self.save_checkpoint(metric_val, model)
            self.counter = 0

    def save_checkpoint(self, metric_val, model):
        """Saves model when validation metric decrease/increase."""
        if self.verbose:
            if self.mode == "min":
                msg = f"Validation loss decreased ({self.val_loss_min:.6f} --> {metric_val:.6f}).  Saving model ..."
                self.val_loss_min = metric_val
            else:
                msg = f"Validation accuracy increased ({self.val_acc_max:.6f} --> {metric_val:.6f}).  Saving model ..."
                self.val_acc_max = metric_val
            self.trace_func(msg)
        
        # We don't save here anymore because 04_train_mlflow handles saving based on best_val_acc logic usually
        # But EarlyStopping usually *should* save the best model found so far according to its metric.
        # However, 04_train_mlflow already has:
        # if val_acc > best_val_acc: ... torch.save(...)
        
        # So this class primarily acts as a signal generator (early_stop = True)
        # We can skip saving to disk here to avoid conflict/duplication, or save to a temp path.
        # Let's keep it simple: Just track state.
        pass
