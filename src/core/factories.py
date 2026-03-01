"""Factory classes for creating pipeline components.

Simple factory pattern: create(name, cfg) -> Component
No service locator, no over-engineering.
"""



from typing import Any

from .interfaces import (
    BaseBackbone,
    BaseDetector,
    BaseFusion,
    BaseLoss,
    BaseTrainingStrategy,
)




class DetectorFactory:
    """Factory for creating detector instances."""

    _registry: dict[str, type[BaseDetector]] = {}

    @classmethod
    def register(cls, name: str, detector_cls: type[BaseDetector]) -> None:
        """Register a detector class."""
        cls._registry[name] = detector_cls

    @classmethod
    def create(cls, name: str, cfg: dict[str, Any]) -> BaseDetector:
        """Create a detector instance."""
        if name not in cls._registry:
            available = list(cls._registry.keys())
            raise ValueError(f"Unknown detector '{name}'. Available: {available}")
        return cls._registry[name](cfg)

    @classmethod
    def available(cls) -> list[str]:
        """List available detector names."""
        return list(cls._registry.keys())


class BackboneFactory:
    """Factory for creating backbone instances."""

    _registry: dict[str, type[BaseBackbone]] = {}

    @classmethod
    def register(cls, name: str, backbone_cls: type[BaseBackbone]) -> None:
        """Register a backbone class."""
        cls._registry[name] = backbone_cls

    @classmethod
    def create(cls, name: str, cfg: dict[str, Any]) -> BaseBackbone:
        """Create a backbone instance.

        Args:
            name: Registered backbone name ('resnet50', 'efficientnet_b4').
            cfg: Configuration dictionary.

        Returns:
            Backbone instance.

        Raises:
            ValueError: If name is not registered.
        """
        if name not in cls._registry:
            available = list(cls._registry.keys())
            raise ValueError(f"Unknown backbone '{name}'. Available: {available}")
        return cls._registry[name](cfg)

    @classmethod
    def available(cls) -> list[str]:
        """List available backbone names."""
        return list(cls._registry.keys())


class LossFactory:
    """Factory for creating loss instances."""

    _registry: dict[str, type[BaseLoss]] = {}

    @classmethod
    def register(cls, name: str, loss_cls: type[BaseLoss]) -> None:
        """Register a loss class."""
        cls._registry[name] = loss_cls

    @classmethod
    def create(cls, name: str, cfg: dict[str, Any]) -> BaseLoss:
        """Create a loss instance.

        Args:
            name: Registered loss name ('smooth_modulation', 'focal').
            cfg: Configuration dictionary.

        Returns:
            Loss instance.

        Raises:
            ValueError: If name is not registered.
        """
        if name not in cls._registry:
            available = list(cls._registry.keys())
            raise ValueError(f"Unknown loss '{name}'. Available: {available}")
        return cls._registry[name](cfg)

    @classmethod
    def available(cls) -> list[str]:
        """List available loss names."""
        return list(cls._registry.keys())


class StrategyFactory:
    """Factory for training strategies."""

    _registry: dict[str, type[BaseTrainingStrategy]] = {}

    @classmethod
    def register(cls, name: str, strategy_cls: type[BaseTrainingStrategy]) -> None:
        """Register a strategy class."""
        cls._registry[name] = strategy_cls

    @classmethod
    def create(cls, name: str, cfg: dict[str, Any], num_classes: int) -> BaseTrainingStrategy:
        """Create a strategy instance."""
        if name not in cls._registry:
            available = list(cls._registry.keys())
            raise ValueError(f"Unknown strategy '{name}'. Available: {available}")
        return cls._registry[name](cfg, num_classes)

    @classmethod
    def available(cls) -> list[str]:
        """List available strategy names."""
        return list(cls._registry.keys())



class FusionFactory:
    """Factory for creating fusion instances."""

    _registry: dict[str, type[BaseFusion]] = {}

    @classmethod
    def register(cls, name: str, fusion_cls: type[BaseFusion]) -> None:
        """Register a fusion class."""
        cls._registry[name] = fusion_cls

    @classmethod
    def create(cls, name: str, cfg: dict[str, Any]) -> BaseFusion:
        """Create a fusion instance.

        Args:
            name: Registered fusion name ('msff', 'simple_concat').
            cfg: Configuration dictionary.

        Returns:
            Fusion instance.

        Raises:
            ValueError: If name is not registered.
        """
        if name not in cls._registry:
            available = list(cls._registry.keys())
            raise ValueError(f"Unknown fusion '{name}'. Available: {available}")
        return cls._registry[name](cfg)

    @classmethod
    def available(cls) -> list[str]:
        """List available fusion names."""
        return list(cls._registry.keys())
