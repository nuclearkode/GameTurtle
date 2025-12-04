"""CollisionSystem: broad-phase and narrow-phase collision detection."""

import math
from typing import List, Tuple
from ..core.system import GameSystem
from ..core.component import Transform, Collider, Projectile, Health, Shield


class CollisionSystem(GameSystem):
    """Handles collision detection and resolution."""
    
    def __init__(self, entity_manager, component_registry):
        super().__init__(entity_manager, component_registry)
        self.priority = 3  # Run after physics and AI
    
    def update(self, dt: float):
        """Check collisions and resolve them."""
        # Get all entities with Transform and Collider
        entity_ids = list(self.component_registry.get_entities_with("Transform", "Collider"))
        
        # Check all pairs (simple O(n²) - could be optimized with spatial partitioning)
        for i, entity_id_a in enumerate(entity_ids):
            transform_a = self.entity_manager.get_component(entity_id_a, "Transform")
            collider_a = self.entity_manager.get_component(entity_id_a, "Collider")
            
            if not transform_a or not collider_a:
                continue
            
            for entity_id_b in entity_ids[i + 1:]:
                transform_b = self.entity_manager.get_component(entity_id_b, "Transform")
                collider_b = self.entity_manager.get_component(entity_id_b, "Collider")
                
                if not transform_b or not collider_b:
                    continue
                
                # Check if collision masks allow collision
                if not collider_a.collides_with(collider_b):
                    continue
                
                # Check distance
                distance = transform_a.distance_to(transform_b)
                min_distance = collider_a.radius + collider_b.radius
                
                if distance < min_distance:
                    self._handle_collision(
                        entity_id_a, transform_a, collider_a,
                        entity_id_b, transform_b, collider_b,
                        distance, min_distance, dt
                    )
    
    def _handle_collision(
        self,
        entity_id_a: str, transform_a: Transform, collider_a: Collider,
        entity_id_b: str, transform_b: Transform, collider_b: Collider,
        distance: float, min_distance: float, dt: float
    ):
        """Handle a collision between two entities."""
        # Check if one is a projectile
        projectile_a = self.entity_manager.get_component(entity_id_a, "Projectile")
        projectile_b = self.entity_manager.get_component(entity_id_b, "Projectile")
        
        # Projectile vs non-projectile collisions
        if projectile_a and not projectile_b:
            self._handle_projectile_collision(entity_id_a, entity_id_b, projectile_a)
        elif projectile_b and not projectile_a:
            self._handle_projectile_collision(entity_id_b, entity_id_a, projectile_b)
        elif not projectile_a and not projectile_b:
            # Entity vs entity collision - push apart
            self._resolve_collision(
                transform_a, collider_a,
                transform_b, collider_b,
                distance, min_distance
            )
    
    def _handle_projectile_collision(self, projectile_id: str, target_id: str, projectile: Projectile):
        """Handle projectile hitting a target."""
        # Don't hit the owner
        if target_id == projectile.owner_id:
            return
        
        # Check if projectile already hit this target (piercing)
        if target_id in projectile.targets_hit and not projectile.piercing:
            return
        
        # Check tags - projectiles might ignore certain entities
        target_collider = self.entity_manager.get_component(target_id, "Collider")
        if target_collider and "projectile" in target_collider.tags:
            return  # Don't collide with other projectiles
        
        # Apply damage
        health = self.entity_manager.get_component(target_id, "Health")
        if health:
            # Check shield first
            shield = self.entity_manager.get_component(target_id, "Shield")
            if shield and shield.is_active():
                shield.hp -= projectile.damage
                shield.time_since_damage = 0.0
                if shield.hp < 0:
                    # Excess damage goes to health
                    health.hp += shield.hp
                    shield.hp = 0
            else:
                health.hp -= projectile.damage
            
            projectile.targets_hit.add(target_id)
        
        # Destroy projectile if not piercing or already hit this target
        if not projectile.piercing or target_id in projectile.targets_hit:
            self.entity_manager.destroy_entity(projectile_id)
    
    def _resolve_collision(
        self,
        transform_a: Transform, collider_a: Collider,
        transform_b: Transform, collider_b: Collider,
        distance: float, min_distance: float
    ):
        """Push two entities apart."""
        if distance == 0:
            # Avoid division by zero
            return
        
        # Calculate overlap
        overlap = min_distance - distance
        
        # Calculate separation direction (normalized)
        dx = (transform_b.x - transform_a.x) / distance
        dy = (transform_b.y - transform_a.y) / distance
        
        # Push apart (simple resolution - could use mass)
        separation = overlap * 0.5
        transform_a.x -= dx * separation
        transform_a.y -= dy * separation
        transform_b.x += dx * separation
        transform_b.y += dy * separation
        
        # Dampen velocities
        transform_a.vx *= 0.8
        transform_a.vy *= 0.8
        transform_b.vx *= 0.8
        transform_b.vy *= 0.8
