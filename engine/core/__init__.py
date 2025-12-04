"""
Core ECS primitives for the game engine.

This module provides the fundamental building blocks:
- Entity: Lightweight identifiers linking components
- Component: Pure data structures (defined in components/)
- EntityManager: Creates/destroys entities, manages component storage
- ComponentRegistry: Indexes entities by component type for fast queries
- GameSystem: Base class for all systems
- SystemManager: Orchestrates system execution order
- EventBus: Decoupled communication between systems
"""

from .entity import Entity, EntityManager
from .component import ComponentRegistry
from .system import GameSystem, SystemManager
from .events import EventBus, Event

__all__ = [
    "Entity",
    "EntityManager",
    "ComponentRegistry", 
    "GameSystem",
    "SystemManager",
    "EventBus",
    "Event",
]
