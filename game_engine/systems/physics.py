"""
PhysicsSystem - handles movement, velocity, friction, acceleration.
Updates Transform components based on Physics components.
"""

from game_engine.core.system import GameSystem
from game_engine.core.component import Transform, Physics, StatusEffects
from game_engine.utils.math_utils import clamp, normalize


class PhysicsSystem(GameSystem):
    """
    Updates entity positions and velocities.
    Applies friction, acceleration, max speed limits.
    """
    
    def update(self, dt: float) -> None:
        """Update physics for all entities with Transform and Physics"""
        entities = self.registry.get_entities_with(Transform, Physics)
        
        for entity_id in entities:
            transform = self.entity_manager.get_component(entity_id, Transform)
            physics = self.entity_manager.get_component(entity_id, Physics)
            status = self.entity_manager.get_component(entity_id, StatusEffects)
            
            if not transform or not physics:
                continue
            
            # Apply status effects
            speed_multiplier = 1.0
            if status and status.slow_timer > 0:
                speed_multiplier *= status.slow_magnitude
            if status and status.stun_timer > 0:
                speed_multiplier = 0.0  # Stunned = no movement
            
            # Apply friction
            transform.vx *= physics.friction
            transform.vy *= physics.friction
            
            # Clamp velocity to max speed
            speed = (transform.vx ** 2 + transform.vy ** 2) ** 0.5
            max_speed = physics.max_speed * speed_multiplier
            
            if speed > max_speed:
                scale = max_speed / speed
                transform.vx *= scale
                transform.vy *= scale
            
            # Update position
            transform.x += transform.vx * dt
            transform.y += transform.vy * dt
            
            # Update rotation
            transform.angle += transform.angular_velocity * dt
            transform.angle %= 360.0  # Wrap angle
