"""
HealthSystem - handles health, shields, status effects, death.
"""

from game_engine.core.system import GameSystem
from game_engine.core.component import Health, Shield, StatusEffects


class HealthSystem(GameSystem):
    """
    Manages health, shields, status effects, and death.
    """
    
    def update(self, dt: float) -> None:
        """Update health, shields, and status effects"""
        # Update status effects
        entities_with_status = self.registry.get_entities_with(StatusEffects)
        for entity_id in entities_with_status:
            status = self.entity_manager.get_component(entity_id, StatusEffects)
            if not status:
                continue
            
            # Update timers
            status.slow_timer = max(0.0, status.slow_timer - dt)
            status.stun_timer = max(0.0, status.stun_timer - dt)
            status.burn_timer = max(0.0, status.burn_timer - dt)
            
            # Apply burn damage
            if status.burn_timer > 0:
                health = self.entity_manager.get_component(entity_id, Health)
                if health:
                    health.hp -= status.burn_dps * dt
        
        # Update shields
        entities_with_shield = self.registry.get_entities_with(Shield)
        for entity_id in entities_with_shield:
            shield = self.entity_manager.get_component(entity_id, Shield)
            if not shield:
                continue
            
            # Recharge shield if not taking damage recently
            # Note: last_damage_time should be updated when damage is taken
            # For now, we'll use a simple timer approach
            if shield.last_damage_time <= 0 and shield.hp < shield.max_hp:
                shield.hp = min(shield.max_hp, shield.hp + shield.recharge_rate * dt)
            elif shield.last_damage_time > 0:
                shield.last_damage_time = max(0.0, shield.last_damage_time - dt)
        
        # Check for death
        entities_with_health = self.registry.get_entities_with(Health)
        for entity_id in entities_with_health:
            health = self.entity_manager.get_component(entity_id, Health)
            if not health:
                continue
            
            # Clamp health
            health.hp = max(0.0, min(health.max_hp, health.hp))
            
            # Check death
            if health.hp <= 0:
                self._handle_death(entity_id)
    
    def _handle_death(self, entity_id: str) -> None:
        """Handle entity death"""
        # Mark for destruction
        self.entity_manager.destroy_entity(entity_id)
        
        # TODO: Spawn particles, loot, etc.
