"""PhysicsSystem: handles movement, velocity, friction, and acceleration."""

import math
from ..core.system import GameSystem
from ..core.component import Transform, Physics, StatusEffects


class PhysicsSystem(GameSystem):
    """Updates entity positions based on physics properties."""
    
    def __init__(self, entity_manager, component_registry):
        super().__init__(entity_manager, component_registry)
        self.priority = 1  # Run early in the frame
    
    def update(self, dt: float):
        """Update physics for all entities with Transform and Physics components."""
        # Get all entities with Transform and Physics
        entity_ids = self.component_registry.get_entities_with("Transform", "Physics")
        
        for entity_id in entity_ids:
            transform = self.entity_manager.get_component(entity_id, "Transform")
            physics = self.entity_manager.get_component(entity_id, "Physics")
            status_effects = self.entity_manager.get_component(entity_id, "StatusEffects")
            
            if not transform or not physics:
                continue
            
            # Apply status effects
            speed_multiplier = 1.0
            if status_effects:
                speed_multiplier *= status_effects.slow
            
            # Apply friction
            transform.vx *= physics.friction
            transform.vy *= physics.friction
            
            # Enforce max speed
            speed = math.sqrt(transform.vx * transform.vx + transform.vy * transform.vy)
            if speed > physics.max_speed * speed_multiplier:
                scale = (physics.max_speed * speed_multiplier) / speed
                transform.vx *= scale
                transform.vy *= scale
            
            # Update position
            transform.x += transform.vx * dt
            transform.y += transform.vy * dt
            
            # Update rotation
            if transform.angular_velocity != 0:
                transform.angle += transform.angular_velocity * dt
                # Normalize angle to 0-360
                transform.angle = transform.angle % 360
