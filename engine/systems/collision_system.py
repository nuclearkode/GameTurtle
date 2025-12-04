"""
Collision System - Collision detection and response.

Uses a two-phase approach:
1. Broad phase: Spatial partitioning to quickly cull non-colliding pairs
2. Narrow phase: Precise collision tests for candidate pairs
"""

from __future__ import annotations
import math
from typing import TYPE_CHECKING, List, Tuple, Dict, Set
from dataclasses import dataclass

from ..core.system import GameSystem, SystemPriority
from ..core.events import CollisionEvent
from ..components.transform import Transform
from ..components.physics import Velocity, Physics
from ..components.collider import Collider, ColliderType, CollisionMask

if TYPE_CHECKING:
    from ..core.entity import Entity


@dataclass
class CollisionPair:
    """Data about a collision between two entities."""
    entity_a: Entity
    entity_b: Entity
    normal_x: float
    normal_y: float
    penetration: float


class SpatialGrid:
    """
    Simple spatial partitioning grid for broad-phase collision.
    
    Divides the arena into cells and only tests collisions
    between entities in the same or adjacent cells.
    """
    
    def __init__(self, width: float, height: float, cell_size: float = 100):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cols = max(1, int(math.ceil(width / cell_size)))
        self.rows = max(1, int(math.ceil(height / cell_size)))
        self.cells: Dict[Tuple[int, int], List[Entity]] = {}
        self.entity_cells: Dict[str, List[Tuple[int, int]]] = {}
    
    def clear(self) -> None:
        """Clear all entities from the grid."""
        self.cells.clear()
        self.entity_cells.clear()
    
    def insert(self, entity: Entity, x: float, y: float, radius: float) -> None:
        """Insert an entity into the grid based on its bounds."""
        # Convert to grid coordinates (offset by half arena size)
        min_col = int((x - radius + self.width/2) / self.cell_size)
        max_col = int((x + radius + self.width/2) / self.cell_size)
        min_row = int((y - radius + self.height/2) / self.cell_size)
        max_row = int((y + radius + self.height/2) / self.cell_size)
        
        # Clamp to grid bounds
        min_col = max(0, min(self.cols - 1, min_col))
        max_col = max(0, min(self.cols - 1, max_col))
        min_row = max(0, min(self.rows - 1, min_row))
        max_row = max(0, min(self.rows - 1, max_row))
        
        entity_cell_list = []
        for col in range(min_col, max_col + 1):
            for row in range(min_row, max_row + 1):
                cell_key = (col, row)
                if cell_key not in self.cells:
                    self.cells[cell_key] = []
                self.cells[cell_key].append(entity)
                entity_cell_list.append(cell_key)
        
        self.entity_cells[entity.id] = entity_cell_list
    
    def get_potential_collisions(self, entity: Entity) -> Set[Entity]:
        """Get all entities that might be colliding with this one."""
        potential = set()
        cells = self.entity_cells.get(entity.id, [])
        for cell_key in cells:
            for other in self.cells.get(cell_key, []):
                if other.id != entity.id:
                    potential.add(other)
        return potential


