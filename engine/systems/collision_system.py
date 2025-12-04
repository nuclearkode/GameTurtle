"""
Collision System

Detects and responds to collisions between entities.
Uses spatial hashing for broad-phase optimization.
"""

from engine.core.system import GameSystem
from engine.core.component import Transform, Collider, Projectile, Health, Physics, Wall
from engine.utils.math_utils import circle_circle_collision, distance_squared, normalize
from typing import List, Tuple, Set
from collections import defaultdict
import math


class CollisionEvent:
    """Represents a collision between two entities."""
    
    def __init__(self, entity_a_id: str, entity_b_id: str, 
                 normal_x: float = 0, normal_y: float = 0,
                 penetration: float = 0):
        self.entity_a_id = entity_a_id
        self.entity_b_id = entity_b_id
        self.normal_x = normal_x  # collision normal (from A to B)
        self.normal_y = normal_y
        self.penetration = penetration


class CollisionSystem(GameSystem):
    """
    Detects collisions and generates collision events.
    
    Features:
    - Spatial hashing for broad-phase optimization
    - Circle-circle collision detection
    - Collision tags/masks for filtering
    - Separation of trigger vs solid collisions
    
    Systems that need collision data should read collision_events.
    """
    
    def __init__(self, entity_manager, priority: int = 20):
        super().__init__(entity_manager, priority)
        self.collision_events: List[CollisionEvent] = []
        self.cell_size = 50  # spatial hash cell size
        self.spatial_hash: dict = {}
    
    def update(self, dt: float) -> None:
        """Detect collisions for this frame."""
        # Clear previous frame's events
        self.collision_events.clear()
        
        # Get all entities with colliders
        entities = self.entity_manager.query_entities(Transform, Collider)
        
        if len(entities) < 2:
            return
        
        # Build spatial hash for broad-phase
        self._build_spatial_hash(entities)
        
        # Check collisions
        checked_pairs: Set[Tuple[str, str]] = set()
        
        for entity in entities:
            transform = entity.get_component(Transform)
            collider = entity.get_component(Collider)
            
            # Get nearby entities from spatial hash
            nearby = self._get_nearby_entities(transform.x, transform.y, collider.radius)
            
            for other_id in nearby:
                # Skip self
                if other_id == entity.id:
                    continue
                
                # Skip if already checked this pair
                pair = tuple(sorted([entity.id, other_id]))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)
                
                other = self.entity_manager.get_entity(other_id)
                if not other or not other.active:
                    continue
                
                other_transform = other.get_component(Transform)
                other_collider = other.get_component(Collider)
                
                if not other_transform or not other_collider:
                    continue
                
                # Check collision masks (do these objects collide with each other?)
                if not self._should_collide(collider, other_collider):
                    continue
                
                # Narrow-phase: actual collision detection
                collision = self._check_collision(
                    transform, collider,
                    other_transform, other_collider
                )
                
                if collision:
                    self.collision_events.append(collision)
                    
                    # Apply collision response (push apart) for solid collisions
                    if not collider.is_trigger and not other_collider.is_trigger:
                        self._resolve_collision(entity, other, collision)
    
    def _build_spatial_hash(self, entities) -> None:
        """Build spatial hash for broad-phase collision detection."""
        self.spatial_hash.clear()
        
        for entity in entities:
            transform = entity.get_component(Transform)
            collider = entity.get_component(Collider)
            
            # Get all cells this entity overlaps
            cells = self._get_cells(transform.x, transform.y, collider.radius)
            
            for cell in cells:
                if cell not in self.spatial_hash:
                    self.spatial_hash[cell] = []
                self.spatial_hash[cell].append(entity.id)
    
    def _get_cells(self, x: float, y: float, radius: float) -> List[Tuple[int, int]]:
        """Get all spatial hash cells that overlap with a circle."""
        min_x = int((x - radius) // self.cell_size)
        max_x = int((x + radius) // self.cell_size)
        min_y = int((y - radius) // self.cell_size)
        max_y = int((y + radius) // self.cell_size)
        
        cells = []
        for cx in range(min_x, max_x + 1):
            for cy in range(min_y, max_y + 1):
                cells.append((cx, cy))
        return cells
    
    def _get_nearby_entities(self, x: float, y: float, radius: float) -> Set[str]:
        """Get all entities in nearby spatial hash cells."""
        cells = self._get_cells(x, y, radius)
        nearby = set()
        
        for cell in cells:
            if cell in self.spatial_hash:
                nearby.update(self.spatial_hash[cell])
        
        return nearby
    
    def _should_collide(self, collider_a: Collider, collider_b: Collider) -> bool:
        """Check if two colliders should collide based on tags/masks."""
        # If no masks are set, collide with everything
        if not collider_a.mask and not collider_b.mask:
            return True
        
        # Check if A's mask includes any of B's tags
        if collider_a.mask and collider_b.tags:
            if collider_a.mask & collider_b.tags:
                return True
        
        # Check if B's mask includes any of A's tags
        if collider_b.mask and collider_a.tags:
            if collider_b.mask & collider_a.tags:
                return True
        
        return False
    
    def _check_collision(self, transform_a: Transform, collider_a: Collider,
                        transform_b: Transform, collider_b: Collider) -> CollisionEvent:
        """Check if two entities are colliding (narrow-phase)."""
        # Currently only supports circle-circle
        if circle_circle_collision(
            transform_a.x, transform_a.y, collider_a.radius,
            transform_b.x, transform_b.y, collider_b.radius
        ):
            # Calculate collision normal and penetration
            dx = transform_b.x - transform_a.x
            dy = transform_b.y - transform_a.y
            dist = math.sqrt(dx * dx + dy * dy)
            
            if dist < 1e-6:
                # Entities at same position, use arbitrary normal
                normal_x, normal_y = 1, 0
                penetration = collider_a.radius + collider_b.radius
            else:
                normal_x = dx / dist
                normal_y = dy / dist
                penetration = (collider_a.radius + collider_b.radius) - dist
            
            # Use entity IDs directly from transform's parent entity
            # We'll need to pass entity IDs explicitly
            return CollisionEvent("", "", normal_x, normal_y, penetration)
        
        return None
    
    def _resolve_collision(self, entity_a, entity_b, collision: CollisionEvent) -> None:
        """Push entities apart to resolve collision."""
        # Update collision event with entity IDs
        collision.entity_a_id = entity_a.id
        collision.entity_b_id = entity_b.id
        
        transform_a = entity_a.get_component(Transform)
        transform_b = entity_b.get_component(Transform)
        
        # Check if either entity is a wall (immovable)
        wall_a = entity_a.has_component(Wall)
        wall_b = entity_b.has_component(Wall)
        
        if wall_a and wall_b:
            return  # Both walls, no movement
        
        # Calculate separation
        separation_x = collision.normal_x * collision.penetration
        separation_y = collision.normal_y * collision.penetration
        
        if wall_b:
            # Only move entity A away from wall
            transform_a.x -= separation_x
            transform_a.y -= separation_y
            # Stop velocity in direction of wall
            transform_a.vx = 0
            transform_a.vy = 0
        elif wall_a:
            # Only move entity B away from wall
            transform_b.x += separation_x
            transform_b.y += separation_y
            transform_b.vx = 0
            transform_b.vy = 0
        else:
            # Both entities can move, split separation
            transform_a.x -= separation_x * 0.5
            transform_a.y -= separation_y * 0.5
            transform_b.x += separation_x * 0.5
            transform_b.y += separation_y * 0.5
    
    def get_collisions_for_entity(self, entity_id: str) -> List[CollisionEvent]:
        """Get all collisions involving a specific entity."""
        return [
            event for event in self.collision_events
            if event.entity_a_id == entity_id or event.entity_b_id == entity_id
        ]
