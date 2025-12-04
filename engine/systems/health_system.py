"""
Health System - Damage processing, death handling, shields.

Processes damage events, updates health/shields, and handles entity death.
Integrates with the upgrade system for effects like evasion and lifesteal.
"""

from __future__ import annotations
import random
from typing import TYPE_CHECKING, Optional

from ..core.system import GameSystem, SystemPriority
from ..core.events import CollisionEvent, DamageEvent, DeathEvent
from ..components.transform import Transform
from ..components.health import Health, Shield
from ..components.weapon import Projectile
from ..components.collider import Collider, CollisionMask
from ..components.renderable import Renderable
from ..components.tags import PlayerTag, EnemyTag, ProjectileTag
from ..components.upgrades import PlayerUpgrades
from ..core.entity import Entity

if TYPE_CHECKING:
    pass


class HealthSystem(GameSystem):
    """
    Handles health, damage, shields, and death.
    
    Features:
    - Processes collision events to apply damage
    - Shield absorption before health damage
    - Shield regeneration
    - Invulnerability frames (i-frames)
    - Death event emission
    - Visual feedback (flash on hit)
    - Evasion from upgrade system
    - Lifesteal from upgrade system
    """
    
    def __init__(self, i_frame_duration: float = 0.5):
        super().__init__(priority=SystemPriority.HEALTH)
        self.i_frame_duration = i_frame_duration
        self._pending_damage: list[tuple[str, str, float]] = []  # (target_id, source_id, damage)
        self._pending_lifesteal: list[tuple[str, float]] = []  # (player_id, amount)
    
    def initialize(self) -> None:
        """Subscribe to collision events."""
        self.events.subscribe(CollisionEvent, self._on_collision)
        self.events.subscribe(DamageEvent, self._on_damage_event)
    
    def _on_collision(self, event: CollisionEvent) -> None:
        """Handle collision event to check for damage."""
        if not event or not event.entity_a_id or not event.entity_b_id:
            return
            
        # Use safe entity lookup
        entity_a = self.entities.get_entity_by_id(event.entity_a_id)
        entity_b = self.entities.get_entity_by_id(event.entity_b_id)
        
        if not entity_a or not entity_b:
            return
        
        # Verify entities are still alive
        if not self.entities.is_alive(entity_a) or not self.entities.is_alive(entity_b):
            return
        
        # Check projectile collisions
        self._check_projectile_hit(entity_a, entity_b)
        self._check_projectile_hit(entity_b, entity_a)
        
        # Check contact damage (enemy touching player)
        self._check_contact_damage(entity_a, entity_b)
    
    def _check_projectile_hit(self, projectile_entity: Entity, target_entity: Entity) -> None:
        """Check if a projectile hit a valid target."""
        projectile = self.entities.get_component(projectile_entity, Projectile)
        if not projectile:
            return
        
        # Check if target has health
        target_health = self.entities.get_component(target_entity, Health)
        if not target_health:
            return
        
        proj_tag = self.entities.get_component(projectile_entity, ProjectileTag)
        
        # Check if it's a valid hit (player projectile vs enemy, or vice versa)
        is_valid_hit = False
        is_player_projectile = False
        
        if proj_tag:
            if proj_tag.is_player_owned:
                # Player projectile - should hit enemies
                is_valid_hit = self.entities.has_component(target_entity, EnemyTag)
                is_player_projectile = True
            else:
                # Enemy projectile - should hit player
                is_valid_hit = self.entities.has_component(target_entity, PlayerTag)
        
        if not is_valid_hit:
            return
        
        # Prevent multi-hit
        if not projectile.register_hit(target_entity.id):
            return
        
        # Calculate damage with upgrade modifiers
        damage = projectile.damage
        
        # Get player for upgrade effects
        player = self.entities.get_named("player")
        if player and is_player_projectile:
            upgrades = self.entities.get_component(player, PlayerUpgrades)
            if upgrades:
                # Apply damage multiplier
                damage *= upgrades.damage_multiplier
                
                # Apply critical hit
                if upgrades.crit_chance > 0 and random.random() < upgrades.crit_chance:
                    damage *= upgrades.crit_multiplier
                
                # Queue lifesteal
                if upgrades.lifesteal > 0:
                    lifesteal_amount = damage * upgrades.lifesteal
                    self._pending_lifesteal.append((player.id, lifesteal_amount))
        
        # Queue damage
        self._pending_damage.append((target_entity.id, projectile.owner_id, damage))
        
        # Get player upgrades for pierce bonus
        pierce_count = projectile.pierce_count
        if player and is_player_projectile:
            upgrades = self.entities.get_component(player, PlayerUpgrades)
            if upgrades:
                pierce_count += upgrades.pierce_bonus
        
        # Destroy projectile (unless piercing)
        if len(projectile.hit_entities) > pierce_count:
            self.entities.destroy_entity(projectile_entity)
    
    def _check_contact_damage(self, entity_a: Entity, entity_b: Entity) -> None:
        """Check for contact damage between entities."""
        # For now, enemies deal contact damage to player
        player = None
        enemy = None
        
        if self.entities.has_component(entity_a, PlayerTag):
            player = entity_a
            enemy = entity_b if self.entities.has_component(entity_b, EnemyTag) else None
        elif self.entities.has_component(entity_b, PlayerTag):
            player = entity_b
            enemy = entity_a if self.entities.has_component(entity_a, EnemyTag) else None
        
        if player and enemy:
            player_health = self.entities.get_component(player, Health)
            if player_health and player_health.invulnerability_timer <= 0:
                # Apply contact damage
                self._pending_damage.append((player.id, enemy.id, 10.0))  # 10 contact damage
    
    def _on_damage_event(self, event: DamageEvent) -> None:
        """Handle explicit damage event."""
        self._pending_damage.append((event.target_id, event.source_id or "", event.amount))
    
    def update(self, dt: float) -> None:
        """Process health updates."""
        # Process pending damage
        for target_id, source_id, damage in self._pending_damage:
            self._apply_damage(target_id, source_id, damage)
        self._pending_damage.clear()
        
        # Process pending lifesteal
        for player_id, amount in self._pending_lifesteal:
            player = self.entities.get_entity_by_id(player_id)
            if player and self.entities.is_alive(player):
                health = self.entities.get_component(player, Health)
                if health:
                    health.heal(amount)
        self._pending_lifesteal.clear()
        
        # Update all entities with health
        for entity in self.entities.get_entities_with(Health):
            health = self.entities.get_component(entity, Health)
            if not health:
                continue
            
            # Update invulnerability timer
            if health.invulnerability_timer > 0:
                health.invulnerability_timer -= dt
            
            # Reset per-frame damage tracking
            health.damage_this_frame = 0.0
            
            # Update shield regeneration
            shield = self.entities.get_component(entity, Shield)
            if shield:
                shield.update_recharge(dt)
            
            # Check for death
            if not health.is_alive:
                self._handle_death(entity, health.last_damage_source)
    
    def _apply_damage(self, target_id: str, source_id: str, damage: float) -> None:
        """Apply damage to an entity."""
        if not target_id:
            return
            
        # Validate damage value
        if not isinstance(damage, (int, float)) or damage <= 0:
            return
        import math
        if not math.isfinite(damage):
            return
            
        # Use safe entity lookup
        target = self.entities.get_entity_by_id(target_id)
        if not target or not self.entities.is_alive(target):
            return
        
        health = self.entities.get_component(target, Health)
        if not health:
            return
        
        # Check invulnerability
        if health.is_invulnerable or health.invulnerability_timer > 0:
            return
        
        # Check for evasion (from upgrade system)
        upgrades = self.entities.get_component(target, PlayerUpgrades)
        if upgrades and upgrades.evasion_chance > 0:
            if random.random() < upgrades.evasion_chance:
                # Evaded! Show visual feedback
                renderable = self.entities.get_component(target, Renderable)
                if renderable:
                    try:
                        renderable.flash(duration=0.15, color="#00ffff")
                    except Exception:
                        pass
                return  # No damage taken
        
        # Calculate actual damage after armor (clamp armor to valid range)
        armor = max(0.0, min(0.99, health.armor))
        actual_damage = damage * (1.0 - armor)
        
        # Apply berserk mode defense reduction
        if upgrades and upgrades.berserk_stacks > 0:
            # Berserk reduces defense
            defense_reduction = 0.30 * upgrades.berserk_stacks
            actual_damage *= (1.0 + defense_reduction)
        
        # Shield absorption
        shield = self.entities.get_component(target, Shield)
        if shield and shield.is_active:
            actual_damage = shield.absorb_damage(actual_damage)
        
        # Mana shield absorption (from upgrades)
        if upgrades and upgrades.mana_shield > 0:
            shield_absorb = min(upgrades.mana_shield, actual_damage)
            upgrades.mana_shield -= shield_absorb
            actual_damage -= shield_absorb
        
        # Apply to health
        if actual_damage > 0:
            health.hp = max(0.0, health.hp - actual_damage)
            health.damage_this_frame += actual_damage
            health.last_damage_source = source_id if source_id else ""
            
            # Trigger i-frames for player
            if self.entities.has_component(target, PlayerTag):
                health.invulnerability_timer = self.i_frame_duration
            
            # Visual feedback
            renderable = self.entities.get_component(target, Renderable)
            if renderable:
                try:
                    renderable.flash(duration=0.1, color="white")
                except Exception:
                    pass  # Ignore rendering errors
            
            # Thorns damage (reflect damage back to attacker)
            if upgrades and upgrades.thorns_percent > 0 and source_id:
                thorns_damage = actual_damage * upgrades.thorns_percent
                if thorns_damage > 0:
                    self._pending_damage.append((source_id, target_id, thorns_damage))
    
    def _handle_death(self, entity: Entity, killer_id: str) -> None:
        """Handle entity death."""
        if not entity:
            return
            
        # Check if entity is still valid
        if not self.entities.is_alive(entity):
            return
            
        try:
            # Emit death event
            self.events.emit(DeathEvent(
                entity_id=entity.id,
                killer_id=killer_id if killer_id else None
            ))
        except Exception:
            pass  # Don't let event errors prevent cleanup
        
        # Mark for destruction
        try:
            self.entities.destroy_entity(entity)
        except Exception:
            pass  # Entity may already be destroyed
    
    def heal_entity(self, entity: Entity, amount: float) -> float:
        """Heal an entity. Returns actual amount healed."""
        health = self.entities.get_component(entity, Health)
        if health:
            return health.heal(amount)
        return 0.0
    
    def damage_entity(
        self,
        entity: Entity,
        amount: float,
        source_id: str = ""
    ) -> None:
        """Apply damage to an entity."""
        self._pending_damage.append((entity.id, source_id, amount))
