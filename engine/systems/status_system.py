"""
Status Effect System - Process active status effects.

Handles ticking down effect durations, applying DoT damage,
and updating effect modifiers.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from ..core.system import GameSystem, SystemPriority
from ..core.events import DamageEvent
from ..components.status import StatusEffects, StatusEffect
from ..components.health import Health

if TYPE_CHECKING:
    from ..core.entity import Entity


class StatusEffectSystem(GameSystem):
    """
    Processes status effects each frame.
    
    Features:
    - Duration countdown
    - Damage over time (DoT) effects
    - Modifier recalculation
    - Effect expiration cleanup
    """
    
    def __init__(self):
        super().__init__(priority=SystemPriority.STATUS_EFFECT)
    
    def update(self, dt: float) -> None:
        """Process all status effects."""
        for entity in self.entities.get_entities_with(StatusEffects):
            status = self.entities.get_component(entity, StatusEffects)
            if not status:
                continue
            
            expired = []
            
            for effect_type, data in status.active_effects.items():
                # Update duration
                data.time_remaining -= dt
                
                if data.is_expired:
                    expired.append(effect_type)
                    continue
                
                # Process DoT effects
                if effect_type in (StatusEffect.BURN, StatusEffect.POISON, StatusEffect.BLEED):
                    self._process_dot(entity, data, dt)
            
            # Remove expired effects
            for effect_type in expired:
                status.remove_effect(effect_type)
    
    def _process_dot(self, entity: Entity, data, dt: float) -> None:
        """Process damage over time effect."""
        data.tick_timer += dt
        
        if data.tick_timer >= data.tick_rate:
            data.tick_timer -= data.tick_rate
            
            # Apply damage
            damage = data.magnitude * data.stacks
            
            self.events.emit(DamageEvent(
                target_id=entity.id,
                source_id=data.source_id,
                amount=damage,
                damage_type="dot"
            ))
    
    def apply_effect(
        self,
        entity: Entity,
        effect_type: StatusEffect,
        duration: float,
        magnitude: float = 1.0,
        source_id: str = ""
    ) -> bool:
        """
        Apply a status effect to an entity.
        
        Returns True if effect was applied, False if entity has no StatusEffects.
        """
        status = self.entities.get_component(entity, StatusEffects)
        if not status:
            return False
        
        status.apply_effect(
            effect_type=effect_type,
            duration=duration,
            magnitude=magnitude,
            source_id=source_id
        )
        return True
    
    def remove_effect(self, entity: Entity, effect_type: StatusEffect) -> bool:
        """Remove a status effect from an entity."""
        status = self.entities.get_component(entity, StatusEffects)
        if status:
            return status.remove_effect(effect_type)
        return False
    
    def clear_effects(self, entity: Entity, debuffs_only: bool = False) -> None:
        """Clear effects from an entity."""
        status = self.entities.get_component(entity, StatusEffects)
        if status:
            if debuffs_only:
                status.clear_debuffs()
            else:
                status.clear_all()
