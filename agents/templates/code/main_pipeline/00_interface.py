#!/usr/bin/env python3
"""00_interface.py - Pipeline Step Interface.

This module defines the abstract base class for all pipeline steps.
Each step (01-08) should implement this interface.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class PipelineStep(ABC):
    """Abstract base class for pipeline steps.

    All pipeline steps (01_detect_crop, 02_prepare_data, etc.) should
    inherit from this class and implement the required methods.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the pipeline step.

        Args:
            config: Configuration dictionary for this step.
        """
        self.config = config or {}

    @abstractmethod
    def run(self) -> int:
        """Execute the pipeline step.

        Returns:
            Exit code (0 for success, non-zero for failure).
        """
        pass

    def validate(self) -> bool:
        """Validate inputs before running.

        Override this method to add custom validation logic.

        Returns:
            True if validation passes, False otherwise.
        """
        return True

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the step name (e.g., '01_detect_crop')."""
        pass

    @property
    def description(self) -> str:
        """Return a brief description of what this step does."""
        return ""
