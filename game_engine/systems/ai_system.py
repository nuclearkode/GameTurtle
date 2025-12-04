"""AISystem: handles AI behavior for enemies."""

import math
from typing import Optional
from ..core.system import GameSystem
from ..core.component import Transform, Physics, AIBrain, Weapon


class AISystem(GameSystem):
    """Manages AI behavior for enemy entities."""
    
    def __init__(self, entity_manager, component_registry):
        super().__init__(entity_manager, component_registry)
        self.priority = 2  # Run after physics, before collisions
        self.player_id: Optional[str] = None
    
    def set_player_id(self, player_id: str):
        """Set the player entity ID for targeting."""
        self.player_id = player_id
    
    def update(self, dt: float):
        """Update AI for all entities with AIBrain."""
        if not self.player_id:
            return
        
        player_transform = self.entity_manager.get_component(self.player_id, "Transform")
        if not player_transform:
            return
        
        # Get all entities with AIBrain
        entity_ids = self.component_registry.get_entities_with("AIBrain", "Transform")
        
        for entity_id in entity_ids:
            ai_brain = self.entity_manager.get_component(entity_id, "AIBrain")
            transform = self.entity_manager.get_component(entity_id, "Transform")
            physics = self.entity_manager.get_component(entity_id, "Physics")
            
            if not ai_brain or not transform:
                continue
            
            # Update cooldowns
            for key in list(ai_brain.cooldowns.keys()):
                ai_brain.cooldowns[key] -= dt
                if ai_brain.cooldowns[key] <= 0:
                    del ai_brain.cooldowns[key]
            
            # Execute behavior based on type
            if ai_brain.behavior_type == "chaser":
                self._update_chaser(entity_id, transform, physics, ai_brain, player_transform, dt)
            elif ai_brain.behavior_type == "turret":
                self._update_turret(entity_id, transform, ai_brain, player_transform, dt)
            elif ai_brain.behavior_type == "swarm":
                self._update_swarm(entity_id, transform, physics, ai_brain, player_transform, dt)
            elif ai_brain.behavior_type == "boss":
                self._update_boss(entity_id, transform, physics, ai_brain, player_transform, dt)
    
    def _update_chaser(
        self, entity_id: str, transform: Transform, physics: Physics,
        ai_brain: AIBrain, target_transform: Transform, dt: float
    ):
        """Chaser behavior: move directly toward target."""
        distance = transform.distance_to(target_transform)
        
        if distance > ai_brain.awareness_range:
            # Out of range, stop moving
            transform.vx *= 0.9
            transform.vy *= 0.9
            return
        
        # Calculate direction to target
        angle_to_target = transform.angle_to(target_transform)
        angle_rad = math.radians(angle_to_target)
        
        # Accelerate toward target
        acceleration = physics.acceleration * dt
        transform.vx += math.cos(angle_rad) * acceleration
        transform.vy += math.sin(angle_rad) * acceleration
        
        # Rotate to face movement direction
        if transform.vx != 0 or transform.vy != 0:
            movement_angle = math.degrees(math.atan2(transform.vy, transform.vx))
            transform.angle = movement_angle
    
    def _update_turret(
        self, entity_id: str, transform: Transform,
        ai_brain: AIBrain, target_transform: Transform, dt: float
    ):
        """Turret behavior: rotate to face target and fire when in range."""
        distance = transform.distance_to(target_transform)
        
        if distance > ai_brain.awareness_range:
            return
        
        # Rotate to face target
        angle_to_target = transform.angle_to(target_transform)
        transform.angle = angle_to_target
        
        # Fire if in attack range
        weapon = self.entity_manager.get_component(entity_id, "Weapon")
        if weapon and distance <= ai_brain.attack_range:
            if weapon.can_fire():
                weapon.cooldown_remaining = 1.0 / weapon.fire_rate
                # Weapon system will handle actual firing
    
    def _update_swarm(
        self, entity_id: str, transform: Transform, physics: Physics,
        ai_brain: AIBrain, target_transform: Transform, dt: float
    ):
        """Swarm behavior: simple boids-like behavior."""
        # Get nearby swarm entities
        swarm_entities = self.component_registry.get_entities_with("AIBrain", "Transform")
        neighbors = []
        for other_id in swarm_entities:
            if other_id == entity_id:
                continue
            other_ai = self.entity_manager.get_component(other_id, "AIBrain")
            if other_ai and other_ai.behavior_type == "swarm":
                other_transform = self.entity_manager.get_component(other_id, "Transform")
                if other_transform:
                    dist = transform.distance_to(other_transform)
                    if dist < 100:  # Neighbor range
                        neighbors.append((other_transform, dist))
        
        # Limit neighbor count for performance
        neighbors = sorted(neighbors, key=lambda x: x[1])[:5]
        
        # Cohesion: move toward center of neighbors
        if neighbors:
            avg_x = sum(n[0].x for n in neighbors) / len(neighbors)
            avg_y = sum(n[0].y for n in neighbors) / len(neighbors)
            cohesion_angle = math.degrees(math.atan2(avg_y - transform.y, avg_x - transform.x))
            cohesion_rad = math.radians(cohesion_angle)
            transform.vx += math.cos(cohesion_rad) * physics.acceleration * dt * 0.3
            transform.vy += math.sin(cohesion_rad) * physics.acceleration * dt * 0.3
        
        # Separation: avoid neighbors
        for neighbor_transform, dist in neighbors:
            if dist < 30:  # Separation distance
                separation_angle = math.degrees(math.atan2(
                    transform.y - neighbor_transform.y,
                    transform.x - neighbor_transform.x
                ))
                separation_rad = math.radians(separation_angle)
                force = (30 - dist) / 30 * physics.acceleration * dt * 0.5
                transform.vx += math.cos(separation_rad) * force
                transform.vy += math.sin(separation_rad) * force
        
        # Alignment: match velocity of neighbors
        if neighbors:
            avg_vx = sum(n[0].vx for n in neighbors) / len(neighbors)
            avg_vy = sum(n[0].vy for n in neighbors) / len(neighbors)
            transform.vx += (avg_vx - transform.vx) * 0.1
            transform.vy += (avg_vy - transform.vy) * 0.1
        
        # Also move toward player
        distance = transform.distance_to(target_transform)
        if distance < ai_brain.awareness_range:
            angle_to_target = transform.angle_to(target_transform)
            angle_rad = math.radians(angle_to_target)
            transform.vx += math.cos(angle_rad) * physics.acceleration * dt * 0.2
            transform.vy += math.sin(angle_rad) * physics.acceleration * dt * 0.2
        
        # Rotate to face movement direction
        if transform.vx != 0 or transform.vy != 0:
            movement_angle = math.degrees(math.atan2(transform.vy, transform.vx))
            transform.angle = movement_angle
    
    def _update_boss(
        self, entity_id: str, transform: Transform, physics: Physics,
        ai_brain: AIBrain, target_transform: Transform, dt: float
    ):
        """Boss behavior: multi-phase state machine."""
        distance = transform.distance_to(target_transform)
        
        # Phase-based behavior
        if ai_brain.phase == 1:
            # Phase 1: Direct chase and fire
            if distance < ai_brain.awareness_range:
                angle_to_target = transform.angle_to(target_transform)
                angle_rad = math.radians(angle_to_target)
                transform.vx += math.cos(angle_rad) * physics.acceleration * dt * 0.5
                transform.vy += math.sin(angle_rad) * physics.acceleration * dt * 0.5
                transform.angle = angle_to_target
                
                weapon = self.entity_manager.get_component(entity_id, "Weapon")
                if weapon and distance <= ai_brain.attack_range and weapon.can_fire():
                    weapon.cooldown_remaining = 1.0 / weapon.fire_rate
        
        elif ai_brain.phase == 2:
            # Phase 2: Spread pattern attacks
            transform.angle += 30 * dt  # Rotate slowly
            weapon = self.entity_manager.get_component(entity_id, "Weapon")
            if weapon and distance <= ai_brain.attack_range * 1.5:
                if weapon.can_fire():
                    weapon.cooldown_remaining = 1.0 / weapon.fire_rate
                    weapon.spread = 30  # Wide spread
        
        # Transition phases based on health
        health = self.entity_manager.get_component(entity_id, "Health")
        if health:
            health_percent = health.hp / health.max_hp
            if health_percent < 0.5 and ai_brain.phase == 1:
                ai_brain.phase = 2
