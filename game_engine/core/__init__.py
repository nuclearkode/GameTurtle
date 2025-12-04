"""Core ECS primitives: entities, components, managers, systems."""

from .entity import Entity
from .component import (
    Component,
    Transform,
    Renderable,
    Collider,
    Physics,
    Health,
    Weapon,
    Projectile,
    AIBrain,
    Shield,
    StatusEffects,
    WaveInfo,
)
from .entity_manager import EntityManager
from .component_registry import ComponentRegistry
from .system import GameSystem
from .system_manager import SystemManager

__all__ = [
    "Entity",
    "Component",
    "Transform",
    "Renderable",
    "Collider",
    "Physics",
    "Health",
    "Weapon",
    "Projectile",
    "AIBrain",
    "Shield",
    "StatusEffects",
    "WaveInfo",
    "EntityManager",
    "ComponentRegistry",
    "GameSystem",
    "SystemManager",
]
