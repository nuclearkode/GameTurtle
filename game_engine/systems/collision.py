"""
CollisionSystem - handles collision detection and response.
Uses circular colliders for simplicity.
"""

from typing import List, Tuple, Optional
from game_engine.core.system import GameSystem
from game_engine.core.component import Transform, Collider, Projectile, Health
from game_engine.utils.math_utils import distance_squared


class CollisionSystem(GameSystem):
    """
    Broad-phase and narrow-phase collision detection.
    Handles projectile-enemy, enemy-player, entity-wall collisions.
    """
    
    def __init__(self, entity_manager, component_registry, arena_bounds=None):
        super().__init__(entity_manager, component_registry)
        self.arena_bounds = arena_bounds or (-400, -400, 400, 400)  # (min_x, min_y, max_x, max_y)
    
    def update(self, dt: float) -> None:
        """Check collisions and apply damage"""
        # Get all collidable entities
        collidables = self.registry.get_entities_with(Transform, Collider)
        projectiles = self.registry.get_entities_with(Transform, Collider, Projectile)
        
        # Check projectile vs non-projectile collisions
        for proj_id in projectiles:
            proj_transform = self.entity_manager.get_component(proj_id, Transform)
            proj_collider = self.entity_manager.get_component(proj_id, Collider)
            proj_projectile = self.entity_manager.get_component(proj_id, Projectile)
            
            if not all([proj_transform, proj_collider, proj_projectile]):
                continue
            
            # Check collision with other entities
            for entity_id in collidables:
                if entity_id == proj_id or entity_id == proj_projectile.owner_id:
                    continue
                
                entity_transform = self.entity_manager.get_component(entity_id, Transform)
                entity_collider = self.entity_manager.get_component(entity_id, Collider)
                
                if not entity_transform or not entity_collider:
                    continue
                
                # Skip if hitting another projectile
                if "projectile" in entity_collider.tags:
                    continue
                
                # Check collision using tags (more flexible than masks)
                # Projectiles hit enemies and player (not other projectiles)
                if "enemy" not in entity_collider.tags and "player" not in entity_collider.tags:
                    continue
                
                # Circular collision check
                dist_sq = distance_squared(
                    proj_transform.x, proj_transform.y,
                    entity_transform.x, entity_transform.y
                )
                radius_sum = proj_collider.radius + entity_collider.radius
                
                if dist_sq < radius_sum * radius_sum:
                    # Collision! Apply damage
                    self._handle_projectile_hit(proj_id, entity_id, proj_projectile)
                    break
        
        # Check wall collisions
        for entity_id in collidables:
            transform = self.entity_manager.get_component(entity_id, Transform)
            collider = self.entity_manager.get_component(entity_id, Collider)
            
            if not transform or not collider:
                continue
            
            min_x, min_y, max_x, max_y = self.arena_bounds
            
            # Bounce off walls
            if transform.x - collider.radius < min_x:
                transform.x = min_x + collider.radius
                transform.vx *= -0.5  # Bounce with damping
            elif transform.x + collider.radius > max_x:
                transform.x = max_x - collider.radius
                transform.vx *= -0.5
            
            if transform.y - collider.radius < min_y:
                transform.y = min_y + collider.radius
                transform.vy *= -0.5
            elif transform.y + collider.radius > max_y:
                transform.y = max_y - collider.radius
                transform.vy *= -0.5
    
    def _handle_projectile_hit(self, proj_id: str, target_id: str, projectile: Projectile) -> None:
        """Handle projectile hitting target"""
        # Don't hit owner
        if target_id == projectile.owner_id:
            return
        
        # Apply damage
        health = self.entity_manager.get_component(target_id, Health)
        if health:
            damage = projectile.damage
            # Apply armor reduction
            if hasattr(health, 'armor'):
                damage *= (1.0 - health.armor)
            health.hp -= damage
        
        # Destroy projectile if no pierce left
        if projectile.pierce_count <= 0:
            self.entity_manager.destroy_entity(proj_id)
        else:
            projectile.pierce_count -= 1
