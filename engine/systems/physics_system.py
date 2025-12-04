"""
Physics System

Handles movement, velocity, acceleration, friction, and rotation.
"""

from engine.core.system import GameSystem
from engine.core.component import Transform, Physics, Arena
from engine.utils.math_utils import clamp, magnitude


class PhysicsSystem(GameSystem):
    """
    Updates entity positions based on velocity and physics properties.
    
    Responsibilities:
    - Apply velocity to position
    - Apply friction to velocity
    - Clamp velocity to max speed
    - Apply rotation
    - Keep entities within arena bounds (if Arena component exists)
    """
    
    def __init__(self, entity_manager, priority: int = 10):
        super().__init__(entity_manager, priority)
        self.arena = None
    
    def update(self, dt: float) -> None:
        """Update all entities with Transform and Physics components."""
        # Get arena bounds if they exist
        arena_entities = self.entity_manager.query_entities(Arena)
        if arena_entities:
            self.arena = arena_entities[0].get_component(Arena)
        
        # Update all physics-enabled entities
        entities = self.entity_manager.query_entities(Transform, Physics)
        
        for entity in entities:
            transform = entity.get_component(Transform)
            physics = entity.get_component(Physics)
            
            # Apply velocity to position
            transform.x += transform.vx * dt
            transform.y += transform.vy * dt
            
            # Apply friction
            if physics.friction > 0:
                friction_factor = max(0, 1.0 - physics.friction * dt)
                transform.vx *= friction_factor
                transform.vy *= friction_factor
            
            # Clamp velocity to max speed
            speed = magnitude(transform.vx, transform.vy)
            if speed > physics.max_speed:
                scale = physics.max_speed / speed
                transform.vx *= scale
                transform.vy *= scale
            
            # Apply rotation
            if physics.can_rotate:
                transform.angle += transform.angular_velocity * dt
                
                # Wrap angle to [-180, 180]
                while transform.angle > 180:
                    transform.angle -= 360
                while transform.angle < -180:
                    transform.angle += 360
            
            # Clamp to arena bounds if available
            if self.arena:
                old_x, old_y = transform.x, transform.y
                transform.x, transform.y = self.arena.clamp_position(transform.x, transform.y)
                
                # Bounce off walls (stop velocity in blocked direction)
                if transform.x != old_x:
                    transform.vx = 0
                if transform.y != old_y:
                    transform.vy = 0