class CollisionSystem(GameSystem):
    """
    Handles collision detection and response.
    
    Features:
    - Spatial partitioning for performance
    - Circle-circle and AABB collision
    - Collision masks for filtering
    - Trigger vs. solid collisions
    - Collision response (separation)
    - CollisionEvent emission
    """
    
    def __init__(self, arena_width: float = 800, arena_height: float = 600):
        super().__init__(priority=SystemPriority.COLLISION)
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.spatial_grid = SpatialGrid(arena_width, arena_height, cell_size=80)
        self._collision_pairs: List[CollisionPair] = []
    
    def update(self, dt: float) -> None:
        """Run collision detection and response."""
        self._collision_pairs.clear()
        
        # Rebuild spatial grid
        self.spatial_grid.clear()
        
        collidable_entities = list(self.entities.get_entities_with(Transform, Collider))
        
        # Insert all entities into spatial grid
        for entity in collidable_entities:
            transform = self.entities.get_component(entity, Transform)
            collider = self.entities.get_component(entity, Collider)
            if transform and collider:
                radius = self._get_effective_radius(collider)
                self.spatial_grid.insert(entity, transform.x, transform.y, radius)
        
        # Broad phase + narrow phase
        tested_pairs: Set[Tuple[str, str]] = set()
        
        for entity_a in collidable_entities:
            potential = self.spatial_grid.get_potential_collisions(entity_a)
            
            for entity_b in potential:
                # Avoid duplicate pair testing
                pair_key = tuple(sorted([entity_a.id, entity_b.id]))
                if pair_key in tested_pairs:
                    continue
                tested_pairs.add(pair_key)
                
                # Check collision
                collision = self._test_collision(entity_a, entity_b)
                if collision:
                    self._collision_pairs.append(collision)
        
        # Reset collision states
        for entity in collidable_entities:
            collider = self.entities.get_component(entity, Collider)
            if collider:
                collider.is_colliding = False
                collider.collision_count = 0
        
        # Process collision pairs
        for pair in self._collision_pairs:
            self._resolve_collision(pair)
    
    def _get_effective_radius(self, collider: Collider) -> float:
        """Get the radius for spatial partitioning."""
        if collider.collider_type == ColliderType.CIRCLE:
            return collider.radius
        else:
            return max(collider.width, collider.height) / 2
    
    def _test_collision(self, entity_a: Entity, entity_b: Entity) -> CollisionPair | None:
        """Test if two entities are colliding."""
        collider_a = self.entities.get_component(entity_a, Collider)
        collider_b = self.entities.get_component(entity_b, Collider)
        transform_a = self.entities.get_component(entity_a, Transform)
        transform_b = self.entities.get_component(entity_b, Transform)
        
        if not all([collider_a, collider_b, transform_a, transform_b]):
            return None
        
        # Check collision masks
        if not collider_a.should_collide_with(collider_b):
            return None
        
        # Get world positions
        ax = transform_a.x + collider_a.offset_x
        ay = transform_a.y + collider_a.offset_y
        bx = transform_b.x + collider_b.offset_x
        by = transform_b.y + collider_b.offset_y
        
        # Test based on collider types
        if (collider_a.collider_type == ColliderType.CIRCLE and 
            collider_b.collider_type == ColliderType.CIRCLE):
            return self._test_circle_circle(
                entity_a, entity_b,
                ax, ay, collider_a.radius,
                bx, by, collider_b.radius
            )
        elif (collider_a.collider_type == ColliderType.AABB and
              collider_b.collider_type == ColliderType.AABB):
            return self._test_aabb_aabb(
                entity_a, entity_b,
                ax, ay, collider_a.width, collider_a.height,
                bx, by, collider_b.width, collider_b.height
            )
        else:
            # Mixed: circle vs AABB
            if collider_a.collider_type == ColliderType.CIRCLE:
                return self._test_circle_aabb(
                    entity_a, entity_b,
                    ax, ay, collider_a.radius,
                    bx, by, collider_b.width, collider_b.height
                )
            else:
                result = self._test_circle_aabb(
                    entity_b, entity_a,
                    bx, by, collider_b.radius,
                    ax, ay, collider_a.width, collider_a.height
                )
                if result:
                    # Swap entities in result
                    return CollisionPair(
                        entity_a=entity_a,
                        entity_b=entity_b,
                        normal_x=-result.normal_x,
                        normal_y=-result.normal_y,
                        penetration=result.penetration
                    )
                return None
    
    def _test_circle_circle(
        self,
        entity_a: Entity, entity_b: Entity,
        ax: float, ay: float, ar: float,
        bx: float, by: float, br: float
    ) -> CollisionPair | None:
        """Test circle-circle collision."""
        dx = bx - ax
        dy = by - ay
        dist_sq = dx * dx + dy * dy
        radius_sum = ar + br
        
        if dist_sq >= radius_sum * radius_sum:
            return None
        
        dist = math.sqrt(dist_sq) if dist_sq > 0 else 0.001
        penetration = radius_sum - dist
        
        # Normal from A to B
        nx = dx / dist if dist > 0 else 1.0
        ny = dy / dist if dist > 0 else 0.0
        
        return CollisionPair(
            entity_a=entity_a,
            entity_b=entity_b,
            normal_x=nx,
            normal_y=ny,
            penetration=penetration
        )
    
    def _test_aabb_aabb(
        self,
        entity_a: Entity, entity_b: Entity,
        ax: float, ay: float, aw: float, ah: float,
        bx: float, by: float, bw: float, bh: float
    ) -> CollisionPair | None:
        """Test AABB-AABB collision."""
        ahw, ahh = aw / 2, ah / 2
        bhw, bhh = bw / 2, bh / 2
        
        # Check overlap
        dx = bx - ax
        dy = by - ay
        overlap_x = ahw + bhw - abs(dx)
        overlap_y = ahh + bhh - abs(dy)
        
        if overlap_x <= 0 or overlap_y <= 0:
            return None
        
        # Use minimum overlap axis as collision normal
        if overlap_x < overlap_y:
            nx = 1.0 if dx > 0 else -1.0
            ny = 0.0
            penetration = overlap_x
        else:
            nx = 0.0
            ny = 1.0 if dy > 0 else -1.0
            penetration = overlap_y
        
        return CollisionPair(
            entity_a=entity_a,
            entity_b=entity_b,
            normal_x=nx,
            normal_y=ny,
            penetration=penetration
        )
    
    def _test_circle_aabb(
        self,
        circle_entity: Entity, aabb_entity: Entity,
        cx: float, cy: float, cr: float,
        bx: float, by: float, bw: float, bh: float
    ) -> CollisionPair | None:
        """Test circle-AABB collision.
        
        Normal convention: points FROM entity_a (circle) TOWARD entity_b (AABB).
        In separation, A moves by: A.pos -= normal * penetration, 
        which pushes A AWAY from B.
        """
        bhw, bhh = bw / 2, bh / 2
        
        # Find closest point on AABB to circle center
        closest_x = max(bx - bhw, min(cx, bx + bhw))
        closest_y = max(by - bhh, min(cy, by + bhh))
        
        dx = cx - closest_x
        dy = cy - closest_y
        dist_sq = dx * dx + dy * dy
        
        # Check if circle center is inside AABB (dist_sq == 0)
        if dist_sq < 0.0001:  # Circle center is inside AABB
            # Find minimum distance to push circle out to nearest edge
            dist_to_left = cx - (bx - bhw)
            dist_to_right = (bx + bhw) - cx
            dist_to_bottom = cy - (by - bhh)
            dist_to_top = (by + bhh) - cy
            
            min_dist = min(dist_to_left, dist_to_right, dist_to_bottom, dist_to_top)
            
            # Normal points from circle TOWARD the AABB interior (from A to B)
            # Separation: A.x -= nx * pen pushes circle OUT through nearest edge
            if min_dist == dist_to_left:
                # Exit left: circle moves left (-x), so normal points right (+x)
                nx, ny = 1.0, 0.0
                penetration = dist_to_left + cr
            elif min_dist == dist_to_right:
                # Exit right: circle moves right (+x), so normal points left (-x)
                nx, ny = -1.0, 0.0
                penetration = dist_to_right + cr
            elif min_dist == dist_to_bottom:
                # Exit down: circle moves down (-y), so normal points up (+y)
                nx, ny = 0.0, 1.0
                penetration = dist_to_bottom + cr
            else:
                # Exit up: circle moves up (+y), so normal points down (-y)
                nx, ny = 0.0, -1.0
                penetration = dist_to_top + cr
            
            return CollisionPair(
                entity_a=circle_entity,
                entity_b=aabb_entity,
                normal_x=nx,
                normal_y=ny,
                penetration=penetration
            )
        
        if dist_sq >= cr * cr:
            return None
        
        dist = math.sqrt(dist_sq)
        penetration = cr - dist
        
        # Normal from circle to closest point on AABB (from A toward B)
        # dx, dy point from closest_point toward circle, so negate for A->B direction
        nx = -dx / dist
        ny = -dy / dist
        
        return CollisionPair(
            entity_a=circle_entity,
            entity_b=aabb_entity,
            normal_x=nx,
            normal_y=ny,
            penetration=penetration
        )
    
    def _resolve_collision(self, pair: CollisionPair) -> None:
        """Handle collision response and events."""
        collider_a = self.entities.get_component(pair.entity_a, Collider)
        collider_b = self.entities.get_component(pair.entity_b, Collider)
        
        if not collider_a or not collider_b:
            return
        
        # Update collision states
        collider_a.is_colliding = True
        collider_b.is_colliding = True
        collider_a.collision_count += 1
        collider_b.collision_count += 1
        
        # Emit collision event
        self.events.emit(CollisionEvent(
            entity_a_id=pair.entity_a.id,
            entity_b_id=pair.entity_b.id,
            normal_x=pair.normal_x,
            normal_y=pair.normal_y,
            penetration=pair.penetration
        ))
        
        # Physical response (only for non-triggers)
        if collider_a.is_trigger or collider_b.is_trigger:
            return
        
        # Separate overlapping entities
        self._separate_entities(pair, collider_a, collider_b)
    
    def _separate_entities(
        self,
        pair: CollisionPair,
        collider_a: Collider,
        collider_b: Collider
    ) -> None:
        """Push overlapping entities apart."""
        transform_a = self.entities.get_component(pair.entity_a, Transform)
        transform_b = self.entities.get_component(pair.entity_b, Transform)
        
        if not transform_a or not transform_b:
            return
        
        # Determine how much each entity moves
        if collider_a.is_static and collider_b.is_static:
            return  # Neither can move
        
        if collider_a.is_static:
            # Only B moves
            transform_b.x += pair.normal_x * pair.penetration
            transform_b.y += pair.normal_y * pair.penetration
        elif collider_b.is_static:
            # Only A moves
            transform_a.x -= pair.normal_x * pair.penetration
            transform_a.y -= pair.normal_y * pair.penetration
        else:
            # Both move equally
            half_pen = pair.penetration / 2
            transform_a.x -= pair.normal_x * half_pen
            transform_a.y -= pair.normal_y * half_pen
            transform_b.x += pair.normal_x * half_pen
            transform_b.y += pair.normal_y * half_pen
        
        # Apply velocity response (bounce)
        self._apply_bounce(pair, collider_a, collider_b)
    
    def _apply_bounce(
        self,
        pair: CollisionPair,
        collider_a: Collider,
        collider_b: Collider
    ) -> None:
        """Apply bounce/velocity response."""
        physics_a = self.entities.get_component(pair.entity_a, Physics)
        physics_b = self.entities.get_component(pair.entity_b, Physics)
        velocity_a = self.entities.get_component(pair.entity_a, Velocity)
        velocity_b = self.entities.get_component(pair.entity_b, Velocity)
        
        bounce_a = physics_a.bounce if physics_a else 0.0
        bounce_b = physics_b.bounce if physics_b else 0.0
        avg_bounce = (bounce_a + bounce_b) / 2
        
        if avg_bounce <= 0:
            return
        
        # Reflect velocity along collision normal
        if velocity_a and not collider_a.is_static:
            dot_a = velocity_a.vx * pair.normal_x + velocity_a.vy * pair.normal_y
            if dot_a < 0:  # Moving toward collision
                velocity_a.vx -= (1 + avg_bounce) * dot_a * pair.normal_x
                velocity_a.vy -= (1 + avg_bounce) * dot_a * pair.normal_y
        
        if velocity_b and not collider_b.is_static:
            dot_b = velocity_b.vx * (-pair.normal_x) + velocity_b.vy * (-pair.normal_y)
            if dot_b < 0:
                velocity_b.vx -= (1 + avg_bounce) * dot_b * (-pair.normal_x)
                velocity_b.vy -= (1 + avg_bounce) * dot_b * (-pair.normal_y)
    
    def get_collisions_for(self, entity: Entity) -> List[CollisionPair]:
        """Get all collisions involving a specific entity."""
        return [p for p in self._collision_pairs 
                if p.entity_a == entity or p.entity_b == entity]
    
    def set_arena_size(self, width: float, height: float) -> None:
        """Update arena dimensions."""
        self.arena_width = width
        self.arena_height = height
        self.spatial_grid = SpatialGrid(width, height, cell_size=80)
