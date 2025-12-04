"""
Pathfinding System - Grid-based A* pathfinding for AI navigation.

Provides pathfinding capabilities for AI entities that need
to navigate around obstacles.
"""

from __future__ import annotations
import heapq
import math
from typing import TYPE_CHECKING, List, Tuple, Optional, Set, Dict
from dataclasses import dataclass, field

from ..core.system import GameSystem, SystemPriority
from ..components.transform import Transform
from ..components.collider import Collider, CollisionMask
from ..components.tags import ObstacleTag

if TYPE_CHECKING:
    from ..core.entity import Entity


@dataclass
class PathNode:
    """A node in the pathfinding grid."""
    x: int
    y: int
    g_cost: float = float('inf')  # Cost from start
    h_cost: float = 0.0  # Heuristic cost to goal
    parent: Optional["PathNode"] = None
    walkable: bool = True
    
    @property
    def f_cost(self) -> float:
        return self.g_cost + self.h_cost
    
    def __lt__(self, other: "PathNode") -> bool:
        return self.f_cost < other.f_cost
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, PathNode):
            return self.x == other.x and self.y == other.y
        return False
    
    def __hash__(self) -> int:
        return hash((self.x, self.y))


class PathfindingGrid:
    """
    Grid representation of the arena for pathfinding.
    
    Uses A* algorithm for pathfinding.
    """
    
    def __init__(
        self,
        width: float,
        height: float,
        cell_size: float = 30.0
    ):
        self.world_width = width
        self.world_height = height
        self.cell_size = cell_size
        
        self.cols = int(math.ceil(width / cell_size))
        self.rows = int(math.ceil(height / cell_size))
        
        # Grid of walkable flags
        self.grid: List[List[bool]] = [
            [True for _ in range(self.cols)]
            for _ in range(self.rows)
        ]
    
    def world_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates to grid coordinates."""
        gx = int((x + self.world_width / 2) / self.cell_size)
        gy = int((y + self.world_height / 2) / self.cell_size)
        return (
            max(0, min(self.cols - 1, gx)),
            max(0, min(self.rows - 1, gy))
        )
    
    def grid_to_world(self, gx: int, gy: int) -> Tuple[float, float]:
        """Convert grid coordinates to world coordinates (center of cell)."""
        x = (gx + 0.5) * self.cell_size - self.world_width / 2
        y = (gy + 0.5) * self.cell_size - self.world_height / 2
        return (x, y)
    
    def is_walkable(self, gx: int, gy: int) -> bool:
        """Check if a grid cell is walkable."""
        if gx < 0 or gx >= self.cols or gy < 0 or gy >= self.rows:
            return False
        return self.grid[gy][gx]
    
    def set_walkable(self, gx: int, gy: int, walkable: bool) -> None:
        """Set whether a grid cell is walkable."""
        if 0 <= gx < self.cols and 0 <= gy < self.rows:
            self.grid[gy][gx] = walkable
    
    def clear(self) -> None:
        """Reset all cells to walkable."""
        for row in self.grid:
            for i in range(len(row)):
                row[i] = True
    
    def mark_obstacle(self, x: float, y: float, radius: float) -> None:
        """Mark cells covered by a circular obstacle as unwalkable."""
        gx, gy = self.world_to_grid(x, y)
        cells_radius = int(math.ceil(radius / self.cell_size)) + 1
        
        for dy in range(-cells_radius, cells_radius + 1):
            for dx in range(-cells_radius, cells_radius + 1):
                cx, cy = gx + dx, gy + dy
                if 0 <= cx < self.cols and 0 <= cy < self.rows:
                    # Check if cell center is within obstacle radius
                    wx, wy = self.grid_to_world(cx, cy)
                    dist = math.sqrt((wx - x)**2 + (wy - y)**2)
                    if dist < radius + self.cell_size * 0.5:
                        self.grid[cy][cx] = False
    
    def get_neighbors(self, gx: int, gy: int) -> List[Tuple[int, int]]:
        """Get walkable neighboring cells."""
        neighbors = []
        # 8-directional movement
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = gx + dx, gy + dy
                if self.is_walkable(nx, ny):
                    # For diagonal movement, check if we can actually move there
                    if dx != 0 and dy != 0:
                        if not self.is_walkable(gx + dx, gy) or not self.is_walkable(gx, gy + dy):
                            continue
                    neighbors.append((nx, ny))
        return neighbors
    
    def find_path(
        self,
        start_x: float,
        start_y: float,
        goal_x: float,
        goal_y: float,
        max_iterations: int = 500
    ) -> Optional[List[Tuple[float, float]]]:
        """
        Find a path from start to goal using A*.
        
        Returns:
            List of waypoints in world coordinates, or None if no path found
        """
        start_gx, start_gy = self.world_to_grid(start_x, start_y)
        goal_gx, goal_gy = self.world_to_grid(goal_x, goal_y)
        
        # Quick check for direct line of sight
        if self._has_line_of_sight(start_gx, start_gy, goal_gx, goal_gy):
            return [(goal_x, goal_y)]
        
        # A* algorithm
        open_set: List[PathNode] = []
        closed_set: Set[Tuple[int, int]] = set()
        nodes: Dict[Tuple[int, int], PathNode] = {}
        
        start_node = PathNode(start_gx, start_gy, g_cost=0)
        start_node.h_cost = self._heuristic(start_gx, start_gy, goal_gx, goal_gy)
        nodes[(start_gx, start_gy)] = start_node
        heapq.heappush(open_set, start_node)
        
        iterations = 0
        
        while open_set and iterations < max_iterations:
            iterations += 1
            current = heapq.heappop(open_set)
            
            if (current.x, current.y) in closed_set:
                continue
            
            closed_set.add((current.x, current.y))
            
            # Goal reached?
            if current.x == goal_gx and current.y == goal_gy:
                return self._reconstruct_path(current)
            
            # Explore neighbors
            for nx, ny in self.get_neighbors(current.x, current.y):
                if (nx, ny) in closed_set:
                    continue
                
                # Calculate movement cost (diagonal is more expensive)
                dx = abs(nx - current.x)
                dy = abs(ny - current.y)
                move_cost = 1.414 if (dx + dy == 2) else 1.0
                new_g = current.g_cost + move_cost
                
                neighbor = nodes.get((nx, ny))
                if neighbor is None:
                    neighbor = PathNode(nx, ny)
                    neighbor.h_cost = self._heuristic(nx, ny, goal_gx, goal_gy)
                    nodes[(nx, ny)] = neighbor
                
                if new_g < neighbor.g_cost:
                    neighbor.g_cost = new_g
                    neighbor.parent = current
                    heapq.heappush(open_set, neighbor)
        
        # No path found
        return None
    
    def _heuristic(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Octile distance heuristic."""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        return max(dx, dy) + 0.414 * min(dx, dy)
    
    def _has_line_of_sight(
        self,
        x1: int, y1: int,
        x2: int, y2: int
    ) -> bool:
        """Check if there's a clear line of sight between two grid cells."""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        
        while True:
            if not self.is_walkable(x, y):
                return False
            
            if x == x2 and y == y2:
                return True
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    def _reconstruct_path(self, node: PathNode) -> List[Tuple[float, float]]:
        """Reconstruct path from goal node back to start."""
        path = []
        current = node
        
        while current is not None:
            wx, wy = self.grid_to_world(current.x, current.y)
            path.append((wx, wy))
            current = current.parent
        
        path.reverse()
        
        # Smooth path by removing unnecessary waypoints
        return self._smooth_path(path)
    
    def _smooth_path(self, path: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Remove redundant waypoints from path."""
        if len(path) <= 2:
            return path
        
        smoothed = [path[0]]
        
        for i in range(1, len(path) - 1):
            # Check if we can skip this waypoint
            prev = smoothed[-1]
            curr = path[i]
            next_pt = path[i + 1]
            
            gx1, gy1 = self.world_to_grid(prev[0], prev[1])
            gx2, gy2 = self.world_to_grid(next_pt[0], next_pt[1])
            
            if not self._has_line_of_sight(gx1, gy1, gx2, gy2):
                smoothed.append(curr)
        
        smoothed.append(path[-1])
        return smoothed


class PathfindingSystem(GameSystem):
    """
    Provides pathfinding services for AI entities.
    
    Features:
    - Grid-based A* pathfinding
    - Obstacle detection and grid updates
    - Path caching
    - Line-of-sight checks
    """
    
    def __init__(
        self,
        arena_width: float = 800,
        arena_height: float = 600,
        cell_size: float = 30.0
    ):
        super().__init__(priority=SystemPriority.AI - 1)  # Before AI
        self.grid = PathfindingGrid(arena_width, arena_height, cell_size)
        
        # Path cache
        self._path_cache: Dict[str, List[Tuple[float, float]]] = {}
        self._cache_timer = 0.0
        self._cache_interval = 0.5  # Recalculate paths every 0.5s
    
    def update(self, dt: float) -> None:
        """Update grid with obstacle positions."""
        # Periodically rebuild grid
        self._cache_timer += dt
        if self._cache_timer >= self._cache_interval:
            self._cache_timer = 0.0
            self._rebuild_grid()
            self._path_cache.clear()
    
    def _rebuild_grid(self) -> None:
        """Rebuild the pathfinding grid from obstacles."""
        self.grid.clear()
        
        for entity in self.entities.get_entities_with(Transform, Collider, ObstacleTag):
            transform = self.entities.get_component(entity, Transform)
            collider = self.entities.get_component(entity, Collider)
            
            if transform and collider:
                self.grid.mark_obstacle(
                    transform.x,
                    transform.y,
                    collider.radius if collider.radius > 0 else max(collider.width, collider.height) / 2
                )
    
    def find_path(
        self,
        start_x: float,
        start_y: float,
        goal_x: float,
        goal_y: float,
        entity_id: str = ""
    ) -> Optional[List[Tuple[float, float]]]:
        """
        Find a path from start to goal.
        
        Args:
            start_x, start_y: Starting position
            goal_x, goal_y: Goal position
            entity_id: Optional entity ID for caching
            
        Returns:
            List of waypoints, or None if no path exists
        """
        # Check cache
        if entity_id and entity_id in self._path_cache:
            return self._path_cache[entity_id]
        
        path = self.grid.find_path(start_x, start_y, goal_x, goal_y)
        
        # Cache result
        if entity_id and path:
            self._path_cache[entity_id] = path
        
        return path
    
    def has_line_of_sight(
        self,
        x1: float, y1: float,
        x2: float, y2: float
    ) -> bool:
        """Check if there's line of sight between two points."""
        gx1, gy1 = self.grid.world_to_grid(x1, y1)
        gx2, gy2 = self.grid.world_to_grid(x2, y2)
        return self.grid._has_line_of_sight(gx1, gy1, gx2, gy2)
    
    def is_walkable(self, x: float, y: float) -> bool:
        """Check if a world position is walkable."""
        gx, gy = self.grid.world_to_grid(x, y)
        return self.grid.is_walkable(gx, gy)
    
    def set_arena_size(self, width: float, height: float) -> None:
        """Update arena dimensions."""
        self.grid = PathfindingGrid(width, height, self.grid.cell_size)
