"""
Permanent Active Upgrade System - Stackable upgrades with degradation.

Design Philosophy:
- Always active = player feels the upgrades every frame
- Stackable = picking up 5 "Damage +" upgrades = 5 stacks visible
- Degradation mechanic = take damage → lose 1 stack of a random upgrade
- Keeps player from becoming unkillable
- Encourages health/defense play
- Risk/reward: grab powerful upgrades but stay healthy
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional
import random


class UpgradeTier(Enum):
    """Upgrade tiers - higher tiers are rarer and more powerful."""
    TIER_1 = 1  # Very Common (Drop Every 1-2 Kills)
    TIER_2 = 2  # Common (Drop Every 3-5 Kills)
    TIER_3 = 3  # Uncommon (Drop Every 8-15 Kills, or Boss Waves)
    TIER_4 = 4  # Rare (Drop on Boss Waves or Special Events)
    TIER_5 = 5  # Epic (Boss-Only Drops, Feels Legendary)


class UpgradeType(Enum):
    """All available upgrade types."""
    # Tier 1: Very Common
    DAMAGE_PLUS = auto()
    FIRE_RATE_PLUS = auto()
    SPEED_PLUS = auto()
    HP_PLUS = auto()
    
    # Tier 2: Common
    CRITICAL_CHANCE = auto()
    ARMOR_PLUS = auto()
    SHIELD_REGEN = auto()
    MULTISHOT = auto()
    PROJECTILE_SIZE = auto()
    ACCURACY = auto()
    
    # Tier 3: Uncommon
    PIERCING = auto()
    RICOCHET = auto()
    KNOCKBACK = auto()
    WALL_PENETRATION = auto()
    LIFESTEAL = auto()
    THORNS = auto()
    REGENERATION = auto()
    
    # Tier 4: Rare
    DOUBLE_JUMP = auto()
    SLOW_AURA = auto()
    CRIT_MULTIPLIER = auto()
    POISON_TOUCH = auto()
    HOMING = auto()
    EXPLOSIVE_IMPACT = auto()
    EVASION = auto()
    
    # Tier 5: Epic
    BERSERK_MODE = auto()
    TIME_DILATION = auto()
    IMMUNE_FRAME = auto()
    ALLY_DRONE = auto()
    MANA_SHIELD = auto()
    FEEDBACK_LOOP = auto()
    PROBABILITY_FIELD = auto()


@dataclass
class UpgradeDefinition:
    """Definition for an upgrade type."""
    upgrade_type: UpgradeType
    name: str
    description: str
    tier: UpgradeTier
    max_stacks: int
    effect_per_stack: float
    icon: str = "⚡"  # Emoji icon for UI
    
    # Visual properties
    color: str = "#ffffff"
    glow_color: str = "#ffff00"


# Upgrade definitions - organized by tier
UPGRADE_DEFINITIONS: Dict[UpgradeType, UpgradeDefinition] = {
    # TIER 1: Very Common
    UpgradeType.DAMAGE_PLUS: UpgradeDefinition(
        upgrade_type=UpgradeType.DAMAGE_PLUS,
        name="Damage+",
        description="+5% damage per stack",
        tier=UpgradeTier.TIER_1,
        max_stacks=20,
        effect_per_stack=0.05,
        icon="⚔️",
        color="#ff4444",
        glow_color="#ff8888"
    ),
    UpgradeType.FIRE_RATE_PLUS: UpgradeDefinition(
        upgrade_type=UpgradeType.FIRE_RATE_PLUS,
        name="Fire Rate+",
        description="-10% cooldown per stack",
        tier=UpgradeTier.TIER_1,
        max_stacks=15,
        effect_per_stack=0.10,
        icon="🔫",
        color="#ffaa00",
        glow_color="#ffcc44"
    ),
    UpgradeType.SPEED_PLUS: UpgradeDefinition(
        upgrade_type=UpgradeType.SPEED_PLUS,
        name="Speed+",
        description="+10% move speed per stack",
        tier=UpgradeTier.TIER_1,
        max_stacks=10,
        effect_per_stack=0.10,
        icon="🏃",
        color="#00ffff",
        glow_color="#88ffff"
    ),
    UpgradeType.HP_PLUS: UpgradeDefinition(
        upgrade_type=UpgradeType.HP_PLUS,
        name="HP+",
        description="+10 max HP per stack",
        tier=UpgradeTier.TIER_1,
        max_stacks=15,
        effect_per_stack=10.0,
        icon="💚",
        color="#00ff00",
        glow_color="#88ff88"
    ),
    
    # TIER 2: Common
    UpgradeType.CRITICAL_CHANCE: UpgradeDefinition(
        upgrade_type=UpgradeType.CRITICAL_CHANCE,
        name="Critical Chance+",
        description="+3% crit chance per stack",
        tier=UpgradeTier.TIER_2,
        max_stacks=12,
        effect_per_stack=0.03,
        icon="🎯",
        color="#ff00ff",
        glow_color="#ff88ff"
    ),
    UpgradeType.ARMOR_PLUS: UpgradeDefinition(
        upgrade_type=UpgradeType.ARMOR_PLUS,
        name="Armor+",
        description="+3 armor per stack",
        tier=UpgradeTier.TIER_2,
        max_stacks=10,
        effect_per_stack=3.0,
        icon="🛡️",
        color="#888888",
        glow_color="#aaaaaa"
    ),
    UpgradeType.SHIELD_REGEN: UpgradeDefinition(
        upgrade_type=UpgradeType.SHIELD_REGEN,
        name="Shield Regen+",
        description="+0.2 HP/frame regen per stack",
        tier=UpgradeTier.TIER_2,
        max_stacks=8,
        effect_per_stack=0.2,
        icon="🔵",
        color="#4444ff",
        glow_color="#8888ff"
    ),
    UpgradeType.MULTISHOT: UpgradeDefinition(
        upgrade_type=UpgradeType.MULTISHOT,
        name="Multishot+",
        description="+0.25 projectiles per stack",
        tier=UpgradeTier.TIER_2,
        max_stacks=6,
        effect_per_stack=0.25,
        icon="🔥",
        color="#ff8800",
        glow_color="#ffaa44"
    ),
    UpgradeType.PROJECTILE_SIZE: UpgradeDefinition(
        upgrade_type=UpgradeType.PROJECTILE_SIZE,
        name="Projectile Size+",
        description="+2% projectile size per stack",
        tier=UpgradeTier.TIER_2,
        max_stacks=10,
        effect_per_stack=0.02,
        icon="⚪",
        color="#ffff00",
        glow_color="#ffff88"
    ),
    UpgradeType.ACCURACY: UpgradeDefinition(
        upgrade_type=UpgradeType.ACCURACY,
        name="Accuracy+",
        description="-5% weapon spread per stack",
        tier=UpgradeTier.TIER_2,
        max_stacks=8,
        effect_per_stack=0.05,
        icon="🎯",
        color="#00ff88",
        glow_color="#88ffaa"
    ),
    
    # TIER 3: Uncommon
    UpgradeType.PIERCING: UpgradeDefinition(
        upgrade_type=UpgradeType.PIERCING,
        name="Piercing+",
        description="+1 pierce per stack",
        tier=UpgradeTier.TIER_3,
        max_stacks=5,
        effect_per_stack=1.0,
        icon="➡️",
        color="#ff00aa",
        glow_color="#ff88cc"
    ),
    UpgradeType.RICOCHET: UpgradeDefinition(
        upgrade_type=UpgradeType.RICOCHET,
        name="Ricochet+",
        description="+1 bounce per stack",
        tier=UpgradeTier.TIER_3,
        max_stacks=4,
        effect_per_stack=1.0,
        icon="↩️",
        color="#00aaff",
        glow_color="#88ccff"
    ),
    UpgradeType.KNOCKBACK: UpgradeDefinition(
        upgrade_type=UpgradeType.KNOCKBACK,
        name="Knockback+",
        description="+20% knockback per stack",
        tier=UpgradeTier.TIER_3,
        max_stacks=6,
        effect_per_stack=0.20,
        icon="💥",
        color="#ffcc00",
        glow_color="#ffdd44"
    ),
    UpgradeType.WALL_PENETRATION: UpgradeDefinition(
        upgrade_type=UpgradeType.WALL_PENETRATION,
        name="Wall Penetration+",
        description="+1 wall penetration per stack",
        tier=UpgradeTier.TIER_3,
        max_stacks=3,
        effect_per_stack=1.0,
        icon="🧱",
        color="#aa8800",
        glow_color="#ccaa44"
    ),
    UpgradeType.LIFESTEAL: UpgradeDefinition(
        upgrade_type=UpgradeType.LIFESTEAL,
        name="Lifesteal+",
        description="+5% damage as HP per stack",
        tier=UpgradeTier.TIER_3,
        max_stacks=5,
        effect_per_stack=0.05,
        icon="❤️",
        color="#ff0044",
        glow_color="#ff4488"
    ),
    UpgradeType.THORNS: UpgradeDefinition(
        upgrade_type=UpgradeType.THORNS,
        name="Thorns+",
        description="+10% damage reflect per stack",
        tier=UpgradeTier.TIER_3,
        max_stacks=4,
        effect_per_stack=0.10,
        icon="🌵",
        color="#44aa00",
        glow_color="#88cc44"
    ),
    UpgradeType.REGENERATION: UpgradeDefinition(
        upgrade_type=UpgradeType.REGENERATION,
        name="Regeneration+",
        description="+0.1 HP/frame regen per stack",
        tier=UpgradeTier.TIER_3,
        max_stacks=5,
        effect_per_stack=0.1,
        icon="💗",
        color="#ff88aa",
        glow_color="#ffaacc"
    ),
    
    # TIER 4: Rare
    UpgradeType.DOUBLE_JUMP: UpgradeDefinition(
        upgrade_type=UpgradeType.DOUBLE_JUMP,
        name="Double Jump",
        description="+1 dash per stack",
        tier=UpgradeTier.TIER_4,
        max_stacks=3,
        effect_per_stack=1.0,
        icon="🦘",
        color="#00ff00",
        glow_color="#88ff88"
    ),
    UpgradeType.SLOW_AURA: UpgradeDefinition(
        upgrade_type=UpgradeType.SLOW_AURA,
        name="Slow Aura",
        description="-10% enemy speed nearby per stack",
        tier=UpgradeTier.TIER_4,
        max_stacks=4,
        effect_per_stack=0.10,
        icon="🌀",
        color="#8888ff",
        glow_color="#aaaaff"
    ),
    UpgradeType.CRIT_MULTIPLIER: UpgradeDefinition(
        upgrade_type=UpgradeType.CRIT_MULTIPLIER,
        name="Crit Multiplier+",
        description="+30% crit damage per stack",
        tier=UpgradeTier.TIER_4,
        max_stacks=5,
        effect_per_stack=0.30,
        icon="💢",
        color="#ff0000",
        glow_color="#ff4444"
    ),
    UpgradeType.POISON_TOUCH: UpgradeDefinition(
        upgrade_type=UpgradeType.POISON_TOUCH,
        name="Poison Touch",
        description="+2 poison damage/s per stack",
        tier=UpgradeTier.TIER_4,
        max_stacks=4,
        effect_per_stack=2.0,
        icon="☠️",
        color="#88ff00",
        glow_color="#aaff44"
    ),
    UpgradeType.HOMING: UpgradeDefinition(
        upgrade_type=UpgradeType.HOMING,
        name="Homing Instinct",
        description="+10% projectile tracking per stack",
        tier=UpgradeTier.TIER_4,
        max_stacks=4,
        effect_per_stack=0.10,
        icon="🎯",
        color="#ff88ff",
        glow_color="#ffaaff"
    ),
    UpgradeType.EXPLOSIVE_IMPACT: UpgradeDefinition(
        upgrade_type=UpgradeType.EXPLOSIVE_IMPACT,
        name="Explosive Impact",
        description="+20% explosion damage per stack",
        tier=UpgradeTier.TIER_4,
        max_stacks=3,
        effect_per_stack=0.20,
        icon="💣",
        color="#ff4400",
        glow_color="#ff8844"
    ),
    UpgradeType.EVASION: UpgradeDefinition(
        upgrade_type=UpgradeType.EVASION,
        name="Evasion+",
        description="+5% dodge chance per stack",
        tier=UpgradeTier.TIER_4,
        max_stacks=6,
        effect_per_stack=0.05,
        icon="💨",
        color="#cccccc",
        glow_color="#eeeeee"
    ),
    
    # TIER 5: Epic
    UpgradeType.BERSERK_MODE: UpgradeDefinition(
        upgrade_type=UpgradeType.BERSERK_MODE,
        name="Berserk Mode",
        description="+50% damage, -30% defense per stack",
        tier=UpgradeTier.TIER_5,
        max_stacks=3,
        effect_per_stack=0.50,
        icon="😈",
        color="#ff0000",
        glow_color="#ff4444"
    ),
    UpgradeType.TIME_DILATION: UpgradeDefinition(
        upgrade_type=UpgradeType.TIME_DILATION,
        name="Time Dilation",
        description="-10% enemy projectile speed per stack",
        tier=UpgradeTier.TIER_5,
        max_stacks=2,
        effect_per_stack=0.10,
        icon="⏰",
        color="#8800ff",
        glow_color="#aa44ff"
    ),
    UpgradeType.IMMUNE_FRAME: UpgradeDefinition(
        upgrade_type=UpgradeType.IMMUNE_FRAME,
        name="Immune Frame",
        description="+1s immunity every 5s per stack",
        tier=UpgradeTier.TIER_5,
        max_stacks=2,
        effect_per_stack=1.0,
        icon="✨",
        color="#ffff00",
        glow_color="#ffff88"
    ),
    UpgradeType.ALLY_DRONE: UpgradeDefinition(
        upgrade_type=UpgradeType.ALLY_DRONE,
        name="Ally Drone",
        description="+1 drone ally per stack",
        tier=UpgradeTier.TIER_5,
        max_stacks=3,
        effect_per_stack=1.0,
        icon="🤖",
        color="#00ffaa",
        glow_color="#88ffcc"
    ),
    UpgradeType.MANA_SHIELD: UpgradeDefinition(
        upgrade_type=UpgradeType.MANA_SHIELD,
        name="Mana Shield",
        description="+20 damage absorption per stack",
        tier=UpgradeTier.TIER_5,
        max_stacks=3,
        effect_per_stack=20.0,
        icon="🔮",
        color="#ff00ff",
        glow_color="#ff88ff"
    ),
    UpgradeType.FEEDBACK_LOOP: UpgradeDefinition(
        upgrade_type=UpgradeType.FEEDBACK_LOOP,
        name="Feedback Loop",
        description="+20% cooldown reset on kill per stack",
        tier=UpgradeTier.TIER_5,
        max_stacks=3,
        effect_per_stack=0.20,
        icon="🔄",
        color="#00ff00",
        glow_color="#88ff88"
    ),
    UpgradeType.PROBABILITY_FIELD: UpgradeDefinition(
        upgrade_type=UpgradeType.PROBABILITY_FIELD,
        name="Probability Field",
        description="+10% upgrade drop chance per stack",
        tier=UpgradeTier.TIER_5,
        max_stacks=2,
        effect_per_stack=0.10,
        icon="🎲",
        color="#ffaa00",
        glow_color="#ffcc44"
    ),
}


@dataclass
class UpgradeStack:
    """A single upgrade with its current stacks."""
    upgrade_type: UpgradeType
    current_stacks: int = 1
    
    @property
    def definition(self) -> UpgradeDefinition:
        """Get the upgrade definition."""
        return UPGRADE_DEFINITIONS[self.upgrade_type]
    
    @property
    def max_stacks(self) -> int:
        """Get max stacks from definition."""
        return self.definition.max_stacks
    
    @property
    def total_effect(self) -> float:
        """Get total effect value based on current stacks."""
        return self.definition.effect_per_stack * self.current_stacks
    
    def add_stack(self) -> bool:
        """Add a stack. Returns True if successful."""
        if self.current_stacks < self.max_stacks:
            self.current_stacks += 1
            return True
        return False
    
    def remove_stack(self) -> bool:
        """Remove a stack. Returns True if stacks remain."""
        if self.current_stacks > 0:
            self.current_stacks -= 1
        return self.current_stacks > 0


@dataclass
class PlayerUpgrades:
    """
    Container for all player upgrades.
    
    This component tracks all active upgrades on the player,
    handles upgrade pickup, and manages degradation on damage.
    """
    upgrades: Dict[UpgradeType, UpgradeStack] = field(default_factory=dict)
    
    # Cached computed modifiers (updated when upgrades change)
    damage_multiplier: float = 1.0
    fire_rate_multiplier: float = 1.0
    speed_multiplier: float = 1.0
    max_hp_bonus: float = 0.0
    crit_chance: float = 0.0
    crit_multiplier: float = 2.0
    armor_bonus: float = 0.0
    shield_regen_bonus: float = 0.0
    lifesteal: float = 0.0
    regeneration: float = 0.0
    pierce_bonus: int = 0
    bounce_bonus: int = 0
    knockback_multiplier: float = 1.0
    evasion_chance: float = 0.0
    projectile_size_multiplier: float = 1.0
    extra_projectiles: float = 0.0
    
    # Special effects
    slow_aura_strength: float = 0.0
    poison_damage: float = 0.0
    thorns_percent: float = 0.0
    explosive_bonus: float = 0.0
    homing_strength: float = 0.0
    berserk_stacks: int = 0
    time_dilation: float = 0.0
    immunity_duration: float = 0.0
    drone_count: int = 0
    mana_shield: float = 0.0
    feedback_percent: float = 0.0
    drop_chance_bonus: float = 0.0
    dash_count: int = 0
    
    # Visual tracking
    total_stacks: int = 0
    glow_intensity: float = 0.0
    
    def add_upgrade(self, upgrade_type: UpgradeType) -> bool:
        """
        Add an upgrade or stack to existing upgrade.
        Returns True if successfully added.
        """
        if upgrade_type in self.upgrades:
            success = self.upgrades[upgrade_type].add_stack()
        else:
            self.upgrades[upgrade_type] = UpgradeStack(upgrade_type=upgrade_type)
            success = True
        
        if success:
            self._recalculate_modifiers()
        return success
    
    def remove_random_stack(self) -> Optional[UpgradeType]:
        """
        Remove one stack from a random upgrade.
        Returns the upgrade type that lost a stack, or None if no upgrades.
        """
        non_empty = [u for u in self.upgrades.values() if u.current_stacks > 0]
        
        if not non_empty:
            return None
        
        target = random.choice(non_empty)
        target.remove_stack()
        
        # Remove upgrade entirely if no stacks left
        if target.current_stacks <= 0:
            del self.upgrades[target.upgrade_type]
        
        self._recalculate_modifiers()
        return target.upgrade_type
    
    def get_stack_count(self, upgrade_type: UpgradeType) -> int:
        """Get current stack count for an upgrade."""
        if upgrade_type in self.upgrades:
            return self.upgrades[upgrade_type].current_stacks
        return 0
    
    def has_upgrade(self, upgrade_type: UpgradeType) -> bool:
        """Check if player has an upgrade."""
        return upgrade_type in self.upgrades and self.upgrades[upgrade_type].current_stacks > 0
    
    def get_all_upgrades(self) -> List[UpgradeStack]:
        """Get list of all active upgrades."""
        return [u for u in self.upgrades.values() if u.current_stacks > 0]
    
    def clear_all(self) -> None:
        """Remove all upgrades."""
        self.upgrades.clear()
        self._recalculate_modifiers()
    
    def _recalculate_modifiers(self) -> None:
        """Recalculate all cached modifiers based on current upgrades."""
        # Reset all modifiers to base values
        self.damage_multiplier = 1.0
        self.fire_rate_multiplier = 1.0
        self.speed_multiplier = 1.0
        self.max_hp_bonus = 0.0
        self.crit_chance = 0.0
        self.crit_multiplier = 2.0
        self.armor_bonus = 0.0
        self.shield_regen_bonus = 0.0
        self.lifesteal = 0.0
        self.regeneration = 0.0
        self.pierce_bonus = 0
        self.bounce_bonus = 0
        self.knockback_multiplier = 1.0
        self.evasion_chance = 0.0
        self.projectile_size_multiplier = 1.0
        self.extra_projectiles = 0.0
        self.slow_aura_strength = 0.0
        self.poison_damage = 0.0
        self.thorns_percent = 0.0
        self.explosive_bonus = 0.0
        self.homing_strength = 0.0
        self.berserk_stacks = 0
        self.time_dilation = 0.0
        self.immunity_duration = 0.0
        self.drone_count = 0
        self.mana_shield = 0.0
        self.feedback_percent = 0.0
        self.drop_chance_bonus = 0.0
        self.dash_count = 0
        
        self.total_stacks = 0
        
        for upgrade in self.upgrades.values():
            if upgrade.current_stacks <= 0:
                continue
                
            self.total_stacks += upgrade.current_stacks
            effect = upgrade.total_effect
            
            # Apply effects based on upgrade type
            match upgrade.upgrade_type:
                # Tier 1
                case UpgradeType.DAMAGE_PLUS:
                    self.damage_multiplier += effect
                case UpgradeType.FIRE_RATE_PLUS:
                    self.fire_rate_multiplier *= (1 - effect)  # Reduce cooldown
                case UpgradeType.SPEED_PLUS:
                    self.speed_multiplier += effect
                case UpgradeType.HP_PLUS:
                    self.max_hp_bonus += effect
                    
                # Tier 2
                case UpgradeType.CRITICAL_CHANCE:
                    self.crit_chance += effect
                case UpgradeType.ARMOR_PLUS:
                    self.armor_bonus += effect
                case UpgradeType.SHIELD_REGEN:
                    self.shield_regen_bonus += effect
                case UpgradeType.MULTISHOT:
                    self.extra_projectiles += effect
                case UpgradeType.PROJECTILE_SIZE:
                    self.projectile_size_multiplier += effect
                case UpgradeType.ACCURACY:
                    pass  # Handled in weapon system
                    
                # Tier 3
                case UpgradeType.PIERCING:
                    self.pierce_bonus += int(effect)
                case UpgradeType.RICOCHET:
                    self.bounce_bonus += int(effect)
                case UpgradeType.KNOCKBACK:
                    self.knockback_multiplier += effect
                case UpgradeType.WALL_PENETRATION:
                    pass  # Handled in collision system
                case UpgradeType.LIFESTEAL:
                    self.lifesteal += effect
                case UpgradeType.THORNS:
                    self.thorns_percent += effect
                case UpgradeType.REGENERATION:
                    self.regeneration += effect
                    
                # Tier 4
                case UpgradeType.DOUBLE_JUMP:
                    self.dash_count += int(effect)
                case UpgradeType.SLOW_AURA:
                    self.slow_aura_strength += effect
                case UpgradeType.CRIT_MULTIPLIER:
                    self.crit_multiplier += effect
                case UpgradeType.POISON_TOUCH:
                    self.poison_damage += effect
                case UpgradeType.HOMING:
                    self.homing_strength += effect
                case UpgradeType.EXPLOSIVE_IMPACT:
                    self.explosive_bonus += effect
                case UpgradeType.EVASION:
                    self.evasion_chance += effect
                    
                # Tier 5
                case UpgradeType.BERSERK_MODE:
                    self.berserk_stacks = upgrade.current_stacks
                    self.damage_multiplier += effect
                case UpgradeType.TIME_DILATION:
                    self.time_dilation += effect
                case UpgradeType.IMMUNE_FRAME:
                    self.immunity_duration += effect
                case UpgradeType.ALLY_DRONE:
                    self.drone_count += int(effect)
                case UpgradeType.MANA_SHIELD:
                    self.mana_shield += effect
                case UpgradeType.FEEDBACK_LOOP:
                    self.feedback_percent += effect
                case UpgradeType.PROBABILITY_FIELD:
                    self.drop_chance_bonus += effect
        
        # Berserk mode reduces defense
        if self.berserk_stacks > 0:
            defense_reduction = 0.30 * self.berserk_stacks
            # This is applied in health system
        
        # Calculate glow intensity based on total stacks
        self.glow_intensity = min(1.0, self.total_stacks / 50.0)


# Tier distribution for drops based on wave number
TIER_DISTRIBUTION = {
    # Wave range -> (Tier1%, Tier2%, Tier3%, Tier4%, Tier5%)
    (1, 2): (90, 10, 0, 0, 0),
    (3, 5): (60, 35, 5, 0, 0),
    (6, 8): (30, 50, 15, 5, 0),
    (9, 12): (20, 40, 25, 12, 3),
    (13, 999): (15, 35, 30, 15, 5),
}

BOSS_TIER_DISTRIBUTION = (0, 0, 20, 50, 30)


def get_tier_distribution(wave_number: int, is_boss: bool = False) -> tuple:
    """Get tier distribution for a given wave."""
    if is_boss:
        return BOSS_TIER_DISTRIBUTION
    
    for (min_wave, max_wave), distribution in TIER_DISTRIBUTION.items():
        if min_wave <= wave_number <= max_wave:
            return distribution
    
    return TIER_DISTRIBUTION[(13, 999)]


def select_random_upgrade_type(wave_number: int, is_boss: bool = False) -> UpgradeType:
    """Select a random upgrade type based on wave and tier distribution."""
    distribution = get_tier_distribution(wave_number, is_boss)
    
    # Roll for tier
    roll = random.uniform(0, 100)
    cumulative = 0
    selected_tier = UpgradeTier.TIER_1
    
    for i, percent in enumerate(distribution):
        cumulative += percent
        if roll <= cumulative:
            selected_tier = UpgradeTier(i + 1)
            break
    
    # Get all upgrades of the selected tier
    tier_upgrades = [
        upgrade_type for upgrade_type, definition in UPGRADE_DEFINITIONS.items()
        if definition.tier == selected_tier
    ]
    
    if not tier_upgrades:
        # Fallback to tier 1 if no upgrades in selected tier
        tier_upgrades = [
            upgrade_type for upgrade_type, definition in UPGRADE_DEFINITIONS.items()
            if definition.tier == UpgradeTier.TIER_1
        ]
    
    return random.choice(tier_upgrades)


def calculate_drop_chance(wave_number: int, probability_bonus: float = 0.0) -> float:
    """
    Calculate the chance of an upgrade dropping from an enemy kill.
    
    Base rate: 40% + 5% per wave (capped at 95%)
    Modified by probability field upgrade.
    """
    base_rate = 0.4 + (wave_number * 0.05)
    base_rate = min(0.95, base_rate)
    
    # Apply probability bonus from upgrade
    base_rate += probability_bonus
    
    return min(1.0, base_rate)
