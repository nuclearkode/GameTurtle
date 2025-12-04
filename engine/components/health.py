"""
Health and Shield components - Combat state.

These components track an entity's vitality and defensive capabilities.
The HealthSystem processes damage events and handles death.
"""

from dataclasses import dataclass, field


@dataclass
class Health:
    """
    Health points and damage tracking.
    
    Attributes:
        hp: Current health points
        max_hp: Maximum health points
        armor: Damage reduction (0.0 = no reduction, 1.0 = immune)
        is_invulnerable: If True, cannot take damage
        invulnerability_timer: Time remaining for temporary invulnerability
        
    Damage Flow:
        1. Damage is reduced by armor: actual = damage * (1 - armor)
        2. If entity has Shield, shield absorbs damage first
        3. Remaining damage reduces HP
        4. If HP <= 0, entity is marked for destruction
        
    Invulnerability:
        - Used for brief immunity after taking damage (i-frames)
        - Or for special states (spawning, cutscenes)
    """
    hp: float = 100.0
    max_hp: float = 100.0
    armor: float = 0.0
    is_invulnerable: bool = False
    invulnerability_timer: float = 0.0
    
    # Damage tracking for effects
    last_damage_time: float = field(default=0.0, repr=False)
    last_damage_source: str = field(default="", repr=False)
    damage_this_frame: float = field(default=0.0, repr=False)
    
    @property
    def is_alive(self) -> bool:
        """Check if entity is still alive."""
        return self.hp > 0
    
    @property
    def health_percent(self) -> float:
        """Get health as a percentage (0.0 to 1.0)."""
        if self.max_hp <= 0:
            return 0.0
        return max(0.0, min(1.0, self.hp / self.max_hp))
    
    def heal(self, amount: float) -> float:
        """
        Heal the entity.
        
        Returns:
            Actual amount healed (may be less if already at max)
        """
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp
    
    def take_damage(self, amount: float, source_id: str = "") -> float:
        """
        Apply damage to this entity.
        
        Note: This is a convenience method. In ECS, the HealthSystem
        typically handles damage application via DamageEvents.
        
        Returns:
            Actual damage taken (after armor)
        """
        if self.is_invulnerable or self.invulnerability_timer > 0:
            return 0.0
        
        # Apply armor reduction
        actual_damage = amount * (1.0 - min(0.99, self.armor))
        
        self.hp -= actual_damage
        self.damage_this_frame += actual_damage
        self.last_damage_source = source_id
        
        return actual_damage


@dataclass
class Shield:
    """
    Energy shield that absorbs damage before health.
    
    Attributes:
        hp: Current shield points
        max_hp: Maximum shield points
        recharge_rate: Shield points regenerated per second
        recharge_delay: Seconds after taking damage before recharge starts
        damage_efficiency: How much shield damage prevents HP damage (1.0 = 100%)
        
    Shield Flow:
        1. When taking damage, shield absorbs first
        2. If shield breaks, overflow goes to health
        3. After not taking damage for recharge_delay seconds, shield regenerates
        
    Example:
        100 damage, 50 shield, efficiency=1.0:
        - Shield takes 50 damage (now 0)
        - Health takes remaining 50 damage
        
        100 damage, 50 shield, efficiency=0.5:
        - Shield takes 50 damage but only blocks 25
        - Health takes 75 damage
    """
    hp: float = 50.0
    max_hp: float = 50.0
    recharge_rate: float = 10.0
    recharge_delay: float = 2.0
    damage_efficiency: float = 1.0
    
    # Tracking for recharge logic
    time_since_damage: float = field(default=999.0, repr=False)
    is_broken: bool = field(default=False, repr=False)
    
    @property
    def is_active(self) -> bool:
        """Check if shield is active (has points)."""
        return self.hp > 0
    
    @property
    def shield_percent(self) -> float:
        """Get shield as a percentage (0.0 to 1.0)."""
        if self.max_hp <= 0:
            return 0.0
        return max(0.0, min(1.0, self.hp / self.max_hp))
    
    def absorb_damage(self, damage: float) -> float:
        """
        Try to absorb damage with shield.
        
        Returns:
            Amount of damage that got through to health
        """
        if self.hp <= 0:
            return damage
        
        # Shield absorbs damage
        absorbed = min(self.hp, damage)
        self.hp -= absorbed
        self.time_since_damage = 0.0
        
        if self.hp <= 0:
            self.is_broken = True
        
        # Return damage that got through
        blocked = absorbed * self.damage_efficiency
        return damage - blocked
    
    def update_recharge(self, dt: float) -> None:
        """
        Update shield recharge.
        Called by HealthSystem each frame.
        """
        self.time_since_damage += dt
        
        if self.time_since_damage >= self.recharge_delay and self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + self.recharge_rate * dt)
            if self.hp > 0:
                self.is_broken = False
