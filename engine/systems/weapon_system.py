"""
Weapon System

Handles weapon firing, cooldowns, and projectile management.
"""

import math
import random
from engine.core.system import GameSystem
from engine.core.component import (
    Transform, Weapon, Projectile, Renderable, Collider, 
    Physics, Player, Enemy, Lifetime
)
from engine.utils.math_utils import rotate_vector


class WeaponSystem(GameSystem):
    """
    Manages weapon firing and projectile lifecycle.
    
    Responsibilities:
    - Update weapon cooldowns
    - Create projectile entities when firing
    - Update projectile lifetimes
    - Handle different fire patterns (single, spread, burst)
    """
    
    def __init__(self, entity_manager, priority: int = 15):
        super().__init__(entity_manager, priority)
    
    def update(self, dt: float) -> None:
        """Update weapon cooldowns and projectile lifetimes."""
        # Update weapon cooldowns
        weapon_entities = self.entity_manager.query_entities(Weapon)
        for entity in weapon_entities:
            weapon = entity.get_component(Weapon)
            if weapon.cooldown > 0:
                weapon.cooldown -= dt
    
    def fire_weapon(self, entity_id: str, target_angle: float = None) -> bool:
        """
        Fire a weapon from an entity.
        
        Args:
            entity_id: Entity firing the weapon
            target_angle: Override firing angle (if None, uses entity's angle)
        
        Returns:
            True if weapon was fired, False if on cooldown
        """
        entity = self.entity_manager.get_entity(entity_id)
        if not entity:
            return False
        
        weapon = entity.get_component(Weapon)
        transform = entity.get_component(Transform)
        
        if not weapon or not transform:
            return False
        
        # Check cooldown
        if weapon.cooldown > 0:
            return False
        
        # Set cooldown
        weapon.cooldown = 1.0 / weapon.fire_rate
        
        # Determine firing angle
        if target_angle is None:
            target_angle = transform.angle
        
        # Determine collision tags based on shooter
        is_player = entity.has_component(Player)
        is_enemy = entity.has_component(Enemy)
        
        if is_player:
            projectile_tags = {"player_projectile"}
            projectile_mask = {"enemy"}
        elif is_enemy:
            projectile_tags = {"enemy_projectile"}
            projectile_mask = {"player"}
        else:
            projectile_tags = {"projectile"}
            projectile_mask = {"player", "enemy"}
        
        # Fire projectiles (handle spread and multiple bullets)
        for i in range(weapon.bullet_count):
            # Calculate angle with spread
            angle = target_angle
            
            if weapon.bullet_count > 1:
                # Spread bullets evenly in an arc
                arc = weapon.spread
                if weapon.bullet_count > 1:
                    angle_step = arc / (weapon.bullet_count - 1)
                    angle = target_angle - arc / 2 + i * angle_step
                else:
                    angle = target_angle
            else:
                # Single bullet with random spread
                if weapon.spread > 0:
                    angle += random.uniform(-weapon.spread / 2, weapon.spread / 2)
            
            # Create projectile
            self._create_projectile(
                entity_id=entity_id,
                x=transform.x,
                y=transform.y,
                angle=angle,
                weapon=weapon,
                tags=projectile_tags,
                mask=projectile_mask
            )
        
        return True
    
    def _create_projectile(self, entity_id: str, x: float, y: float, 
                          angle: float, weapon: Weapon,
                          tags: set, mask: set) -> None:
        """Create a projectile entity."""
        # Offset spawn position slightly in front of shooter
        offset_dist = 15
        angle_rad = math.radians(angle)
        spawn_x = x + math.cos(angle_rad) * offset_dist
        spawn_y = y + math.sin(angle_rad) * offset_dist
        
        # Calculate velocity
        vx = math.cos(angle_rad) * weapon.projectile_speed
        vy = math.sin(angle_rad) * weapon.projectile_speed
        
        # Create entity
        projectile = self.entity_manager.create_entity()
        
        # Add components
        self.entity_manager.add_component(projectile.id, Transform(
            x=spawn_x,
            y=spawn_y,
            vx=vx,
            vy=vy,
            angle=angle
        ))
        
        self.entity_manager.add_component(projectile.id, Projectile(
            owner_id=entity_id,
            damage=weapon.damage,
            lifetime=weapon.bullet_lifetime,
            time_alive=0.0,
            piercing=weapon.projectile_piercing,
            knockback=weapon.knockback
        ))
        
        self.entity_manager.add_component(projectile.id, Renderable(
            shape="circle",
            color=weapon.bullet_color,
            size=weapon.bullet_size / 10.0,  # Scale down for turtle
            layer=5
        ))
        
        self.entity_manager.add_component(projectile.id, Collider(
            radius=weapon.bullet_size,
            is_trigger=True,  # Don't push entities around
            tags=tags,
            mask=mask
        ))
        
        # Minimal physics (no friction, projectiles don't slow down)
        self.entity_manager.add_component(projectile.id, Physics(
            mass=0.1,
            friction=0.0,
            max_speed=weapon.projectile_speed * 1.5,
            can_rotate=False
        ))
        
        # Auto-destroy after lifetime
        self.entity_manager.add_component(projectile.id, Lifetime(
            max_lifetime=weapon.bullet_lifetime,
            time_alive=0.0
        ))
    
    def update_lifetimes(self, dt: float) -> None:
        """Update projectile and other lifetime-limited entities."""
        lifetime_entities = self.entity_manager.query_entities(Lifetime)
        
        for entity in lifetime_entities:
            lifetime = entity.get_component(Lifetime)
            lifetime.time_alive += dt
            
            if lifetime.time_alive >= lifetime.max_lifetime:
                self.entity_manager.destroy_entity(entity.id)
