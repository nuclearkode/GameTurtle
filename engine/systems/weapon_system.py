"""
Weapon System - Firing weapons and spawning projectiles.

Handles weapon cooldowns, firing patterns, and projectile creation.
"""

from __future__ import annotations
import math
import random
from typing import TYPE_CHECKING, Optional

from ..core.system import GameSystem, SystemPriority
from ..core.events import ProjectileFiredEvent
from ..components.transform import Transform
from ..components.physics import Physics, Velocity
from ..components.weapon import Weapon, Projectile, WeaponType
from ..components.renderable import Renderable, RenderShape, RenderLayer
from ..components.collider import Collider, ColliderType, CollisionMask
from ..components.tags import PlayerTag, ProjectileTag

if TYPE_CHECKING:
    from ..core.entity import Entity


class WeaponSystem(GameSystem):
    """
    Handles weapon firing and projectile management.
    
    Features:
    - Multiple weapon types with different patterns
    - Cooldown management
    - Projectile spawning
    - Ammo and reload handling
    - Burst fire support
    """
    
    def __init__(self):
        super().__init__(priority=SystemPriority.WEAPON)
    
    def update(self, dt: float) -> None:
        """Process weapons and projectiles."""
        # Update weapons
        for entity in self.entities.get_entities_with(Weapon, Transform):
            weapon = self.entities.get_component(entity, Weapon)
            transform = self.entities.get_component(entity, Transform)
            
            if not weapon or not transform:
                continue
            
            # Update cooldowns
            if weapon.cooldown > 0:
                weapon.cooldown -= dt
            
            if weapon.burst_cooldown > 0:
                weapon.burst_cooldown -= dt
            
            # Handle reload
            if weapon.is_reloading:
                weapon.reload_timer -= dt
                if weapon.reload_timer <= 0:
                    weapon.ammo = weapon.max_ammo
                    weapon.is_reloading = False
            
            # Handle firing
            if weapon.is_firing and weapon.can_fire:
                self._fire_weapon(entity, weapon, transform)
            
            # Handle burst continuation
            if weapon.burst_remaining > 0 and weapon.burst_cooldown <= 0:
                self._fire_burst_shot(entity, weapon, transform)
        
        # Update projectiles
        for entity in self.entities.get_entities_with(Projectile):
            projectile = self.entities.get_component(entity, Projectile)
            
            if projectile:
                projectile.time_alive += dt
                
                if projectile.is_expired:
                    self.entities.destroy_entity(entity)
    
    def _fire_weapon(
        self,
        entity: Entity,
        weapon: Weapon,
        transform: Transform
    ) -> None:
        """Fire a weapon based on its type."""
        # Consume ammo if applicable
        if weapon.max_ammo > 0:
            weapon.ammo -= 1
        
        # Set cooldown
        weapon.cooldown = 1.0 / weapon.fire_rate
        
        # Determine if player-owned
        is_player = self.entities.has_component(entity, PlayerTag)
        
        # Fire based on weapon type
        if weapon.weapon_type == WeaponType.SINGLE:
            self._spawn_projectile(entity, weapon, transform, 0, is_player)
        
        elif weapon.weapon_type == WeaponType.SHOTGUN:
            spread_per_bullet = weapon.spread / max(1, weapon.bullet_count - 1)
            start_angle = -weapon.spread / 2
            
            for i in range(weapon.bullet_count):
                angle_offset = start_angle + (spread_per_bullet * i)
                # Add some random variation
                angle_offset += random.uniform(-3, 3)
                self._spawn_projectile(entity, weapon, transform, angle_offset, is_player)
        
        elif weapon.weapon_type == WeaponType.BURST:
            weapon.burst_remaining = weapon.burst_count - 1
            weapon.burst_cooldown = weapon.burst_delay
            self._spawn_projectile(entity, weapon, transform, 0, is_player)
        
        elif weapon.weapon_type == WeaponType.RAPID:
            # Same as single but relies on high fire_rate
            angle_offset = random.uniform(-weapon.spread/2, weapon.spread/2)
            self._spawn_projectile(entity, weapon, transform, angle_offset, is_player)
        
        elif weapon.weapon_type == WeaponType.ROCKET:
            # Slower, larger projectile
            self._spawn_projectile(entity, weapon, transform, 0, is_player, size_mult=2.0)
    
    def _fire_burst_shot(
        self,
        entity: Entity,
        weapon: Weapon,
        transform: Transform
    ) -> None:
        """Fire a single shot in a burst."""
        is_player = self.entities.has_component(entity, PlayerTag)
        self._spawn_projectile(entity, weapon, transform, 0, is_player)
        
        weapon.burst_remaining -= 1
        if weapon.burst_remaining > 0:
            weapon.burst_cooldown = weapon.burst_delay
    
    def _spawn_projectile(
        self,
        owner: Entity,
        weapon: Weapon,
        owner_transform: Transform,
        angle_offset: float,
        is_player: bool,
        size_mult: float = 1.0
    ) -> Entity:
        """Spawn a projectile entity."""
        # Calculate spawn position (slightly in front of owner)
        spawn_distance = 25.0
        angle = owner_transform.angle + angle_offset
        rad = math.radians(angle)
        
        spawn_x = owner_transform.x + math.cos(rad) * spawn_distance
        spawn_y = owner_transform.y + math.sin(rad) * spawn_distance
        
        # Calculate velocity
        vx = math.cos(rad) * weapon.projectile_speed
        vy = math.sin(rad) * weapon.projectile_speed
        
        # Create projectile entity
        proj_entity = self.entities.create_entity()
        
        # Transform
        self.entities.add_component(proj_entity, Transform(
            x=spawn_x,
            y=spawn_y,
            angle=angle
        ))
        
        # Velocity
        self.entities.add_component(proj_entity, Velocity(
            vx=vx,
            vy=vy
        ))
        
        # Projectile data
        proj = Projectile(
            owner_id=owner.id,
            damage=weapon.damage,
            lifetime=weapon.range / weapon.projectile_speed,
            is_explosive=(weapon.weapon_type == WeaponType.ROCKET)
        )
        self.entities.add_component(proj_entity, proj)
        
        # Renderable
        self.entities.add_component(proj_entity, Renderable(
            shape=RenderShape.CIRCLE,
            color=weapon.projectile_color,
            outline_color=weapon.projectile_color,
            size=weapon.projectile_size * size_mult,
            layer=RenderLayer.PROJECTILE
        ))
        
        # Collider
        collision_layer = CollisionMask.PLAYER_PROJECTILE if is_player else CollisionMask.ENEMY_PROJECTILE
        collision_mask = CollisionMask.ENEMY | CollisionMask.OBSTACLE if is_player else CollisionMask.PLAYER | CollisionMask.OBSTACLE
        
        self.entities.add_component(proj_entity, Collider(
            collider_type=ColliderType.CIRCLE,
            radius=5.0 * weapon.projectile_size * size_mult,
            layer=collision_layer,
            mask=collision_mask,
            is_trigger=True  # Projectiles don't push things
        ))
        
        # Tag
        self.entities.add_component(proj_entity, ProjectileTag(
            is_player_owned=is_player
        ))
        self.entities.add_tag(proj_entity, "projectile")
        
        # Emit event
        self.events.emit(ProjectileFiredEvent(
            projectile_id=proj_entity.id,
            owner_id=owner.id,
            x=spawn_x,
            y=spawn_y,
            angle=angle
        ))
        
        return proj_entity
