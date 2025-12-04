"""
Component definitions - Pure data structures.

Components contain ONLY data. All behavior lives in systems.
Each component represents one aspect of an entity's state.

Naming convention:
- Components are named as nouns (Transform, not Transformable)
- Group related data together, but keep components focused
"""

from .transform import Transform
from .physics import Physics, Velocity
from .renderable import Renderable, RenderShape, RenderLayer
from .collider import Collider, ColliderType, CollisionMask
from .health import Health, Shield
from .weapon import Weapon, Projectile, WeaponType
from .ai import AIBrain, AIBehavior, AIState
from .status import StatusEffects, StatusEffect
from .tags import PlayerTag, EnemyTag, ProjectileTag, ObstacleTag, PowerupTag

__all__ = [
    # Transform & Physics
    "Transform",
    "Physics", 
    "Velocity",
    
    # Rendering
    "Renderable",
    "RenderShape",
    "RenderLayer",
    
    # Collision
    "Collider",
    "ColliderType", 
    "CollisionMask",
    
    # Combat
    "Health",
    "Shield",
    "Weapon",
    "Projectile",
    "WeaponType",
    
    # AI
    "AIBrain",
    "AIBehavior",
    "AIState",
    
    # Status Effects
    "StatusEffects",
    "StatusEffect",
    
    # Tags
    "PlayerTag",
    "EnemyTag",
    "ProjectileTag",
    "ObstacleTag",
    "PowerupTag",
]
