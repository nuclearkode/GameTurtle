"""
Advanced Turtle Arena Game Engine

A modern 2D game engine built on Python's turtle library using:
- Entity-Component-System (ECS) architecture
- Data-oriented design principles
- Light OOP for structure and extensibility

This engine provides a clear separation between:
- Data (Components) - Pure data structures
- Logic (Systems) - Behavior operating on component data
- Identity (Entities) - IDs linking components together
"""

from .core import (
    Entity,
    EntityManager,
    ComponentRegistry,
    GameSystem,
    SystemManager,
    EventBus,
    Event,
)

# GameLoop requires turtle/tkinter, so import conditionally
try:
    from .game_loop import GameLoop
    _HAS_TURTLE = True
except ImportError:
    GameLoop = None
    _HAS_TURTLE = False

__version__ = "1.0.0"
__all__ = [
    "Entity",
    "EntityManager", 
    "ComponentRegistry",
    "GameSystem",
    "SystemManager",
    "EventBus",
    "Event",
    "GameLoop",
]
