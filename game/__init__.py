"""
Robo-Arena Game

A top-down arena shooter built on the Turtle Arena Game Engine.
"""

from .config import GameConfig
from .prefabs import create_player, create_obstacle
from .main import main

__all__ = [
    "GameConfig",
    "create_player",
    "create_obstacle",
    "main",
]
