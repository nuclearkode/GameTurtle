"""
Pathfinding utilities using A* algorithm.
"""

import heapq
from typing import List, Tuple, Set, Optional
import math


class Grid:
    """
    Grid representation for pathfinding.
    """
    
    def __init__(self, min_x: float, max_x: float, min_y: float, max_y: float, cell_size: float = 20):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y
        self.cell_size = cell_size
        
        # Calculate grid dimensions
        self.width = int((max_x - min_x) / cell_size) + 1
        self.height = int((max_y - min_y) / cell_size) + 1
        
        # Blocked cells (set of (grid_x, grid_y) tuples)
        self.blocked: Set[Tuple[int, int]] = set()
    
    def world_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates to grid coordinates."""
        grid_x = int((x - self.min_x) / self.cell_size)
        grid_y = int((y - self.min_y) / self.cell_size)
        return grid_x, grid_y
    
    def grid_to_world(self, grid_x: int, grid_y: int) -> Tuple[float, float]:
        """Convert grid coordinates to world coordinates (cell center)."""
        x = self.min_x + grid_x * self.cell_size + self.cell_size / 2
        y = self.min_y + grid_y * self.cell_size + self.cell_size / 2
        return x, y
    
    def is_valid(self, grid_x: int, grid_y: int) -> bool:
        """Check if grid coordinates are valid and not blocked."""
        if grid_x < 0 or grid_x >= self.width:
            return False
        if grid_y < 0 or grid_y >= self.height:
            return False
        return (grid_x, grid_y) not in self.blocked
    
    def block_cell(self, grid_x: int, grid_y: int) -> None:
        """Mark a cell as blocked."""
        self.blocked.add((grid_x, grid_y))
    
    def unblock_cell(self, grid_x: int, grid_y: int) -> None:
        """Mark a cell as unblocked."""
        self.blocked.discard((grid_x, grid_y))
    
    def clear_blocked(self) -> None:
        """Clear all blocked cells."""
        self.blocked.clear()


def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    """Manhattan distance heuristic."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid: Grid, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
    """
    A* pathfinding algorithm.
    
    Args:
        grid: Grid object
        start: Start grid coordinates (grid_x, grid_y)
        goal: Goal grid coordinates (grid_x, grid_y)
    
    Returns:
        List of grid coordinates forming the path, or None if no path exists.
    """
    # Check if start and goal are valid
    if not grid.is_valid(start[0], start[1]) or not grid.is_valid(goal[0], goal[1]):
        return None
    
    # Priority queue: (f_score, counter, node)
    # counter ensures consistent ordering when f_scores are equal
    counter = 0
    open_set = [(0, counter, start)]
    counter += 1
    
    # Track visited nodes
    came_from = {}
    
    # Cost from start to node
    g_score = {start: 0}
    
    # Estimated total cost
    f_score = {start: heuristic(start, goal)}
    
    # Nodes in open set (for fast membership testing)
    open_set_hash = {start}
    
    # Directions: up, down, left, right, and diagonals
    directions = [
        (0, 1), (0, -1), (1, 0), (-1, 0),
        (1, 1), (1, -1), (-1, 1), (-1, -1)
    ]
    
    while open_set:
        _, _, current = heapq.heappop(open_set)
        
        if current not in open_set_hash:
            continue
        open_set_hash.remove(current)
        
        # Goal reached
        if current == goal:
            return _reconstruct_path(came_from, current)
        
        # Explore neighbors
        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)
            
            if not grid.is_valid(neighbor[0], neighbor[1]):
                continue
            
            # Cost to move (diagonal = sqrt(2), straight = 1)
            move_cost = 1.414 if dx != 0 and dy != 0 else 1.0
            tentative_g_score = g_score[current] + move_cost
            
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                # This path to neighbor is better
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                
                if neighbor not in open_set_hash:
                    heapq.heappush(open_set, (f_score[neighbor], counter, neighbor))
                    counter += 1
                    open_set_hash.add(neighbor)
    
    # No path found
    return None


def _reconstruct_path(came_from: dict, current: Tuple[int, int]) -> List[Tuple[int, int]]:
    """Reconstruct path from came_from map."""
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def simplify_path(path: List[Tuple[int, int]], max_points: int = 10) -> List[Tuple[int, int]]:
    """
    Simplify a path by keeping only key waypoints.
    
    Useful for reducing the number of waypoints while maintaining path shape.
    """
    if not path or len(path) <= max_points:
        return path
    
    # Simple approach: sample evenly along path
    step = len(path) / max_points
    simplified = [path[0]]  # Always keep start
    
    for i in range(1, max_points - 1):
        index = int(i * step)
        simplified.append(path[index])
    
    simplified.append(path[-1])  # Always keep end
    return simplified
