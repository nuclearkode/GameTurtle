"""
WeaponSystem - handles weapon firing, cooldowns, projectile creation.
"""

import random
import math
from game_engine.core.system import GameSystem
from game_engine.core.component import (
    Transform, Weapon, Projectile, Collider, Renderable, AIBrain
)
from game_engine.utils.math_utils import rotate_vector, normalize
from game_engine.input.input_handler import InputAction, InputState


class WeaponSystem(GameSystem):
    """
    Handles weapon firing logic.
    Creates projectiles when weapons fire.
    """
    
    def __init__(self, entity_manager, component_registry, input_state: InputState = None):
        super().__init__(entity_manager, component_registry)
        self.input_state = input_state
    
    def update(self, dt: float) -> None:
        """Update weapon cooldowns and handle firing"""
        # Update projectile lifetimes first
        self._update_projectile_lifetimes(dt)
        
        entities = self.registry.get_entities_with(Transform, Weapon)
        
        for entity_id in entities:
            transform = self.entity_manager.get_component(entity_id, Transform)
            weapon = self.entity_manager.get_component(entity_id, Weapon)
            
            if not transform or not weapon:
                continue
            
            # Update cooldown
            weapon.cooldown = max(0.0, weapon.cooldown - dt)
            
            # Check if should fire
            should_fire = False
            
            # Player fires on input
            if self.input_state and self.input_state.is_active(InputAction.FIRE):
                # Check if this is the player (no AIBrain)
                if not self.entity_manager.has_component(entity_id, AIBrain):
                    should_fire = True
            
            # AI fires based on AIBrain cooldown
            brain = self.entity_manager.get_component(entity_id, AIBrain)
            if brain and "fire" in brain.cooldowns and brain.cooldowns["fire"] <= 0:
                should_fire = True
                brain.cooldowns["fire"] = 1.0 / weapon.fire_rate  # Reset cooldown
            
            # Fire if ready
            if should_fire and weapon.cooldown <= 0:
                self._fire_weapon(entity_id, transform, weapon)
                weapon.cooldown = 1.0 / weapon.fire_rate
    
    def _fire_weapon(self, entity_id: str, transform: Transform, weapon: Weapon) -> None:
        """Create projectile(s) for weapon fire"""
        # Calculate base direction (forward from entity angle)
        angle_rad = math.radians(transform.angle)
        base_dir_x = math.cos(angle_rad)
        base_dir_y = math.sin(angle_rad)
        
        # Fire multiple bullets (for shotgun/spread)
        for i in range(weapon.bullet_count):
            # Calculate spread angle
            spread_angle = 0.0
            if weapon.bullet_count > 1:
                # Distribute bullets evenly across spread
                spread_range = weapon.spread
                if weapon.bullet_count == 1:
                    spread_angle = 0.0
                else:
                    t = i / (weapon.bullet_count - 1)  # 0 to 1
                    spread_angle = (t - 0.5) * spread_range
            else:
                # Add random spread for single bullets
                spread_angle = random.uniform(-weapon.spread / 2, weapon.spread / 2)
            
            # Rotate direction by spread
            dir_x, dir_y = rotate_vector(base_dir_x, base_dir_y, spread_angle)
            
            # Create projectile entity
            proj_id = self.entity_manager.create_entity()
            
            # Transform
            proj_transform = Transform(
                x=transform.x + dir_x * 20,  # Spawn slightly ahead
                y=transform.y + dir_y * 20,
                vx=dir_x * weapon.projectile_speed,
                vy=dir_y * weapon.projectile_speed,
                angle=transform.angle + spread_angle
            )
            self.entity_manager.add_component(proj_id, proj_transform)
            self.registry.register(proj_id, proj_transform)
            
            # Projectile component
            proj_projectile = Projectile(
                owner_id=entity_id,
                damage=weapon.damage,
                lifetime=weapon.range / weapon.projectile_speed,
                time_alive=0.0,
                pierce_count=0
            )
            self.entity_manager.add_component(proj_id, proj_projectile)
            self.registry.register(proj_id, proj_projectile)
            
            # Collider
            proj_collider = Collider(
                radius=5.0,
                mask=0x0001,  # Projectile mask (not used for collision, tags are)
                tags={"projectile"}
            )
            self.entity_manager.add_component(proj_id, proj_collider)
            self.registry.register(proj_id, proj_collider)
            
            # Renderable
            proj_renderable = Renderable(
                shape="circle",
                color="yellow",
                size=0.3
            )
            self.entity_manager.add_component(proj_id, proj_renderable)
            self.registry.register(proj_id, proj_renderable)
    
    def _update_projectile_lifetimes(self, dt: float) -> None:
        """Update projectile lifetimes and destroy expired ones"""
        projectiles = self.registry.get_entities_with(Transform, Projectile)
        for proj_id in projectiles:
            proj_projectile = self.entity_manager.get_component(proj_id, Projectile)
            if proj_projectile:
                proj_projectile.time_alive += dt
                if proj_projectile.time_alive >= proj_projectile.lifetime:
                    self.entity_manager.destroy_entity(proj_id)
