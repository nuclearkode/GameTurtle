"""Core ECS primitives and game engine orchestrator."""

# Import core ECS components that don't depend on turtle
from .entity import Entity, EntityManager, ComponentRegistry
from .component import *
from .system import GameSystem, SystemManager

# GameEngine requires turtle, so import it only when needed
# from .game_engine import GameEngine

__all__ = [
    'Entity',
    'EntityManager', 
    'ComponentRegistry',
    'GameSystem',
    'SystemManager',
    # 'GameEngine',  # Import directly from game_engine when needed
]
