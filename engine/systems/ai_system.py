"""
AI System

Handles enemy AI behaviors: chaser, turret, swarm, boss.
"""

import math
from engine.core.system import GameSystem
from engine.core.component import (
    AIBrain, AIBehavior, AIState, Transform, Physics, Player, Weapon
)
from engine.utils.math_utils import (
    distance, normalize, angle_to, angle_difference, move_toward_angle
)
from typing import List, Tuple


class AISystem(GameSystem):
    """
    AI behavior system for enemies.
    
    Responsibilities:
    - Find and track targets (usually the player)
    - Execute behavior-specific logic
    - Update AI state machines
    - Set desired velocities and actions
    """
    
    def __init__(self, entity_manager, weapon_system=None, priority: int = 5):
        super().__init__(entity_manager, priority)
        self.weapon_system = weapon_system
    
    def update(self, dt: float) -> None:
        """Update all AI entities."""
        # Find player position (common target for most AI)
        player_pos = self._get_player_position()
        
        # Update each AI entity
        ai_entities = self.entity_manager.query_entities(AIBrain, Transform)
        
        for entity in ai_entities:
            ai = entity.get_component(AIBrain)
            transform = entity.get_component(Transform)
            
            # Update cooldowns
            if ai.attack_cooldown > 0:
                ai.attack_cooldown -= dt
            if ai.state_change_cooldown > 0:
                ai.state_change_cooldown -= dt
            
            # Update target
            if player_pos:
                ai.target_id = "player"  # Simplified - assumes single player
            
            # Dispatch to behavior handler
            if ai.behavior_type == AIBehavior.CHASER:
                self._update_chaser(entity, ai, transform, player_pos, dt)
            elif ai.behavior_type == AIBehavior.TURRET:
                self._update_turret(entity, ai, transform, player_pos, dt)
            elif ai.behavior_type == AIBehavior.SWARM:
                self._update_swarm(entity, ai, transform, player_pos, dt)
            elif ai.behavior_type == AIBehavior.BOSS:
                self._update_boss(entity, ai, transform, player_pos, dt)
    
    def _get_player_position(self) -> Tuple[float, float]:
        """Get player position."""
        player_entities = self.entity_manager.query_entities(Player, Transform)
        if player_entities:
            transform = player_entities[0].get_component(Transform)
            return (transform.x, transform.y)
        return None
    
    def _update_chaser(self, entity, ai: AIBrain, transform: Transform, 
                       player_pos: Tuple[float, float], dt: float) -> None:
        """
        Chaser AI: Rushes toward the player.
        
        States:
        - IDLE: Not aware of player
        - CHASE: Moving toward player
        - ATTACK: Close to player (could trigger special attack)
        """
        if not player_pos:
            ai.state = AIState.IDLE
            return
        
        # Calculate distance to player
        dist = distance(transform.x, transform.y, player_pos[0], player_pos[1])
        
        # State transitions
        if dist > ai.awareness_range:
            ai.state = AIState.IDLE
        elif dist <= ai.attack_range:
            ai.state = AIState.ATTACK
        else:
            ai.state = AIState.CHASE
        
        # Behavior
        physics = entity.get_component(Physics)
        
        if ai.state == AIState.IDLE:
            # Stand still or patrol
            if physics:
                transform.vx = 0
                transform.vy = 0
        
        elif ai.state == AIState.CHASE or ai.state == AIState.ATTACK:
            # Move toward player, maintaining personal space
            if dist > ai.personal_space:
                # Calculate direction to player
                dx = player_pos[0] - transform.x
                dy = player_pos[1] - transform.y
                nx, ny = normalize(dx, dy)
                
                # Set velocity
                if physics:
                    move_speed = physics.max_speed
                    transform.vx = nx * move_speed
                    transform.vy = ny * move_speed
                    
                    # Rotate to face movement direction
                    if physics.can_rotate:
                        target_angle = angle_to(transform.x, transform.y, player_pos[0], player_pos[1])
                        transform.angle = move_toward_angle(transform.angle, target_angle, 
                                                           physics.rotation_speed * dt)
            else:
                # Too close, stop
                if physics:
                    transform.vx = 0
                    transform.vy = 0
    
    def _update_turret(self, entity, ai: AIBrain, transform: Transform,
                       player_pos: Tuple[float, float], dt: float) -> None:
        """
        Turret AI: Stationary, rotates to track player, shoots when in range.
        
        States:
        - IDLE: No target in range
        - TRACKING: Rotating to face target
        - ATTACK: Firing at target
        """
        if not player_pos:
            ai.state = AIState.IDLE
            return
        
        # Calculate distance to player
        dist = distance(transform.x, transform.y, player_pos[0], player_pos[1])
        
        # State transitions
        if dist > ai.attack_range:
            ai.state = AIState.IDLE
        else:
            # Calculate angle to player
            target_angle = angle_to(transform.x, transform.y, player_pos[0], player_pos[1])
            angle_diff = abs(angle_difference(transform.angle, target_angle))
            
            if angle_diff > 5:  # Not facing player
                ai.state = AIState.TRACKING
            else:
                ai.state = AIState.ATTACK
        
        # Behavior
        physics = entity.get_component(Physics)
        
        if ai.state == AIState.IDLE:
            # Idle animation (could slowly rotate)
            pass
        
        elif ai.state == AIState.TRACKING or ai.state == AIState.ATTACK:
            # Rotate to face player
            target_angle = angle_to(transform.x, transform.y, player_pos[0], player_pos[1])
            
            if physics and physics.can_rotate:
                transform.angle = move_toward_angle(transform.angle, target_angle,
                                                   physics.rotation_speed * dt)
            
            # Shoot when aimed and cooldown ready
            if ai.state == AIState.ATTACK and ai.attack_cooldown <= 0:
                weapon = entity.get_component(Weapon)
                if weapon and self.weapon_system:
                    if self.weapon_system.fire_weapon(entity.id):
                        ai.attack_cooldown = 1.0  # 1 second between shots
    
    def _update_swarm(self, entity, ai: AIBrain, transform: Transform,
                      player_pos: Tuple[float, float], dt: float) -> None:
        """
        Swarm AI: Flocking behavior with player as attractor.
        
        Uses simplified boids:
        - Cohesion: Move toward center of nearby swarm members
        - Separation: Avoid crowding neighbors
        - Alignment: Match velocity of neighbors
        - Target: Bias toward player
        """
        # Get nearby swarm members
        neighbors = self._get_neighbors(entity, ai.flock_radius, ai.max_neighbors)
        
        # Initialize forces
        cohesion_x, cohesion_y = 0.0, 0.0
        separation_x, separation_y = 0.0, 0.0
        alignment_x, alignment_y = 0.0, 0.0
        target_x, target_y = 0.0, 0.0
        
        # Calculate cohesion (move toward center of flock)
        if neighbors:
            center_x = sum(t.x for _, t, _ in neighbors) / len(neighbors)
            center_y = sum(t.y for _, t, _ in neighbors) / len(neighbors)
            cohesion_x, cohesion_y = normalize(center_x - transform.x, center_y - transform.y)
        
        # Calculate separation (avoid crowding)
        for _, other_transform, _ in neighbors:
            dx = transform.x - other_transform.x
            dy = transform.y - other_transform.y
            dist = distance(transform.x, transform.y, other_transform.x, other_transform.y)
            if dist > 0.1:
                # Force inversely proportional to distance
                force = 1.0 / dist
                separation_x += (dx / dist) * force
                separation_y += (dy / dist) * force
        
        if neighbors:
            separation_x /= len(neighbors)
            separation_y /= len(neighbors)
            sep_mag = math.sqrt(separation_x**2 + separation_y**2)
            if sep_mag > 0:
                separation_x /= sep_mag
                separation_y /= sep_mag
        
        # Calculate alignment (match velocity)
        if neighbors:
            avg_vx = sum(t.vx for _, t, _ in neighbors) / len(neighbors)
            avg_vy = sum(t.vy for _, t, _ in neighbors) / len(neighbors)
            alignment_x, alignment_y = normalize(avg_vx, avg_vy)
        
        # Calculate target attraction (toward player)
        if player_pos:
            dist_to_player = distance(transform.x, transform.y, player_pos[0], player_pos[1])
            if dist_to_player > ai.personal_space:
                target_x, target_y = normalize(
                    player_pos[0] - transform.x,
                    player_pos[1] - transform.y
                )
        
        # Combine forces with weights
        cohesion_weight = 1.0
        separation_weight = 2.0  # Avoid crowding is important
        alignment_weight = 1.0
        target_weight = 1.5  # Bias toward target
        
        desired_x = (cohesion_x * cohesion_weight +
                    separation_x * separation_weight +
                    alignment_x * alignment_weight +
                    target_x * target_weight)
        desired_y = (cohesion_y * cohesion_weight +
                    separation_y * separation_weight +
                    alignment_y * alignment_weight +
                    target_y * target_weight)
        
        # Normalize and apply
        desired_x, desired_y = normalize(desired_x, desired_y)
        
        physics = entity.get_component(Physics)
        if physics:
            move_speed = physics.max_speed * 0.8  # Swarm is slightly slower
            transform.vx = desired_x * move_speed
            transform.vy = desired_y * move_speed
            
            # Rotate to face movement direction
            if physics.can_rotate and (desired_x != 0 or desired_y != 0):
                target_angle = math.degrees(math.atan2(desired_y, desired_x))
                transform.angle = move_toward_angle(transform.angle, target_angle,
                                                   physics.rotation_speed * dt)
    
    def _update_boss(self, entity, ai: AIBrain, transform: Transform,
                     player_pos: Tuple[float, float], dt: float) -> None:
        """
        Boss AI: Multi-phase state machine.
        
        Phases stored in ai.custom_data['phase']:
        - Phase 1: Chase player, shoot single bullets
        - Phase 2 (<66% HP): Spread fire pattern
        - Phase 3 (<33% HP): Summon minions
        """
        # Initialize phase if needed
        if 'phase' not in ai.custom_data:
            ai.custom_data['phase'] = 1
        
        # Check health for phase transitions
        health = entity.get_component(Health)
        if health:
            hp_percent = health.hp / health.max_hp
            if hp_percent < 0.33 and ai.custom_data['phase'] < 3:
                ai.custom_data['phase'] = 3
            elif hp_percent < 0.66 and ai.custom_data['phase'] < 2:
                ai.custom_data['phase'] = 2
        
        phase = ai.custom_data['phase']
        
        # Phase-specific behavior
        if phase == 1:
            # Simple chase and shoot
            self._update_chaser(entity, ai, transform, player_pos, dt)
            if ai.attack_cooldown <= 0:
                weapon = entity.get_component(Weapon)
                if weapon and self.weapon_system:
                    if self.weapon_system.fire_weapon(entity.id):
                        ai.attack_cooldown = 2.0
        
        elif phase == 2:
            # Spread shot pattern
            self._update_chaser(entity, ai, transform, player_pos, dt)
            if ai.attack_cooldown <= 0:
                weapon = entity.get_component(Weapon)
                if weapon and self.weapon_system:
                    # Fire 3 bullets in spread pattern
                    old_count = weapon.bullet_count
                    old_spread = weapon.spread
                    weapon.bullet_count = 5
                    weapon.spread = 60
                    self.weapon_system.fire_weapon(entity.id)
                    weapon.bullet_count = old_count
                    weapon.spread = old_spread
                    ai.attack_cooldown = 3.0
        
        elif phase == 3:
            # TODO: Summon minions (requires wave system integration)
            self._update_turret(entity, ai, transform, player_pos, dt)
    
    def _get_neighbors(self, entity, radius: float, max_neighbors: int) -> List:
        """Get nearby entities with AIBrain (for flocking)."""
        transform = entity.get_component(Transform)
        neighbors = []
        
        all_ai = self.entity_manager.query_entities(AIBrain, Transform)
        
        for other in all_ai:
            if other.id == entity.id:
                continue
            
            other_transform = other.get_component(Transform)
            dist = distance(transform.x, transform.y, other_transform.x, other_transform.y)
            
            if dist <= radius:
                neighbors.append((other, other_transform, dist))
        
        # Sort by distance and limit
        neighbors.sort(key=lambda x: x[2])
        return neighbors[:max_neighbors]
