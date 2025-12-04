"""
Collider component - Collision detection and physics interaction.

The collision system uses these components to detect overlaps
and generate collision events.
"""

from dataclasses import dataclass, field
from enum import Flag, auto
from typing import Optional


class ColliderType(Flag):
    """Type of collider shape."""
    CIRCLE = auto()
    AABB = auto()  # Axis-Aligned Bounding Box


class CollisionMask(Flag):
    """
    Collision layer masks for filtering collisions.
    
    An entity collides with another if:
        (a.layer & b.mask) and (b.layer & a.mask)
    
    This allows fine-grained control over what collides with what.
    """
    NONE = 0
    PLAYER = auto()
    ENEMY = auto()
    PLAYER_PROJECTILE = auto()
    ENEMY_PROJECTILE = auto()
    OBSTACLE = auto()
    POWERUP = auto()
    TRIGGER = auto()  # Triggers events but doesn't block
    
    # Convenience combinations
    ALL = PLAYER | ENEMY | PLAYER_PROJECTILE | ENEMY_PROJECTILE | OBSTACLE | POWERUP | TRIGGER
    SOLID = PLAYER | ENEMY | OBSTACLE


@dataclass
class Collider:
    """
    Collision detection component.
    
    Attributes:
        collider_type: Shape of the collider (CIRCLE or AABB)
        radius: Radius for circle colliders
        width: Width for AABB colliders
        height: Height for AABB colliders
        offset_x: Offset from entity position (for non-centered colliders)
        offset_y: Offset from entity position
        layer: What layer this entity is on
        mask: What layers this entity collides WITH
        is_trigger: If True, detects overlaps but doesn't block movement
        is_static: If True, doesn't move when collided with
        
    Collision Resolution:
        - Non-triggers: Generate collision response (separation, bounce)
        - Triggers: Only generate events, no physical response
        - Static vs Dynamic: Only dynamic entities are moved during resolution
        
    Example Setups:
        Player:     layer=PLAYER, mask=ENEMY|OBSTACLE|POWERUP|ENEMY_PROJECTILE
        Enemy:      layer=ENEMY, mask=PLAYER|OBSTACLE|PLAYER_PROJECTILE
        Wall:       layer=OBSTACLE, mask=ALL, is_static=True
        Bullet:     layer=PLAYER_PROJECTILE, mask=ENEMY|OBSTACLE
        Pickup:     layer=POWERUP, mask=PLAYER, is_trigger=True
    """
    collider_type: ColliderType = ColliderType.CIRCLE
    radius: float = 15.0
    width: float = 30.0
    height: float = 30.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    
    layer: CollisionMask = CollisionMask.NONE
    mask: CollisionMask = CollisionMask.NONE
    
    is_trigger: bool = False
    is_static: bool = False
    
    # Runtime collision data (filled by CollisionSystem)
    is_colliding: bool = field(default=False, repr=False)
    collision_count: int = field(default=0, repr=False)
    
    def get_bounds(self, x: float, y: float) -> tuple[float, float, float, float]:
        """
        Get AABB bounds for broad-phase collision.
        
        Returns (min_x, min_y, max_x, max_y) in world coordinates.
        """
        cx = x + self.offset_x
        cy = y + self.offset_y
        
        if self.collider_type == ColliderType.CIRCLE:
            return (
                cx - self.radius,
                cy - self.radius,
                cx + self.radius,
                cy + self.radius
            )
        else:  # AABB
            hw = self.width / 2
            hh = self.height / 2
            return (cx - hw, cy - hh, cx + hw, cy + hh)
    
    def should_collide_with(self, other: "Collider") -> bool:
        """Check if this collider should test collision with another."""
        return bool(self.layer & other.mask) and bool(other.layer & self.mask)
