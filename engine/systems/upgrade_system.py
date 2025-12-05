"""
Upgrade System - Manages permanent active upgrades.

Handles:
- Applying upgrade effects to player stats each frame
- Degradation when player takes damage
- Upgrade pickup processing
- Visual feedback for upgrades
"""

from __future__ import annotations
import random
import math
from typing import TYPE_CHECKING, Optional

from ..core.system import GameSystem, SystemPriority
from ..core.events import DamageEvent, DeathEvent
from ..components.transform import Transform
from ..components.physics import Physics, Velocity
from ..components.health import Health, Shield
from ..components.weapon import Weapon
from ..components.tags import PlayerTag, EnemyTag
from ..components.upgrades import (
    PlayerUpgrades, UpgradeType, UpgradeStack,
    UPGRADE_DEFINITIONS, select_random_upgrade_type,
    calculate_drop_chance
)
from ..components.renderable import Renderable, RenderShape, RenderLayer
from ..components.collider import Collider, ColliderType, CollisionMask

if TYPE_CHECKING:
    from ..core.entity import Entity


class UpgradeSystem(GameSystem):
    """
    System for managing the permanent active upgrade system.
    
    Features:
    - Applies all active upgrades to player stats each frame
    - Handles upgrade degradation (50% chance to lose 1 stack on damage)
    - Spawns upgrade pickups when enemies die
    - Tracks kill count for drop mechanics
    """
    
    def __init__(self):
        super().__init__(priority=SystemPriority.AI)  # Before physics/movement
        
        self.kills_since_last_drop = 0
        self.current_wave = 1
        
        # Degradation settings
        self.degradation_chance = 0.5  # 50% chance to lose stack on damage
        
        # Tracking for regeneration
        self._regen_timer = 0.0
        
        # Base player stats (stored for resetting)
        self._base_max_hp: Optional[float] = None
        self._base_max_shield: Optional[float] = None
        self._base_speed: Optional[float] = None
        
    def initialize(self) -> None:
        """Subscribe to events."""
        self.events.subscribe(DamageEvent, self._on_player_damaged)
        self.events.subscribe(DeathEvent, self._on_enemy_death)
    
    def _on_player_damaged(self, event: DamageEvent) -> None:
        """Handle player taking damage - may degrade an upgrade."""
        if not event or not event.target_id:
            return
        
        # Find player
        player = self.entities.get_named("player")
        if not player or event.target_id != player.id:
            return
        
        # Check if player has upgrades component
        upgrades = self.entities.get_component(player, PlayerUpgrades)
        if not upgrades or not upgrades.upgrades:
            return
        
        # 50% chance to lose a random upgrade stack
        if random.random() < self.degradation_chance:
            lost_type = upgrades.remove_random_stack()
            if lost_type:
                # Visual/audio feedback would go here
                definition = UPGRADE_DEFINITIONS[lost_type]
                # Could emit an event for UI feedback
                pass
    
    def _on_enemy_death(self, event: DeathEvent) -> None:
        """Handle enemy death - may spawn upgrade pickup."""
        if not event or not event.entity_id:
            return
        
        entity = self.entities.get_entity_by_id(event.entity_id)
        if not entity:
            return
        
        enemy_tag = self.entities.get_component(entity, EnemyTag)
        if not enemy_tag:
            return
        
        self.kills_since_last_drop += 1
        
        # Get player for probability bonus
        player = self.entities.get_named("player")
        probability_bonus = 0.0
        if player:
            upgrades = self.entities.get_component(player, PlayerUpgrades)
            if upgrades:
                probability_bonus = upgrades.drop_chance_bonus
        
        # Calculate drop chance
        is_boss = enemy_tag.enemy_type == "boss"
        drop_chance = calculate_drop_chance(self.current_wave, probability_bonus)
        
        # Boss always drops
        if is_boss or random.random() < drop_chance:
            # Get enemy position
            transform = self.entities.get_component(entity, Transform)
            if transform:
                # Select random upgrade type
                upgrade_type = select_random_upgrade_type(self.current_wave, is_boss)
                
                # Spawn upgrade pickup
                self._spawn_upgrade_pickup(transform.x, transform.y, upgrade_type)
                
            self.kills_since_last_drop = 0
    
    def _spawn_upgrade_pickup(self, x: float, y: float, upgrade_type: UpgradeType) -> Entity:
        """Spawn an upgrade pickup entity at the given position."""
        entity = self.entities.create_entity()
        definition = UPGRADE_DEFINITIONS[upgrade_type]
        
        # Transform with slight random offset
        offset_x = random.uniform(-20, 20)
        offset_y = random.uniform(-20, 20)
        self.entities.add_component(entity, Transform(
            x=x + offset_x,
            y=y + offset_y,
            angle=0
        ))
        
        # Slight floating animation
        self.entities.add_component(entity, Velocity(angular=45))
        
        # Get text symbol for the upgrade type
        symbol = self._get_upgrade_symbol(upgrade_type, definition)
        
        # Renderable - uses STAR shape with text symbol
        # Size based on tier (higher tier = larger/more visible)
        tier_sizes = {1: 0.7, 2: 0.8, 3: 0.9, 4: 1.0, 5: 1.2}
        size = tier_sizes.get(definition.tier.value, 0.7)
        
        self.entities.add_component(entity, Renderable(
            shape=RenderShape.STAR,  # Star shape for pickups (distinct from enemies)
            color=definition.color,
            outline_color=definition.glow_color,
            size=size,
            layer=RenderLayer.POWERUP,
            text_symbol=symbol,  # Letter/symbol displayed
            glow=True,  # Pulsing glow effect
            pulse_speed=2.0
        ))
        
        # Collider (trigger for pickup)
        self.entities.add_component(entity, Collider(
            collider_type=ColliderType.CIRCLE,
            radius=18.0,
            layer=CollisionMask.POWERUP,
            mask=CollisionMask.PLAYER,
            is_trigger=True
        ))
        
        # Tag for identification
        self.entities.add_component(entity, UpgradePickupTag(
            upgrade_type=upgrade_type,
            lifetime=15.0  # Despawn after 15 seconds
        ))
        self.entities.add_tag(entity, "upgrade_pickup")
        
        return entity
    
    def _get_upgrade_symbol(self, upgrade_type: UpgradeType, definition: "UpgradeDefinition") -> str:
        """Get a letter/symbol to represent the upgrade type."""
        # Map upgrade types to letter symbols
        symbol_map = {
            # Tier 1 - Simple letters
            UpgradeType.DAMAGE_PLUS: "D",
            UpgradeType.FIRE_RATE_PLUS: "F",
            UpgradeType.SPEED_PLUS: "S",
            UpgradeType.HP_PLUS: "H",
            
            # Tier 2
            UpgradeType.CRITICAL_CHANCE: "C",
            UpgradeType.ARMOR_PLUS: "A",
            UpgradeType.SHIELD_REGEN: "R",
            UpgradeType.MULTISHOT: "M",
            UpgradeType.PROJECTILE_SIZE: "P",
            UpgradeType.ACCURACY: "a",
            
            # Tier 3
            UpgradeType.PIERCING: "→",
            UpgradeType.RICOCHET: "↺",
            UpgradeType.KNOCKBACK: "K",
            UpgradeType.WALL_PENETRATION: "W",
            UpgradeType.LIFESTEAL: "L",
            UpgradeType.THORNS: "T",
            UpgradeType.REGENERATION: "+",
            
            # Tier 4
            UpgradeType.DOUBLE_JUMP: "J",
            UpgradeType.SLOW_AURA: "~",
            UpgradeType.CRIT_MULTIPLIER: "X",
            UpgradeType.POISON_TOUCH: "☠",
            UpgradeType.HOMING: "◎",
            UpgradeType.EXPLOSIVE_IMPACT: "☆",
            UpgradeType.EVASION: "E",
            
            # Tier 5 - Epic
            UpgradeType.BERSERK_MODE: "B",
            UpgradeType.TIME_DILATION: "⏱",
            UpgradeType.IMMUNE_FRAME: "I",
            UpgradeType.ALLY_DRONE: "♦",
            UpgradeType.MANA_SHIELD: "⬡",
            UpgradeType.FEEDBACK_LOOP: "∞",
            UpgradeType.PROBABILITY_FIELD: "?",
        }
        
        return symbol_map.get(upgrade_type, "?")
    
    def update(self, dt: float) -> None:
        """Apply upgrades and process pickup collisions."""
        if not isinstance(dt, (int, float)) or dt <= 0:
            dt = 0.016
        
        # Find player
        player = self.entities.get_named("player")
        if not player:
            return
        
        upgrades = self.entities.get_component(player, PlayerUpgrades)
        if not upgrades:
            return
        
        # Apply upgrade effects to player
        self._apply_upgrade_effects(player, upgrades, dt)
        
        # Process upgrade pickups
        self._process_pickups(player, upgrades)
        
        # Update pickup lifetimes
        self._update_pickups(dt)
    
    def _apply_upgrade_effects(self, player: Entity, upgrades: PlayerUpgrades, dt: float) -> None:
        """Apply all upgrade effects to the player."""
        # Get player components
        health = self.entities.get_component(player, Health)
        shield = self.entities.get_component(player, Shield)
        physics = self.entities.get_component(player, Physics)
        weapon = self.entities.get_component(player, Weapon)
        
        # Store base stats on first run
        if health and self._base_max_hp is None:
            self._base_max_hp = health.max_hp
        if shield and self._base_max_shield is None:
            self._base_max_shield = shield.max_hp
        if physics and self._base_speed is None:
            self._base_speed = physics.max_speed
        
        # Apply HP bonus
        if health and self._base_max_hp is not None:
            new_max = self._base_max_hp + upgrades.max_hp_bonus
            if health.max_hp != new_max:
                # If max HP increased, also heal the difference
                diff = new_max - health.max_hp
                health.max_hp = new_max
                if diff > 0:
                    health.hp = min(health.hp + diff, health.max_hp)
        
        # Apply speed bonus
        if physics and self._base_speed is not None:
            physics.max_speed = self._base_speed * upgrades.speed_multiplier
        
        # Apply regeneration
        if health and upgrades.regeneration > 0:
            self._regen_timer += dt
            if self._regen_timer >= 0.1:  # Regen every 0.1 seconds
                heal_amount = upgrades.regeneration * (self._regen_timer / 0.1)
                health.heal(heal_amount)
                self._regen_timer = 0
        
        # Apply shield regen bonus
        if shield and upgrades.shield_regen_bonus > 0:
            bonus_regen = upgrades.shield_regen_bonus * dt
            shield.hp = min(shield.max_hp, shield.hp + bonus_regen)
        
        # Apply armor bonus
        if health:
            # Convert armor bonus to damage reduction (diminishing returns)
            armor_dr = min(0.75, upgrades.armor_bonus / 100.0)
            health.armor = armor_dr
        
        # Evasion is handled in health system
        # Weapon effects (fire rate, damage) are handled in weapon system
        
        # Apply visual glow based on upgrade stacks
        renderable = self.entities.get_component(player, Renderable)
        if renderable and upgrades.total_stacks > 0:
            # Increase outline brightness based on stacks
            intensity = min(255, 100 + upgrades.total_stacks * 10)
            renderable.outline_color = f"#{intensity:02x}{intensity:02x}ff"
    
    def _process_pickups(self, player: Entity, upgrades: PlayerUpgrades) -> None:
        """Check for and process upgrade pickups."""
        player_transform = self.entities.get_component(player, Transform)
        if not player_transform:
            return
        
        # Check all upgrade pickups
        for entity in self.entities.get_entities_with(UpgradePickupTag):
            if not self.entities.is_alive(entity):
                continue
            
            pickup_tag = self.entities.get_component(entity, UpgradePickupTag)
            pickup_transform = self.entities.get_component(entity, Transform)
            
            if not pickup_tag or not pickup_transform:
                continue
            
            # Check distance
            dx = pickup_transform.x - player_transform.x
            dy = pickup_transform.y - player_transform.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            pickup_radius = 25.0  # Player pickup range
            if distance < pickup_radius:
                # Add upgrade to player
                success = upgrades.add_upgrade(pickup_tag.upgrade_type)
                
                if success:
                    # Visual feedback could go here
                    pass
                
                # Destroy pickup
                self.entities.destroy_entity(entity)
    
    def _update_pickups(self, dt: float) -> None:
        """Update pickup lifetimes and despawn expired ones."""
        for entity in self.entities.get_entities_with(UpgradePickupTag):
            if not self.entities.is_alive(entity):
                continue
            
            pickup_tag = self.entities.get_component(entity, UpgradePickupTag)
            if pickup_tag:
                pickup_tag.lifetime -= dt
                
                if pickup_tag.lifetime <= 0:
                    self.entities.destroy_entity(entity)
                elif pickup_tag.lifetime < 3.0:
                    # Flash when about to despawn
                    renderable = self.entities.get_component(entity, Renderable)
                    if renderable:
                        # Toggle visibility for flashing effect
                        renderable.visible = int(pickup_tag.lifetime * 4) % 2 == 0
    
    def set_wave(self, wave_number: int) -> None:
        """Update current wave number for drop calculations."""
        self.current_wave = wave_number
    
    def reset_player_upgrades(self) -> None:
        """Reset player upgrades (on death/restart)."""
        player = self.entities.get_named("player")
        if player:
            upgrades = self.entities.get_component(player, PlayerUpgrades)
            if upgrades:
                upgrades.clear_all()
        
        # Reset base stats
        self._base_max_hp = None
        self._base_max_shield = None
        self._base_speed = None


from dataclasses import dataclass


@dataclass
class UpgradePickupTag:
    """Tag for upgrade pickup entities."""
    upgrade_type: UpgradeType
    lifetime: float = 15.0  # Seconds until despawn
