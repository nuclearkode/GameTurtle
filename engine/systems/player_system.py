"""
Player System

Handles player input and control.
"""

from engine.core.system import GameSystem
from engine.core.component import Player, Transform, Physics, Weapon
from engine.utils.input_manager import InputManager, InputAction
from engine.utils.math_utils import normalize
import math


class PlayerSystem(GameSystem):
    """
    Handles player input and actions.
    
    Responsibilities:
    - Process player movement input
    - Process player rotation input
    - Process firing input
    - Apply input to player components
    """
    
    def __init__(self, entity_manager, input_manager: InputManager, 
                 weapon_system=None, priority: int = 0):
        super().__init__(entity_manager, priority)
        self.input_manager = input_manager
        self.weapon_system = weapon_system
    
    def update(self, dt: float) -> None:
        """Update player based on input."""
        # Get player entity
        player_entities = self.entity_manager.query_entities(Player, Transform, Physics)
        
        if not player_entities:
            return
        
        player = player_entities[0]
        transform = player.get_component(Transform)
        physics = player.get_component(Physics)
        weapon = player.get_component(Weapon)
        
        # Handle movement
        move_x, move_y = self.input_manager.get_movement_vector()
        
        if move_x != 0 or move_y != 0:
            # Apply acceleration in movement direction
            transform.vx += move_x * physics.acceleration * dt
            transform.vy += move_y * physics.acceleration * dt
        
        # Handle rotation
        rotation_input = self.input_manager.get_rotation_input()
        if rotation_input != 0:
            transform.angular_velocity = rotation_input * physics.rotation_speed
        else:
            transform.angular_velocity = 0
        
        # Auto-rotate to face movement direction (optional alternative)
        # Uncomment to enable:
        # if move_x != 0 or move_y != 0:
        #     target_angle = math.degrees(math.atan2(move_y, move_x))
        #     angle_diff = target_angle - transform.angle
        #     while angle_diff > 180:
        #         angle_diff -= 360
        #     while angle_diff < -180:
        #         angle_diff += 360
        #     transform.angle += angle_diff * dt * 5.0  # Smooth rotation
        
        # Handle firing
        if self.input_manager.is_action_active(InputAction.FIRE):
            if weapon and self.weapon_system:
                self.weapon_system.fire_weapon(player.id)
