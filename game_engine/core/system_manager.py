"""SystemManager: manages systems and calls them in priority order."""

from typing import List
from .system import GameSystem


class SystemManager:
    """Manages game systems and their update order."""
    
    def __init__(self):
        self._systems: List[GameSystem] = []
        self._sorted = False
    
    def register_system(self, system: GameSystem):
        """Register a system."""
        if system not in self._systems:
            self._systems.append(system)
            self._sorted = False
    
    def unregister_system(self, system: GameSystem):
        """Unregister a system."""
        if system in self._systems:
            self._systems.remove(system)
    
    def update_all(self, dt: float):
        """Update all systems in priority order."""
        if not self._sorted:
            self._systems.sort(key=lambda s: s.priority)
            self._sorted = True
        
        for system in self._systems:
            if system.enabled:
                system.update(dt)
    
    def get_systems(self) -> List[GameSystem]:
        """Get all registered systems."""
        return self._systems.copy()
