"""PlayerControllerSystem: handles player input and movement."""

import math
from ..core.system import GameSystem
from ..core.component import Transform, Physics, Weapon
from ..input import InputState


class PlayerControllerSystem(GameSystem):
    """Handles player movement and shooting based on input."""
    
    def __init__(self, entity_manager, component_registry, input_handler, weapon_system):
        super().__init__(entity_manager, component_registry)
        self.input_handler = input_handler
        self.weapon_system = weapon_system
        self.player_id: str = None
        self.priority = 1  # Run early, same as physics
    
    def set_player_id(self, player_id: str):
        """Set the player entity ID."""
        self.player_id = player_id
    
    def update(self, dt: float):
        """Update player based on input."""
        if not self.player_id:
            return
        
        transform = self.entity_manager.get_component(self.player_id, "Transform")
        physics = self.entity_manager.get_component(self.player_id, "Physics")
        
        if not transform or not physics:
            return
        
        input_state = self.input_handler.state
        
        # Handle rotation
        rotation_speed = 180.0  # degrees per second
        if input_state.rotate_left:
            transform.angular_velocity = -rotation_speed
        elif input_state.rotate_right:
            transform.angular_velocity = rotation_speed
        else:
            transform.angular_velocity = 0.0
        
        # Handle movement
        move_forward = input_state.move_up
        move_backward = input_state.move_down
        move_left = input_state.move_left
        move_right = input_state.move_right
        
        if move_forward or move_backward or move_left or move_right:
            # Calculate movement direction
            angle_rad = math.radians(transform.angle)
            
            # Forward/backward movement
            if move_forward:
                transform.vx += math.cos(angle_rad) * physics.acceleration * dt
                transform.vy += math.sin(angle_rad) * physics.acceleration * dt
            elif move_backward:
                transform.vx -= math.cos(angle_rad) * physics.acceleration * dt * 0.5
                transform.vy -= math.sin(angle_rad) * physics.acceleration * dt * 0.5
            
            # Strafe movement
            strafe_angle = angle_rad + math.pi / 2
            if move_left:
                transform.vx += math.cos(strafe_angle) * physics.acceleration * dt * 0.7
                transform.vy += math.sin(strafe_angle) * physics.acceleration * dt * 0.7
            elif move_right:
                transform.vx -= math.cos(strafe_angle) * physics.acceleration * dt * 0.7
                transform.vy -= math.sin(strafe_angle) * physics.acceleration * dt * 0.7
        
        # Handle firing
        if input_state.fire:
            weapon = self.entity_manager.get_component(self.player_id, "Weapon")
            if weapon:
                self.weapon_system.fire_weapon(self.player_id)
