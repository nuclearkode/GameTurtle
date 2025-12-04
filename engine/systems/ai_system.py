"""
AI System - Enemy behavior and decision making.

Processes entities with AIBrain components and applies
behavior-specific logic for different enemy types.
"""

from __future__ import annotations
import math
import random
from typing import TYPE_CHECKING, List, Optional, Tuple

from ..core.system import GameSystem, SystemPriority
from ..components.transform import Transform
from ..components.physics import Physics, Velocity
from ..components.weapon import Weapon
from ..components.ai import AIBrain, AIBehavior, AIState
from ..components.health import Health
from ..components.tags import PlayerTag, EnemyTag

if TYPE_CHECKING:
    from ..core.entity import Entity


class AISystem(GameSystem):
    """
    Handles all enemy AI behavior.
    
    Supported Behaviors:
    - CHASER: Moves directly toward player
    - TURRET: Stationary, rotates to face player, fires
    - SWARM: Flocking behavior (boids algorithm)
    - PATROL: Follows waypoints, chases if player in range
    - ORBIT: Circles around target at preferred distance
    - BOSS: Multi-phase state machine behavior
    - WANDER: Random movement
    - FLEE: Runs away from target
    """
    
    def __init__(self):
        super().__init__(priority=SystemPriority.AI)
        self._player_entity: Optional[Entity] = None
        self._player_transform: Optional[Transform] = None
    
    def update(self, dt: float) -> None:
        """Process AI for all entities with AIBrain."""
        # Validate dt
        if not isinstance(dt, (int, float)) or dt <= 0 or dt > 1.0:
            dt = 0.016  # Default to ~60fps
        
        # Cache player reference
        self._update_player_cache()
        
        # Get all AI entities
        try:
            ai_entities = list(self.entities.get_entities_with(AIBrain, Transform))
        except Exception:
            return
        
        for entity in ai_entities:
            # Skip destroyed entities
            if not self.entities.is_alive(entity):
                continue
                
            brain = self.entities.get_component(entity, AIBrain)
            transform = self.entities.get_component(entity, Transform)
            
            if not brain or not transform:
                continue
            
            try:
                # Update cooldowns
                if brain.current_attack_cooldown > 0:
                    brain.current_attack_cooldown -= dt
                
                brain.state_timer += dt
                
                # Process based on behavior type
                if brain.behavior == AIBehavior.CHASER:
                    self._process_chaser(entity, brain, transform, dt)
                elif brain.behavior == AIBehavior.TURRET:
                    self._process_turret(entity, brain, transform, dt)
                elif brain.behavior == AIBehavior.SWARM:
                    self._process_swarm(entity, brain, transform, ai_entities, dt)
                elif brain.behavior == AIBehavior.PATROL:
                    self._process_patrol(entity, brain, transform, dt)
                elif brain.behavior == AIBehavior.ORBIT:
                    self._process_orbit(entity, brain, transform, dt)
                elif brain.behavior == AIBehavior.BOSS:
                    self._process_boss(entity, brain, transform, dt)
                elif brain.behavior == AIBehavior.WANDER:
                    self._process_wander(entity, brain, transform, dt)
                elif brain.behavior == AIBehavior.FLEE:
                    self._process_flee(entity, brain, transform, dt)
            except Exception:
                # Continue processing other entities if one fails
                continue
    
    def _update_player_cache(self) -> None:
        """Find and cache player entity."""
        self._player_entity = self.entities.get_named("player")
        if not self._player_entity:
            for entity in self.entities.get_entities_with(PlayerTag):
                self._player_entity = entity
                break
        
        if self._player_entity:
            self._player_transform = self.entities.get_component(
                self._player_entity, Transform
            )
        else:
            self._player_transform = None
    
    def _get_direction_to_player(
        self,
        transform: Transform
    ) -> Tuple[float, float, float]:
        """Get normalized direction and distance to player."""
        if not self._player_transform:
            return (0, 0, float('inf'))
        
        dx = self._player_transform.x - transform.x
        dy = self._player_transform.y - transform.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > 0.001:
            return (dx / dist, dy / dist, dist)
        return (0, 0, 0)
    
    def _rotate_toward(
        self,
        transform: Transform,
        brain: AIBrain,
        target_x: float,
        target_y: float,
        dt: float
    ) -> float:
        """Smoothly rotate toward a target. Returns angle difference."""
        target_angle = transform.angle_to(target_x, target_y)
        
        # Calculate shortest rotation direction
        diff = target_angle - transform.angle
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        
        # Apply rotation with speed limit
        max_rotation = brain.turn_speed * dt
        if abs(diff) < max_rotation:
            transform.angle = target_angle
        else:
            transform.angle += math.copysign(max_rotation, diff)
        
        transform.angle = transform.angle % 360
        return diff
    
    def _apply_movement(
        self,
        entity: Entity,
        dir_x: float,
        dir_y: float,
        speed_mult: float = 1.0
    ) -> None:
        """Apply movement in a direction."""
        # Validate direction values
        if not math.isfinite(dir_x) or not math.isfinite(dir_y):
            return
        
        physics = self.entities.get_component(entity, Physics)
        velocity = self.entities.get_component(entity, Velocity)
        brain = self.entities.get_component(entity, AIBrain)
        
        if not brain:
            return
            
        # Clamp speed multiplier to reasonable values
        speed_mult = max(0.0, min(5.0, speed_mult))
        brain_speed = max(0.0, min(5.0, brain.speed_multiplier))
        
        if physics:
            base_speed = physics.acceleration * brain_speed * speed_mult
            if math.isfinite(base_speed):
                physics.accel_x = dir_x * base_speed
                physics.accel_y = dir_y * base_speed
        elif velocity:
            final_speed = 200 * brain_speed * speed_mult
            if math.isfinite(final_speed):
                velocity.vx = dir_x * final_speed
                velocity.vy = dir_y * final_speed
    
    def _try_attack(self, entity: Entity, brain: AIBrain) -> bool:
        """Attempt to fire weapon if possible."""
        weapon = self.entities.get_component(entity, Weapon)
        if weapon and brain.can_attack:
            weapon.is_firing = True
            brain.current_attack_cooldown = brain.attack_cooldown
            return True
        elif weapon:
            weapon.is_firing = False
        return False
    
    # Behavior implementations
    
    def _process_chaser(
        self,
        entity: Entity,
        brain: AIBrain,
        transform: Transform,
        dt: float
    ) -> None:
        """Chaser AI: Rush directly at player."""
        dir_x, dir_y, dist = self._get_direction_to_player(transform)
        
        if dist == float('inf'):
            brain.change_state(AIState.IDLE)
            return
        
        if dist < brain.awareness_range:
            brain.change_state(AIState.CHASING)
            
            # Rotate toward player
            if self._player_transform:
                self._rotate_toward(
                    transform, brain,
                    self._player_transform.x,
                    self._player_transform.y,
                    dt
                )
            
            # Move toward player
            self._apply_movement(entity, dir_x, dir_y)
            
            # Attack if in range
            if dist < brain.attack_range:
                brain.change_state(AIState.ATTACKING)
                self._try_attack(entity, brain)
        else:
            brain.change_state(AIState.SEEKING)
            # Wander or stay still
            physics = self.entities.get_component(entity, Physics)
            if physics:
                physics.accel_x = 0
                physics.accel_y = 0
    
    def _process_turret(
        self,
        entity: Entity,
        brain: AIBrain,
        transform: Transform,
        dt: float
    ) -> None:
        """Turret AI: Stationary, rotate and shoot."""
        dir_x, dir_y, dist = self._get_direction_to_player(transform)
        
        if dist == float('inf'):
            brain.change_state(AIState.IDLE)
            return
        
        # Stop movement (turrets don't move)
        physics = self.entities.get_component(entity, Physics)
        if physics:
            physics.accel_x = 0
            physics.accel_y = 0
        velocity = self.entities.get_component(entity, Velocity)
        if velocity:
            velocity.vx = 0
            velocity.vy = 0
        
        if dist < brain.awareness_range:
            # Rotate toward player
            if self._player_transform:
                angle_diff = self._rotate_toward(
                    transform, brain,
                    self._player_transform.x,
                    self._player_transform.y,
                    dt
                )
                
                # Only fire if roughly facing player
                if dist < brain.attack_range and abs(angle_diff) < 15:
                    brain.change_state(AIState.ATTACKING)
                    self._try_attack(entity, brain)
                else:
                    brain.change_state(AIState.SEEKING)
        else:
            brain.change_state(AIState.IDLE)
    
    def _process_swarm(
        self,
        entity: Entity,
        brain: AIBrain,
        transform: Transform,
        all_ai_entities: List[Entity],
        dt: float
    ) -> None:
        """Swarm AI: Flocking behavior (boids)."""
        # Boids forces
        separation = [0.0, 0.0]
        alignment = [0.0, 0.0]
        cohesion = [0.0, 0.0]
        neighbor_count = 0
        
        for other in all_ai_entities:
            if other.id == entity.id:
                continue
            
            other_brain = self.entities.get_component(other, AIBrain)
            if not other_brain or other_brain.behavior != AIBehavior.SWARM:
                continue
            
            other_transform = self.entities.get_component(other, Transform)
            if not other_transform:
                continue
            
            dx = other_transform.x - transform.x
            dy = other_transform.y - transform.y
            dist = math.sqrt(dx * dx + dy * dy)
            
            if dist < brain.neighbor_distance and dist > 0.001:
                neighbor_count += 1
                
                # Separation: push away from very close neighbors
                if dist < brain.separation_distance:
                    separation[0] -= dx / dist
                    separation[1] -= dy / dist
                
                # Alignment: match velocity of neighbors
                other_velocity = self.entities.get_component(other, Velocity)
                if other_velocity:
                    alignment[0] += other_velocity.vx
                    alignment[1] += other_velocity.vy
                
                # Cohesion: move toward center of flock
                cohesion[0] += dx
                cohesion[1] += dy
        
        # Normalize and weight forces
        move_x, move_y = 0.0, 0.0
        
        if neighbor_count > 0:
            # Separation
            sep_mag = math.sqrt(separation[0]**2 + separation[1]**2)
            if sep_mag > 0:
                move_x += (separation[0] / sep_mag) * brain.separation_weight
                move_y += (separation[1] / sep_mag) * brain.separation_weight
            
            # Alignment
            alignment[0] /= neighbor_count
            alignment[1] /= neighbor_count
            align_mag = math.sqrt(alignment[0]**2 + alignment[1]**2)
            if align_mag > 0:
                move_x += (alignment[0] / align_mag) * brain.alignment_weight
                move_y += (alignment[1] / align_mag) * brain.alignment_weight
            
            # Cohesion
            cohesion[0] /= neighbor_count
            cohesion[1] /= neighbor_count
            coh_mag = math.sqrt(cohesion[0]**2 + cohesion[1]**2)
            if coh_mag > 0:
                move_x += (cohesion[0] / coh_mag) * brain.cohesion_weight
                move_y += (cohesion[1] / coh_mag) * brain.cohesion_weight
        
        # Add attraction to player
        dir_x, dir_y, dist = self._get_direction_to_player(transform)
        if dist < brain.awareness_range:
            move_x += dir_x * 2.0
            move_y += dir_y * 2.0
            
            if dist < brain.attack_range:
                self._try_attack(entity, brain)
        
        # Normalize final direction
        mag = math.sqrt(move_x**2 + move_y**2)
        if mag > 0.001:
            move_x /= mag
            move_y /= mag
            self._apply_movement(entity, move_x, move_y)
            
            # Face movement direction
            transform.angle = math.degrees(math.atan2(move_y, move_x))
    
    def _process_patrol(
        self,
        entity: Entity,
        brain: AIBrain,
        transform: Transform,
        dt: float
    ) -> None:
        """Patrol AI: Follow waypoints, chase if player nearby."""
        dir_x, dir_y, dist = self._get_direction_to_player(transform)
        
        # Check if should chase player
        if dist < brain.awareness_range:
            # Switch to chasing
            if self._player_transform:
                self._rotate_toward(
                    transform, brain,
                    self._player_transform.x,
                    self._player_transform.y,
                    dt
                )
            self._apply_movement(entity, dir_x, dir_y)
            
            if dist < brain.attack_range:
                self._try_attack(entity, brain)
            return
        
        # Follow patrol waypoints
        waypoint = brain.get_current_waypoint()
        if not waypoint:
            return
        
        wp_dx = waypoint[0] - transform.x
        wp_dy = waypoint[1] - transform.y
        wp_dist = math.sqrt(wp_dx * wp_dx + wp_dy * wp_dy)
        
        if wp_dist < brain.waypoint_threshold:
            # Reached waypoint, move to next
            brain.advance_waypoint()
        else:
            # Move toward waypoint
            self._rotate_toward(transform, brain, waypoint[0], waypoint[1], dt)
            if wp_dist > 0.001:
                self._apply_movement(entity, wp_dx/wp_dist, wp_dy/wp_dist, 0.5)
    
    def _process_orbit(
        self,
        entity: Entity,
        brain: AIBrain,
        transform: Transform,
        dt: float
    ) -> None:
        """Orbit AI: Circle around target."""
        if not self._player_transform:
            return
        
        dir_x, dir_y, dist = self._get_direction_to_player(transform)
        
        if dist == float('inf'):
            return
        
        # Calculate orbit direction (perpendicular to player)
        orbit_x = -dir_y
        orbit_y = dir_x
        
        # Adjust distance to preferred range
        range_diff = dist - brain.preferred_range
        approach_weight = max(-1, min(1, range_diff / 50))
        
        move_x = orbit_x + dir_x * approach_weight
        move_y = orbit_y + dir_y * approach_weight
        
        mag = math.sqrt(move_x**2 + move_y**2)
        if mag > 0.001:
            self._apply_movement(entity, move_x/mag, move_y/mag)
        
        # Always face player
        self._rotate_toward(
            transform, brain,
            self._player_transform.x,
            self._player_transform.y,
            dt
        )
        
        # Attack if in range
        if dist < brain.attack_range:
            self._try_attack(entity, brain)
    
    def _process_boss(
        self,
        entity: Entity,
        brain: AIBrain,
        transform: Transform,
        dt: float
    ) -> None:
        """Boss AI: Multi-phase behavior."""
        health = self.entities.get_component(entity, Health)
        
        # Check for phase transition
        if health and brain.boss_phase < len(brain.phase_hp_thresholds):
            threshold = brain.phase_hp_thresholds[brain.boss_phase]
            if health.health_percent <= threshold:
                brain.boss_phase += 1
                brain.change_state(AIState.IDLE, duration=1.0)  # Brief pause
        
        # Phase-specific behavior
        if brain.state == AIState.IDLE and brain.state_timer < brain.state_duration:
            # Pause between phases
            return
        
        phase = brain.boss_phase
        
        if phase == 0:
            # Phase 1: Aggressive chasing
            self._process_chaser(entity, brain, transform, dt)
        elif phase == 1:
            # Phase 2: Orbit and shoot
            brain.speed_multiplier = 1.3
            self._process_orbit(entity, brain, transform, dt)
        else:
            # Phase 3: Desperate rush
            brain.speed_multiplier = 1.5
            brain.attack_cooldown = 0.3
            self._process_chaser(entity, brain, transform, dt)
    
    def _process_wander(
        self,
        entity: Entity,
        brain: AIBrain,
        transform: Transform,
        dt: float
    ) -> None:
        """Wander AI: Random movement."""
        # Change direction periodically
        if brain.state_timer > brain.state_duration:
            new_angle = random.uniform(0, 360)
            brain.state_duration = random.uniform(1.0, 3.0)
            brain.change_state(AIState.SEEKING, brain.state_duration)
        
        # Move forward
        fx, fy = transform.forward_vector()
        self._apply_movement(entity, fx, fy, 0.5)
        
        # Slight random turning
        velocity = self.entities.get_component(entity, Velocity)
        if velocity:
            velocity.angular = random.uniform(-30, 30)
    
    def _process_flee(
        self,
        entity: Entity,
        brain: AIBrain,
        transform: Transform,
        dt: float
    ) -> None:
        """Flee AI: Run away from player."""
        dir_x, dir_y, dist = self._get_direction_to_player(transform)
        
        if dist < brain.awareness_range:
            # Run away
            self._apply_movement(entity, -dir_x, -dir_y, 1.2)
            
            # Face away from player
            transform.angle = math.degrees(math.atan2(-dir_y, -dir_x))
        else:
            # Safe, stop fleeing
            brain.change_state(AIState.IDLE)
            physics = self.entities.get_component(entity, Physics)
            if physics:
                physics.accel_x = 0
                physics.accel_y = 0
