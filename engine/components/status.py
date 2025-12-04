"""
Status Effects component - Temporary buffs and debuffs.

Status effects modify entity behavior/stats for a duration.
The StatusEffectSystem processes these each frame.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Optional


class StatusEffect(Enum):
    """Types of status effects."""
    # Debuffs
    SLOW = auto()        # Reduce movement speed
    STUN = auto()        # Cannot move or act
    BURN = auto()        # Damage over time (fire)
    POISON = auto()      # Damage over time (slower)
    FREEZE = auto()      # Slowed + cannot shoot
    BLEED = auto()       # Damage on movement
    
    # Buffs
    SPEED_BOOST = auto()   # Increased movement speed
    DAMAGE_BOOST = auto()  # Increased damage
    SHIELD_BOOST = auto()  # Temporary shield increase
    INVULNERABLE = auto()  # Cannot take damage
    RAPID_FIRE = auto()    # Increased fire rate


@dataclass
class StatusEffectData:
    """
    Data for a single active status effect.
    
    Attributes:
        effect_type: The type of effect
        duration: Total duration in seconds
        time_remaining: Time left before effect expires
        magnitude: Strength of the effect (interpretation varies by type)
        source_id: Entity that applied this effect
        stacks: Number of stacks (some effects stack)
        tick_rate: For DoT effects, damage is applied every tick_rate seconds
        tick_timer: Timer for next DoT tick
    
    Magnitude Interpretations:
        SLOW: Speed multiplier (0.5 = 50% speed)
        STUN: Not used (binary effect)
        BURN/POISON: Damage per second
        SPEED_BOOST: Speed multiplier (1.5 = 50% faster)
        DAMAGE_BOOST: Damage multiplier
    """
    effect_type: StatusEffect
    duration: float
    time_remaining: float
    magnitude: float = 1.0
    source_id: str = ""
    stacks: int = 1
    max_stacks: int = 1
    tick_rate: float = 0.5
    tick_timer: float = 0.0
    
    @property
    def is_expired(self) -> bool:
        """Check if effect has expired."""
        return self.time_remaining <= 0
    
    @property
    def progress(self) -> float:
        """Get effect progress (0.0 = just started, 1.0 = expired)."""
        if self.duration <= 0:
            return 1.0
        return 1.0 - (self.time_remaining / self.duration)


@dataclass
class StatusEffects:
    """
    Container for all active status effects on an entity.
    
    The StatusEffectSystem iterates over entities with this component
    and processes each active effect.
    """
    active_effects: Dict[StatusEffect, StatusEffectData] = field(
        default_factory=dict
    )
    
    # Cached modifiers (updated when effects change)
    speed_modifier: float = 1.0
    damage_modifier: float = 1.0
    fire_rate_modifier: float = 1.0
    
    # Flags for quick checks
    is_stunned: bool = False
    is_invulnerable: bool = False
    can_move: bool = True
    can_shoot: bool = True
    
    def apply_effect(
        self,
        effect_type: StatusEffect,
        duration: float,
        magnitude: float = 1.0,
        source_id: str = "",
        max_stacks: int = 1,
        tick_rate: float = 0.5
    ) -> None:
        """
        Apply or refresh a status effect.
        
        If the effect already exists:
        - Refresh duration if new duration is longer
        - Add stacks up to max_stacks
        - Update magnitude if higher
        """
        if effect_type in self.active_effects:
            existing = self.active_effects[effect_type]
            # Refresh duration
            existing.time_remaining = max(existing.time_remaining, duration)
            # Stack if applicable
            if existing.stacks < max_stacks:
                existing.stacks += 1
            # Update magnitude if higher
            if magnitude > existing.magnitude:
                existing.magnitude = magnitude
        else:
            self.active_effects[effect_type] = StatusEffectData(
                effect_type=effect_type,
                duration=duration,
                time_remaining=duration,
                magnitude=magnitude,
                source_id=source_id,
                stacks=1,
                max_stacks=max_stacks,
                tick_rate=tick_rate
            )
        
        self._update_modifiers()
    
    def remove_effect(self, effect_type: StatusEffect) -> bool:
        """Remove a status effect. Returns True if it was present."""
        if effect_type in self.active_effects:
            del self.active_effects[effect_type]
            self._update_modifiers()
            return True
        return False
    
    def has_effect(self, effect_type: StatusEffect) -> bool:
        """Check if an effect is active."""
        return effect_type in self.active_effects
    
    def get_effect(self, effect_type: StatusEffect) -> Optional[StatusEffectData]:
        """Get data for an active effect."""
        return self.active_effects.get(effect_type)
    
    def clear_all(self) -> None:
        """Remove all status effects."""
        self.active_effects.clear()
        self._update_modifiers()
    
    def clear_debuffs(self) -> None:
        """Remove all negative effects."""
        debuffs = [StatusEffect.SLOW, StatusEffect.STUN, StatusEffect.BURN,
                   StatusEffect.POISON, StatusEffect.FREEZE, StatusEffect.BLEED]
        for debuff in debuffs:
            self.active_effects.pop(debuff, None)
        self._update_modifiers()
    
    def _update_modifiers(self) -> None:
        """Recalculate cached modifier values."""
        self.speed_modifier = 1.0
        self.damage_modifier = 1.0
        self.fire_rate_modifier = 1.0
        self.is_stunned = False
        self.is_invulnerable = False
        self.can_move = True
        self.can_shoot = True
        
        for effect_type, data in self.active_effects.items():
            if effect_type == StatusEffect.SLOW:
                self.speed_modifier *= data.magnitude
            elif effect_type == StatusEffect.STUN:
                self.is_stunned = True
                self.can_move = False
                self.can_shoot = False
            elif effect_type == StatusEffect.FREEZE:
                self.speed_modifier *= 0.3
                self.can_shoot = False
            elif effect_type == StatusEffect.SPEED_BOOST:
                self.speed_modifier *= data.magnitude
            elif effect_type == StatusEffect.DAMAGE_BOOST:
                self.damage_modifier *= data.magnitude
            elif effect_type == StatusEffect.RAPID_FIRE:
                self.fire_rate_modifier *= data.magnitude
            elif effect_type == StatusEffect.INVULNERABLE:
                self.is_invulnerable = True
