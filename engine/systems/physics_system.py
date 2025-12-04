"""
Physics System - Movement, velocity, and physics simulation.

Processes all entities with Transform and Velocity components.
Applies acceleration, friction, drag, and updates positions.
"""

from __future__ import annotations
import math
from typing import TYPE_CHECKING

from ..core.system import GameSystem, SystemPriority
from ..components.transform import Transform
from ..components.physics import Physics, Velocity

if TYPE_CHECKING:
    from ..core.entity import Entity


def _is_valid_float(value: float) -> bool:
    """Check if a float is valid (not NaN or infinity)."""
    return math.isfinite(value)


def _clamp_float(value: float, min_val: float, max_val: float) -> float:
    """Clamp a float to a range, returning 0 if invalid."""
    if not _is_valid_float(value):
        return 0.0
    return max(min_val, min(max_val, value))


def _sanitize_float(value: float, default: float = 0.0) -> float:
    """Return the value if valid, otherwise return default."""
    return value if _is_valid_float(value) else default


class PhysicsSystem(GameSystem):
    """
    Handles movement and physics simulation.
    
    Processing Order:
    1. Apply acceleration to velocity
    2. Apply friction and drag
    3. Clamp to max speed
    4. Integrate velocity to position
    5. Apply angular velocity to rotation
    6. Clear accumulated forces
    
    Arena Bounds:
    The system keeps entities within arena bounds by clamping positions
    and optionally bouncing off walls.
    """
    
    def __init__(
        self,
        arena_width: float = 800,
        arena_height: float = 600,
        enforce_bounds: bool = True
    ):
        super().__init__(priority=SystemPriority.PHYSICS)
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.arena_half_width = arena_width / 2
        self.arena_half_height = arena_height / 2
        self.enforce_bounds = enforce_bounds
    
    def update(self, dt: float) -> None:
        """Process physics for all relevant entities."""
        
        # Get all entities with Transform and Velocity
        for entity in self.entities.get_entities_with(Transform, Velocity):
            transform = self.entities.get_component(entity, Transform)
            velocity = self.entities.get_component(entity, Velocity)
            
            if transform is None or velocity is None:
                continue
            
            # Check for Physics component (optional for advanced physics)
            physics = self.entities.get_component(entity, Physics)
            
            if physics is not None and not physics.is_kinematic:
                self._process_physics(transform, velocity, physics, dt)
            else:
                # Simple velocity integration (no physics modifiers)
                self._integrate_simple(transform, velocity, dt)
            
            # Enforce arena bounds
            if self.enforce_bounds:
                self._enforce_bounds(entity, transform, velocity, physics)
    
    def _process_physics(
        self,
        transform: Transform,
        velocity: Velocity,
        physics: Physics,
        dt: float
    ) -> None:
        """Full physics processing with acceleration, friction, drag."""
        
        # Sanitize dt to prevent physics explosion
        dt = _clamp_float(dt, 0.0, 0.1)
        
        # Apply accumulated acceleration (sanitize values)
        accel_x = _sanitize_float(physics.accel_x)
        accel_y = _sanitize_float(physics.accel_y)
        angular_accel = _sanitize_float(physics.angular_accel)
        
        velocity.vx = _sanitize_float(velocity.vx) + accel_x * dt
        velocity.vy = _sanitize_float(velocity.vy) + accel_y * dt
        velocity.angular = _sanitize_float(velocity.angular) + angular_accel * dt
        
        # Apply friction (ground contact)
        if physics.friction > 0:
            friction_factor = 1.0 - (physics.friction * dt)
            friction_factor = max(0.0, friction_factor)
            velocity.vx *= friction_factor
            velocity.vy *= friction_factor
        
        # Apply drag (air resistance)
        if physics.drag < 1.0 and physics.drag > 0:
            drag_factor = physics.drag ** dt
            velocity.vx *= drag_factor
            velocity.vy *= drag_factor
        
        # Clamp to max speed
        speed = velocity.speed
        if _is_valid_float(speed) and speed > physics.max_speed and speed > 0:
            factor = physics.max_speed / speed
            velocity.vx *= factor
            velocity.vy *= factor
        
        # Clamp angular velocity
        if abs(velocity.angular) > physics.max_angular_speed:
            velocity.angular = math.copysign(physics.max_angular_speed, velocity.angular)
        
        # Final sanitization of velocity
        velocity.vx = _clamp_float(velocity.vx, -10000, 10000)
        velocity.vy = _clamp_float(velocity.vy, -10000, 10000)
        velocity.angular = _clamp_float(velocity.angular, -3600, 3600)
        
        # Integrate position
        transform.x += velocity.vx * dt
        transform.y += velocity.vy * dt
        transform.angle += velocity.angular * dt
        
        # Sanitize final position
        transform.x = _clamp_float(transform.x, -10000, 10000)
        transform.y = _clamp_float(transform.y, -10000, 10000)
        
        # Normalize angle to [0, 360)
        transform.angle = _sanitize_float(transform.angle) % 360
        
        # Clear forces for next frame
        physics.clear_forces()
    
    def _integrate_simple(
        self,
        transform: Transform,
        velocity: Velocity,
        dt: float
    ) -> None:
        """Simple velocity integration without physics component."""
        # Sanitize inputs
        dt = _clamp_float(dt, 0.0, 0.1)
        vx = _sanitize_float(velocity.vx)
        vy = _sanitize_float(velocity.vy)
        angular = _sanitize_float(velocity.angular)
        
        transform.x = _sanitize_float(transform.x) + vx * dt
        transform.y = _sanitize_float(transform.y) + vy * dt
        transform.angle = _sanitize_float(transform.angle) + angular * dt
        
        # Clamp position to reasonable bounds
        transform.x = _clamp_float(transform.x, -10000, 10000)
        transform.y = _clamp_float(transform.y, -10000, 10000)
        transform.angle = transform.angle % 360
    
    def _enforce_bounds(
        self,
        entity: Entity,
        transform: Transform,
        velocity: Velocity,
        physics: Physics | None
    ) -> None:
        """Keep entity within arena bounds."""
        
        # Get collider radius if available, else use default
        from ..components.collider import Collider
        collider = self.entities.get_component(entity, Collider)
        radius = collider.radius if collider else 15.0
        
        min_x = -self.arena_half_width + radius
        max_x = self.arena_half_width - radius
        min_y = -self.arena_half_height + radius
        max_y = self.arena_half_height - radius
        
        bounce = physics.bounce if physics else 0.0
        
        # X bounds
        if transform.x < min_x:
            transform.x = min_x
            if bounce > 0:
                velocity.vx = abs(velocity.vx) * bounce
            else:
                velocity.vx = 0
        elif transform.x > max_x:
            transform.x = max_x
            if bounce > 0:
                velocity.vx = -abs(velocity.vx) * bounce
            else:
                velocity.vx = 0
        
        # Y bounds
        if transform.y < min_y:
            transform.y = min_y
            if bounce > 0:
                velocity.vy = abs(velocity.vy) * bounce
            else:
                velocity.vy = 0
        elif transform.y > max_y:
            transform.y = max_y
            if bounce > 0:
                velocity.vy = -abs(velocity.vy) * bounce
            else:
                velocity.vy = 0
    
    def set_arena_size(self, width: float, height: float) -> None:
        """Update arena dimensions."""
        self.arena_width = width
        self.arena_height = height
        self.arena_half_width = width / 2
        self.arena_half_height = height / 2
