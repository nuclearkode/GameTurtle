"""
PowerUp System

Manages power-up pickups and their effects.
"""

from engine.core.system import GameSystem
from engine.core.component import PowerUp, Transform, Collider, Player, Health, Shield, Weapon, Physics
from engine.systems.collision_system import CollisionSystem


class PowerUpSystem(GameSystem):
    """
    Manages power-up pickups.
    
    Responsibilities:
    - Update power-up lifetimes
    - Detect player collisions with power-ups
    - Apply power-up effects
    """
    
    def __init__(self, entity_manager, collision_system: CollisionSystem, priority: int = 60):
        super().__init__(entity_manager, priority)
        self.collision_system = collision_system
    
    def update(self, dt: float) -> None:
        """Update power-ups and check for pickups."""
        # Update power-up lifetimes
        powerups = self.entity_manager.query_entities(PowerUp)
        
        for entity in powerups:
            powerup = entity.get_component(PowerUp)
            powerup.time_alive += dt
            
            # Despawn if lifetime exceeded
            if powerup.time_alive >= powerup.lifetime:
                self.entity_manager.destroy_entity(entity.id)
        
        # Check for player collisions with power-ups
        self._check_pickups()
    
    def _check_pickups(self) -> None:
        """Check if player has picked up any power-ups."""
        # Get player
        player_entities = self.entity_manager.query_entities(Player, Transform)
        if not player_entities:
            return
        
        player_entity = player_entities[0]
        
        # Check collisions
        for collision in self.collision_system.collision_events:
            # Check if one entity is the player
            player_involved = False
            powerup_entity = None
            
            if collision.entity_a_id == player_entity.id:
                player_involved = True
                powerup_entity = self.entity_manager.get_entity(collision.entity_b_id)
            elif collision.entity_b_id == player_entity.id:
                player_involved = True
                powerup_entity = self.entity_manager.get_entity(collision.entity_a_id)
            
            if not player_involved or not powerup_entity:
                continue
            
            # Check if other entity is a power-up
            powerup = powerup_entity.get_component(PowerUp)
            if not powerup:
                continue
            
            # Apply power-up effect
            self._apply_powerup(player_entity, powerup)
            
            # Destroy power-up
            self.entity_manager.destroy_entity(powerup_entity.id)
    
    def _apply_powerup(self, player_entity, powerup: PowerUp) -> None:
        """Apply power-up effect to player."""
        if powerup.type == "health":
            health = player_entity.get_component(Health)
            if health:
                health.hp = min(health.hp + powerup.value, health.max_hp)
        
        elif powerup.type == "shield":
            shield = player_entity.get_component(Shield)
            if shield:
                shield.hp = min(shield.hp + powerup.value, shield.max_hp)
        
        elif powerup.type == "weapon_upgrade":
            weapon = player_entity.get_component(Weapon)
            if weapon:
                weapon.fire_rate *= 1.2  # 20% faster fire rate
        
        elif powerup.type == "speed":
            physics = player_entity.get_component(Physics)
            if physics:
                physics.max_speed *= 1.1  # 10% faster movement
        
        elif powerup.type == "damage":
            weapon = player_entity.get_component(Weapon)
            if weapon:
                weapon.damage *= 1.2  # 20% more damage
