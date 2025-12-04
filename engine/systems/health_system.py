"""
Health System

Handles damage application, death, and entity destruction.
"""

from engine.core.system import GameSystem
from engine.core.component import Health, Shield, Projectile, Transform, Player, Enemy
from engine.systems.collision_system import CollisionSystem
import time


class HealthSystem(GameSystem):
    """
    Manages health, shields, damage, and death.
    
    Responsibilities:
    - Process collision events from CollisionSystem
    - Apply damage to entities
    - Handle shields (absorb damage, recharge)
    - Manage invulnerability frames
    - Trigger death/destruction
    """
    
    def __init__(self, entity_manager, collision_system: CollisionSystem, priority: int = 30):
        super().__init__(entity_manager, priority)
        self.collision_system = collision_system
        self.current_time = time.time()
    
    def update(self, dt: float) -> None:
        """Update health, shields, and process damage."""
        self.current_time += dt
        
        # Update invulnerability timers
        self._update_invulnerability(dt)
        
        # Update shields
        self._update_shields(dt)
        
        # Process collision-based damage
        self._process_collision_damage()
        
        # Check for deaths
        self._process_deaths()
    
    def _update_invulnerability(self, dt: float) -> None:
        """Update invulnerability timers."""
        health_entities = self.entity_manager.query_entities(Health)
        
        for entity in health_entities:
            health = entity.get_component(Health)
            if health.invulnerable_time > 0:
                health.invulnerable_time -= dt
    
    def _update_shields(self, dt: float) -> None:
        """Update shield recharge."""
        shield_entities = self.entity_manager.query_entities(Shield)
        
        for entity in shield_entities:
            shield = entity.get_component(Shield)
            
            # Recharge if enough time has passed since last damage
            time_since_damage = self.current_time - shield.last_damage_time
            
            if time_since_damage >= shield.recharge_delay and shield.hp < shield.max_hp:
                shield.hp += shield.recharge_rate * dt
                shield.hp = min(shield.hp, shield.max_hp)
    
    def _process_collision_damage(self) -> None:
        """Process damage from collisions."""
        for collision in self.collision_system.collision_events:
            entity_a = self.entity_manager.get_entity(collision.entity_a_id)
            entity_b = self.entity_manager.get_entity(collision.entity_b_id)
            
            if not entity_a or not entity_b:
                continue
            
            # Check for projectile collisions
            projectile_a = entity_a.get_component(Projectile)
            projectile_b = entity_b.get_component(Projectile)
            
            # Projectile A hits entity B
            if projectile_a and projectile_a.owner_id != entity_b.id:
                self._apply_projectile_damage(projectile_a, entity_a, entity_b)
            
            # Projectile B hits entity A
            if projectile_b and projectile_b.owner_id != entity_a.id:
                self._apply_projectile_damage(projectile_b, entity_b, entity_a)
    
    def _apply_projectile_damage(self, projectile: Projectile, 
                                 projectile_entity, target_entity) -> None:
        """Apply damage from a projectile to a target."""
        # Check if target has already been hit by this projectile (for piercing)
        if target_entity.id in projectile.hits:
            return
        
        # Mark as hit
        projectile.hits.add(target_entity.id)
        
        # Apply damage
        self.apply_damage(target_entity.id, projectile.damage)
        
        # Destroy projectile if it can't pierce more enemies
        if projectile.piercing <= 0:
            self.entity_manager.destroy_entity(projectile_entity.id)
        else:
            projectile.piercing -= 1
    
    def apply_damage(self, entity_id: str, damage: float) -> float:
        """
        Apply damage to an entity.
        
        Args:
            entity_id: Target entity
            damage: Raw damage amount
        
        Returns:
            Actual damage dealt (after shields, armor, invulnerability)
        """
        entity = self.entity_manager.get_entity(entity_id)
        if not entity:
            return 0.0
        
        health = entity.get_component(Health)
        if not health or health.is_dead:
            return 0.0
        
        # Check invulnerability
        if health.invulnerable_time > 0:
            return 0.0
        
        # Apply armor reduction
        actual_damage = damage * (1.0 - health.armor)
        
        # Try to absorb with shield first
        shield = entity.get_component(Shield)
        if shield and shield.hp > 0:
            shield_damage = min(actual_damage, shield.hp)
            shield.hp -= shield_damage
            shield.last_damage_time = self.current_time
            actual_damage -= shield_damage
        
        # Apply remaining damage to health
        health.hp -= actual_damage
        
        # Set invulnerability frames if hit
        if actual_damage > 0 and health.invulnerable_duration > 0:
            health.invulnerable_time = health.invulnerable_duration
        
        # Clamp health
        health.hp = max(0, health.hp)
        
        return actual_damage
    
    def heal(self, entity_id: str, amount: float) -> float:
        """
        Heal an entity.
        
        Returns:
            Actual amount healed.
        """
        entity = self.entity_manager.get_entity(entity_id)
        if not entity:
            return 0.0
        
        health = entity.get_component(Health)
        if not health:
            return 0.0
        
        old_hp = health.hp
        health.hp = min(health.hp + amount, health.max_hp)
        return health.hp - old_hp
    
    def restore_shield(self, entity_id: str, amount: float) -> float:
        """
        Restore shield energy.
        
        Returns:
            Actual amount restored.
        """
        entity = self.entity_manager.get_entity(entity_id)
        if not entity:
            return 0.0
        
        shield = entity.get_component(Shield)
        if not shield:
            return 0.0
        
        old_hp = shield.hp
        shield.hp = min(shield.hp + amount, shield.max_hp)
        return shield.hp - old_hp
    
    def _process_deaths(self) -> None:
        """Check for dead entities and destroy them."""
        health_entities = self.entity_manager.query_entities(Health)
        
        for entity in health_entities:
            health = entity.get_component(Health)
            
            if health.hp <= 0 and not health.is_dead:
                health.is_dead = True
                self._on_entity_death(entity)
    
    def _on_entity_death(self, entity) -> None:
        """Handle entity death."""
        # Update player score if this was an enemy
        enemy = entity.get_component(Enemy)
        if enemy:
            self._add_score(enemy.points)
        
        # Spawn death particle effects (TODO: integrate with ParticleSystem)
        # ...
        
        # Destroy entity
        self.entity_manager.destroy_entity(entity.id)
    
    def _add_score(self, points: int) -> None:
        """Add points to player score."""
        player_entities = self.entity_manager.query_entities(Player)
        if player_entities:
            player = player_entities[0].get_component(Player)
            player.score += points
