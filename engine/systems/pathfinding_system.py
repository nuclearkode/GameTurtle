"""
Pathfinding System

Manages grid-based pathfinding for AI entities.
"""

from engine.core.system import GameSystem
from engine.core.component import AIBrain, Transform, Wall
from engine.utils.pathfinding import Grid, astar, simplify_path
from typing import Optional


class PathfindingSystem(GameSystem):
    """
    Provides pathfinding services for AI entities.
    
    Responsibilities:
    - Maintain grid representation of the arena
    - Update blocked cells based on walls
    - Compute paths on request
    - Cache paths for performance
    """
    
    def __init__(self, entity_manager, priority: int = 50):
        super().__init__(entity_manager, priority)
        
        # Create pathfinding grid
        self.grid = Grid(-400, 400, -300, 300, cell_size=30)
        
        # Path cache: (start_grid, goal_grid) -> path
        self.path_cache = {}
        self.cache_size_limit = 100
        
        # Update grid periodically, not every frame
        self.update_interval = 0.5  # seconds
        self.time_since_update = 0.0
    
    def update(self, dt: float) -> None:
        """Update grid and process pathfinding requests."""
        self.time_since_update += dt
        
        # Update grid periodically
        if self.time_since_update >= self.update_interval:
            self._update_grid()
            self.time_since_update = 0.0
    
    def _update_grid(self) -> None:
        """Update grid based on current wall positions."""
        # Clear old blocked cells
        self.grid.clear_blocked()
        
        # Mark cells occupied by walls as blocked
        walls = self.entity_manager.query_entities(Wall, Transform)
        
        for wall_entity in walls:
            transform = wall_entity.get_component(Transform)
            wall = wall_entity.get_component(Wall)
            
            if wall.blocks_movement:
                # Mark grid cell at wall position as blocked
                grid_x, grid_y = self.grid.world_to_grid(transform.x, transform.y)
                self.grid.block_cell(grid_x, grid_y)
                
                # Block neighboring cells too (walls are larger than a single cell)
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        self.grid.block_cell(grid_x + dx, grid_y + dy)
    
    def find_path(self, start_x: float, start_y: float, 
                  goal_x: float, goal_y: float) -> Optional[list]:
        """
        Find path from start to goal in world coordinates.
        
        Returns:
            List of world coordinates [(x, y), ...] or None if no path.
        """
        # Convert to grid coordinates
        start_grid = self.grid.world_to_grid(start_x, start_y)
        goal_grid = self.grid.world_to_grid(goal_x, goal_y)
        
        # Check cache
        cache_key = (start_grid, goal_grid)
        if cache_key in self.path_cache:
            return self.path_cache[cache_key]
        
        # Compute path
        grid_path = astar(self.grid, start_grid, goal_grid)
        
        if not grid_path:
            return None
        
        # Simplify path
        grid_path = simplify_path(grid_path, max_points=8)
        
        # Convert to world coordinates
        world_path = [
            self.grid.grid_to_world(gx, gy)
            for gx, gy in grid_path
        ]
        
        # Cache result
        self._cache_path(cache_key, world_path)
        
        return world_path
    
    def _cache_path(self, key: tuple, path: list) -> None:
        """Add path to cache with size limit."""
        self.path_cache[key] = path
        
        # Remove oldest entries if cache is too large
        if len(self.path_cache) > self.cache_size_limit:
            # Simple FIFO eviction
            keys_to_remove = list(self.path_cache.keys())[:10]
            for k in keys_to_remove:
                del self.path_cache[k]
    
    def clear_cache(self) -> None:
        """Clear the path cache."""
        self.path_cache.clear()
