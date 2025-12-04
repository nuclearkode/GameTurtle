"""Core ECS primitives"""

from .entity import Entity, EntityManager
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
from .system import GameSystem, SystemManager
from .registry import ComponentRegistry

__all__ = [
    "Entity",
    "EntityManager",
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
    "GameSystem",
    "SystemManager",
    "ComponentRegistry",
]
