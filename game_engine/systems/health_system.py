"""HealthSystem: handles damage, death, and status effects."""

from ..core.system import GameSystem
from ..core.component import Health, Shield, StatusEffects


class HealthSystem(GameSystem):
    """Manages health, shields, and status effects."""
    
    def __init__(self, entity_manager, component_registry):
        super().__init__(entity_manager, component_registry)
        self.priority = 5  # Run after collisions
    
    def update(self, dt: float):
        """Update health, shields, and status effects."""
        # Update shields
        entity_ids = self.component_registry.get_entities_with("Shield")
        for entity_id in entity_ids:
            shield = self.entity_manager.get_component(entity_id, "Shield")
            if shield:
                shield.time_since_damage += dt
                if shield.time_since_damage >= shield.recharge_delay:
                    # Recharge shield
                    shield.hp = min(shield.max_hp, shield.hp + shield.recharge_rate * dt)
        
        # Update status effects
        entity_ids = self.component_registry.get_entities_with("StatusEffects")
        for entity_id in entity_ids:
            status = self.entity_manager.get_component(entity_id, "StatusEffects")
            if status:
                # Update timers
                if status.slow_duration > 0:
                    status.slow_duration -= dt
                    if status.slow_duration <= 0:
                        status.slow = 1.0
                
                if status.stun > 0:
                    status.stun -= dt
                
                if status.burn_duration > 0:
                    status.burn_duration -= dt
                    # Apply burn damage
                    health = self.entity_manager.get_component(entity_id, "Health")
                    if health:
                        health.hp -= status.burn * dt
                    if status.burn_duration <= 0:
                        status.burn = 0.0
        
        # Check for death
        entity_ids = self.component_registry.get_entities_with("Health")
        for entity_id in entity_ids:
            health = self.entity_manager.get_component(entity_id, "Health")
            if health and not health.is_alive():
                # Entity is dead
                self._handle_death(entity_id)
    
    def _handle_death(self, entity_id: str):
        """Handle entity death."""
        # Mark for destruction
        self.entity_manager.destroy_entity(entity_id)
        
        # Could spawn particles, loot, etc. here
