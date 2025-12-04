"""
Game Systems - All game logic lives here.

Systems process entities with specific component signatures.
They are called in priority order each frame by the SystemManager.
"""

from .physics_system import PhysicsSystem
from .collision_system import CollisionSystem
from .ai_system import AISystem
from .weapon_system import WeaponSystem
from .health_system import HealthSystem
from .wave_system import WaveSystem
from .status_system import StatusEffectSystem
from .pathfinding_system import PathfindingSystem

# Systems requiring turtle/tkinter
try:
    from .render_system import RenderSystem
    from .input_system import InputSystem
    _HAS_TURTLE = True
except ImportError:
    RenderSystem = None
    InputSystem = None
    _HAS_TURTLE = False

__all__ = [
    "PhysicsSystem",
    "CollisionSystem", 
    "RenderSystem",
    "InputSystem",
    "AISystem",
    "WeaponSystem",
    "HealthSystem",
    "WaveSystem",
    "StatusEffectSystem",
    "PathfindingSystem",
]
