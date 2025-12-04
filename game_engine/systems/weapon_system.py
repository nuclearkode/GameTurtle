"""WeaponSystem: handles weapon cooldowns and projectile spawning."""

import math
import random
from ..core.system import GameSystem
from ..core.component import Transform, Weapon, Projectile, Renderable, Collider, Physics


class WeaponSystem(GameSystem):
    """Manages weapon firing and projectiles."""
    
    def __init__(self, entity_manager, component_registry):
        super().__init__(entity_manager, component_registry)
        self.priority = 4  # Run after AI, before collisions
    
    def update(self, dt: float):
        """Update weapon cooldowns and handle firing."""
        # Get all entities with Weapon and Transform
        entity_ids = self.component_registry.get_entities_with("Weapon", "Transform")
        
        for entity_id in entity_ids:
            weapon = self.entity_manager.get_component(entity_id, "Weapon")
            transform = self.entity_manager.get_component(entity_id, "Transform")
            
            if not weapon or not transform:
                continue
            
            # Update cooldown
            if weapon.cooldown_remaining > 0:
                weapon.cooldown_remaining -= dt
            
            # Check if weapon should fire (handled by AI or player input)
            # Actual firing is triggered externally via fire_weapon method
    
    def fire_weapon(self, entity_id: str, target_angle: Optional[float] = None):
        """Fire a weapon for an entity."""
        weapon = self.entity_manager.get_component(entity_id, "Weapon")
        transform = self.entity_manager.get_component(entity_id, "Transform")
        
        if not weapon or not transform:
            return False
        
        if not weapon.can_fire():
            return False
        
        # Use transform angle if target_angle not provided
        fire_angle = target_angle if target_angle is not None else transform.angle
        
        # Reset cooldown
        weapon.cooldown_remaining = 1.0 / weapon.fire_rate
        
        # Spawn projectiles based on weapon type
        if weapon.weapon_type == "single":
            self._spawn_projectile(entity_id, transform, fire_angle, weapon)
        elif weapon.weapon_type == "shotgun":
            # Multiple projectiles with spread
            for i in range(weapon.bullet_count):
                spread_offset = (i - weapon.bullet_count / 2) * weapon.spread
                self._spawn_projectile(entity_id, transform, fire_angle + spread_offset, weapon)
        elif weapon.weapon_type == "burst":
            # Fire multiple shots in quick succession (simplified - fires all at once)
            for i in range(weapon.bullet_count):
                spread_offset = (i - weapon.bullet_count / 2) * (weapon.spread / weapon.bullet_count)
                self._spawn_projectile(entity_id, transform, fire_angle + spread_offset, weapon)
        elif weapon.weapon_type == "beam":
            # Beam weapon (spawns fast, short-lived projectile)
            beam_weapon = weapon
            beam_weapon.projectile_speed *= 2
            beam_weapon.damage *= 0.5
            self._spawn_projectile(entity_id, transform, fire_angle, beam_weapon)
            beam_weapon.projectile_speed /= 2
            beam_weapon.damage /= 0.5
        
        return True
    
    def _spawn_projectile(
        self, owner_id: str, owner_transform: Transform,
        angle: float, weapon: Weapon
    ):
        """Spawn a projectile."""
        # Add spread randomness
        spread_rad = math.radians(weapon.spread)
        angle_rad = math.radians(angle) + random.uniform(-spread_rad / 2, spread_rad / 2)
        
        # Calculate velocity
        speed = weapon.projectile_speed
        vx = math.cos(angle_rad) * speed
        vy = math.sin(angle_rad) * speed
        
        # Spawn position (slightly ahead of owner)
        spawn_distance = 20
        spawn_x = owner_transform.x + math.cos(angle_rad) * spawn_distance
        spawn_y = owner_transform.y + math.sin(angle_rad) * spawn_distance
        
        # Create projectile entity
        projectile_id = self.entity_manager.create_entity()
        
        # Add components
        from ..core.component import Transform, Projectile, Renderable, Collider, Physics
        
        transform = Transform(
            x=spawn_x,
            y=spawn_y,
            vx=vx,
            vy=vy,
            angle=math.degrees(angle_rad)
        )
        self.entity_manager.add_component(projectile_id, transform)
        self.component_registry.register_component(projectile_id, "Transform")
        
        projectile = Projectile(
            owner_id=owner_id,
            damage=weapon.damage,
            lifetime=2.0,
            time_alive=0.0
        )
        self.entity_manager.add_component(projectile_id, projectile)
        self.component_registry.register_component(projectile_id, "Projectile")
        
        renderable = Renderable(
            shape="circle",
            color="yellow",
            size=0.3
        )
        self.entity_manager.add_component(projectile_id, renderable)
        self.component_registry.register_component(projectile_id, "Renderable")
        
        collider = Collider(
            radius=5.0,
            mask=0x0006,  # Can collide with player (0x0004) and enemy (0x0002)
            tags={"projectile"}
        )
        self.entity_manager.add_component(projectile_id, collider)
        self.component_registry.register_component(projectile_id, "Collider")
        
        physics = Physics(
            mass=0.1,
            friction=1.0,  # No friction for projectiles
            max_speed=speed * 1.5,
            acceleration=0.0
        )
        self.entity_manager.add_component(projectile_id, physics)
        self.component_registry.register_component(projectile_id, "Physics")
    
    def update_projectiles(self, dt: float):
        """Update projectile lifetimes."""
        entity_ids = self.component_registry.get_entities_with("Projectile", "Transform")
        
        for entity_id in entity_ids:
            projectile = self.entity_manager.get_component(entity_id, "Projectile")
            if projectile:
                projectile.time_alive += dt
                if projectile.time_alive >= projectile.lifetime:
                    self.entity_manager.destroy_entity(entity_id)
