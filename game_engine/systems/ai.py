"""
AISystem - handles AI behavior for enemies.
Chaser, Turret, Swarm, and Boss behaviors.
"""

import random
import math
from game_engine.core.system import GameSystem
from game_engine.core.component import (
    Transform, AIBrain, Physics, Collider, Weapon, Health
)
from game_engine.core.component import AIBehaviorType
from game_engine.utils.math_utils import distance, angle_between, normalize
from game_engine.input.input_handler import InputAction


class AISystem(GameSystem):
    """
    Updates AI behavior for enemies.
    Each behavior type has different logic.
    """
    
    def __init__(self, entity_manager, component_registry, player_id: str):
        super().__init__(entity_manager, component_registry)
        self.player_id = player_id
    
    def update(self, dt: float) -> None:
        """Update all AI entities"""
        entities = self.registry.get_entities_with(Transform, AIBrain)
        
        player_transform = self.entity_manager.get_component(self.player_id, Transform)
        if not player_transform:
            return
        
        for entity_id in entities:
            transform = self.entity_manager.get_component(entity_id, Transform)
            brain = self.entity_manager.get_component(entity_id, AIBrain)
            physics = self.entity_manager.get_component(entity_id, Physics)
            
            if not transform or not brain:
                continue
            
            # Update cooldowns
            for key in list(brain.cooldowns.keys()):
                brain.cooldowns[key] = max(0.0, brain.cooldowns[key] - dt)
            
            # Behavior-specific logic
            if brain.behavior_type == AIBehaviorType.CHASER:
                self._update_chaser(entity_id, transform, brain, physics, player_transform, dt)
            elif brain.behavior_type == AIBehaviorType.TURRET:
                self._update_turret(entity_id, transform, brain, physics, player_transform, dt)
            elif brain.behavior_type == AIBehaviorType.SWARM:
                self._update_swarm(entity_id, transform, brain, physics, player_transform, dt)
            elif brain.behavior_type == AIBehaviorType.BOSS:
                self._update_boss(entity_id, transform, brain, physics, player_transform, dt)
    
    def _update_chaser(self, entity_id: str, transform: Transform, brain: AIBrain,
                      physics: Optional[Physics], player_transform: Transform, dt: float) -> None:
        """Chaser: move directly toward player"""
        dist = distance(transform.x, transform.y, player_transform.x, player_transform.y)
        
        if dist < brain.awareness_range:
            brain.target_id = self.player_id
            brain.state = "chasing"
            
            # Move toward player
            if physics:
                dx = player_transform.x - transform.x
                dy = player_transform.y - transform.y
                dir_x, dir_y = normalize(dx, dy)
                
                # Apply acceleration
                transform.vx += dir_x * physics.acceleration * dt
                transform.vy += dir_y * physics.acceleration * dt
                
                # Face movement direction
                transform.angle = angle_between(transform.x, transform.y,
                                               player_transform.x, player_transform.y)
        else:
            brain.state = "idle"
            brain.target_id = None
    
    def _update_turret(self, entity_id: str, transform: Transform, brain: AIBrain,
                      physics: Optional[Physics], player_transform: Transform, dt: float) -> None:
        """Turret: stationary, rotate to face player, fire when in range"""
        dist = distance(transform.x, transform.y, player_transform.x, player_transform.y)
        
        if dist < brain.awareness_range:
            brain.target_id = self.player_id
            brain.state = "tracking"
            
            # Rotate to face player
            target_angle = angle_between(transform.x, transform.y,
                                        player_transform.x, player_transform.y)
            
            # Smooth rotation
            angle_diff = target_angle - transform.angle
            # Normalize angle difference to [-180, 180]
            while angle_diff > 180:
                angle_diff -= 360
            while angle_diff < -180:
                angle_diff += 360
            
            rotation_speed = 90.0  # degrees per second
            max_rotation = rotation_speed * dt
            if abs(angle_diff) < max_rotation:
                transform.angle = target_angle
            else:
                transform.angle += max_rotation if angle_diff > 0 else -max_rotation
            
            # Fire if in attack range
            if dist < brain.attack_range:
                brain.state = "attacking"
                weapon = self.entity_manager.get_component(entity_id, Weapon)
                if weapon and weapon.cooldown <= 0:
                    # Signal to fire (WeaponSystem will handle actual firing)
                    brain.cooldowns["fire"] = 0.0
        else:
            brain.state = "idle"
            brain.target_id = None
    
    def _update_swarm(self, entity_id: str, transform: Transform, brain: AIBrain,
                     physics: Optional[Physics], player_transform: Transform, dt: float) -> None:
        """Swarm: boids-like behavior - cohesion, separation, alignment"""
        dist = distance(transform.x, transform.y, player_transform.x, player_transform.y)
        
        if dist < brain.awareness_range:
            brain.target_id = self.player_id
            
            # Get nearby swarm members
            swarm_entities = self.registry.get_entities_with(Transform, AIBrain)
            neighbors = []
            for other_id in swarm_entities:
                if other_id == entity_id:
                    continue
                other_brain = self.entity_manager.get_component(other_id, AIBrain)
                if other_brain and other_brain.behavior_type == AIBehaviorType.SWARM:
                    other_transform = self.entity_manager.get_component(other_id, Transform)
                    if other_transform:
                        neighbor_dist = distance(transform.x, transform.y,
                                               other_transform.x, other_transform.y)
                        if neighbor_dist < 100.0:  # Neighbor radius
                            neighbors.append((other_transform, neighbor_dist))
            
            # Limit neighbor count for performance
            neighbors.sort(key=lambda n: n[1])
            neighbors = neighbors[:5]
            
            if physics:
                # Cohesion: move toward center of neighbors
                cohesion_x, cohesion_y = 0.0, 0.0
                if neighbors:
                    avg_x = sum(n[0].x for n in neighbors) / len(neighbors)
                    avg_y = sum(n[0].y for n in neighbors) / len(neighbors)
                    cohesion_x = avg_x - transform.x
                    cohesion_y = avg_y - transform.y
                    cohesion_x, cohesion_y = normalize(cohesion_x, cohesion_y)
                    cohesion_x *= 0.5  # Weight
                    cohesion_y *= 0.5
                
                # Separation: avoid neighbors
                separation_x, separation_y = 0.0, 0.0
                for neighbor_transform, neighbor_dist in neighbors:
                    if neighbor_dist < 30.0:  # Separation distance
                        dx = transform.x - neighbor_transform.x
                        dy = transform.y - neighbor_transform.y
                        sep_x, sep_y = normalize(dx, dy)
                        separation_x += sep_x / neighbor_dist
                        separation_y += sep_y / neighbor_dist
                if neighbors:
                    separation_x /= len(neighbors)
                    separation_y /= len(neighbors)
                    separation_x *= 1.5  # Weight
                    separation_y *= 1.5
                
                # Seek player
                seek_x = player_transform.x - transform.x
                seek_y = player_transform.y - transform.y
                seek_x, seek_y = normalize(seek_x, seek_y)
                seek_x *= 0.8
                seek_y *= 0.8
                
                # Combine forces
                total_x = cohesion_x + separation_x + seek_x
                total_y = cohesion_y + separation_y + seek_y
                total_x, total_y = normalize(total_x, total_y)
                
                # Apply acceleration
                transform.vx += total_x * physics.acceleration * dt
                transform.vy += total_y * physics.acceleration * dt
                
                # Face movement direction
                if total_x != 0 or total_y != 0:
                    transform.angle = angle_between(0, 0, total_x, total_y)
        else:
            brain.state = "idle"
    
    def _update_boss(self, entity_id: str, transform: Transform, brain: AIBrain,
                    physics: Optional[Physics], player_transform: Transform, dt: float) -> None:
        """Boss: multi-phase behavior"""
        dist = distance(transform.x, transform.y, player_transform.x, player_transform.y)
        
        if dist < brain.awareness_range:
            brain.target_id = self.player_id
            
            health = self.entity_manager.get_component(entity_id, Health)
            if health:
                # Phase transitions based on health
                if health.hp / health.max_hp > 0.66:
                    brain.phase = 1
                elif health.hp / health.max_hp > 0.33:
                    brain.phase = 2
                else:
                    brain.phase = 3
            
            # Phase 1: Direct chase and fire
            if brain.phase == 1:
                if physics:
                    dx = player_transform.x - transform.x
                    dy = player_transform.y - transform.y
                    dir_x, dir_y = normalize(dx, dy)
                    transform.vx += dir_x * physics.acceleration * dt * 0.5  # Slower movement
                    transform.vy += dir_y * physics.acceleration * dt * 0.5
                    transform.angle = angle_between(transform.x, transform.y,
                                                   player_transform.x, player_transform.y)
            
            # Phase 2: Spread fire pattern
            elif brain.phase == 2:
                weapon = self.entity_manager.get_component(entity_id, Weapon)
                if weapon:
                    weapon.bullet_count = 3
                    weapon.spread = 30.0
            
            # Phase 3: Aggressive movement + spread
            elif brain.phase == 3:
                if physics:
                    dx = player_transform.x - transform.x
                    dy = player_transform.y - transform.y
                    dir_x, dir_y = normalize(dx, dy)
                    transform.vx += dir_x * physics.acceleration * dt * 0.7
                    transform.vy += dir_y * physics.acceleration * dt * 0.7
                    transform.angle = angle_between(transform.x, transform.y,
                                                   player_transform.x, player_transform.y)
                
                weapon = self.entity_manager.get_component(entity_id, Weapon)
                if weapon:
                    weapon.bullet_count = 5
                    weapon.spread = 45.0
